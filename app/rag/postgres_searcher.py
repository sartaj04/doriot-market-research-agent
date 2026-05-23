from typing import Optional, Union, List, Dict, Any
import numpy as np
from openai import AsyncAzureOpenAI, AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.embeddings import compute_text_embedding 
from models.api_models import Intent, DataSource
import logging

logger = logging.getLogger(__name__)

class MarketResearchSearcher:
    def __init__(
        self,
        db_session: AsyncSession,
        openai_embed_client: Union[AsyncOpenAI, AsyncAzureOpenAI],
        embed_deployment: Optional[str],
        embed_model: str,
        embed_dimensions: Optional[int],
        embedding_column: str,
    ):
        self.db_session = db_session
        self.openai_embed_client = openai_embed_client
        self.embed_model = embed_model
        self.embed_deployment = embed_deployment
        self.embed_dimensions = embed_dimensions
        self.embedding_column = embedding_column

    async def search_articles(
        self,
        query: str,
        source: str,  # 'techcrunch_startup', 'techcrunch_venture', or 'funding_news'
        top_k: int = 5,
        days: int = 30,
        filters: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Search articles using text search instead of vector similarity"""
        # Build base query based on source
        table_map = {
            'techcrunch_startup': 'techcrunch_startup_articles',
            'techcrunch_venture': 'techcrunch_venture_articles',
            'funding_news': 'funding_news'
        }
        table_name = table_map[source]

        # Build filter clause
        filter_clause = ""
        if filters:
            filter_conditions = []
            for filter in filters:
                if isinstance(filter["value"], str):
                    filter["value"] = f"'{filter['value']}'"
                filter_conditions.append(
                    f"{filter['column']} {filter['comparison_operator']} {filter['value']}"
                )
            if filter_conditions:
                filter_clause = "AND " + " AND ".join(filter_conditions)

        # Use text search instead of vector similarity
        query = text(f"""
            SELECT *
            FROM {table_name}
            WHERE published_at >= NOW() - INTERVAL '{days} days'
            AND (
                title ILIKE :search_term
                OR article_text ILIKE :search_term
            )
            {filter_clause}
            ORDER BY published_at DESC
            LIMIT :limit
        """)

        results = (await self.db_session.execute(
            query,
            {
                "search_term": f"%{query}%",
                "limit": top_k
            }
        )).fetchall()

        return [dict(row._mapping) for row in results]

    async def search_companies(
        self,
        query: str,
        include_funding: bool = False,
        include_acquisitions: bool = False,
        filters: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Search companies using structured SQL queries"""
        try:
            # Build filter clause
            filter_clause = ""
            if filters:
                filter_conditions = []
                for filter in filters:
                    if isinstance(filter["value"], str):
                        filter["value"] = f"'{filter['value']}'"
                    filter_conditions.append(
                        f"c.{filter['column']} {filter['comparison_operator']} {filter['value']}"
                    )
                if filter_conditions:
                    filter_clause = "AND " + " AND ".join(filter_conditions)

            # Base query with proper text search for company name/description
            base_query = f"""
                WITH company_matches AS (
                    SELECT c.*
                    FROM companies c
                    WHERE (
                        c.name ILIKE :search_term
                        OR c.short_description ILIKE :search_term
                        OR c.category_list ILIKE :search_term
                    )
                    {filter_clause}
                    ORDER BY 
                        CASE 
                            WHEN c.name ILIKE :exact_match THEN 0  -- Exact name match
                            WHEN c.name ILIKE :starts_with THEN 1  -- Starts with query
                            ELSE 2  -- Contains query somewhere
                        END,
                        c.total_funding_usd DESC NULLS LAST  -- Secondary sort by funding
                )
            """

            # Add related data based on flags
            if include_funding:
                base_query = f"""
                    SELECT 
                        c.*,
                        json_agg(
                            json_build_object(
                                'round_type', fr.investment_type,
                                'amount_usd', fr.raised_amount_usd,
                                'date', fr.announced_on,
                                'investors', fr.investor_count
                            ) ORDER BY fr.announced_on DESC
                        ) FILTER (WHERE fr.id IS NOT NULL) as funding_rounds
                    FROM company_matches c
                    LEFT JOIN funding_rounds fr ON c.uuid = fr.org_uuid
                    GROUP BY c.uuid, c.name
                """

            if include_acquisitions:
                base_query = f"""
                    SELECT 
                        c.*,
                        json_agg(
                            json_build_object(
                                'date', a.acquired_on,
                                'type', CASE 
                                    WHEN a.acquirer_uuid = c.uuid THEN 'acquirer'
                                    ELSE 'acquired'
                                END,
                                'company', CASE 
                                    WHEN a.acquirer_uuid = c.uuid THEN a.acquiree_name
                                    ELSE a.acquirer_name
                                END,
                                'price_usd', a.price_usd
                            ) ORDER BY a.acquired_on DESC
                        ) FILTER (WHERE a.id IS NOT NULL) as acquisitions
                    FROM company_matches c
                    LEFT JOIN acquisitions a 
                        ON c.uuid = a.acquirer_uuid 
                        OR c.uuid = a.acquiree_uuid
                    GROUP BY c.uuid, c.name
                """

            # Execute query with parameters
            results = (await self.db_session.execute(
                text(base_query),
                {
                    "search_term": f"%{query}%",
                    "exact_match": query,
                    "starts_with": f"{query}%"
                }
            )).fetchall()

            return [dict(row._mapping) for row in results]

        except Exception as e:
            logger.error(f"Error in search_companies: {str(e)}")
            raise
        # Add more search methods for other structured data types...