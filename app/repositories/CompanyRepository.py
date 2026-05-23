from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from models.companies import Companies
from .BaseRepository import BaseRepository
from core.embeddings import compute_text_embedding  # Import the function from the appropriate module

from typing import List, Optional, Dict, Any, Union
from openai import AsyncOpenAI, AsyncAzureOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from datetime import datetime, timedelta

from models.companies import Companies
from models.fundingrounds import FundingRounds
from models.acquisitions import Acquisitions
from .BaseRepository import BaseRepository
from .ArticlesRepository import ArticlesRepository
from models.organizationdescriptions import OrganizationDescriptions
import logging

logger = logging.getLogger(__name__)

class CompanyRepository(BaseRepository[Companies]):
    def __init__(self):
        super().__init__(Companies)

    def search_companies(
        self,
        db: Session,
        *,
        name: Optional[str] = None,
        categories: Optional[List[str]] = None,
        min_funding: Optional[float] = None,
        founded_after: Optional[str] = None,
        country_code: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Search companies with multiple criteria"""
        query = db.query(self.model)
        
        if name:
            query = query.filter(
                or_(
                    self.model.name.ilike(f"%{name}%"),
                    self.model.legal_name.ilike(f"%{name}%")
                )
            )
            
        if categories:
            category_filters = [
                self.model.category_list.ilike(f"%{cat}%")
                for cat in categories
            ]
            query = query.filter(or_(*category_filters))
            
        if min_funding:
            query = query.filter(func.COALESCE(self.model.total_funding_usd, 0) >= min_funding)
            
        if founded_after:
            func.TO_DATE(self.model.founded_on, 'YYYY-MM-DD') >= founded_after
            
        if country_code:
            query = query.filter(self.model.country_code == country_code)
            
        if status:
            query = query.filter(self.model.status == status)
            
        return query.order_by(desc(func.COALESCE(self.model.total_funding_usd, 0)))\
            .offset(skip).limit(limit).all()

    async def get_competitors(
        self,
        db: Session,
        company_uuid: str,
        openai_client: Union[AsyncOpenAI, AsyncAzureOpenAI],
        limit: int = 10
    ) -> List[Companies]:
        """Get potential competitors based on category and funding range"""
        # Get company by UUID
        company = self.get_by_uuid(db, company_uuid)
        if not company:
            return []

        # Get company's categories
        categories = company.category_list.split(",") if company.category_list else []

        # Base query
        base_query = db.query(self.model).filter(self.model.uuid != company_uuid)

        # Apply category filters if available
        if categories:
            base_query = base_query.filter(
                or_(*[self.model.category_list.ilike(f"%{cat}%") for cat in categories])
            )

        # Apply funding range filter if company has funding
        if company.total_funding_usd:
            base_query = base_query.filter(
                func.COALESCE(self.model.total_funding_usd, 0).between(
                    company.total_funding_usd * 0.5,
                    company.total_funding_usd * 2
                )
            )

        # Add employee count similarity if available
        if company.employee_count:
            base_query = base_query.filter(self.model.employee_count == company.employee_count)

        # Order by funding amount similarity
        return base_query\
            .order_by(
                func.abs(
                    func.COALESCE(self.model.total_funding_usd, 0) - 
                    func.COALESCE(company.total_funding_usd, 0)
                )
            )\
            .limit(limit)\
            .all()
    
    def get_companies_by_funding_range(
        self,
        db: Session,
        min_amount: float,
        max_amount: Optional[float] = None,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Get companies within a funding range"""
        query = db.query(self.model)\
            .filter(func.COALESCE(self.model.total_funding_usd, 0) >= min_amount)
            
        if max_amount:
            query = query.filter(func.COALESCE(self.model.total_funding_usd, 0) <= max_amount)
            
        return query.order_by(desc(func.COALESCE(self.model.total_funding_usd, 0)))\
            .offset(skip).limit(limit).all()

    def get_companies_by_employee_count(
        self,
        db: Session,
        employee_range: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Get companies by employee count range"""
        return db.query(self.model)\
            .filter(self.model.employee_count == employee_range)\
            .order_by(desc(func.COALESCE(self.model.total_funding_usd, 0)))\
            .offset(skip).limit(limit).all()

    def get_recently_funded(
        self,
        db: Session,
        days: int = 30,
        min_amount: Optional[float] = None,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Get companies that received funding recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = db.query(self.model)\
            .filter(func.TO_DATE(self.model.last_funding_on, 'YYYY-MM-DD') >= cutoff_date)
            
        if min_amount:
            query = query.filter(func.COALESCE(self.model.total_funding_usd, 0) >= min_amount)
            
        return query.order_by(desc(func.TO_DATE(self.model.last_funding_on, 'YYYY-MM-DD')))\
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
    ) -> List[Companies]:
        """Get companies by location"""
        query = db.query(self.model)
        
        if country_code:
            query = query.filter(self.model.country_code == country_code)
        if state_code:
            query = query.filter(self.model.state_code == state_code)
        if city:
            query = query.filter(self.model.city.ilike(f"%{city}%"))
            
        return query.order_by(desc(func.COALESCE(self.model.total_funding_usd, 0)))\
            .offset(skip).limit(limit).all()

    def get_by_category(
        self,
        db: Session,
        category: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Get companies by category"""
        return db.query(self.model)\
            .filter(self.model.category_list.ilike(f"%{category}%"))\
            .order_by(desc(func.COALESCE(self.model.total_funding_usd, 0)))\
            .offset(skip).limit(limit).all()

    def get_top_funded(
        self,
        db: Session,
        *,
        category: Optional[str] = None,
        country_code: Optional[str] = None,
        limit: int = 10
    ) -> List[Companies]:
        """Get top funded companies, optionally filtered by category or country"""
        query = db.query(self.model)
        
        if category:
            query = query.filter(self.model.category_list.ilike(f"%{category}%"))
        if country_code:
            query = query.filter(self.model.country_code == country_code)
            
        return query.order_by(desc(func.COALESCE(self.model.total_funding_usd, 0))).limit(limit).all()

    def get_stats_by_category(
        self,
        db: Session,
        category: str
    ) -> Dict[str, Any]:
        """Get statistics for companies in a category"""
        query = db.query(self.model)\
            .filter(self.model.category_list.ilike(f"%{category}%"))
            
        results = db.query(
            func.count(self.model.uuid).label('total_companies'),
            func.sum(func.COALESCE(self.model.total_funding_usd, 0)).label('total_funding'),
            func.avg(func.COALESCE(self.model.total_funding_usd, 0)).label('avg_funding'),
            func.count(func.TO_DATE(self.model.last_funding_on, 'YYYY-MM-DD')).label('companies_with_funding')
        ).filter(self.model.category_list.ilike(f"%{category}%")).first()
        
        return {
            "total_companies": results.total_companies,
            "total_funding": results.total_funding,
            "avg_funding": results.avg_funding,
            "companies_with_funding": results.companies_with_funding
        }

    def get_funding_timeline(
        self,
        db: Session,
        company_uuid: str
    ) -> List[Dict[str, Any]]:
        """Get company's funding timeline"""
        company = self.get_by_uuid(db, company_uuid)
        if not company:
            return []
            
        funding_rounds = db.query(FundingRounds)\
            .filter(FundingRounds.org_uuid == company_uuid)\
            .order_by(FundingRounds.announced_on.asc())\
            .all()
            
        return [
            {
                "date": round.announced_on,
                "type": round.investment_type,
                "amount": round.raised_amount_usd,
                "investors": round.investor_count,
                "valuation": round.post_money_valuation_usd
            }
            for round in funding_rounds
        ]

    def get_acquisition_history(
        self,
        db: Session,
        company_uuid: str
    ) -> List[Dict[str, Any]]:
        """Get company's acquisition history (both as acquirer and acquired)"""
        acquisitions = db.query(Acquisitions).filter(
            or_(
                Acquisitions.acquirer_uuid == company_uuid,
                Acquisitions.acquiree_uuid == company_uuid
            )
        ).order_by(Acquisitions.acquired_on.asc()).all()
        
        return [
            {
                "date": acq.acquired_on,
                "role": "acquirer" if acq.acquirer_uuid == company_uuid else "acquired",
                "other_party": acq.acquiree_name if acq.acquirer_uuid == company_uuid else acq.acquirer_name,
                "price": acq.price_usd
            }
            for acq in acquisitions
        ]

    def get_company_full_profile(
        self,
        db: Session,
        company_uuid: str
    ) -> Dict[str, Any]:
        """Get comprehensive company profile including related data"""
        company = self.get_by_uuid(db, company_uuid)
        if not company:
            return {}
            
        # Get basic info
        profile = company.__dict__
        
        # Add funding timeline
        profile['funding_timeline'] = self.get_funding_timeline(db, company_uuid)
        
        # Add acquisition history
        profile['acquisitions'] = self.get_acquisition_history(db, company_uuid)
        
        # Get competitors
        profile['competitors'] = [
            comp.__dict__ for comp in self.get_competitors(db, company.uuid, limit=5)
        ]
        



        # Get TechCrunch startup articles
        profile['related_articles'] = []
        try:
            startup_repo = ArticlesRepository()
            startup_articles = startup_repo.get_articles(
                db, 
                keywords=[company.name], 
                days=90, 
                limit=5
            )
            profile['related_articles'] = [
                {
                    'title': article.title,
                    'url': article.url,
                    'published_at': article.published_at,
                    'author': article.author
                } for article in startup_articles
            ]
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")


    def get_trending_companies(
        self,
        db: Session,
        *,
        days: int = 30,
        min_funding: Optional[float] = None,
        categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Companies]:
        """Get trending companies based on recent funding and growth"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(self.model)\
            .filter(func.TO_DATE(self.model.last_funding_on, 'YYYY-MM-DD') >= cutoff_date)
            
        if min_funding:
            query = query.filter(func.COALESCE(self.model.total_funding_usd, 0) >= min_funding)
            
        if categories:
            category_filters = [
                self.model.category_list.ilike(f"%{cat}%")
                for cat in categories
            ]
            query = query.filter(or_(*category_filters))
            
        return query.order_by(
            desc(func.TO_DATE(self.model.last_funding_on, 'YYYY-MM-DD')),
            desc(func.COALESCE(self.model.total_funding_usd, 0))
        ).limit(limit).all()

    def get_companies_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Get companies by their current status"""
        return db.query(self.model)\
            .filter(self.model.status == status)\
            .order_by(desc(func.COALESCE(self.model.total_funding_usd, 0)))\
            .offset(skip).limit(limit).all()

    def get_companies_without_funding(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Companies]:
        """Get companies that haven't received funding yet"""
        return db.query(self.model)\
            .filter(self.model.total_funding_usd.is_(None))\
            .order_by(func.TO_DATE(self.model.founded_on, 'YYYY-MM-DD').desc())\
            .offset(skip).limit(limit).all()