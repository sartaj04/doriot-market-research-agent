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

# SQL script to create tables if they don't exist
def create_tables():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            uuid UUID UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(255),
            permalink VARCHAR(255),
            cb_url TEXT,
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            legal_name VARCHAR(255),
            roles VARCHAR(255),
            domain VARCHAR(255),
            homepage_url TEXT,
            country_code VARCHAR(10),
            state_code VARCHAR(10),
            region VARCHAR(255),
            city VARCHAR(255),
            address TEXT,
            postal_code VARCHAR(50),
            status VARCHAR(100),
            short_description TEXT,
            category_list TEXT,
            category_groups_list TEXT,
            num_funding_rounds INT,
            total_funding_usd BIGINT,
            total_funding BIGINT,
            total_funding_currency_code VARCHAR(10),
            founded_on DATE,
            last_funding_on DATE,
            closed_on DATE,
            employee_count VARCHAR(50),
            email VARCHAR(255),
            phone VARCHAR(50),
            facebook_url TEXT,
            linkedin_url TEXT,
            twitter_url TEXT,
            logo_url TEXT,
            primary_role VARCHAR(255),
            num_exits INT,
            revenue_range VARCHAR(255)
        );
        
        CREATE TABLE IF NOT EXISTS organization_descriptions (
            id SERIAL PRIMARY KEY,
            company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            description TEXT
        );
        
        CREATE TABLE IF NOT EXISTS category_groups (
            id SERIAL PRIMARY KEY,
            company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            uuid UUID UNIQUE NOT NULL,
            name VARCHAR(255),
            type VARCHAR(100),
            permalink VARCHAR(255),
            cb_url TEXT,
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS people (
            id SERIAL PRIMARY KEY,
            uuid UUID UNIQUE NOT NULL,
            name VARCHAR(255),
            type VARCHAR(100),
            permalink VARCHAR(255),
            cb_url TEXT,
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            gender VARCHAR(50),
            country_code VARCHAR(10),
            state_code VARCHAR(10),
            region VARCHAR(255),
            city VARCHAR(255),
            featured_job_organization_uuid UUID,
            featured_job_organization_name VARCHAR(255),
            featured_job_title VARCHAR(255),
            facebook_url TEXT,
            linkedin_url TEXT,
            twitter_url TEXT,
            logo_url TEXT
        );
        
        CREATE TABLE IF NOT EXISTS people_descriptions (
            id SERIAL PRIMARY KEY,
            person_id INT REFERENCES people(id) ON DELETE CASCADE,
            description TEXT
        );
        
        CREATE TABLE IF NOT EXISTS degrees (
            id SERIAL PRIMARY KEY,
            person_id INT REFERENCES people(id) ON DELETE CASCADE,
            institution VARCHAR(255),
            degree_type VARCHAR(255),
            subject VARCHAR(255),
            graduated_on DATE
        );
        
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            person_id INT REFERENCES people(id) ON DELETE CASCADE,
            company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            title VARCHAR(255),
            started_on DATE,
            ended_on DATE
        );
        
        CREATE TABLE IF NOT EXISTS investors (
            id SERIAL PRIMARY KEY,
            uuid UUID UNIQUE NOT NULL,
            name VARCHAR(255),
            permalink VARCHAR(255),
            cb_url TEXT,
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            investor_type VARCHAR(100),
            investment_count INT,
            total_funding_usd BIGINT
        );
        
        CREATE TABLE IF NOT EXISTS investments (
            id SERIAL PRIMARY KEY,
            uuid UUID UNIQUE NOT NULL,
            name VARCHAR(255),
            type VARCHAR(100),
            permalink VARCHAR(255),
            cb_url TEXT,
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            funding_round_uuid UUID,
            funding_round_name VARCHAR(255),
            investor_uuid UUID,
            investor_name VARCHAR(255),
            investor_type VARCHAR(100),
            is_lead_investor BOOLEAN
        );
        
        CREATE TABLE IF NOT EXISTS investment_partners (
            id SERIAL PRIMARY KEY,
            investor_id INT REFERENCES investors(id) ON DELETE CASCADE,
            person_id INT REFERENCES people(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS funds (
            id SERIAL PRIMARY KEY,
            investor_id INT REFERENCES investors(id) ON DELETE CASCADE,
            name VARCHAR(255),
            amount BIGINT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS org_parents (
            id SERIAL PRIMARY KEY,
            parent_id INT REFERENCES companies(id) ON DELETE CASCADE,
            subsidiary_id INT REFERENCES companies(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS ipos (
            id SERIAL PRIMARY KEY,
            company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            uuid UUID UNIQUE NOT NULL,
            stock_exchange VARCHAR(255),
            stock_symbol VARCHAR(50),
            valuation BIGINT,
            ipo_date DATE,
            cb_url TEXT,
            rank INT
        );
        
        CREATE TABLE IF NOT EXISTS acquisitions (
            id SERIAL PRIMARY KEY,
            acquiring_company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            acquired_company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            uuid UUID UNIQUE NOT NULL,
            name VARCHAR(255),
            price BIGINT,
            announced_on DATE,
            cb_url TEXT,
            rank INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """))
        print("Tables checked and created if necessary.")

# Ensure tables exist
create_tables()
