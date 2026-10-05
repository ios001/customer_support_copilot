"""Central configuration, read from environment variables (set in app.yaml or a local .env)."""
import os

CATALOG = os.environ.get("CATALOG", "main")
SCHEMA = os.environ.get("SCHEMA", "support_copilot")
FQ = f"{CATALOG}.{SCHEMA}"
VS_INDEX = os.environ.get("VS_INDEX", f"{FQ}.doc_chunks_index")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT", "")  # e.g. /Users/you@example.com/support-copilot
TOP_K = int(os.environ.get("TOP_K", "5"))
