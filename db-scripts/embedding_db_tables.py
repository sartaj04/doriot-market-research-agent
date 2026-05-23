import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from openai import AsyncAzureOpenAI
from tqdm import tqdm
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_TOKENS = 8191
SAFE_LIMIT = 7500  

# Load environment variables
load_dotenv()

# Configuration dictionaries for different table structures
TABLE_CONFIGS = {
    'techcrunch_startup_articles': {
        'content_column': 'article_text',
        'query': """
            SELECT id, title, article_text 
            FROM techcrunch_startup_articles
            WHERE embedding IS NULL
            AND article_text IS NOT NULL
        """
    },
    'techcrunch_venture_articles': {
        'content_column': 'article_text',
        'query': """
            SELECT id, title, article_text 
            FROM techcrunch_venture_articles
            WHERE embedding IS NULL
            AND article_text IS NOT NULL
        """
    },
    'funding_news': {
        'content_column': 'content',
        'query': """
            SELECT id, title, content 
            FROM funding_news
            WHERE embedding IS NULL
            AND content IS NOT NULL
        """
    }
}

def get_openai_client():
    """Initialize Azure OpenAI client"""
    return AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_VERSION")
    )

async def generate_embedding(text: str, client) -> list:
    """Generate embedding for text using Azure OpenAI"""
    try:
        response = await client.embeddings.create(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None
    

async def summarize_text(text: str, client) -> str:
    """Summarize text if it's too long"""
    try:
        response = await client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role": "system", "content": "Summarize the following text concisely while preserving key information."},
                      {"role": "user", "content": text}],
            max_tokens=1024  # Generate a short summary
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        return text[:SAFE_LIMIT]  # Fallback to truncation

async def update_table_embeddings(table_name: str, session, client):
    """Update embeddings for a specific table"""
    try:
        table_config = TABLE_CONFIGS[table_name]
        content_column = table_config['content_column']
        
        # Get articles without embeddings
        query = text(table_config['query'])
        articles = session.execute(query).fetchall()

        logger.debug(f"Found {len(articles)} articles without embeddings in {table_name}")

        # Process articles in batches
        batch_size = 5
        for i in tqdm(range(0, len(articles), batch_size)):
            batch = articles[i:i + batch_size]
            for article in batch:
                try:
                    # Get content based on table structure
                    content = getattr(article, content_column)
                    text_to_embed = f"Title: {article.title}\n\nContent: {content}"

                    token_count = len(text_to_embed.split())  # Approximate token count
                    if token_count > SAFE_LIMIT:
                        logger.warning(f"Article {article.id} exceeds token limit ({token_count} tokens). Summarizing...")
                        text_to_embed = await summarize_text(text_to_embed, client)
                    
                    # Generate embedding
                    embedding = await generate_embedding(text_to_embed, client)
                    
                    if embedding:
                        # Update database
                        update_query = text(f"""
                            UPDATE {table_name}
                            SET embedding = :embedding
                            WHERE id = :id
                        """)
                        session.execute(update_query, {
                            "embedding": embedding,
                            "id": article.id
                        })
                        session.commit()
                        logger.debug(f"Updated embedding for article {article.id}")
                    else:
                        logger.warning(f"Failed to generate embedding for article {article.id}")
                        
                except Exception as e:
                    logger.error(f"Error processing article {article.id}: {str(e)}")
                    session.rollback()
                    continue
            
            await asyncio.sleep(1)  # Rate limiting

    except Exception as e:
        logger.error(f"Error processing {table_name}: {str(e)}")
        raise

async def main():
    DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        client = get_openai_client()
        logger.debug("Successfully initialized OpenAI client")

        for table_name in TABLE_CONFIGS.keys():
            logger.debug(f"\nProcessing table: {table_name}")
            await update_table_embeddings(table_name, session, client)

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())