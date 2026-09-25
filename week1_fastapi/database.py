import os
from dotenv import load_dotenv
from teradataml import create_context, remove_context, execute_sql
import teradatasql

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

def init_db():
    print("\nConnecting to Teradata...")

    create_context(
        host=TD_HOST,
        username=TD_USERNAME,
        password=TD_PASSWORD,
        database=TD_DATABASE
    )

    print("Connected successfully!")

def close_db():
    try:
        remove_context()
        print("\nDisconnected cleanly.")
    except Exception:
        pass   

def get_db():
    try:
        yield execute_sql
    except Exception as e:
        raise e

def get_raw_connection():
    return teradatasql.connect(
        host=TD_HOST,
        user=TD_USERNAME,
        password=TD_PASSWORD,
        database=TD_DATABASE
    )