import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration for different tables
TABLE_CONFIGS = {
    'techcrunch_startup_articles': 'article_text',
    'techcrunch_venture_articles': 'article_text',
    'funding_news': 'content'
}

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_missing_embeddings():
    """Check for missing embeddings in each table."""
    session = Session()
    try:
        for table_name, content_column in TABLE_CONFIGS.items():
            query = text(f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE embedding IS NULL 
                AND {content_column} IS NOT NULL
            """
            )
            result = session.execute(query).scalar()
            logger.debug(f"Table {table_name}: {result} records missing embeddings")
        
    except Exception as e:
        logger.error(f"Error checking missing embeddings: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    check_missing_embeddings()
