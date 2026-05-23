from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text
from datetime import datetime, timedelta

from models.peopledescriptions import PeopleDescriptions
from .BaseRepository import BaseRepository


class PeopleDescriptionsRepository(BaseRepository[PeopleDescriptions]):
    def __init__(self):
        super().__init__(PeopleDescriptions)

    def get_person_descriptions(
        self,
        db: Session,
        person_uuid: str
    ) -> List[PeopleDescriptions]:
        """Get all descriptions for a person"""
        return db.query(self.model)\
            .filter(self.model.uuid == person_uuid)\
            .order_by(desc(self.model.rank))\
            .all()

    def search_descriptions(
        self,
        db: Session,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[PeopleDescriptions]:
        """Search within people descriptions"""
        return db.query(self.model)\
            .filter(self.model.description.ilike(f"%{search_term}%"))\
            .order_by(desc(self.model.rank))\
            .offset(skip).limit(limit).all()

    def get_person_full_description(
        self,
        db: Session,
        person_uuid: str
    ) -> Optional[str]:
        """Get complete description for a person"""
        descriptions = self.get_person_descriptions(db, person_uuid)
        if not descriptions:
            return None
            
        # Combine all descriptions, ordered by rank
        return "\n\n".join(d.description for d in descriptions)

    def update_person_description(
        self,
        db: Session,
        person_uuid: str,
        description: str
    ) -> PeopleDescriptions:
        """Update or create person description"""
        existing = db.query(self.model)\
            .filter(self.model.uuid == person_uuid)\
            .first()
            
        if existing:
            existing.description = description
            db.add(existing)
        else:
            existing = PeopleDescriptions(
                uuid=person_uuid,
                description=description
            )
            db.add(existing)
            
        db.commit()
        db.refresh(existing)
        return existing