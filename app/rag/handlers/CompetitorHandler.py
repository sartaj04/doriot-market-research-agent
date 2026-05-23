from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.CompanyRepository import CompanyRepository
from repositories.CategoryGroupRepository import CategoryGroupRepository
from models.companies import Companies

logger = logging.getLogger(__name__)

class CompetitorHandler:
    """Handles COMPETITOR_LOOKUP intent operations"""
    
    def __init__(self, db: Session, openai_client: Any):
        self.openai_client = openai_client
        self.db = db
        self.company_repo = CompanyRepository()
        self.category_repo = CategoryGroupRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for competitor lookup queries"""
        return {
            "name": "get_competitors",
            "description": "Get competitive analysis and market competitors",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to analyze"
                    },
                    "category": {
                        "type": "string",
                        "description": "Specific category to focus on",
                        "optional": True
                    },
                    "max_competitors": {
                        "type": "integer",
                        "description": "Maximum number of competitors to return",
                        "default": 5
                    },
                    "include_metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["funding", "employees", "acquisitions", "revenue"]
                        },
                        "description": "Metrics to include in comparison"
                    }
                },
                "required": ["company_name"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the competitor lookup query"""
        try:
            # Find company by name
            companies = self.company_repo.search_companies(
                self.db,
                name=params["company_name"],
                limit=1
            )
            
            if not companies:
                return {
                    "status": "error",
                    "error": f"Company '{params['company_name']}' not found"
                }
            company_query = companies[0]
            # Get competitors using company ID
            competitors = await self.company_repo.get_competitors(
                db=self.db,
                company_uuid=company_query.uuid,
                openai_client=self.openai_client,
                limit=5
            )

            

            if not competitors:
                return {
                    "status": "error",
                    "error": "No competitors found matching the criteria"
                }

            # Get category information if specified
            category_info = {
                "name": params.get("category", "Unknown"),
                "total_companies": 0,
                "total_funding": 0,
                "avg_funding": 0
            }  # Initialize with default values
            
            if params.get("category"):
                try:
                    category_stats = self.company_repo.get_stats_by_category(
                        self.db,
                        params["category"]
                    )
                    
                    # Only update if category_stats exists and has the required keys
                    if category_stats and isinstance(category_stats, dict):
                        if "total_companies" in category_stats:
                            category_info["total_companies"] = category_stats["total_companies"]
                        if "total_funding" in category_stats:
                            category_info["total_funding"] = category_stats["total_funding"]
                        if "avg_funding" in category_stats:
                            category_info["avg_funding"] = category_stats["avg_funding"]
                except Exception as e:
                    logger.warning(f"Error getting category stats: {str(e)}")
                    # Keep the default category_info values
            else:
                # If no category is specified, set category_info to an empty dict with proper structure
                category_info = {
                    "name": "Unknown",
                    "total_companies": 0,
                    "total_funding": 0,
                    "avg_funding": 0
                }

            # Format competitor data
            formatted_competitors = []
            include_metrics = params.get("include_metrics", [])
            
            for comp in competitors:
                competitor_data = {
                    "name": comp.name,
                    "description": comp.short_description,
                    "website": comp.homepage_url,
                    "location": {
                        "country": comp.country_code,
                        "city": comp.city
                    },
                    "category": comp.category_list
                }

                # Add requested metrics
                if "funding" in include_metrics:
                    competitor_data["funding"] = {
                        "total_funding_usd": comp.total_funding_usd,
                        "last_funding_date": comp.last_funding_on,
                        "funding_rounds": comp.num_funding_rounds
                    }

                if "employees" in include_metrics:
                    competitor_data["employees"] = comp.employee_count

                if "acquisitions" in include_metrics:
                    competitor_data["acquisitions"] = comp.num_exits

                formatted_competitors.append(competitor_data)

            response = {
                "main_company": {
                    "name": company_query.name,
                    "category": company_query.category_list,
                    "total_funding_usd": company_query.total_funding_usd
                },
                "competitors": formatted_competitors,
                "category_info": category_info
            }

            return {
                "status": "success",
                "data": response
            }

        except Exception as e:
            logger.error(f"Error processing competitor lookup: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process competitor lookup: {str(e)}"
            }
        
    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format competitor data for context injection"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        result_data = data.get("data", {})
        context_parts = []

        # Format main company info
        main_company = result_data.get("main_company", {})
        context_parts.append("MAIN COMPANY")
        context_parts.append(f"Name: {main_company.get('name', 'N/A')}")
        context_parts.append(f"Category: {main_company.get('category', 'N/A')}")
        
        if main_company.get("total_funding_usd"):
            context_parts.append(f"Total Funding: ${float(main_company['total_funding_usd']):,.2f}")
        context_parts.append("")

        # Format category info if available
        category_info = result_data.get("category_info")
        if category_info:
            context_parts.append("CATEGORY INSIGHTS")
            context_parts.append(f"Category: {category_info.get('name', 'N/A')}")
            context_parts.append(f"Total Companies: {category_info.get('total_companies', 'N/A')}")
            if category_info.get('total_funding'):
                context_parts.append(f"Total Category Funding: ${float(category_info['total_funding']):,.2f}")
            if category_info.get('avg_funding'):
                context_parts.append(f"Average Funding: ${float(category_info['avg_funding']):,.2f}")
            context_parts.append("")

        # Format competitors
        competitors = result_data.get("competitors", [])
        if competitors:
            context_parts.append("COMPETITORS")
            for comp in competitors:
                context_parts.append(f"\n{comp.get('name', 'Unknown')}")
                if comp.get('description'):
                    context_parts.append(f"Description: {comp['description']}")
                
                location = comp.get('location', {})
                if location:
                    loc_str = f"{location.get('city', '')}, {location.get('country', '')}"
                    context_parts.append(f"Location: {loc_str.strip(', ')}")
                
                if comp.get('category'):
                    context_parts.append(f"Category: {comp['category']}")
                
                # Add metrics if available
                if comp.get('funding'):
                    funding = comp['funding']
                    if funding.get('total_funding_usd'):
                        context_parts.append(f"Total Funding: ${float(funding['total_funding_usd']):,.2f}")
                    if funding.get('funding_rounds'):
                        context_parts.append(f"Funding Rounds: {funding['funding_rounds']}")
                
                if comp.get('employees'):
                    context_parts.append(f"Employee Count: {comp['employees']}")
                
                if comp.get('acquisitions'):
                    context_parts.append(f"Number of Exits: {comp['acquisitions']}")

        return "\n".join(context_parts)