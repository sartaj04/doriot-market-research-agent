import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Read database credentials from environment
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Construct the database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
# List of tables to verify
tables = [
    # "companies",
    # "organization_descriptions",
    # "category_groups",
    # "people",
    # "people_descriptions",
    # "degrees",
    # "jobs",
    # "investors",
    # "investments",
    # "investment_partners",
    # "funds",
    "funding_rounds",
    # "org_parents",
    # "ipos",
    # "acquisitions",
    # "events",
    # "event_appearances"
]

# Function to print two rows from each table
def preview_db_data():
    with engine.connect() as conn:
        for table in tables:
            try:
                df = pd.read_sql(f"SELECT * FROM {table} LIMIT 2", conn)
                print(f"\nPreview of {table}:")
                print(df.to_string(index=False))
            except Exception as e:
                print(f"Error retrieving data from {table}: {e}")

# Run the preview function
preview_db_data()
