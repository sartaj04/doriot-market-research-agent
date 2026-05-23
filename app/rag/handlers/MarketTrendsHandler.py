from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from core.embeddings import compute_text_embedding
from .NewsBaseHandler import NewsBaseHandler
from models.api_models import ArticleSource

logger = logging.getLogger(__name__)

class MarketTrendsHandler(NewsBaseHandler):
    """Handles MARKET_TRENDS_QUERY intent operations"""

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for market trends queries"""
        return {
            "name": "get_market_trends",
            "description": "Analyze market trends from news articles",
            "parameters": {
                "type": "object",
                "properties": {
                    "market_sector": {
                        "type": "string",
                        "description": "Specific market sector to analyze"
                    },
                    "trend_type": {
                        "type": "string",
                        "enum": ["technology", "investment", "startup", "industry"],
                        "description": "Type of trends to focus on"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["last_week", "last_month", "last_quarter"],
                        "default": "last_month",
                        "description": "Timeframe for trend analysis"
                    }
                },
                "required": ["market_sector"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> List[ArticleSource]:
        """Execute the tech news query using repository methods"""
        try:
            days = params.get("days_back", 30)
            
            # Ensure keywords and topics are lists
            keywords = params.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]
                
            topics = params.get("topics", [])
            if isinstance(topics, str):
                topics = [topics]
            
            # Combine search terms
            search_terms = keywords + topics if keywords or topics else []
            search_query = " ".join(search_terms) if search_terms else None
            
            # Get embedding for search query
            query_embedding = None
            if search_query and self.openai_embed_client:
                try:
                    query_embedding = await compute_text_embedding(
                        search_query,
                        self.openai_embed_client,
                        self.embed_model,
                        self.embed_deployment
                    )
                except Exception as e:
                    logger.warning(f"Failed to compute embedding: {e}")
            
            articles = []
            
            # Use hybrid search if both query and embedding available
            if search_query and query_embedding:
                startup_articles = await self.articles_repo.get_hybrid_search(
                    self.db,
                    query=search_query,
                    embedding=query_embedding,
                    days=days,
                    limit=3
                )

            else:
                # Fall back to regular search
                startup_articles = await self.articles_repo.get_articles(
                    self.db,
                    query=search_query,
                    days=days,
                    limit=3
                )
            
            
            processed_articles = []
            # Process startup articles
            for article in startup_articles:
                if article.article_text and article.url:  # Only add articles with content and URL
                    processed_articles.append(ArticleSource(
                        title=article.title if article.title else "No Title",
                        url=article.url if article.url else "Failed to retrieve URL",
                        published_at=str(article.published_at),
                        source=article.source if article.source else "article.url",
                        source_url=article.url,
                        content=article.article_text
                    ))
            
            # Sort by date
            processed_articles.sort(
                key=lambda x: x.published_at,
                reverse=True
            )
            
            return {
                "status": "success",
                "data": processed_articles,
                "total_articles": len(processed_articles)
            }
            
        except Exception as e:
            logger.error(f"Error processing market trends query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def format_for_context(self, response: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if response.get("status") != "success":
            return f"Error: {response.get('error', 'Unknown error')}"

        articles = response.get("data", [])
        context_parts = ["MARKET TRENDS ANALYSIS"]
        
        if not articles:
            return "\n".join(context_parts + ["No relevant articles found."])
        
        # Add articles
        context_parts.extend([
            f"\nFOUND {len(articles)} RELEVANT ARTICLES:",
            ""  # Empty line for better readability
        ])
        
        for article in articles:
            context_parts.extend([
                f"Title: {article.title}",
                f"Source: {article.source}",
                f"Published: {article.published_at}",
                f"URL: {article.url}",
                "\nContent:",
                f"{article.content[:1000]}..." if len(article.content) > 1000 else article.content,
                "\n---"
            ])

        return "\n".join(context_parts)