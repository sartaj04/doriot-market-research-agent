from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, select
from datetime import datetime, timedelta
from pgvector.sqlalchemy import Vector

from models.startuparticles import StartupArticles
from .BaseRepository import BaseRepository

class ArticlesRepository(BaseRepository[StartupArticles]):
    def __init__(self):
        super().__init__(StartupArticles)

    async def get_articles(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        days: Optional[int] = 30,
        skip: int = 0,
        limit: int = 20
    ) -> List[StartupArticles]:
        """Get articles with combined keyword and vector search"""
        stmt = select(self.model)

        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            stmt = stmt.where(self.model.published_at >= cutoff_date)

        # Add text search conditions if query provided
        if query:
            stmt = stmt.where(
                or_(
                    self.model.title.ilike(f"%{query}%"),
                    self.model.article_text.ilike(f"%{query}%")
                )
            )

        # Add vector similarity if embedding provided
        if embedding:
            # Using pgvector's cosine distance
            stmt = stmt.order_by(self.model.embedding.cosine_distance(embedding))
        else:
            stmt = stmt.order_by(desc(self.model.published_at))

        stmt = stmt.offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()

    async def search_by_embedding(
        self,
        db: Session,
        embedding: List[float],
        *,
        limit: int = 5
    ) -> List[StartupArticles]:
        """Search articles using pure vector similarity"""
        stmt = (
            select(self.model)
            .where(self.model.embedding.is_not(None))
            .order_by(self.model.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        
        result = db.execute(stmt)
        return result.scalars().all()

    async def get_hybrid_search(
        self,
        db: Session,
        query: str,
        embedding: List[float],
        *,
        days: Optional[int] = 30,
        text_weight: float = 0.3,
        vector_weight: float = 0.7,
        limit: int = 5
    ) -> List[StartupArticles]:
        """Hybrid search combining keyword and vector similarity"""
        # Calculate text similarity using ts_rank
        ts_query = func.plainto_tsquery('english', query)
        ts_vector = func.to_tsvector('english', 
            self.model.title + ' ' + self.model.article_text
        )
        text_rank = func.ts_rank(ts_vector, ts_query)

        # Calculate vector similarity using cosine distance
        vector_similarity = self.model.embedding.cosine_distance(embedding)

        # Combine scores with weights
        combined_score = (
            text_rank * text_weight + 
            (1 - vector_similarity) * vector_weight
        )

        stmt = (
            select(self.model)
            .where(self.model.embedding.is_not(None))
        )

        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            stmt = stmt.where(self.model.published_at >= cutoff_date)

        stmt = (
            stmt.order_by(desc(combined_score))
            .limit(limit)
        )

        result = db.execute(stmt)
        return result.scalars().all()

    async def search_nearest_neighbors(
        self,
        db: Session,
        embedding: List[float],
        *,
        distance_threshold: float = 0.3,
        limit: int = 5
    ) -> List[StartupArticles]:
        """Search for nearest neighbors within a distance threshold"""
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.embedding.is_not(None),
                    self.model.embedding.cosine_distance(embedding) <= distance_threshold
                )
            )
            .order_by(self.model.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        
        result = db.execute(stmt)
        return result.scalars().all()