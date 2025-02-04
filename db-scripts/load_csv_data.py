import pandas as pd
import os
from sqlalchemy import create_engine
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "csv_files")

# Function to import CSV data into the database
def import_csv_to_db(file_path, table_name, chunksize=1000):
    df_iter = pd.read_csv(file_path, chunksize=chunksize)
    for chunk in df_iter:
        chunk.to_sql(table_name, con=engine, if_exists='append', index=False)
    print(f"Data imported successfully into {table_name}")

# List of CSV files and their corresponding tables
csv_files = {
    # "organizations.csv": "companies",
    # "organization_descriptions.csv": "organization_descriptions",
    # "category_groups.csv": "category_groups",
    # "people.csv": "people",
    # "people_descriptions.csv": "people_descriptions",
    # "degrees.csv": "degrees",
    # "jobs.csv": "jobs",
    # "investors.csv": "investors",
    # "investments.csv": "investments",
    # "funds.csv": "funds",
    # "funding_rounds.csv": "funding_rounds",
    # "ipos.csv": "ipos",
    # "acquisitions.csv": "acquisitions",
    # "events.csv": "events",
    # "event_appearances.csv": "event_appearances"
}

# Import all CSV files
for file_name, table in csv_files.items():
    file_path = os.path.join(CSV_DIR, file_name)
    if os.path.exists(file_path):
        try:
            import_csv_to_db(file_path, table)
        except Exception as e:
            print(f"Error importing {file_path} into {table}: {e}")
    else:
        print(f"File not found: {file_path}")


def load_uuid_mapping(table, uuid_column):
    query = f"SELECT {uuid_column} FROM {table}"
    df = pd.read_sql(query, engine)
    return set(df[uuid_column])

# Function to import CSV data into the database
def import_csv_to_db(file_path, table_name):
    df = pd.read_csv(file_path)
    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    print(f"Data imported successfully into {table_name}")

# Load mappings before inserting data
company_uuids = load_uuid_mapping("companies", "uuid")
investor_uuids = load_uuid_mapping("investors", "uuid")
people_uuids = load_uuid_mapping("people", "uuid")
# Import org_parents with UUID to ID mapping
org_parents_file = os.path.join(CSV_DIR, "org_parents.csv")
if os.path.exists(org_parents_file):
    df = pd.read_csv(org_parents_file)
    df = df[df["parent_uuid"].isin(company_uuids) & df["uuid"].isin(company_uuids)]  # Ensure both columns match valid UUIDs
    df.to_sql("org_parents", con=engine, if_exists='append', index=False)
    print("Data imported successfully into org_parents")

# Import investment_partners using UUIDs
investment_partners_file = os.path.join(CSV_DIR, "investment_partners.csv")
if os.path.exists(investment_partners_file):
    df = pd.read_csv(investment_partners_file)
    df = df[df["investor_uuid"].isin(investor_uuids) & df["partner_uuid"].isin(people_uuids)]
    df.to_sql("investment_partners", con=engine, if_exists='append', index=False)
    print("Data imported successfully into investment_partners")

