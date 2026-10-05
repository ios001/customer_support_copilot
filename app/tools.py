"""The agent's three tools, exposed to Claude as an in-process MCP server.

search_docs           -> Databricks vector index (RAG over product docs)
get_customer_context  -> SQL warehouse query over customers / tickets / orders Delta tables
create_escalation     -> INSERT into the escalations Delta table
"""
import json

from claude_agent_sdk import create_sdk_mcp_server, tool
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem, StatementState

from config import FQ, TOP_K, VS_INDEX, WAREHOUSE_ID
from tracing import trace

_ws = None


def ws() -> WorkspaceClient:
    """Databricks client. Uses unified auth: your CLI profile locally, the app's service principal in Databricks Apps."""
    global _ws
    if _ws is None:
        _ws = WorkspaceClient()
    return _ws


def run_sql(statement: str, params: dict | None = None) -> list[dict]:
    if not WAREHOUSE_ID:
        raise RuntimeError("DATABRICKS_WAREHOUSE_ID is not set")
    parameters = [
        StatementParameterListItem(name=k, value=str(v), type="INT" if isinstance(v, int) else "STRING")
        for k, v in (params or {}).items()
    ]
    resp = ws().statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID, statement=statement, parameters=parameters, wait_timeout="30s"
    )
    if resp.status.state != StatementState.SUCCEEDED:
        msg = resp.status.error.message if resp.status.error else resp.status.state
        raise RuntimeError(f"SQL failed: {msg}")
    if not resp.result or not resp.manifest or not resp.manifest.schema:
        return []
    cols = [c.name for c in resp.manifest.schema.columns]
    return [dict(zip(cols, row)) for row in (resp.result.data_array or [])]


def _text(payload) -> dict:
    return {"content": [{"type": "text", "text": payload if isinstance(payload, str) else json.dumps(payload, default=str)}]}


def _error(msg: str) -> dict:
    return {"content": [{"type": "text", "text": f"ERROR: {msg}"}], "is_error": True}


# ---------- core implementations (plain functions: easy to unit-test and to trace) ----------

@trace("search_docs", span_type="RETRIEVER")
async def search_docs_impl(query: str, k: int = TOP_K) -> list[dict]:
    resp = ws().vector_search_indexes.query_index(
        index_name=VS_INDEX, columns=["source", "section", "content"], query_text=query, num_results=k
    )
    cols = [c.name for c in resp.manifest.columns]  # last column is the similarity score
    return [dict(zip(cols, row)) for row in (resp.result.data_array or [])]


@trace("get_customer_context", span_type="TOOL")
async def get_customer_context_impl(customer_id: int) -> dict:
    cust = run_sql(f"SELECT * FROM {FQ}.customers WHERE customer_id = :cid", {"cid": customer_id})
    if not cust:
        return {"error": f"No customer with id {customer_id}"}
    tickets = run_sql(
        f"SELECT ticket_id, subject, category, status, created_at FROM {FQ}.tickets "
        f"WHERE customer_id = :cid ORDER BY created_at DESC LIMIT 5", {"cid": customer_id})
    orders = run_sql(
        f"SELECT order_id, item, amount_usd, status, order_date FROM {FQ}.orders "
        f"WHERE customer_id = :cid ORDER BY order_date DESC LIMIT 5", {"cid": customer_id})
    return {"customer": cust[0], "recent_tickets": tickets, "recent_orders": orders}


@trace("create_escalation", span_type="TOOL")
async def create_escalation_impl(customer_id: int, summary: str, priority: str) -> dict:
    priority = priority.lower()
    if priority not in {"low", "medium", "high"}:
        return {"error": "priority must be low, medium or high"}
    run_sql(
        f"INSERT INTO {FQ}.escalations VALUES (uuid(), :cid, :summary, :priority, current_timestamp())",
        {"cid": customer_id, "summary": summary[:2000], "priority": priority})
    return {"status": "escalation created", "customer_id": customer_id, "priority": priority}


# ---------- tool wrappers exposed to Claude ----------

@tool(
    "search_docs",
    "Search Acme Analytics product documentation (plans, limits, error codes, SSO, billing, API, retention). "
    "Returns relevant passages with their source file. Use for any product or policy question.",
    {"query": str},
)
async def search_docs(args):
    try:
        hits = await search_docs_impl(args["query"])
    except Exception as e:
        return _error(f"search failed: {e}")
    if not hits:
        return _text("No relevant documentation found.")
    # Wrap retrieved text in tags so the model treats it as data, not instructions.
    blocks = [
        f'<document source="{h["source"]}" section="{h["section"]}">\n{h["content"]}\n</document>' for h in hits
    ]
    return _text("\n\n".join(blocks))


@tool(
    "get_customer_context",
    "Look up a customer's account: plan, region, recent support tickets and recent orders/payments.",
    {"customer_id": int},
)
async def get_customer_context(args):
    try:
        return _text(await get_customer_context_impl(int(args["customer_id"])))
    except Exception as e:
        return _error(f"lookup failed: {e}")


@tool(
    "create_escalation",
    "Escalate a case to a human support specialist. Use only when policy requires human approval, "
    "the docs do not answer the question, or the customer is at risk. priority is low, medium or high.",
    {"customer_id": int, "summary": str, "priority": str},
)
async def create_escalation(args):
    try:
        return _text(await create_escalation_impl(int(args["customer_id"]), args["summary"], args["priority"]))
    except Exception as e:
        return _error(f"escalation failed: {e}")


SERVER_NAME = "support"
support_server = create_sdk_mcp_server(
    name=SERVER_NAME, version="1.0.0", tools=[search_docs, get_customer_context, create_escalation]
)
TOOL_NAMES = [f"mcp__{SERVER_NAME}__{n}" for n in ("search_docs", "get_customer_context", "create_escalation")]
