from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.InvestmentPartnerRepository import InvestmentPartnerRepository

logger = logging.getLogger(__name__)

class InvestmentPartnerHandler:
    """Handles queries for investment partners (VC firm partners) in funding rounds"""
    
    def __init__(self, db: Session):
        self.db = db
        self.partner_repo = InvestmentPartnerRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for VC partner queries"""
        return {
            "name": "get_investment_partners",
            "description": "Get information about VC firm partners involved in investments",
            "parameters": {
                "type": "object",
                "properties": {
                    "investor_name": {
                        "type": "string",
                        "description": "Name of the VC firm/investor to find their partners",
                        "optional": True
                    },
                    "partner_name": {
                        "type": "string",
                        "description": "Name or partial name of the partner to search for",
                        "optional": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "optional": True
                    }
                },
                "required": []
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the VC partner query"""
        try:
            partners = None
            query_type = "general"
            limit = params.get("limit", 10)

            # Query based on provided parameters
            if params.get("investor_name"):
                partners = self.partner_repo.get_partners_by_investor_name(
                    self.db,
                    params["investor_name"]
                )
                query_type = "investor"
                
            elif params.get("partner_name"):
                partners = self.partner_repo.get_partners_by_name(
                    self.db,
                    params["partner_name"]
                )
                query_type = "partner"
            
            else:
                # Get recent/notable partners as default
                partners = self.partner_repo.get_recent_partners(self.db, limit=limit)

            if not partners:
                return {
                    "status": "error",
                    "error": "No investment partners found matching the criteria"
                }

            # Limit results if specified
            partners = partners[:limit]

            # Format partner information
            formatted_partners = [{
                "name": partner.name,
                "permalink": partner.permalink,
                "cb_url": partner.cb_url,
                "investor": {
                    "name": partner.investor_name
                },
                "funding_round": {
                    "name": partner.funding_round_name
                },
                "created_at": partner.created_at,
                "updated_at": partner.updated_at
            } for partner in partners]

            return {
                "status": "success",
                "data": {
                    "query_type": query_type,
                    "total_found": len(partners),
                    "partners": formatted_partners
                }
            }

        except Exception as e:
            logger.error(f"Error processing VC partner query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process VC partner query: {str(e)}"
            }

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the VC partner results for context"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        context_parts = ["VENTURE CAPITAL PARTNERS INFORMATION"]
        partners = data["data"]["partners"]
        query_type = data["data"]["query_type"]

        context_parts.append(f"\nQuery Type: {query_type.replace('_', ' ').title()}")
        context_parts.append(f"Total Partners Found: {len(partners)}")
        
        for partner in partners:
            context_parts.extend([
                f"\n- Partner: {partner['name']}",
                f"  Role: {partner['type'] or 'Not specified'}",
                f"  Firm: {partner['investor']['name']}",
                f"  Recent Deal: {partner['funding_round']['name']}",
                "---"
            ])

        return "\n".join(context_parts)