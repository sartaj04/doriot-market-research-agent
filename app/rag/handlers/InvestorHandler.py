from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.InvestorRepository import InvestorsRepository

logger = logging.getLogger(__name__)

class InvestorHandler:
    """Handles investor-related queries and operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.investor_repo = InvestorsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for investor queries"""
        return {
            "name": "get_investor_information",
            "description": "Get comprehensive information about investors including their profiles, investments, and network",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name or partial name of the investor to search for",
                        "optional": True
                    },
                    "investor_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of investors to filter by (e.g., ['Organization', 'Person'])",
                        "optional": True
                    },
                    "category": {
                        "type": "string",
                        "description": "Industry/category to filter investors by (e.g., 'Fintech', 'AI', 'Healthcare')",
                        "optional": True
                    },
                    "query_type": {
                        "type": "string",
                        "enum": ["search", "top_investors", "similar_investors", "full_profile", "category_leaders"],
                        "description": "Type of query to perform",
                        "default": "search"
                    },
                    "min_investments": {
                        "type": "integer",
                        "description": "Minimum number of investments made",
                        "optional": True
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Filter by country code",
                        "optional": True
                    },
                    "min_rank": {
                        "type": "number",
                        "description": "Minimum investor rank to include",
                        "optional": True
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["investment_count", "total_funding_usd", "rank"],
                        "description": "Metric to sort results by",
                        "default": "investment_count"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["all", "year", "half_year"],
                        "description": "Time period for filtering results",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "optional": True
                    }
                },
                "required": ["query_type"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the investor query based on parameters"""
        try:
            query_type = params.get("query_type", "search")
            limit = params.get("limit", 10)
            investors = None
            category = params.get("category")

            if query_type == "category_leaders" and category:
                # Get top investors in specific category
                investors = self.investor_repo.get_category_leaders(
                    self.db,
                    category=category,
                    limit=limit
                )

            elif query_type == "top_investors":
                investors = self.investor_repo.get_top_investors(
                    self.db,
                    by_metric=params.get("sort_by", "investment_count"),
                    investor_type=params.get("investor_types", [None])[0],
                    category=category,
                    time_period=params.get("time_period"),
                    limit=limit
                )
            elif query_type == "similar_investors" and params.get("name"):
                # First find the investor by name to get UUID
                base_investors = self.investor_repo.search_investors(
                    self.db,
                    name=params["name"],
                    limit=1
                )
                if base_investors:
                    investors = self.investor_repo.get_similar_investors(
                        self.db,
                        base_investors[0].uuid,
                        limit=limit
                    )
            elif query_type == "full_profile" and params.get("name"):
                # Get full investor profile with all details
                investors = self.investor_repo.search_investors(
                    self.db,
                    name=params["name"],
                    limit=1
                )
                if investors:
                    stats = self.investor_repo.get_investor_stats(
                        self.db,
                        investors[0].uuid
                    )
                    return {
                        "status": "success",
                        "data": {
                            "query_type": "full_profile",
                            "profile": stats
                        }
                    }
            else:
                # Default search
                investors = self.investor_repo.search_investors(
                    self.db,
                    name=params.get("name"),
                    investor_types=params.get("investor_types"),
                    min_investments=params.get("min_investments"),
                    country_code=params.get("country_code"),
                    min_rank=params.get("min_rank"),
                    limit=limit
                )

            if not investors:
                return {
                    "status": "error",
                    "error": "No investors found matching the criteria"
                }

            # Format investor information
            formatted_investors = [{
                "basic_info": {
                    "name": inv.name,
                    "type": inv.type,
                    "rank": inv.rank,
                    "description": inv.description
                },
                "metrics": {
                    "investment_count": inv.investment_count,
                    "total_investments": inv.total_investments,
                    "total_funding_usd": inv.total_funding_usd
                },
                "location": {
                    "country": inv.country_code,
                    "city": inv.city,
                    "region": inv.region
                },
                "links": {
                    "website": inv.domain,
                    "linkedin": inv.linkedin_url,
                    "cb_url": inv.cb_url
                }
            } for inv in investors]

            return {
                "status": "success",
                "data": {
                    "query_type": query_type,
                    "total_found": len(formatted_investors),
                    "investors": formatted_investors
                }
            }

        except Exception as e:
            logger.error(f"Error processing investor query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process investor query: {str(e)}"
            }

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the investor results for context"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        query_type = data["data"]["query_type"]
        context_parts = ["INVESTOR INFORMATION"]
        
        if query_type == "full_profile":
            profile = data["data"]["profile"]
            basic = profile["basic_info"]
            metrics = profile["investment_metrics"]
            location = profile["location"]
            analysis = profile.get("investment_analysis", {})
            network = profile.get("co_investment_network", {})
            
            context_parts.extend([
                f"\nInvestor Profile:",
                f"Name: {basic['name']}",
                f"Type: {basic['type']}",
                f"Rank: {basic['rank']}",
                f"Location: {location['city']}, {location['country']}",
                
                f"\nInvestment Metrics:",
                f"- Total Investments: {metrics['investment_count']}",
                f"- Total Funding (USD): ${metrics['total_funding_usd']:,.2f}" if metrics['total_funding_usd'] else "",
                
                "\nInvestment Focus:",
                "Top Investment Rounds:",
                *[f"- {k}: {v}" for k, v in analysis.get("top_investment_rounds", {}).items()],
                
                "\nTop Categories:",
                *[f"- {k}: {v}" for k, v in analysis.get("top_categories", {}).items()],
                
                "\nTop Investment Locations:",
                *[f"- {k}: {v}" for k, v in analysis.get("top_locations", {}).items()],
                
                "\nTop Co-investors:",
                *[f"- {inv['name']}" for inv in network.get("co_investors", [])[:5]]
            ])
            
        else:
            investors = data["data"]["investors"]
            context_parts.extend([
                f"\nQuery Type: {query_type.replace('_', ' ').title()}",
                f"Total Results: {len(investors)}"
            ])
            
            for inv in investors:
                basic = inv["basic_info"]
                metrics = inv["metrics"]
                location = inv["location"]
                
                context_parts.extend([
                    f"\n- {basic['name']}",
                    f"  Type: {basic['type']}",
                    f"  Rank: {basic['rank']}",
                    f"  Investments: {metrics['investment_count']}",
                    f"  Location: {location['city']}, {location['country']}",
                    "  ---"
                ])

        return "\n".join(filter(None, context_parts))