import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def check_vector_extension(session):
    """Check if vector extension is available and installed"""
    try:
        # Check if extension is available
        result = session.execute(text(
            "SELECT * FROM pg_available_extensions WHERE name = 'vector'"
        )).fetchone()
        
        if not result:
            logger.error("pgvector extension is not available in this RDS instance")
            logger.error("Please enable pgvector in RDS parameter group")
            return False
            
        # Check if extension is installed
        result = session.execute(text(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )).fetchone()
        
        return bool(result)
        
    except Exception as e:
        logger.error(f"Error checking vector extension: {str(e)}")
        return False

def setup_vector_columns():
    """Setup vector columns in tables"""
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if vector extension is installed
        if not check_vector_extension(session):
            logger.debug("Attempting to create vector extension...")
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
            logger.debug("Vector extension created successfully")

        # Add vector columns to tables
        tables = [
            'techcrunch_startup_articles',
            'techcrunch_venture_articles',
            'funding_news'
        ]

        for table in tables:
            logger.debug(f"\nProcessing table: {table}")
            try:
                # Check if column exists
                result = session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name = 'embedding';
                """)).fetchone()
                
                if result:
                    logger.debug(f"Embedding column already exists in {table}")
                else:
                    # Add vector column
                    session.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN embedding vector(1536);
                    """))
                    logger.debug(f"Added embedding column to {table}")

                # Check if index exists
                result = session.execute(text(f"""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = '{table}' 
                    AND indexname = '{table}_embedding_idx';
                """)).fetchone()
                
                if not result:
                    # Create index for similarity search
                    logger.debug(f"Creating similarity search index for {table}...")
                    session.execute(text(f"""
                        CREATE INDEX {table}_embedding_idx 
                        ON {table} 
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """))
                    logger.debug(f"Created index for {table}")
                
                session.commit()
                logger.debug(f"Successfully processed {table}")
                
            except Exception as e:
                logger.error(f"Error processing {table}: {str(e)}")
                session.rollback()
                continue

    except Exception as e:
        logger.error(f"Error in setup: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    logger.debug("Setting up vector columns for AWS RDS...")
    setup_vector_columns()