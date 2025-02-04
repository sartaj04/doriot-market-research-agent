import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import datetime
import json
import os
from typing import List, Dict, Optional, Tuple
import random


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArticleData:
    """Class to store article data with full content"""
    def __init__(self, title: str, url: str, published_at: str, author: str, 
                 category: str, full_content: str = "", summary: str = "", 
                 article_text: str = "", article_html: str = ""):
        self.title = title
        self.url = url
        self.published_at = published_at
        self.author = author
        self.category = category
        self.full_content = full_content
        self.summary = summary
        self.article_text = article_text  # Full article text content
        self.article_html = article_html  # Raw HTML of article

class TechCrunchScraper:
    """Enhanced TechCrunch scraper with article content extraction"""
    
    BASE_URL = "https://techcrunch.com/category/startups/"
    MAX_PAGES = 333  
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    THREAD_DELAY = (2, 5)
    MAX_WORKERS = 3  # Reduced to avoid rate limiting
    PAGE_DELAY = (3, 7) 
    
    def __init__(self, start_page, max_pages: int = 1):
        self.options = self._configure_chrome_options()
        self.thread_local = threading.local()
        self.driver_lock = threading.Lock()
        self.start_page = start_page
        self.max_pages = max_pages
    
    def _configure_chrome_options(self) -> Options:
        """Configure Chrome webdriver options"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        return options

    def _get_driver(self) -> webdriver.Chrome:
        """Get thread-local webdriver instance"""
        if not hasattr(self.thread_local, "driver"):
            with self.driver_lock:
                service = Service(ChromeDriverManager().install())
                self.thread_local.driver = webdriver.Chrome(service=service, options=self.options)
        return self.thread_local.driver

    def _extract_article_content(self, driver: webdriver.Chrome) -> Tuple[str, str]:
        """Extract article content and HTML from the article page"""
        try:
            wait = WebDriverWait(driver, 15)
            
            # First get the article hero section for metadata
            article_hero = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "article-hero"))
            )
            
            # Get title
            try:
                title = article_hero.find_element(By.CLASS_NAME, "article-hero__title").text.strip()
            except NoSuchElementException:
                title = ""
            
            # Get post content
            post_content = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "wp-block-post-content"))
            )
            
            content_parts = []
            
            # Get speakable summary if available
            try:
                summary = post_content.find_element(By.ID, "speakable-summary")
                content_parts.append(summary.text.strip())
            except NoSuchElementException:
                pass
            
            # Get main content paragraphs
            paragraphs = post_content.find_elements(By.CLASS_NAME, "wp-block-paragraph")
            
            for p in paragraphs:
                text = p.text.strip()
                if text and not any(skip in text.lower() for skip in [
                    "advertisement", "ad-unit", "follow us", "©",
                    "subscribe", "newsletter", "sign up",
                    "marfeel"
                ]):
                    content_parts.append(text)
            
            # Get all blockquotes
            blockquotes = post_content.find_elements(By.TAG_NAME, "blockquote")
            for quote in blockquotes:
                text = quote.text.strip()
                if text:
                    content_parts.append(f"Quote: {text}")
            
            # Combine all content
            article_text = "\n\n".join(content_parts)
            
            # Get the raw HTML
            article_html = post_content.get_attribute('outerHTML')
            
            # Add title at the beginning
            if title:
                article_text = f"{title}\n\n{article_text}"
            
            if not article_text:
                logger.warning("No article content found")
                return "", ""
                
            return article_text, article_html
            
        except Exception as e:
            logger.error(f"Error extracting article content: {e}")
            return "", ""

    def _process_article_page(self, driver: webdriver.Chrome, url: str) -> Tuple[str, str]:
        """Process a single article page to extract content"""
        try:
            if "podcast" in url:
                logger.info(f"Skipping podcast URL: {url}")
                return "", ""
                
            driver.get(url)
            
            # Handle cookie consent if present
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                )
                cookie_button.click()
                time.sleep(random.uniform(1, 3)) # Wait for cookie banner to disappear
            except:
                pass  # No cookie notice or already accepted
            
            # Wait for critical elements
            wait = WebDriverWait(driver, 15)
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "article-hero"))
            )
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "wp-block-post-content"))
            )
            
            # Let dynamic content load
            time.sleep(random.uniform(3, 7))  
            
            # Extract content
            return self._extract_article_content(driver)
            
        except Exception as e:
            logger.error(f"Error processing article page {url}: {e}")
            return "", ""

    def _get_next_page_url(self, driver: webdriver.Chrome) -> Optional[str]:
        """Get URL of next page if it exists"""
        try:
            next_link = driver.find_element(By.CLASS_NAME, "wp-block-query-pagination-next")
            return next_link.get_attribute("href")
        except NoSuchElementException:
            return None

    def _process_article(self, article_element) -> Optional[ArticleData]:
        """Process a single article element to extract metadata and content"""
        try:
            driver = self._get_driver()
            
            # Extract basic article info
            title_link = article_element.find_element(By.CSS_SELECTOR, "a.loop-card__title-link")
            title = title_link.text.strip()
            url = title_link.get_attribute("href")
            
            # Extract author and date
            try:
                author = article_element.find_element(By.CSS_SELECTOR, ".loop-card__author").text.strip()
            except NoSuchElementException:
                author = "Unknown"
                
            try:
                date_element = article_element.find_element(By.CSS_SELECTOR, "time")
                published_at = date_element.get_attribute("datetime")
            except NoSuchElementException:
                published_at = ""
                
            # Extract category
            try:
                category = article_element.find_element(By.CSS_SELECTOR, ".loop-card__cat").text.strip()
            except NoSuchElementException:
                category = "Uncategorized"
            
            # Get full article content
            article_text, article_html = self._process_article_page(driver, url)
            
            # Create article data object
            article_data = ArticleData(
                title=title,
                url=url,
                published_at=published_at,
                author=author,
                category=category,
                article_text=article_text,
                article_html=article_html
            )
            
            logger.info(f"Successfully processed article: {title}")
            return article_data
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None

    def fetch_articles(self) -> List[ArticleData]:
        """Fetch 3 articles from each page up to max_pages"""
        all_articles = []
        main_driver = None
        current_page = 1
        
        try:
            # Initialize main driver
            service = Service(ChromeDriverManager().install())
            main_driver = webdriver.Chrome(service=service, options=self.options)
            current_url = self.BASE_URL

            if self.start_page > 1:
                current_url = f"{self.BASE_URL}page/{self.start_page}/"
                print(f"Current URL: {current_url}")
                current_page = self.start_page
            
            while current_page <= self.max_pages:
                logger.info(f"Processing page {current_page}")
                main_driver.get(current_url)
                time.sleep(random.uniform(3, 7))    # Allow page to load
                
                # Get article elements on current page
                wait = WebDriverWait(main_driver, 15)
                articles = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.wp-block-post"))
                )
                
                # Process first 5 articles on this page to get 3 successful ones
                successful_count = 0
                
                for article in articles:

                        
                    try:
                        # Get basic info first
                        title_link = article.find_element(By.CSS_SELECTOR, "a.loop-card__title-link")
                        title = title_link.text.strip()
                        url = title_link.get_attribute("href")
                        
                        # Skip podcasts
                        if "podcast" in url.lower():
                            logger.info(f"Skipping podcast: {title}")
                            continue
                        
                        # Get author
                        try:
                            author = article.find_element(By.CSS_SELECTOR, ".loop-card__author").text.strip()
                        except NoSuchElementException:
                            author = "Unknown"
                        
                        # Get date
                        try:
                            date_element = article.find_element(By.CSS_SELECTOR, "time")
                            published_at = date_element.get_attribute("datetime")
                        except NoSuchElementException:
                            published_at = ""
                        
                        # Get category
                        try:
                            category = article.find_element(By.CSS_SELECTOR, ".loop-card__cat").text.strip()
                        except NoSuchElementException:
                            category = "Uncategorized"
                        
                        # Process full article
                        driver = self._get_driver()
                        article_text, article_html = self._process_article_page(driver, url)
                        
                        # Validate content was extracted
                        if article_text and len(article_text.strip()) > 100:  # Minimum content validation
                            article_data = ArticleData(
                                title=title,
                                url=url,
                                published_at=published_at,
                                author=author,
                                category=category,
                                article_text=article_text,
                                article_html=article_html
                            )
                            all_articles.append(article_data)
                            successful_count += 1
                            logger.info(f"Page {current_page}: Successfully processed article {successful_count}: {title}")
                    
                    except Exception as e:
                        logger.error(f"Error processing article: {e}")
                        continue
                
                # Get next page URL if we haven't reached max pages
                if current_page >= self.max_pages:
                    break
                    
                try:
                    # Look for the next page link
                    next_link = main_driver.find_element(By.CLASS_NAME, "wp-block-query-pagination-next")
                    current_url = next_link.get_attribute("href")
                    if not current_url:
                        logger.info("No more pages available")
                        break
                    current_page += 1
                    time.sleep(random.uniform(2, 6))  # Delay between pages
                except NoSuchElementException:
                    logger.info("No more pages available")
                    break
            
            logger.info(f"Successfully processed {len(all_articles)} articles from {current_page} page(s)")
            
        except Exception as e:
            logger.error(f"Error in fetch_articles: {e}")
        finally:
            if main_driver:
                main_driver.quit()
            if hasattr(self.thread_local, "driver"):
                self.thread_local.driver.quit()
        
        return all_articles , current_page

    def save_articles(self, articles: List[ArticleData], output_dir: str = "output"):
        """Save articles to JSON files with full content"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save full content including article text
            full_filename = os.path.join(output_dir, f"techcrunch_startups_full_{timestamp}.json")
            full_data = [{
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at,
                "author": article.author,
                "category": article.category,
                "article_text": article.article_text,
                "article_html": article.article_html
            } for article in articles]
            
            with open(full_filename, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)
            
            # Save metadata only
            meta_filename = os.path.join(output_dir, f"techcrunch_startups_meta_{timestamp}.json")
            meta_data = [{
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at,
                "author": article.author,
                "category": article.category
            } for article in articles]
            
            with open(meta_filename, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(articles)} articles to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
            raise

def main():
    """Main entry point"""
    # Create scraper instance with maximum pages to scrape
    scraper = TechCrunchScraper(start_page = 200, max_pages=333)
    
    try:
        articles,current_page = scraper.fetch_articles()
        
        if articles:
            scraper.save_articles(articles)
            
            print(f"\nExtracted {len(articles)} articles:")
            print("-" * 80)
            for article in articles:
                print(f"Title: {article.title}")
                print(f"Author: {article.author}")
                print(f"Category: {article.category}")
                print(f"URL: {article.url}")
                print(f"Published: {article.published_at}")
                print(f"Article length: {len(article.article_text)} characters")
                print("-" * 80)

            print(f"Total pages processed: {current_page}")
        else:
            logger.warning("No articles found")
            
    except Exception as e:
        logger.error(f"Script failed: {e}")

if __name__ == "__main__":
    main()