from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text, type_coerce, Numeric
from datetime import datetime, timedelta

from models.investments import Investments
from .BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class InvestmentsRepository(BaseRepository[Investments]):
    def __init__(self):
        super().__init__(Investments)

    def _handle_query(self, query):
        """Execute query with error handling"""
        try:
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    def get_by_investor(
        self,
        db: Session,
        investor_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Investments]:
        """Get investments by investor"""
        return db.query(self.model)\
            .filter(self.model.investor_uuid == investor_uuid)\
            .order_by(desc(self.model.announced_on)).offset(skip).limit(limit).all()
    
    def get_by_investor_name(
        self,
        db: Session,
        investor_name: str,
        *,
        lead_only: bool = False,
        limit: int = 10
    ) -> List[Investments]:
        """Get investments by investor name"""
        query = db.query(self.model)\
            .filter(self.model.investor_name.ilike(f"%{investor_name}%"))
            
        if lead_only:
            query = query.filter(self.model.is_lead_investor == True)
            
        return query.order_by(desc(self.model.announced_on)).limit(limit).all()

    def get_by_funding_round(
        self,
        db: Session,
        investment_round: str  # Changed from funding_round_uuid
    ) -> List[Investments]:
        """Get all investments in a funding round"""
        return db.query(self.model)\
            .filter(self.model.investment_round == investment_round)\
            .order_by(self.model.is_lead_investor.desc())\
            .all()

    def get_lead_investments(
        self,
        db: Session,
        investor_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Investments]:
        """Get investments where investor was lead investor"""
        return db.query(self.model)\
            .filter(
                and_(
                    self.model.investor_uuid == investor_uuid,
                    self.model.is_lead_investor == True
                )
            )\
            .order_by(desc(self.model.announced_on)).offset(skip).limit(limit).all()

    def get_investments_by_type(
        self,
        db: Session,
        investor_type: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Investments]:
        """Get investments by investor type"""
        return db.query(self.model)\
            .filter(self.model.investor_type == investor_type)\
            .order_by(desc(self.model.announced_on)).offset(skip).limit(limit).all()

    def _handle_numeric_filter(self, column, value):
        """Handle money value comparison safely"""
        if value is None:
            return None
        # Convert the value to string format for money comparison
        money_str = f"${value:.2f}"  # Format as money string
        return column >= money_str

    def get_recent_investments(
        self,
        db: Session,
        *,
        days: int = 30,
        min_amount: Optional[float] = None,
        investor_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Investments]:
        try:
            query = db.query(self.model)
            
            if days > 0:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(self.model.announced_on >= cutoff_date)
            
            if min_amount is not None:
                filter_condition = self._handle_numeric_filter(
                    self.model.raised_amount, 
                    min_amount
                )
                if filter_condition is not None:
                    query = query.filter(filter_condition)
            
            if investor_type:
                query = query.filter(self.model.investor_type.ilike(f"%{investor_type}%"))
            
            query = query.order_by(
                desc(self.model.announced_on),
                desc(self.model.raised_amount)
            )
            
            return self._handle_query(query.offset(skip).limit(limit))
            
        except Exception as e:
            logger.error(f"Error in get_recent_investments: {str(e)}", exc_info=True)
            return []