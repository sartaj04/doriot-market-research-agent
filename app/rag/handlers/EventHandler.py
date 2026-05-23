from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from repositories.EventRepository import EventRepository
from repositories.ArticlesRepository import ArticlesRepository

logger = logging.getLogger(__name__)

class EventHandler:
    """Handles EVENT_QUERY intent operations"""
    
    def __init__(self, db: Session, openai_embed_client=None, embed_model=None, embed_deployment=None, embed_dimensions=None):
        self.db = db
        self.event_repo = EventRepository()
        self.articles_repo = ArticlesRepository()
        self.openai_embed_client = openai_embed_client
        self.embed_model = embed_model
        self.embed_deployment = embed_deployment
        self.embed_dimensions = embed_dimensions

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for event queries"""
        return {
            "name": "get_events",
            "description": "Get information about tech and startup events",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": ["conference", "meetup", "webinar", "hackathon", "all"],
                        "description": "Type of event to search for"
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Country code for location-based filtering"
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to look ahead",
                        "default": 90
                    },
                    "max_events": {
                        "type": "integer",
                        "description": "Maximum number of events to return",
                        "default": 10
                    },
                    "search_articles": {
                        "type": "boolean",
                        "description": "Whether to search for related articles",
                        "default": True
                    }
                },
                "required": []
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the event query"""
        try:
            response = {}
            
            # Get upcoming events from database
            events = self.event_repo.get_upcoming_events(
                self.db,
                country_code=params.get("country_code"),
                limit=params.get("max_events", 10)
            )

            # Format event data
            formatted_events = []
            for event in events:
                formatted_events.append({
                    "name": event.name,
                    "description": event.short_description,
                    "dates": {
                        "start": event.started_on,
                        "end": event.ended_on
                    },
                    "location": {
                        "venue": event.venue_name,
                        "city": event.city,
                        "country": event.country_code,
                        "region": event.region
                    },
                    "urls": {
                        "event": event.event_url,
                        "registration": event.registration_url
                    },
                    "logo_url": event.logo_url,
                    "roles": event.event_roles
                })

            response["events"] = formatted_events
            response["total_events"] = len(formatted_events)

            # Search for related articles if requested
            if params.get("search_articles", True):
                # Prepare article search query
                search_terms = []
                for event in events[:3]:  # Use top 3 events for article search
                    search_terms.extend([
                        event.name,
                        event.short_description if event.short_description else ""
                    ])
                search_query = " ".join(search_terms)

                # Get relevant articles from TechCrunch Startup
                startup_articles = await self.articles_repo.get_articles(
                    self.db,
                    query=search_query,
                    days=90,
                    limit=5
                )


                # Format articles
                formatted_articles = []
                
                # Process startup articles
                for article in startup_articles:
                    if article.article_text and article.url:
                        formatted_articles.append({
                            "title": article.title,
                            "url": article.url,
                            "published_at": str(article.published_at),
                            "source": "TechCrunch Startup",
                            "content": article.article_text[:500] + "..."  # Truncate content
                        })


                # Sort articles by date
                formatted_articles.sort(
                    key=lambda x: x["published_at"],
                    reverse=True
                )

                response["related_articles"] = formatted_articles
                response["total_articles"] = len(formatted_articles)

            return {
                "status": "success",
                "data": response
            }

        except Exception as e:
            logger.error(f"Error processing event query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process event query: {str(e)}"
            }

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        context_parts = ["UPCOMING EVENTS AND RELATED NEWS"]
        
        # Format events
        events = data["data"].get("events", [])
        context_parts.append(f"\nTotal Events Found: {len(events)}")
        
        for event in events:
            context_parts.extend([
                f"\nEvent: {event['name']}",
                f"Description: {event['description']}",
                f"Date: {event['dates']['start']} to {event['dates']['end']}",
                f"Location: {event['location']['venue']}, {event['location']['city']}, {event['location']['country']}",
                f"Registration: {event['urls']['registration']}",
                "---"
            ])

        # Format related articles if available
        articles = data["data"].get("related_articles", [])
        if articles:
            context_parts.extend([
                f"\nRELATED NEWS ARTICLES ({len(articles)} found):",
                ""
            ])
            
            for article in articles:
                context_parts.extend([
                    f"Title: {article['title']}",
                    f"Source: {article['source']}",
                    f"Published: {article['published_at']}",
                    f"URL: {article['url']}",
                    f"Summary: {article['content'][:200]}...",
                    "---"
                ])

        return "\n".join(context_parts)