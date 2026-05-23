from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from core.embeddings import compute_text_embedding
from .NewsBaseHandler import NewsBaseHandler
from models.api_models import ArticleSource

logger = logging.getLogger(__name__)

class TechNewsHandler(NewsBaseHandler):
    """Handles TECH_NEWS_QUERY intent operations"""

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for tech news queries"""
        return {
            "name": "get_tech_news",
            "description": "Get technology news articles based on specific criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to search for in articles"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 30
                    },
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "ai",
                                "blockchain",
                                "cloud",
                                "cybersecurity",
                                "fintech",
                                "hardware",
                                "mobile",
                                "software"
                            ]
                        },
                        "description": "Specific tech topics to focus on"
                    }
                },
                "required": ["keywords"]
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
                    limit=5
                )
                
            
            

            articles = []
            # Process startup articles
            for article in startup_articles:
                if article.article_text and article.url:
                    articles.append(ArticleSource(
                        title=article.title if article.title else "No Title",
                        url=article.url if article.url else "Failed to retrieve URL",
                        published_at=str(article.published_at),
                        source=article.source if article.source else "Techcrunch",
                        source_url=article.url,
                        content=article.article_text
                    ))
            
            # Sort by date
            articles.sort(
                key=lambda x: x.published_at,
                reverse=True
            )
            
            return {
                "status": "success",
                "data": articles,
                "total_articles": len(articles)
            }
            
        except Exception as e:
            logger.error(f"Error processing tech news query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def format_for_context(self, response: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if response.get("status") != "success":
            return f"Error: {response.get('error', 'Unknown error')}"

        articles = response.get("data", [])
        context_parts = ["TECH NEWS ANALYSIS"]
        
        if not articles:
            return "\n".join(context_parts + ["No relevant articles found."])
        
        # Add articles
        context_parts.extend([
            f"\nFOUND {len(articles)} RELEVANT ARTICLES:",
            ""  # Empty line for better readability
        ])
        
        for article in articles:
            # Truncate content if too long (e.g., limit to 1000 characters)
            content = article.content[:1000] + "..." if len(article.content) > 1000 else article.content
            
            context_parts.extend([
                f"\nTitle: {article.title}",
                f"URL: {article.url}",
                f"Published: {article.published_at}",
                f"Source: {article.source}",
                "\nSummary:",
                content,
                "\n---"
            ])

        return "\n".join(context_parts)