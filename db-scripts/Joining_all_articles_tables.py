from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def migrate_tables():
    session = Session()
    try:
        # # Step 1: Rename existing `techcrunch_startup_articles` table to `startup_articles`
        # session.execute(text("ALTER TABLE techcrunch_startup_articles RENAME TO startup_articles;"))
        # session.commit()
        # print("Renamed techcrunch_startup_articles to startup_articles.")

        # # Step 2: Add missing `source` column if not exists
        # session.execute(text("ALTER TABLE startup_articles ADD COLUMN IF NOT EXISTS source TEXT;"))
        # session.commit()
        # print("Added source column to startup_articles.")

        # Step 3: Migrate data from `techcrunch_venture_articles`
        session.execute(text("""
            INSERT INTO startup_articles (title, url, published_at, author, category, article_text, source)
            SELECT title, url, published_at, author, category, article_text, 'TechCrunch Venture'
            FROM techcrunch_venture_articles ON CONFLICT (url) DO NOTHING;

        """))
        session.commit()
        print("Migrated data from techcrunch_venture_articles to startup_articles.")

        # Step 4: Migrate data from `funding_news`
        session.execute(text("""
            INSERT INTO startup_articles (title, url, published_at, article_text, source)
            SELECT title, url, published_at, content, source FROM funding_news ON CONFLICT (url) DO NOTHING;
        """))
        session.commit()
        print("Migrated data from funding_news to startup_articles.")

        # Step 5: Drop old tables
        session.execute(text("DROP TABLE IF EXISTS techcrunch_venture_articles;"))
        session.execute(text("DROP TABLE IF EXISTS funding_news;"))
        session.commit()
        print("Dropped old tables: techcrunch_venture_articles and funding_news.")

    except Exception as e:
        session.rollback()
        print(f"Error during migration: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_tables()
