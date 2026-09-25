# connection_test.py
import os
from dotenv import load_dotenv
from teradataml import create_context, remove_context, get_context

# Load credentials from .env file
load_dotenv()

TD_HOST     = os.getenv("TD_HOST")
TD_USERNAME = os.getenv("TD_USERNAME")
TD_PASSWORD = os.getenv("TD_PASSWORD")
TD_DATABASE = os.getenv("TD_DATABASE")

print(f"Connecting to: {TD_HOST}")
print(f"Username:      {TD_USERNAME}")
print(f"Database:      {TD_DATABASE}")
print(f"Password:      {'*' * len(TD_PASSWORD) if TD_PASSWORD else 'NOT SET'}")

# ── Connect ─────────────────────────────────────────────────────
print("\nConnecting to Vantage...")

context = create_context(
    host=TD_HOST,
    username=TD_USERNAME,
    password=TD_PASSWORD,
    database=TD_DATABASE
)

print("Connected successfully!")
print(f"Context type: {type(context)}")

from teradataml import DataFrame

# ── Query 1: what version am I on? ──────────────────────────────
print("\n--- Database version ---")
from teradataml import execute_sql
result = execute_sql("SELECT InfoKey, InfoData FROM DBC.DBCInfoV")
rows = result.fetchall()
#print(rows)
for row in rows:
    print(f"  {row[0]}: {row[1]}")

# ── Query 2: list tables you own ────────────────────────────────
print("\n--- Your tables ---")
tables_df = DataFrame.from_query("""
    SELECT TableName, TableKind
    FROM DBC.TablesV
    WHERE DatabaseName = 'demo_user'
""")
# Show as pandas for clean printing
print(tables_df.to_pandas())

# ── Query 3: the capability gate from Day 1 ─────────────────────
print("\n--- AI/ML functions available ---")
functions_result = execute_sql("""
    SELECT FunctionName
    FROM DBC.FunctionsV
    WHERE FunctionName IN (
        'TD_VECTORDISTANCE', 'ONNXEMBEDDINGS', 'ONNXPREDICT'
    )
""")
rows = functions_result.fetchall()
print(f"Found {len(rows)} ML functions:")
for row in rows:
    print(f"  ✓ {row[0]}")  

# ── Always disconnect cleanly ────────────────────────────────────
remove_context()
print("\nDisconnected cleanly.")