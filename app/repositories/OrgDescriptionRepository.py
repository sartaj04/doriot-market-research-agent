from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text
from datetime import datetime, timedelta

from models.organizationdescriptions import OrganizationDescriptions
from .BaseRepository import BaseRepository

class OrgDescriptionRepository(BaseRepository[OrganizationDescriptions]):
    def __init__(self):
        super().__init__(OrganizationDescriptions)

    def get_descriptions(
        self,
        db: Session,
        company_uuid: str
    ) -> List[OrganizationDescriptions]:
        """Get all descriptions for a company"""
        return db.query(self.model)\
            .filter(self.model.uuid == company_uuid)\
            .order_by(desc(self.model.rank))\
            .all()

    def search_descriptions(
        self,
        db: Session,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrganizationDescriptions]:
        """Search within organization descriptions"""
        return db.query(self.model)\
            .filter(self.model.description.ilike(f"%{search_term}%"))\
            .order_by(desc(self.model.rank))\
            .offset(skip).limit(limit).all()

    def get_company_full_description(
        self,
        db: Session,
        company_uuid: str
    ) -> Optional[str]:
        """Get complete description for a company"""
        descriptions = self.get_descriptions(db, company_uuid)
        if not descriptions:
            return None
            
        # Combine all descriptions, ordered by rank
        return "\n\n".join(d.description for d in descriptions)