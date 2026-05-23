from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from repositories.CompanyRepository import CompanyRepository
from repositories.FundingRoundsRepository import FundingRoundsRepository
from repositories.CategoryGroupRepository import CategoryGroupRepository
from repositories.ArticlesRepository import ArticlesRepository

logger = logging.getLogger(__name__)

class MarketAnalysisHandler:
    """Handles MARKET_ANALYSIS_QUERY intent operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.company_repo = CompanyRepository()
        self.funding_repo = FundingRoundsRepository()
        self.category_repo = CategoryGroupRepository()
        self.articles_repo = ArticlesRepository()


    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "analyze_market",
            "description": "Perform comprehensive market analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "market_segment": {
                        "type": "string",
                        "description": "Market segment or category to analyze (e.g., 'AI', 'Fintech', 'Healthcare')"
                    },
                    "timeframe": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Analysis start date (YYYY-MM-DD)",
                                "pattern": "^\d{4}-\d{2}-\d{2}$"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Analysis end date (YYYY-MM-DD)",
                                "pattern": "^\d{4}-\d{2}-\d{2}$"
                            }
                        },
                        "optional": True
                    },
                    "analysis_type": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "funding_trends",
                                "company_growth",
                                "geographic_distribution",
                                "investor_activity",
                                "market_news"
                            ]
                        },
                        "description": "Types of analysis to perform (defaults to all if not specified)",
                        "default": ["funding_trends", "company_growth", "geographic_distribution", "investor_activity", "market_news"]
                    },
                    "region": {
                        "type": "string",
                        "description": "Geographic region to focus on (e.g., 'North America', 'Europe', 'Asia')",
                        "optional": True
                    }
                },
                "required": ["market_segment"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the market analysis query"""
        try:
            response = {
                "market_segment": params["market_segment"],
                "analysis_date": datetime.now().isoformat()
            }

            # Get category overview
            category_stats = self.company_repo.get_stats_by_category(
                self.db,
                params["market_segment"]
            )
            
            response["market_overview"] = {
                "total_companies": category_stats["total_companies"],
                "total_funding": category_stats["total_funding"],
                "avg_funding": category_stats["avg_funding"],
                "companies_with_funding": category_stats["companies_with_funding"]
            }

            analysis_types = params.get("analysis_type", [])

            # Analyze funding trends
            if "funding_trends" in analysis_types:
                trending_sectors = self.funding_repo.get_trending_sectors(
                    self.db,
                    days=90,
                    limit=5
                )
                
                funding_stats = self.funding_repo.get_funding_stats(
                    self.db,
                    days=90
                )
                
                response["funding_analysis"] = {
                    "trending_sectors": trending_sectors,
                    "recent_stats": funding_stats
                }

            # Analyze company growth
            if "company_growth" in analysis_types:
                trending_companies = self.company_repo.get_trending_companies(
                    self.db,
                    days=90,
                    categories=[params["market_segment"]],
                    limit=10
                )
                
                response["growth_analysis"] = {
                    "trending_companies": [
                        {
                            "name": company.name,
                            "growth_metrics": {
                                "funding_growth": company.total_funding_usd,
                                "employee_growth": company.employee_count,
                                "last_funding": company.last_funding_on
                            }
                        }
                        for company in trending_companies
                    ]
                }

            # Analyze geographic distribution
            if "geographic_distribution" in analysis_types:
                companies = self.company_repo.get_by_category(
                    self.db,
                    params["market_segment"],
                    limit=1000
                )
                
                # Group companies by region
                geo_distribution = {}
                for company in companies:
                    region = company.region or "Unknown"
                    if region not in geo_distribution:
                        geo_distribution[region] = {
                            "company_count": 0,
                            "total_funding": 0
                        }
                    geo_distribution[region]["company_count"] += 1
                    geo_distribution[region]["total_funding"] += (company.total_funding_usd or 0)
                
                response["geographic_analysis"] = {
                    "distribution": geo_distribution
                }

            # Analyze investor activity
            if "investor_activity" in analysis_types:
                recent_rounds = self.funding_repo.get_latest_rounds(
                    self.db,
                    days=90,
                    limit=10
                )
                
                response["investor_analysis"] = {
                    "recent_investments": [
                        {
                            "round_type": round.investment_type,
                            "amount": round.raised_amount_usd,
                            "company": round.org_name,
                            "investor_count": round.investor_count,
                            "date": round.announced_on
                        }
                        for round in recent_rounds
                    ]
                }

            # Analyze market news
            if "market_news" in analysis_types:
                # Get recent market news from TechCrunch
                startup_articles = await self.articles_repo.get_articles(
                    self.db,
                    query=params["market_segment"],
                    days=90,
                    limit=5
                )
                
                
                response["news_analysis"] = {
                    "recent_articles": [
                        {
                            "title": article.title if article.title else "No Title",
                            "url": article.url if article.url else "Failed to retrieve URL",
                            "published_at": str(article.published_at) if article.published_at else "Unknown",
                            "source": source if source else "Techcrunch"
                        }
                        for source, articles in [
                            ("News Articles", startup_articles)
                        ]
                        for article in articles
                    ]
                }

            return {
                "status": "success",
                "data": response
            }

        except Exception as e:
            logger.error(f"Error processing market analysis query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process market analysis query: {str(e)}"
            }

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        context_parts = ["MARKET ANALYSIS REPORT"]
        
        # Market Overview
        market_data = data["data"]
        overview = market_data["market_overview"]
        context_parts.extend([
            f"\nMarket Segment: {market_data['market_segment']}",
            f"Analysis Date: {market_data['analysis_date']}",
            "\nMarket Overview:",
            f"- Total Companies: {overview['total_companies'] or 0}",
            f"- Total Market Funding: ${overview['total_funding']:,.2f}" if overview['total_funding'] is not None else "- Total Market Funding: N/A",
            f"- Average Company Funding: ${overview['avg_funding']:,.2f}" if overview['avg_funding'] is not None else "- Average Company Funding: N/A",
            f"- Companies with Funding: {overview['companies_with_funding'] or 0}"
        ])

        # Funding Analysis
        if "funding_analysis" in market_data:
            funding = market_data["funding_analysis"]
            context_parts.extend([
                "\nFunding Trends:",
                "Top Sectors by Funding:"
            ])
            for sector in funding["trending_sectors"]:
                total_raised = sector['total_raised'] or 0
                round_count = sector['round_count'] or 0
                context_parts.append(
                    f"- {sector['category']}: ${total_raised:,.2f} "
                    f"({round_count} rounds)"
                )

        # Growth Analysis
        if "growth_analysis" in market_data:
            growth = market_data["growth_analysis"]
            context_parts.extend([
                "\nTop Growing Companies:"
            ])
            for company in growth["trending_companies"]:
                metrics = company["growth_metrics"]
                funding_growth = metrics['funding_growth'] or 0
                employee_count = metrics['employee_growth'] or 'N/A'
                last_funding = metrics['last_funding'] or 'N/A'
                context_parts.extend([
                    f"- {company['name']}:",
                    f"  * Total Funding: ${funding_growth:,.2f}",
                    f"  * Employees: {employee_count}",
                    f"  * Last Funding: {last_funding}"
                ])

        # Geographic Analysis
        if "geographic_analysis" in market_data:
            geo = market_data["geographic_analysis"]["distribution"]
            context_parts.extend([
                "\nGeographic Distribution:"
            ])
            for region, stats in geo.items():
                total_funding = stats['total_funding'] or 0
                context_parts.append(
                    f"- {region}: {stats['company_count']} companies, "
                    f"${total_funding:,.2f} total funding"
                )

        # Investor Activity
        if "investor_analysis" in market_data:
            investor = market_data["investor_analysis"]
            context_parts.extend([
                "\nRecent Investment Activity:"
            ])
            for investment in investor["recent_investments"]:
                amount = investment['amount'] or 0
                context_parts.append(
                    f"- {investment['company']}: {investment['round_type']}, "
                    f"${amount:,.2f} ({investment['date']})"
                )

        # Market News
        if "news_analysis" in market_data:
            news = market_data["news_analysis"]
            context_parts.extend([
                "\nRecent Market News:"
            ])
            for article in news["recent_articles"]:
                context_parts.extend([
                    f"- {article['title']}",
                    f"  Published: {article['published_at']} ({article['source']})",
                    f"  URL: {article['url']}"
                ])

        return "\n".join(context_parts)