from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text
from datetime import datetime, timedelta
from models.acquisitions import Acquisitions
from .BaseRepository import BaseRepository

class AcquisitionRepository(BaseRepository[Acquisitions]):
    def __init__(self):
        super().__init__(Acquisitions)

    def get_recent_acquisitions(
        self,
        db: Session,
        *,
        days: int = 90,
        min_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Acquisitions]:
        """Get recent acquisitions with filters"""
        query = db.query(self.model)
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(func.TO_DATE(self.model.acquired_on, 'YYYY-MM-DD') >= cutoff_date)
            
        if min_price:
            query = query.filter(func.COALESCE(self.model.price_usd, 0) >= min_price)
            
        return query.order_by(desc(func.TO_DATE(self.model.acquired_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_company_acquisitions(
        self,
        db: Session,
        company_uuid: str,
        role: Optional[str] = None  # 'acquirer' or 'acquired'
    ) -> List[Acquisitions]:
        """Get acquisitions involving a company"""
        if role == 'acquirer':
            query = db.query(self.model)\
                .filter(self.model.acquirer_uuid == company_uuid)
        elif role == 'acquired':
            query = db.query(self.model)\
                .filter(self.model.acquiree_uuid == company_uuid)
        else:
            query = db.query(self.model)\
                .filter(
                    or_(
                        self.model.acquirer_uuid == company_uuid,
                        self.model.acquiree_uuid == company_uuid
                    )
                )
            
        return query.order_by(desc(func.TO_DATE(self.model.acquired_on, 'YYYY-MM-DD'))).all()

    def get_acquisitions_by_type(
        self,
        db: Session,
        acquisition_type: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Acquisitions]:
        """Get acquisitions by type"""
        return db.query(self.model)\
            .filter(self.model.acquisition_type == acquisition_type)\
            .order_by(desc(func.TO_DATE(self.model.acquired_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_by_price_range(
        self,
        db: Session,
        min_price: float,
        max_price: Optional[float] = None,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Acquisitions]:
        """Get acquisitions by price range"""
        query = db.query(self.model)\
            .filter(func.COALESCE(self.model.price_usd, 0) >= min_price)
            
        if max_price:
            query = query.filter(func.COALESCE(self.model.price_usd, 0) <= max_price)
            
        return query.order_by(desc(func.TO_DATE(self.model.acquired_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_acquisition_details(
        self,
        db: Session,
        acquisition_uuid: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed acquisition information"""
        acq = self.get_by_uuid(db, acquisition_uuid)
        if not acq:
            return None
            
        return {
            "acquired_on": acq.acquired_on,
            "acquisition_type": acq.acquisition_type,
            "price_usd": acq.price_usd,
            "acquirer": {
                "uuid": acq.acquirer_uuid,
                "name": acq.acquirer_name,
                "country": acq.acquirer_country_code,
                "city": acq.acquirer_city
            },
            "acquiree": {
                "uuid": acq.acquiree_uuid,
                "name": acq.acquiree_name,
                "country": acq.acquiree_country_code,
                "city": acq.acquiree_city
            }
        }