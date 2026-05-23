from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text
from datetime import datetime, timedelta

from models.people import People
from .BaseRepository import BaseRepository

class PeopleRepository(BaseRepository[People]):
    def __init__(self):
        super().__init__(People)

    def search_people(
        self,
        db: Session,
        *,
        name: Optional[str] = None,
        job_title: Optional[str] = None,
        organization_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[People]:
        """Search people with filters"""
        query = db.query(self.model)
        
        if name:
            query = query.filter(
                or_(
                    self.model.first_name.ilike(f"%{name}%"),
                    self.model.last_name.ilike(f"%{name}%"),
                    self.model.name.ilike(f"%{name}%")
                )
            )
            
        if job_title:
            query = query.filter(self.model.featured_job_title.ilike(f"%{job_title}%"))
            
        if organization_name:
            query = query.filter(self.model.featured_job_organization_name.ilike(f"%{organization_name}%"))
            
        return query.order_by(self.model.rank.desc())\
            .offset(skip).limit(limit).all()

    def get_by_location(
        self,
        db: Session,
        *,
        country_code: Optional[str] = None,
        state_code: Optional[str] = None,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[People]:
        """Get people by location"""
        query = db.query(self.model)
        
        if country_code:
            query = query.filter(self.model.country_code == country_code)
        if state_code:
            query = query.filter(self.model.state_code == state_code)
        if city:
            query = query.filter(self.model.city.ilike(f"%{city}%"))
            
        return query.order_by(self.model.rank.desc())\
            .offset(skip).limit(limit).all()

    def get_by_organization(
        self,
        db: Session,
        organization_uuid: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[People]:
        """Get people by their featured organization"""
        return db.query(self.model)\
            .filter(self.model.featured_job_organization_uuid == organization_uuid)\
            .order_by(self.model.rank.desc())\
            .offset(skip).limit(limit).all()

