from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text
from datetime import datetime, timedelta

from models.degrees import Degrees
from .BaseRepository import BaseRepository

class DegreesRepository(BaseRepository[Degrees]):
    def __init__(self):
        super().__init__(Degrees)

    def get_person_degrees(
        self,
        db: Session,
        person_uuid: str
    ) -> List[Degrees]:
        """Get all degrees for a person"""
        return db.query(self.model)\
            .filter(self.model.person_uuid == person_uuid)\
            .order_by(desc(func.TO_DATE(self.model.completed_on, 'YYYY-MM-DD')))\
            .all()

    def get_by_institution(
        self,
        db: Session,
        institution_name: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Degrees]:
        """Get degrees from a specific institution"""
        return db.query(self.model)\
            .filter(self.model.institution_name.ilike(f"%{institution_name}%"))\
            .order_by(desc(func.TO_DATE(self.model.completed_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_by_degree_type(
        self,
        db: Session,
        degree_type: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Degrees]:
        """Get degrees by type"""
        return db.query(self.model)\
            .filter(self.model.degree_type.ilike(f"%{degree_type}%"))\
            .order_by(desc(func.TO_DATE(self.model.completed_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_by_subject(
        self,
        db: Session,
        subject: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Degrees]:
        """Get degrees by subject"""
        return db.query(self.model)\
            .filter(self.model.subject.ilike(f"%{subject}%"))\
            .order_by(desc(func.TO_DATE(self.model.completed_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_completed_degrees(
        self,
        db: Session,
        person_uuid: str
    ) -> List[Degrees]:
        """Get completed degrees for a person"""
        return db.query(self.model)\
            .filter(
                and_(
                    self.model.person_uuid == person_uuid,
                    self.model.is_completed == True
                )
            )\
            .order_by(desc(func.TO_DATE(self.model.completed_on, 'YYYY-MM-DD')))\
            .all()

