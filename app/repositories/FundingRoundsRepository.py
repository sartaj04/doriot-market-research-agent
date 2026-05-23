from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.fundingrounds import FundingRounds
from .BaseRepository import BaseRepository

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta

from models.fundingrounds import FundingRounds
from models.companies import Companies
from models.investments import Investments
from repositories.BaseRepository import BaseRepository

class FundingRoundsRepository(BaseRepository[FundingRounds]):
    def __init__(self):
        super().__init__(FundingRounds)

    def get_latest_rounds(
        self,
        db: Session,
        *,
        days: int = 30,
        investment_type: Optional[str] = None,
        min_amount: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FundingRounds]:
        """Get latest funding rounds with filters"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(self.model)\
            .filter(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD') >= cutoff_date)
            
        if investment_type:
            query = query.filter(self.model.investment_type == investment_type)
            
        if min_amount:
            query = query.filter(func.COALESCE(self.model.raised_amount_usd, 0) >= min_amount)
            
        return query.order_by(desc(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()
    
    def get_funding_rounds(
        self,
        db: Session,
        *,
        investment_type: Optional[str] = None,
        min_amount: Optional[float] = None,
        recent_only: bool = False,
        sort_by: str = "date",
        limit: int = 10
    ) -> List[FundingRounds]:
        """Get funding rounds with flexible filtering"""
        query = db.query(self.model)
        
        if investment_type:
            query = query.filter(self.model.investment_type.ilike(f"%{investment_type}%"))
            
        if min_amount:
            query = query.filter(self.model.raised_amount_usd >= min_amount)
            
        if recent_only:
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            query = query.filter(self.model.announced_on >= cutoff_date.strftime('%Y-%m-%d'))
        
        # Apply sorting
        if sort_by == "date":
            query = query.order_by(desc(self.model.announced_on))
        elif sort_by == "amount":
            query = query.order_by(desc(self.model.raised_amount_usd))
        elif sort_by == "company":
            query = query.join(Companies).order_by(Companies.name)
        
        return query.limit(limit).all()

    def get_company_rounds(
        self,
        db: Session,
        company_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[FundingRounds]:
        """Get funding rounds for a specific company"""
        return db.query(self.model)\
            .filter(self.model.org_uuid == company_uuid)\
            .order_by(desc(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_rounds_by_type(
        self,
        db: Session,
        investment_type: str,
        *,
        days: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FundingRounds]:
        """Get funding rounds by investment type"""
        query = db.query(self.model)\
            .filter(self.model.investment_type == investment_type)
            
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD') >= cutoff_date)
            
        return query.order_by(desc(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD')))\
            .offset(skip).limit(limit).all()

    def get_top_rounds(
        self,
        db: Session,
        *,
        days: Optional[int] = None,
        limit: int = 10
    ) -> List[FundingRounds]:
        """Get top funding rounds by amount"""
        query = db.query(self.model)
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD') >= cutoff_date)
            
        return query.order_by(desc(func.COALESCE(self.model.raised_amount_usd, 0)))\
            .limit(limit).all()

    def get_funding_stats(
        self,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get funding statistics for a time period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            func.count(self.model.uuid).label('total_rounds'),
            func.sum(func.COALESCE(self.model.raised_amount_usd, 0)).label('total_raised'),
            func.avg(func.COALESCE(self.model.raised_amount_usd, 0)).label('avg_round_size'),
            func.count(func.distinct(self.model.org_uuid)).label('companies_funded')
        ).filter(func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD') >= cutoff_date).first()
        
        # Get stats by investment type
        type_stats = db.query(
            self.model.investment_type,
            func.count(self.model.uuid).label('count'),
            func.sum(func.COALESCE(self.model.raised_amount_usd, 0)).label('total_amount')
        ).filter(
            func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD') >= cutoff_date
        ).group_by(
            self.model.investment_type
        ).all()
        
        return {
            "total_rounds": results.total_rounds,
            "total_raised": results.total_raised,
            "avg_round_size": results.avg_round_size,
            "companies_funded": results.companies_funded,
            "by_type": [
                {
                    "type": type_stat.investment_type,
                    "count": type_stat.count,
                    "total_amount": type_stat.total_amount
                }
                for type_stat in type_stats
            ]
        }

    def get_rounds_with_investors(
        self,
        db: Session,
        round_uuid: str
    ) -> Optional[Dict[str, Any]]:
        """Get funding round details with investor information"""
        round = self.get_by_uuid(db, round_uuid)
        if not round:
            return None
            
        # Get investors for this round
        investors = db.query(Investments)\
            .filter(Investments.funding_round_uuid == round_uuid)\
            .all()
            
        return {
            "round_info": round.__dict__,
            "investors": [
                {
                    "name": inv.investor_name,
                    "type": inv.investor_type,
                    "is_lead": inv.is_lead_investor
                }
                for inv in investors
            ]
        }

    def get_company_funding_stats(
        self,
        db: Session,
        company_uuid: str
    ) -> Dict[str, Any]:
        """Get comprehensive funding statistics for a company"""
        rounds = self.get_company_rounds(db, company_uuid)
        
        total_raised = sum(r.raised_amount_usd or 0 for r in rounds)
        avg_round_size = total_raised / len(rounds) if rounds else 0
        
        return {
            "total_rounds": len(rounds),
            "total_raised": total_raised,
            "avg_round_size": avg_round_size,
            "first_funding": min((r.announced_on for r in rounds), default=None),
            "last_funding": max((r.announced_on for r in rounds), default=None),
            "rounds": [
                {
                    "date": r.announced_on,
                    "type": r.investment_type,
                    "amount": r.raised_amount_usd,
                    "investors": r.investor_count
                }
                for r in rounds
            ]
        }

    def get_trending_sectors(
        self,
        db: Session,
        days: int = 90,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending sectors based on funding activity"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Join with companies to get category information
        results = db.query(
            Companies.category_list,
            func.count(self.model.uuid).label('round_count'),
            func.sum(func.COALESCE(self.model.raised_amount_usd, 0)).label('total_raised')
        ).join(
            Companies,
            Companies.uuid == self.model.org_uuid
        ).filter(
            func.TO_DATE(self.model.announced_on, 'YYYY-MM-DD') >= cutoff_date
        ).group_by(
            Companies.category_list
        ).order_by(
            desc('total_raised')
        ).limit(limit).all()
        
        return [
            {
                "category": r.category_list,
                "round_count": r.round_count,
                "total_raised": r.total_raised
            }
            for r in results
        ]