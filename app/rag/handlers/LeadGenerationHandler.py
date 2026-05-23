from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.CompanyRepository import CompanyRepository
from repositories.FundingRoundsRepository import FundingRoundsRepository
from repositories.CategoryGroupRepository import CategoryGroupRepository
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LeadGenerationHandler:
    """Handles lead generation queries for potential business opportunities"""
    
    def __init__(self, db: Session):
        self.db = db
        self.company_repo = CompanyRepository()
        self.funding_repo = FundingRoundsRepository()
        self.category_repo = CategoryGroupRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for lead generation queries"""
        return {
            "name": "get_potential_leads",
            "description": "Generate potential business leads based on criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_category": {
                        "type": "string",
                        "description": "Industry category to focus on (e.g., 'AI', 'Fintech', 'Healthcare')"
                    },
                    "location": {
                        "type": "object",
                        "properties": {
                            "country_code": {
                                "type": "string",
                                "description": "Two-letter country code (e.g., 'US', 'GB')"
                            },
                            "state_code": {
                                "type": "string",
                                "description": "State/province code"
                            },
                            "city": {
                                "type": "string",
                                "description": "City name"
                            }
                        },
                        "optional": True
                    },
                    "funding_criteria": {
                        "type": "object",
                        "properties": {
                            "min_funding": {
                                "type": "number",
                                "description": "Minimum total funding in USD"
                            },
                            "max_funding": {
                                "type": "number",
                                "description": "Maximum total funding in USD"
                            },
                            "days_since_funding": {
                                "type": "integer",
                                "description": "Only include companies funded within this many days",
                                "default": 365
                            }
                        },
                        "optional": True
                    },
                    "employee_range": {
                        "type": "string",
                        "description": "Employee count range (e.g., '1-10', '11-50', '51-200', '201-500', '501+')",
                        "optional": True
                    },
                    "max_leads": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of leads to return (1-50)",
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["target_category"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the lead generation query"""
        try:
            # Validate and prepare parameters
            max_leads = min(max(1, params.get("max_leads", 20)), 50)
            funding_criteria = params.get("funding_criteria", {})
            location = params.get("location", {})
            
            # Calculate funding date filter
            days_since_funding = funding_criteria.get("days_since_funding", 365)
            funding_after = None
            if days_since_funding:
                funding_after = (datetime.utcnow() - timedelta(days=days_since_funding)).strftime("%Y-%m-%d")

            # Search for companies matching criteria
            companies = self.company_repo.search_companies(
                self.db,
                categories=[params["target_category"]],
                min_funding=funding_criteria.get("min_funding"),
                founded_after=funding_after,
                country_code=location.get("country_code"),
                state_code=location.get("state_code"),
                city=location.get("city"),
                employee_range=params.get("employee_range"),
                status="operating",
                limit=max_leads
            )

            if not companies:
                return {
                    "status": "error",
                    "error": "No potential leads found matching the criteria",
                    "suggestions": [
                        "Try broadening your search criteria",
                        "Remove some filters",
                        "Try a different industry category",
                        "Expand the geographic area"
                    ]
                }

            # Get category statistics
            category_stats = self.company_repo.get_stats_by_category(
                self.db,
                params["target_category"]
            )

            # Get sector funding trends
            sector_trends = self.funding_repo.get_trending_sectors(
                self.db,
                days=90,
                limit=5
            )

            # Format lead data with enhanced information
            formatted_leads = []
            for company in companies:
                funding_history = self.funding_repo.get_company_funding_stats(
                    self.db,
                    company.uuid
                )

                lead_data = {
                    "company": {
                        "uuid": company.uuid,
                        "name": company.name,
                        "description": company.short_description,
                        "website": company.homepage_url,
                        "founded_on": company.founded_on,
                        "status": company.status,
                        "categories": company.category_list.split(",") if company.category_list else []
                    },
                    "contact": {
                        "email": company.email,
                        "phone": company.phone,
                        "linkedin": company.linkedin_url,
                        "twitter": company.twitter_url
                    },
                    "location": {
                        "country": company.country_code,
                        "state": company.state_code,
                        "city": company.city,
                        "address": company.address
                    },
                    "metrics": {
                        "total_funding": company.total_funding_usd,
                        "employee_count": company.employee_count,
                        "funding_rounds": funding_history.get("total_rounds", 0),
                        "last_funding": funding_history.get("last_funding"),
                        "avg_round_size": funding_history.get("avg_round_size")
                    }
                }
                formatted_leads.append(lead_data)

            response = {
                "leads": formatted_leads,
                "category_insights": {
                    "name": params["target_category"],
                    "total_companies": category_stats["total_companies"],
                    "total_funding": category_stats["total_funding"],
                    "avg_funding": category_stats["avg_funding"],
                    "recent_trends": sector_trends
                },
                "meta_data": {
                    "total_leads": len(formatted_leads),
                    "criteria_used": {
                        "category": params["target_category"],
                        "location": location,
                        "funding_criteria": funding_criteria,
                        "employee_range": params.get("employee_range"),
                        "search_date": datetime.utcnow().isoformat()
                    }
                }
            }

            return {"status": "success", "data": response}

        except Exception as e:
            logger.error(f"Error processing lead generation query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "details": "An error occurred while processing your request"
            }

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if data.get("status") != "success":
            return (
                f"Error: {data.get('error', 'Unknown error')}\n"
                f"Suggestions:\n" + 
                "\n".join(f"- {s}" for s in data.get("suggestions", []))
            )

        context_parts = ["📊 POTENTIAL BUSINESS LEADS REPORT"]
        
        # Category insights
        insights = data["data"]["category_insights"]
        context_parts.extend([
            f"\n🏢 Industry: {insights['name']}",
            f"\nMarket Overview:",
            f"• Total Companies: {insights['total_companies']:,}",
            f"• Average Funding: ${insights['avg_funding']:,.2f}",
            f"• Total Industry Funding: ${insights['total_funding']:,.2f}"
        ])

        # Recent trends
        if insights.get("recent_trends"):
            context_parts.extend([
                f"\n📈 Recent Trends:",
                *[f"• {trend['category']}: ${trend['total_raised']:,.2f} ({trend['round_count']} rounds)"
                  for trend in insights["recent_trends"][:3]]
            ])
        
        # Search criteria
        meta_data = data["data"]["meta_data"]
        criteria = meta_data["criteria_used"]
        context_parts.extend([
            f"\n🎯 Search Parameters:",
            f"• Category: {criteria['category']}",
            f"• Location: {str(criteria['location']) if criteria['location'] else 'Any'}",
            f"• Employee Range: {criteria['employee_range'] if criteria['employee_range'] else 'Any'}",
            f"• Date: {criteria['search_date'][:10]}"
        ])
        
        # Lead details
        leads = data["data"]["leads"]
        context_parts.extend([
            f"\n💼 Leads Generated: {len(leads)}",
            "\nTop Prospects:"
        ])
        
        for lead in leads:
            company = lead["company"]
            metrics = lead["metrics"]
            contact = lead["contact"]
            location = lead["location"]
            
            context_parts.extend([
                f"\n🏢 {company['name']}",
                f"📝 {company['description']}",
                f"📍 {location['city']}, {location['country']}",
                f"💰 Metrics:",
                f"  • Total Funding: ${metrics['total_funding']:,.2f}",
                f"  • Team Size: {metrics['employee_count']}",
                f"  • Last Round: {metrics['last_funding']}",
                f"📱 Contact:",
                f"  • Web: {company['website']}",
                f"  • LinkedIn: {contact['linkedin']}",
                "──────────────"
            ])

        return "\n".join(context_parts)