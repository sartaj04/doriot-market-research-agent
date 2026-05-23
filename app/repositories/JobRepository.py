from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy import or_, and_, desc, func, text
from models.jobs import Jobs
from .BaseRepository import BaseRepository

class JobRepository(BaseRepository[Jobs]):
    def __init__(self):
        super().__init__(Jobs)


    def get_person_jobs_by_name(
        self,
        db: Session,
        person_name: str,
        *,
        current_only: bool = False,
        limit: int = 10
    ) -> List[Jobs]:
        """Get jobs for a person by their name"""
        query = db.query(self.model)\
            .filter(self.model.person_name.ilike(f"%{person_name}%"))
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).limit(limit).all()

    def get_organization_jobs_by_name(
        self,
        db: Session,
        org_name: str,
        *,
        current_only: bool = False,
        limit: int = 10
    ) -> List[Jobs]:
        """Get jobs at an organization by name"""
        query = db.query(self.model)\
            .filter(self.model.org_name.ilike(f"%{org_name}%"))
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).limit(limit).all()

    def search_by_location(
        self,
        db: Session,
        location: str,
        *,
        current_only: bool = False,
        limit: int = 10
    ) -> List[Jobs]:
        """Search jobs by location (city or country code)"""
        query = db.query(self.model)\
            .filter(
                or_(
                    self.model.city.ilike(f"%{location}%"),
                    self.model.country_code.ilike(f"%{location}%")
                )
            )
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).limit(limit).all()

    def get_person_jobs(
        self,
        db: Session,
        person_uuid: str,
        *,
        current_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Jobs]:
        """Get jobs for a person"""
        query = db.query(self.model)\
            .filter(self.model.person_uuid == person_uuid)
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).offset(skip).limit(limit).all()

    def get_organization_jobs(
        self,
        db: Session,
        org_uuid: str,
        *,
        current_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Jobs]:
        """Get jobs at an organization"""
        query = db.query(self.model)\
            .filter(self.model.org_uuid == org_uuid)
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).offset(skip).limit(limit).all()

    def search_by_title(
        self,
        db: Session,
        title: str,
        *,
        current_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Jobs]:
        """Search jobs by title"""
        query = db.query(self.model)\
            .filter(self.model.title.ilike(f"%{title}%"))
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).offset(skip).limit(limit).all()

    def get_jobs_by_type(
        self,
        db: Session,
        job_type: str,
        *,
        current_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Jobs]:
        """Get jobs by type"""
        query = db.query(self.model)\
            .filter(self.model.job_type == job_type)
            
        if current_only:
            query = query.filter(self.model.is_current == True)
            
        return query.order_by(
            self.model.is_current.desc(),
            desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD'))
        ).offset(skip).limit(limit).all()

    def get_current_jobs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Jobs]:
        """Get all current jobs"""
        return db.query(self.model)\
            .filter(self.model.is_current == True)\
            .order_by(desc(func.TO_DATE(self.model.started_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_job_history(
        self,
        db: Session,
        person_uuid: str
    ) -> Dict[str, Any]:
        """Get comprehensive job history for a person"""
        jobs = self.get_person_jobs(db, person_uuid)
        
        current_jobs = [j for j in jobs if j.is_current]
        past_jobs = [j for j in jobs if not j.is_current]
        
        return {
            "current_positions": [
                {
                    "title": job.title,
                    "organization": job.org_name,
                    "started_on": job.started_on,
                    "type": job.job_type
                } for job in current_jobs
            ],
            "past_positions": [
                {
                    "title": job.title,
                    "organization": job.org_name,
                    "started_on": job.started_on,
                    "ended_on": job.ended_on,
                    "type": job.job_type
                } for job in past_jobs
            ]
        }