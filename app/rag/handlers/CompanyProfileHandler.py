from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from repositories.ArticlesRepository import ArticlesRepository

from repositories.CompanyRepository import CompanyRepository
from repositories.FundingRoundsRepository import FundingRoundsRepository
from repositories.AcquisitionRepository import AcquisitionRepository
from repositories.PeopleRepository import PeopleRepository
from repositories.CategoryGroupRepository import CategoryGroupRepository
from repositories.OrgDescriptionRepository import OrgDescriptionRepository

logger = logging.getLogger(__name__)

class CompanyProfileHandler:
    """Handles COMPANY_PROFILE_QUERY intent operations"""
    
    def __init__(self, db: Session, openai_client: Any):
        self.db = db
        self.openai_client = openai_client 

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for company profile queries"""
        return {
            "name": "get_company_profile",
            "description": "Get comprehensive information about a company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to search for"
                    },
                    "include_data": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "funding",
                                "acquisitions",
                                "people",
                                "news",
                                "competitors"
                            ]
                        },
                        "description": "Additional data to include in the profile"
                    }
                },
                "required": ["company_name"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the company profile query"""
        try:
            # Initialize repositories
            company_repo = CompanyRepository()
            funding_repo = FundingRoundsRepository()
            acq_repo = AcquisitionRepository()
            people_repo = PeopleRepository()
            org_desc_repo = OrgDescriptionRepository()
            articles_repo = ArticlesRepository()

            
            # Search for company
            companies = company_repo.search_companies(
                self.db,
                name=params["company_name"],
                limit=1
            )
            
            if not companies:
                return {
                    "error": f"Company not found: {params['company_name']}"
                }
                
            company = companies[0]
            
            # Get full description
            description = org_desc_repo.get_company_full_description(
                self.db, 
                company.uuid
            ) or company.short_description

            # Initialize response with basic company info
            response = {
                "company_info": {
                    "name": company.name,
                    "description": description,
                    "website": company.homepage_url,
                    "founded": company.founded_on,
                    "location": {
                        "country": company.country_code,
                        "state": company.state_code,
                        "city": company.city,
                        "region": company.region
                    },
                    "status": company.status,
                    "category": company.category_list,
                    "total_funding_usd": company.total_funding_usd,
                    "employee_count": company.employee_count,
                    "domain": company.domain
                }
            }

            # Get requested additional data
            include_data = params.get("include_data", [])

            # Get funding information
            if "funding" in include_data:
                funding_rounds = funding_repo.get_company_rounds(
                    self.db,
                    company_uuid=company.uuid,
                    limit=5
                )
                response["funding"] = [{
                    "investment_type": round.investment_type,
                    "raised_amount_usd": round.raised_amount_usd,
                    "announced_on": round.announced_on,
                    "investor_count": round.investor_count,
                    "post_money_valuation_usd": round.post_money_valuation_usd
                } for round in funding_rounds]

            # Get acquisition information
            if "acquisitions" in include_data:
                acquisitions = acq_repo.get_company_acquisitions(
                    self.db,
                    company.uuid
                )
                response["acquisitions"] = [{
                    "acquired_on": acq.acquired_on,
                    "price_usd": acq.price_usd,
                    "type": "acquired" if acq.acquiree_uuid == company.uuid else "acquirer",
                    "other_party": {
                        "name": acq.acquiree_name if acq.acquirer_uuid == company.uuid else acq.acquirer_name,
                        "country_code": acq.acquiree_country_code if acq.acquirer_uuid == company.uuid else acq.acquirer_country_code,
                        "city": acq.acquiree_city if acq.acquirer_uuid == company.uuid else acq.acquirer_city
                    }
                } for acq in acquisitions]

            # Get key people
            if "people" in include_data:
                jobs = people_repo.get_by_organization(
                    self.db,
                    company.uuid,
                    limit=5
                )
                response["people"] = [{
                    "name": person.name,
                    "title": person.featured_job_title,
                    "city": person.city,
                    "country_code": person.country_code,
                    "linkedin_url": person.linkedin_url
                } for person in jobs]

            # Get recent news using vector search
            if "news" in include_data:
                all_news = []
                
                # Get startup articles with embeddings
                startup_articles = await articles_repo.get_articles(
                    self.db,
                    query=f"news about {company.name}",
                    days=90,
                    limit=3
                )
                all_news.extend([{
                    "title": article.title,
                    "published_at": article.published_at,
                    "url": article.url,
                    "source": "TechCrunch Startup"
                } for article in startup_articles])


                response["news"] = sorted(
                    all_news,
                    key=lambda x: x["published_at"],
                    reverse=True
                )

            # Get competitors using vector similarity
            if "competitors" in include_data:
                competitors = await company_repo.get_competitors(
                    self.db,
                    company.uuid,
                    self.openai_client,
                    limit=5
                )
                response["competitors"] = [{
                    "name": comp.name,
                    "description": comp.short_description,
                    "total_funding_usd": comp.total_funding_usd,
                    "category_list": comp.category_list,
                    "employee_count": comp.employee_count
                } for comp in competitors]

            return {
                "status": "success",
                "data": response
            }

        except Exception as e:
            logger.error(f"Error processing company profile: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process company profile: {str(e)}"
            }
    

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if isinstance(data, list):
            # Handle list of results
            if not data:
                return "No company information found."
            # Use the first result if multiple are returned
            company_data = data[0]
        else:
            # Handle single result dictionary
            if data.get("status") != "success":
                return f"Error: {data.get('error', 'Unknown error')}"
            company_data = data["data"]

        context_parts = []
        info = company_data.get("company_info", company_data)  # Fall back to entire object if no company_info key

        # Format basic info
        context_parts.append("COMPANY INFORMATION")
        context_parts.append(f"Name: {info.get('name', 'N/A')}")
        context_parts.append(f"Description: {info.get('description', 'N/A')}")
        context_parts.append(f"Founded: {info.get('founded', 'N/A')}")
        
        location = info.get('location', {})
        if isinstance(location, dict):
            context_parts.append(f"Location: {location.get('city', 'N/A')}, {location.get('country', 'N/A')}")
        
        context_parts.append(f"Category: {info.get('category', 'N/A')}")
        context_parts.append("")
        
        # KEY METRICS section
        context_parts.append("KEY METRICS")
        total_funding = info.get('total_funding_usd')
        if total_funding:
            try:
                context_parts.append(f"Total Funding: ${float(total_funding):,.2f}")
            except (ValueError, TypeError):
                context_parts.append(f"Total Funding: {total_funding}")
        
        context_parts.append(f"Employee Count: {info.get('employee_count', 'N/A')}")
        context_parts.append("")

        # Format funding rounds
        funding = company_data.get("funding", [])
        if funding:
            context_parts.append("FUNDING HISTORY")
            for round in funding:
                amount = round.get('raised_amount_usd', 'Undisclosed')
                if amount != 'Undisclosed':
                    try:
                        amount = f"${float(amount):,.2f}"
                    except (ValueError, TypeError):
                        pass
                
                context_parts.append(
                    f"- {round.get('investment_type', 'Investment')}: {amount} "
                    f"({round.get('announced_on', 'Date N/A')}, "
                    f"{round.get('investor_count', 0)} investors)"
                )
            context_parts.append("")

        # Format acquisitions
        acquisitions = company_data.get("acquisitions", [])
        if acquisitions:
            context_parts.append("ACQUISITIONS")
            for acq in acquisitions:
                price = acq.get('price_usd', 'Undisclosed')
                if price != 'Undisclosed':
                    try:
                        price = f"${float(price):,.2f}"
                    except (ValueError, TypeError):
                        pass
                
                other_party = acq.get('other_party', {})
                party_name = other_party.get('name', 'Unknown') if isinstance(other_party, dict) else 'Unknown'
                
                context_parts.append(
                    f"- {acq.get('type', 'Transaction').title()}: {party_name} "
                    f"({acq.get('announced_on', 'Date N/A')}, {price})"
                )
            context_parts.append("")

        # Format news
        news = company_data.get("news", [])
        if news:
            context_parts.append("RECENT NEWS")
            for article in news:
                context_parts.append(
                    f"- {article.get('title', 'No title')} "
                    f"({article.get('source', 'Unknown source')}, "
                    f"{article.get('published_at', 'Date N/A')})"
                )
            context_parts.append("")

        return "\n".join(context_parts)