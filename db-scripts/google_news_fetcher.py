from newsapi import NewsApiClient
import psycopg2
import datetime
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Read database credentials from environment
API_KEY = os.getenv("NEWS_API_KEY")

# Google News API Key (Replace with your actual key)
newsapi = NewsApiClient(api_key=API_KEY)

# Database connection details (Modify accordingly)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive"
}

DB_PARAMS = {
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "host": DB_HOST,
    "port": DB_PORT
}

# Simplified search terms relevant for startup market research
QUERY = "startup OR funding OR venture capital OR seed investment OR series A OR acquisitions OR startup trends OR emerging markets OR startup growth OR investments OR acquisition OR IPO OR market trends"

NEWSAPI_EARLIEST_DATE = datetime.datetime.strptime("2025-01-03", "%Y-%m-%d").date()

LATEST_DATE = datetime.datetime.now().date()

# Function to ensure the table exists
def ensure_table_exists():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS funding_news (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            source TEXT,
            published_at DATE,
            content TEXT
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()

# Function to get the last stored date from the database
def get_last_fetched_date():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT MAX(published_at) FROM funding_news;")
    last_date = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    if last_date is None or last_date < NEWSAPI_EARLIEST_DATE:
        return NEWSAPI_EARLIEST_DATE  # Use earliest allowed date from NewsAPI
    return last_date

# Function to fetch funding/acquisition news
def fetch_funding_news():
    ensure_table_exists()  # Ensure table exists before fetching
    days_per_request = 1  # Fetch data in 15-day chunks
    last_fetched_date = get_last_fetched_date()
    
    while last_fetched_date < LATEST_DATE:
        from_date = last_fetched_date
        to_date = from_date + datetime.timedelta(days=days_per_request)
        if to_date > LATEST_DATE:
            to_date = LATEST_DATE
        
        print(f"Fetching news from {from_date} to {to_date} for query: {QUERY}")
        
        page = 1
        while True:
            try:
                articles = newsapi.get_everything(q=QUERY, 
                                                  language="en", 
                                                  from_param=from_date.strftime('%Y-%m-%d'), 
                                                  to=to_date.strftime('%Y-%m-%d'), 
                                                  sort_by="publishedAt", 
                                                  page_size=50,
                                                  page=page)
                
                if articles and "articles" in articles:
                    store_news_in_db(articles["articles"])  # Store immediately
                    if len(articles["articles"]) < 50:
                        break  # Stop pagination if fewer than 50 articles were returned
                else:
                    print(f"No articles found from {from_date} to {to_date}")
                    break
                
                page += 1
                time.sleep(1)  # Avoid hitting API limits
            
            except Exception as e:
                print(f"Error fetching news: {e}")
                if "rateLimited" in str(e):
                    print("Rate limit reached. Stopping execution. Try again later.")
                    return
        
        # Update last fetched date
        last_fetched_date = to_date

# Function to store news data in PostgreSQL
def store_news_in_db(articles):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    for article in articles:
        cur.execute(
            """
            INSERT INTO funding_news (title, url, source, published_at, content)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING;
            """,
            (article["title"], article["url"], article["source"]["name"], article["publishedAt"], article.get("content", ""))
        )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Stored {len(articles)} news articles.")

if __name__ == "__main__":
    fetch_funding_news()
