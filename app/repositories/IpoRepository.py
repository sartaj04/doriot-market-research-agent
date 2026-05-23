from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text
from datetime import datetime, timedelta

from models.ipos import Ipos
from models.acquisitions import Acquisitions
from .BaseRepository import BaseRepository

class IpoRepository(BaseRepository[Ipos]):
    def __init__(self):
        super().__init__(Ipos)

    def get_recent_ipos(
        self,
        db: Session,
        *,
        days: int = 90,
        min_valuation: Optional[float] = None,
        country_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Ipos]:
        """Get recent IPOs with filters"""
        query = db.query(self.model)
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(func.TO_DATE(self.model.went_public_on, 'YYYY-MM-DD') >= cutoff_date)
            
        if min_valuation:
            query = query.filter(func.COALESCE(self.model.valuation_price_usd, 0) >= min_valuation)
            
        if country_code:
            query = query.filter(self.model.country_code == country_code)
            
        return query.order_by(desc(func.TO_DATE(self.model.went_public_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_by_stock_exchange(
        self,
        db: Session,
        exchange_symbol: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Ipos]:
        """Get IPOs by stock exchange"""
        return db.query(self.model)\
            .filter(self.model.stock_exchange_symbol == exchange_symbol)\
            .order_by(desc(func.TO_DATE(self.model.went_public_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()
    
    def get_by_company_name(
        self,
        db: Session,
        company_name: str,
        limit: int = 10
    ) -> List[Ipos]:
        """Get IPOs by company name"""
        return db.query(self.model)\
            .filter(self.model.company_name.ilike(f"%{company_name}%"))\
            .order_by(desc(func.TO_DATE(self.model.went_public_on, 'YYYY-MM-DD')))\
            .limit(limit)\
            .all()

    def get_by_price_range(
        self,
        db: Session,
        min_price: float,
        max_price: Optional[float] = None,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Ipos]:
        """Get IPOs by share price range"""
        query = db.query(self.model)\
            .filter(func.COALESCE(self.model.share_price_usd, 0) >= min_price)
            
        if max_price:
            query = query.filter(func.COALESCE(self.model.share_price_usd, 0) <= max_price)
            
        return query.order_by(desc(func.TO_DATE(self.model.went_public_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_ipo_details(
        self,
        db: Session,
        org_uuid: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed IPO information for a company"""
        ipo = db.query(self.model)\
            .filter(self.model.org_uuid == org_uuid)\
            .first()
            
        if not ipo:
            return None
            
        return {
            "went_public_on": ipo.went_public_on,
            "stock_exchange": ipo.stock_exchange_symbol,
            "stock_symbol": ipo.stock_symbol,
            "share_price_usd": ipo.share_price_usd,
            "money_raised_usd": ipo.money_raised_usd,
            "valuation_price_usd": ipo.valuation_price_usd
        }

