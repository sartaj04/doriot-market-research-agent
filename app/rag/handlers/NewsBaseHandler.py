from typing import Dict, Any, List, Optional, Union
import asyncio
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta, date
from openai import AsyncOpenAI, AsyncAzureOpenAI

from core.embeddings import compute_text_embedding
from repositories.ArticlesRepository import ArticlesRepository
from models.api_models import ArticleSource

logger = logging.getLogger(__name__)

class NewsBaseHandler:
    """Base handler for news-related queries with enhanced vector search capabilities"""
    
    def __init__(
        self,
        db: Session,
        openai_embed_client: Optional[Union[AsyncOpenAI, AsyncAzureOpenAI]] = None,
        embed_model: Optional[str] = None,
        embed_deployment: Optional[str] = None,
        embed_dimensions: Optional[int] = None
    ):
        self.db = db
        self.articles_repo = ArticlesRepository()
        
        # OpenAI embedding settings
        self.openai_embed_client = openai_embed_client
        self.embed_model = embed_model
        self.embed_deployment = embed_deployment
        self.embed_dimensions = embed_dimensions

    async def compute_query_embedding(self, query: str) -> List[float]:
        """Compute embedding for a search query"""
        if not self.openai_embed_client:
            raise ValueError("OpenAI embedding client not initialized")
            
        return await compute_text_embedding(
            query,
            self.openai_embed_client,
            self.embed_model,
            self.embed_deployment
        )

    async def search_all_sources(
        self,
        query: str,
        days: int = 30,
        limit_per_source: int = 5,
        use_vector_search: bool = True
    ) -> List[Dict[str, Any]]:
        """Search across all news sources with optional vector search"""
        # Compute query embedding once if using vector search
        query_embedding = None
        if use_vector_search and self.openai_embed_client:
            try:
                query_embedding = await self.compute_query_embedding(query)
            except Exception as e:
                logger.warning(f"Failed to compute embedding, falling back to keyword search: {e}")

        # Define concurrent search tasks
        async def fetch_startup_articles():
            try:
                articles = await self.articles_repo.get_articles(
                    self.db,
                    query=query,
                    days=days,
                    skip=0,
                    limit=limit_per_source
                )
                return [(article, "TechCrunch Startup", "article_text") for article in articles]
            except Exception as e:
                logger.error(f"Error fetching startup articles: {e}")
                return []



        # Execute all searches concurrently
        search_results = await asyncio.gather(
            fetch_startup_articles(),
            return_exceptions=False
        )

        # Process and combine articles
        all_articles = []
        for source_articles in search_results:
            for article, source_name, content_field in source_articles:
                content = getattr(article, content_field, None)
                if content and article.url:  # Only add articles with content and URL
                    # Convert datetime/date to string for consistent comparison
                    published_at = article.published_at
                    if isinstance(published_at, (datetime, date)):
                        published_at = published_at.isoformat()
                        
                    all_articles.append({
                        "title": article.title if hasattr(article, 'title') else "",
                        "content": content,
                        "published_at": published_at,
                        "url": article.url,
                        "source": source_name,
                        "relevance_score": getattr(article, 'relevance_score', 0)
                    })

        # Sort by relevance score and date string
        all_articles.sort(
            key=lambda x: (x["relevance_score"], x["published_at"]),
            reverse=True
        )

        return all_articles

    def filter_articles_by_keywords(
        self,
        articles: List[Dict[str, Any]],
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter articles by keywords"""
        if not keywords:
            return articles
            
        filtered_articles = []
        for article in articles:
            if any(
                keyword.lower() in article["title"].lower() or
                keyword.lower() in article["content"].lower()
                for keyword in keywords
            ):
                filtered_articles.append(article)
        
        return filtered_articles

    def extract_topics_from_articles(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Extract and count common topics from articles"""
        topic_counts = {}
        
        # Common tech topics to look for
        tech_topics = [
            "AI", "Machine Learning", "Blockchain", "Cloud",
            "Cybersecurity", "Fintech", "IoT", "5G",
            "SaaS", "E-commerce", "Digital Health", "EdTech"
        ]
        
        for article in articles:
            content = f"{article['title']} {article['content']}"
            for topic in tech_topics:
                if topic.lower() in content.lower():
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    
        return dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))

    def analyze_sentiment_trends(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze trends and sentiment in articles"""
        # This is a placeholder for more sophisticated sentiment analysis
        total_articles = len(articles)
        if not total_articles:
            return {}
            
        # Get publication timeline
        dates = [article["published_at"] for article in articles]
        earliest_date = min(dates)
        latest_date = max(dates)
        
        # Get top topics
        topics = self.extract_topics_from_articles(articles)
        
        return {
            "date_range": {
                "start": earliest_date,
                "end": latest_date
            },
            "total_articles": total_articles,
            "top_topics": topics,
            "sources": {
                "TechCrunch Startup": len([a for a in articles if a["source"] == "TechCrunch Startup"]),
                "TechCrunch Venture": len([a for a in articles if a["source"] == "TechCrunch Venture"]),
                "Funding News": len([a for a in articles if a["source"] == "Funding News"])
            }
        }