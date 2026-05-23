from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text, Text
from datetime import datetime, timedelta
import json

from models.investors import Investors
from .BaseRepository import BaseRepository

class InvestorsRepository(BaseRepository[Investors]):
    def __init__(self):
        super().__init__(Investors)

    def search_investors(
        self,
        db: Session,
        *,
        name: Optional[str] = None,
        investor_types: Optional[List[str]] = None,
        min_investments: Optional[int] = None,
        country_code: Optional[str] = None,
        founded_after: Optional[str] = None,
        founded_before: Optional[str] = None,
        min_rank: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Investors]:
        """Enhanced search with additional criteria"""
        query = db.query(self.model)
        
        if name:
            query = query.filter(or_(
                self.model.name.ilike(f"%{name}%"),
                self.model.permalink.ilike(f"%{name}%")
            ))
            
        if investor_types:
            type_filters = [
                self.model.investor_types.ilike(f"%{t}%")
                for t in investor_types
            ]
            query = query.filter(or_(*type_filters))
            
        if min_investments:
            query = query.filter(func.COALESCE(self.model.investment_count, 0) >= min_investments)
            
        if country_code:
            query = query.filter(self.model.country_code == country_code)
            
        if founded_after:
            query = query.filter(self.model.founded_on >= founded_after)
            
        if founded_before:
            query = query.filter(self.model.founded_on <= founded_before)
            
        if min_rank:
            query = query.filter(func.COALESCE(self.model.rank, float('inf')) <= min_rank)
            
        return query.order_by(desc(func.COALESCE(self.model.investment_count, 0)))\
            .offset(skip).limit(limit).all()
    
    def get_investor_network(
        self,
        db: Session,
        investor_uuid: str
    ) -> Dict[str, Any]:
        """Get investor's co-investment network"""
        investor = self.get_by_uuid(db, investor_uuid)
        if not investor or not investor.combined_co_lead_list:
            return {
                "co_investors": [],
                "total_co_investors": 0
            }

        try:
            co_investors = investor.combined_co_lead_list
            if isinstance(co_investors, str):
                co_investors = json.loads(co_investors)
            
            return {
                "co_investors": [{"name": name} for name in co_investors],
                "total_co_investors": len(co_investors)
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "co_investors": [],
                "total_co_investors": 0
            }

    def get_competitive_landscape(
        self,
        db: Session,
        investor_uuid: str,
        *,
        time_period: Optional[str] = None  # Kept for API compatibility
    ) -> Dict[str, Any]:
        """
        Get investor's competitive landscape from pre-analyzed list
        Returns top competitors
        """
        investor = self.get_by_uuid(db, investor_uuid)
        if not investor or not investor.competitors_list:
            return {
                "competitors": [],
                "total_competitors": 0
            }

        try:
            competitors_list = investor.competitors_list
            if isinstance(competitors_list, str):
                competitors_list = json.loads(competitors_list)
            
            return {
                "competitors": [{"name": name} for name in competitors_list],
                "total_competitors": len(competitors_list)
            }
            
        except (json.JSONDecodeError, AttributeError):
            return {
                "competitors": [],
                "total_competitors": 0
            }
    def get_investment_preferences(
        self,
        db: Session,
        investor_uuid: str
    ) -> Dict[str, Any]:
        """Get investor's investment preferences based on their top series, categories, and locations"""
        investor = self.get_by_uuid(db, investor_uuid)
        if not investor:
            return {}

        preferences = {}

        # Handle dictionary format for top_3_series: {'series_type': count}
        if investor.top_3_series:
            series_data = investor.top_3_series
            if isinstance(series_data, str):
                series_data = json.loads(series_data)
            preferences["preferred_rounds"] = [
                {"round_type": series_type, "count": count}
                for series_type, count in series_data.items()
            ]

        # Handle dictionary format for top_3_categories: {'category': count}
        if investor.top_3_categories:
            categories_data = investor.top_3_categories
            if isinstance(categories_data, str):
                categories_data = json.loads(categories_data)
            preferences["preferred_categories"] = [
                {"category": category, "count": count}
                for category, count in categories_data.items()
            ]

        # Handle dictionary format for top_3_locations: {'location': count}
        if investor.top_3_locations:
            locations_data = investor.top_3_locations
            if isinstance(locations_data, str):
                locations_data = json.loads(locations_data)
            preferences["preferred_locations"] = [
                {"location": location, "count": count}
                for location, count in locations_data.items()
            ]

        return preferences
    def get_category_leaders(
        self,
        db: Session,
        category: str,
        *,
        limit: int = 10
    ) -> List[Investors]:
        """Get top investors in a specific category based on their top_3_categories"""
        investors = []
        # First get all investors with top_3_categories
        query = db.query(self.model).filter(
            self.model.top_3_categories.isnot(None)
        )
        
        all_investors = query.all()
        category_scores = []
        
        for investor in all_investors:
            try:
                categories = investor.top_3_categories
                if isinstance(categories, str):
                    categories = json.loads(categories)
                    
                # Check if the category exists in top categories
                if category.lower() in {k.lower(): v for k, v in categories.items()}:
                    category_scores.append({
                        "investor": investor,
                        "score": categories.get(category, 0)
                    })
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Sort by category score and return top N
        sorted_investors = sorted(
            category_scores,
            key=lambda x: x["score"],
            reverse=True
        )
        return [item["investor"] for item in sorted_investors[:limit]]

    def get_top_investors(
        self,
        db: Session,
        *,
        by_metric: str = "investment_count",
        investor_type: Optional[str] = None,
        category: Optional[str] = None,
        time_period: Optional[str] = None,
        limit: int = 10
    ) -> List[Investors]:
        """Get top investors with additional filtering"""
        query = db.query(self.model)
        
        if investor_type:
            query = query.filter(self.model.investor_types.ilike(f"%{investor_type}%"))
            
        if category:
            # Filter investors who have invested in this category
            query = query.filter(
                self.model.top_3_categories.cast(Text).ilike(f"%{category}%")
            )
            
        if time_period:
            date_threshold = datetime.now() - timedelta(days=365 if time_period == "year" else 180)
            query = query.filter(self.model.created_at >= date_threshold)
            
        order_column = getattr(self.model, by_metric)
        return query.filter(order_column.isnot(None))\
            .order_by(desc(order_column))\
            .limit(limit).all()

    def get_investor_stats(
        self,
        db: Session,
        investor_uuid: str
    ) -> Dict[str, Any]:
        """Get comprehensive investor statistics"""
        investor = self.get_by_uuid(db, investor_uuid)
        if not investor:
            return {}
            
        stats = {
            "basic_info": {
                "name": investor.name,
                "type": investor.type,
                "rank": investor.rank,
                "description": investor.description,
            },
            "investment_metrics": {
                "investment_count": investor.investment_count,
                "total_investments": investor.total_investments,
                "total_funding_usd": investor.total_funding_usd,
                "total_funding": investor.total_funding,
                "total_funding_currency_code": investor.total_funding_currency_code,
            },
            "location": {
                "country": investor.country_code,
                "state": investor.state_code,
                "region": investor.region,
                "city": investor.city
            },
            "dates": {
                "founded_on": investor.founded_on,
                "closed_on": investor.closed_on,
                "created_at": investor.created_at,
                "updated_at": investor.updated_at
            },
            "social_presence": {
                "domain": investor.domain,
                "facebook": investor.facebook_url,
                "linkedin": investor.linkedin_url,
                "twitter": investor.twitter_url,
                "logo": investor.logo_url
            }
        }

        investment_analysis = {}
        
        if investor.top_3_series:
            series_data = investor.top_3_series
            if isinstance(series_data, str):
                series_data = json.loads(series_data)
            investment_analysis["top_investment_rounds"] = series_data

        if investor.top_3_categories:
            categories_data = investor.top_3_categories
            if isinstance(categories_data, str):
                categories_data = json.loads(categories_data)
            investment_analysis["top_categories"] = categories_data

        if investor.top_3_locations:
            locations_data = investor.top_3_locations
            if isinstance(locations_data, str):
                locations_data = json.loads(locations_data)
            investment_analysis["top_locations"] = locations_data

        stats["investment_analysis"] = investment_analysis

        # Add network information
        network_info = self.get_investor_network(db, investor_uuid)
        stats["co_investment_network"] = network_info

        # Add competitive landscape
        competitive_info = self.get_competitive_landscape(db, investor_uuid)
        stats["competitive_landscape"] = competitive_info

        return stats

    def get_similar_investors(
        self,
        db: Session,
        investor_uuid: str,
        limit: int = 10
    ) -> List[Investors]:
        """Find similar investors based on categories and investment patterns"""
        investor = self.get_by_uuid(db, investor_uuid)
        if not investor:
            return []
            
        return db.query(self.model)\
            .filter(
                and_(
                    self.model.uuid != investor_uuid,
                    self.model.investor_types == investor.investor_types,
                    func.COALESCE(self.model.investment_count, 0) > 0
                )
            )\
            .order_by(
                func.abs(self.model.investment_count - investor.investment_count)
            )\
            .limit(limit).all()