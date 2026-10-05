# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Set up data
# MAGIC Creates the schema, a volume of product docs (Markdown), and fake `customers`, `orders`,
# MAGIC `tickets` and `escalations` Delta tables for a fictional SaaS company, "Acme Analytics".

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "support_copilot")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
FQ = f"{CATALOG}.{SCHEMA}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FQ}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {FQ}.docs")
DOCS_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/docs"

# COMMAND ----------

# MAGIC %md ## Product documentation (the RAG corpus)
# MAGIC Replace or extend these with real docs (PDF/HTML) later. Each `##` heading becomes a chunk.

# COMMAND ----------

DOCS = {
"plans_and_pricing.md": """# Plans and Pricing
## Plan overview
Acme Analytics offers three plans: Basic ($29/user/month), Pro ($79/user/month) and Enterprise (custom pricing).
## Basic plan
Basic includes up to 5 dashboards, CSV exports capped at 10,000 rows per export, 7-day query history and email support with a 2 business day response target.
## Pro plan
Pro includes unlimited dashboards, exports up to 1,000,000 rows, 90-day query history, scheduled reports and chat support with a 4 business hour response target.
## Enterprise plan
Enterprise adds SSO/SAML, audit logs, unlimited exports, custom data retention and a dedicated support manager with a 1 hour response target for P1 issues.
## Upgrading and downgrading
Upgrades take effect immediately and are prorated. Downgrades take effect at the start of the next billing cycle.
""",
"exports.md": """# Exporting Data
## Export formats
Data can be exported as CSV, XLSX or Parquet from any table or chart via the Export button.
## Export limits
Export size limits depend on plan: Basic 10,000 rows, Pro 1,000,000 rows, Enterprise unlimited. Exports over the limit fail with error EXP-413.
## Troubleshooting failed exports
Error EXP-413 means the export exceeded the plan row limit; filter the data, split the export by date range, or upgrade the plan. Error EXP-504 means the export timed out after 10 minutes; schedule it as a background export instead.
## Scheduled exports
Pro and Enterprise customers can schedule recurring exports to S3, Azure Blob or Google Cloud Storage.
""",
"sso_setup.md": """# Single Sign-On (SSO)
## Availability
SSO via SAML 2.0 and OIDC is available on the Enterprise plan only.
## Supported identity providers
Okta, Microsoft Entra ID, Google Workspace and OneLogin are supported. Other SAML 2.0 providers usually work but are not officially tested.
## Setup steps
An admin opens Settings > Security > SSO, uploads the IdP metadata XML, maps the email attribute and tests the login before enforcing SSO for all users.
## Common SSO errors
Error SSO-401 means the email attribute is not mapped. Error SSO-409 means the user already exists with a password login; an admin must convert the account.
""",
"billing_and_refunds.md": """# Billing and Refunds
## Billing cycle
Plans are billed monthly or annually in advance. Annual billing receives a 15% discount.
## Payment methods
Credit card is accepted on all plans. Invoicing with net-30 terms is available on Enterprise.
## Refund policy
Monthly plans are non-refundable. Annual plans can be refunded pro rata within the first 30 days. Refunds over $1,000 require approval from the billing team and must be escalated.
## Failed payments
After a failed payment the account enters a 14-day grace period, after which it is downgraded to read-only.
""",
"api_rate_limits.md": """# API and Rate Limits
## API access
The REST API is available on Pro and Enterprise plans. Basic plan accounts receive error API-403 when calling the API.
## Rate limits
Pro: 100 requests per minute. Enterprise: 1,000 requests per minute. Exceeding the limit returns HTTP 429 with a Retry-After header.
## Authentication
API calls use personal access tokens created under Settings > API Tokens. Tokens expire after 90 days by default.
""",
"data_retention.md": """# Data Retention and Deletion
## Query history retention
Query history is kept for 7 days on Basic, 90 days on Pro and is configurable up to 7 years on Enterprise.
## Account deletion
Deleted accounts are recoverable for 30 days, after which all data is permanently removed.
## Data residency
Data is stored in the US by default. Enterprise customers can choose EU or Canada data residency.
""",
"dashboards_troubleshooting.md": """# Dashboard Troubleshooting
## Dashboard not refreshing
Dashboards refresh on the schedule set by their owner. If a dashboard shows stale data, check the data source connection under Settings > Connections.
## Slow dashboards
Dashboards with more than 25 charts load slowly. Split them into multiple dashboards or enable query caching (Pro and Enterprise).
## Dashboard limit reached
Basic plan accounts are limited to 5 dashboards; creating a sixth shows error DSH-402.
""",
}

for name, body in DOCS.items():
    dbutils.fs.put(f"{DOCS_PATH}/{name}", body, overwrite=True)
display(dbutils.fs.ls(DOCS_PATH))

# COMMAND ----------

# MAGIC %md ## Fake operational data (the SQL tool's source)

# COMMAND ----------

import random
from datetime import date, datetime, timedelta

random.seed(42)
first = ["Ava", "Liam", "Noah", "Emma", "Olivia", "Ethan", "Mia", "Lucas", "Amara", "Kenji", "Sofia", "Tunde"]
companies = ["Northwind", "Globex", "Initech", "Umbrella Retail", "Stark Logistics", "Wayne Foods", "Soylent", "Hooli", "Vandelay", "Pied Piper"]
plans = ["Basic", "Pro", "Enterprise"]
regions = ["US", "EU", "Canada"]

customers = []
for cid in range(1001, 1051):
    plan = random.choices(plans, weights=[5, 3, 2])[0]
    customers.append((cid, f"{random.choice(companies)} #{cid}", random.choice(first), plan,
                      random.choice(regions), date(2025, 1, 1) + timedelta(days=random.randint(0, 600))))
# Pin a few customers for demo / eval questions
customers[41] = (1042, "Globex #1042", "Kenji", "Basic", "Canada", date(2025, 6, 3))
customers[6] = (1007, "Hooli #1007", "Amara", "Enterprise", "EU", date(2025, 2, 11))
customers[14] = (1015, "Initech #1015", "Lucas", "Pro", "US", date(2025, 9, 20))

ticket_templates = [
    ("Export failing with EXP-413", "exports"), ("Export timing out", "exports"),
    ("Cannot set up SSO", "sso"), ("Refund request for annual plan", "billing"),
    ("API returns 429", "api"), ("Dashboard not refreshing", "dashboards"),
    ("Payment failed", "billing"), ("Cannot create new dashboard", "dashboards"),
]
tickets, orders = [], []
tid = 5000
for c in customers:
    for _ in range(random.randint(0, 3)):
        subj, cat = random.choice(ticket_templates)
        tid += 1
        tickets.append((tid, c[0], subj, cat, random.choice(["open", "closed"]),
                        datetime(2026, 1, 1) + timedelta(days=random.randint(0, 270))))
    price = {"Basic": 29, "Pro": 79, "Enterprise": 250}[c[3]]
    for m in range(1, 4):
        orders.append((c[0] * 10 + m, c[0], f"{c[3]} subscription", price * random.randint(1, 20),
                       random.choice(["paid", "paid", "paid", "failed"]), date(2026, 6 + m, 1)))

tickets += [
    (6001, 1042, "Export keeps failing with EXP-413", "exports", "open", datetime(2026, 9, 28, 9, 30)),
    (6002, 1007, "Want a refund on annual plan ($4,800)", "billing", "open", datetime(2026, 9, 25, 14, 0)),
    (6003, 1015, "Getting 429 errors from API", "api", "open", datetime(2026, 9, 30, 11, 15)),
]

spark.createDataFrame(customers, "customer_id INT, company STRING, contact_name STRING, plan STRING, region STRING, signup_date DATE") \
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.customers")
spark.createDataFrame(tickets, "ticket_id INT, customer_id INT, subject STRING, category STRING, status STRING, created_at TIMESTAMP") \
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.tickets")
spark.createDataFrame(orders, "order_id INT, customer_id INT, item STRING, amount_usd DOUBLE, status STRING, order_date DATE") \
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.orders")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FQ}.escalations (
  escalation_id STRING, customer_id INT, summary STRING, priority STRING, created_at TIMESTAMP)
""")

display(spark.sql(f"SELECT plan, count(*) AS n FROM {FQ}.customers GROUP BY plan"))
