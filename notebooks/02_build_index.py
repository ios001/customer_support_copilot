# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Chunk docs and build the vector index
# MAGIC Reads Markdown docs from the volume, splits them on `##` headings, writes a `doc_chunks`
# MAGIC Delta table (Change Data Feed on), then creates a Delta-sync vector index with
# MAGIC Databricks-managed embeddings. Re-running is safe: it re-chunks and re-syncs.

# COMMAND ----------

# MAGIC %pip install -U databricks-sdk
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "support_copilot")
dbutils.widgets.text("vs_endpoint", "support-copilot-vs")
dbutils.widgets.text("embedding_model", "databricks-gte-large-en")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
VS_ENDPOINT = dbutils.widgets.get("vs_endpoint")
EMBEDDING_MODEL = dbutils.widgets.get("embedding_model")
FQ = f"{CATALOG}.{SCHEMA}"
CHUNKS_TABLE = f"{FQ}.doc_chunks"
INDEX_NAME = f"{FQ}.doc_chunks_index"
DOCS_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/docs"

# COMMAND ----------

# MAGIC %md ## Chunk
# MAGIC Section-based chunking: each `##` section becomes one chunk, prefixed with the doc title
# MAGIC so the chunk is self-describing. Long sections are split further at ~1,500 characters.

# COMMAND ----------

import hashlib, os, re

MAX_CHARS = 1500

def chunk_markdown(source: str, text: str):
    title_match = re.search(r"^# (.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else source
    for section in re.split(r"(?m)^## ", text)[1:]:
        heading, _, body = section.partition("\n")
        body = body.strip()
        pieces = [body[i:i + MAX_CHARS] for i in range(0, len(body), MAX_CHARS)] or [""]
        for n, piece in enumerate(pieces):
            content = f"{title} — {heading.strip()}\n{piece}"
            chunk_id = hashlib.md5(f"{source}|{heading}|{n}".encode()).hexdigest()
            yield (chunk_id, source, heading.strip(), content)

rows = []
for f in os.listdir(DOCS_PATH):
    if f.endswith(".md"):
        with open(os.path.join(DOCS_PATH, f)) as fh:
            rows.extend(chunk_markdown(f, fh.read()))

df = spark.createDataFrame(rows, "chunk_id STRING, source STRING, section STRING, content STRING")
(df.write.mode("overwrite").option("overwriteSchema", "true")
   .option("delta.enableChangeDataFeed", "true").saveAsTable(CHUNKS_TABLE))
spark.sql(f"ALTER TABLE {CHUNKS_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
print(f"{len(rows)} chunks written to {CHUNKS_TABLE}")
display(spark.table(CHUNKS_TABLE))

# COMMAND ----------

# MAGIC %md ## Vector search endpoint + Delta-sync index

# COMMAND ----------

import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest, EmbeddingSourceColumn, EndpointType,
    PipelineType, VectorIndexType,
)

w = WorkspaceClient()

existing = {e.name for e in w.vector_search_endpoints.list_endpoints()}
if VS_ENDPOINT not in existing:
    print(f"Creating endpoint {VS_ENDPOINT} (can take ~10 min)...")
    w.vector_search_endpoints.create_endpoint_and_wait(name=VS_ENDPOINT, endpoint_type=EndpointType.STANDARD)
else:
    w.vector_search_endpoints.wait_get_endpoint_vector_search_endpoint_online(VS_ENDPOINT)

try:
    w.vector_search_indexes.get_index(INDEX_NAME)
    print("Index exists; triggering sync")
    w.vector_search_indexes.sync_index(INDEX_NAME)
except NotFound:
    print("Creating index...")
    w.vector_search_indexes.create_index(
        name=INDEX_NAME,
        endpoint_name=VS_ENDPOINT,
        primary_key="chunk_id",
        index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=CHUNKS_TABLE,
            pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[EmbeddingSourceColumn(name="content", embedding_model_endpoint_name=EMBEDDING_MODEL)],
            columns_to_sync=["chunk_id", "source", "section", "content"],
        ),
    )

# Wait until ready
for _ in range(60):
    status = w.vector_search_indexes.get_index(INDEX_NAME).status
    print(f"ready={status.ready} rows={status.indexed_row_count} {status.message or ''}")
    if status.ready:
        break
    time.sleep(20)

# COMMAND ----------

# MAGIC %md ## Smoke test retrieval

# COMMAND ----------

resp = w.vector_search_indexes.query_index(
    index_name=INDEX_NAME,
    columns=["source", "section", "content"],
    query_text="why does my export fail with EXP-413",
    num_results=3,
)
cols = [c.name for c in resp.manifest.columns]
for row in resp.result.data_array:
    print(dict(zip(cols, row)))
