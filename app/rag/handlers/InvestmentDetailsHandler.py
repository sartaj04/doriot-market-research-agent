from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.InvestmentRepository import InvestmentsRepository
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class InvestmentDetailsHandler:
    """Handles investment details queries"""
    
    def __init__(self, db: Session):
        self.db = db
        self.investment_repo = InvestmentsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for investment queries"""
        return {
            "name": "get_investment_details",
            "description": "Get detailed information about investments and funding rounds",
            "parameters": {
                "type": "object",
                "properties": {
                    "investor_name": {
                        "type": "string",
                        "description": "Name of the investor to find their investments",
                        "optional": True
                    },
                    "organization_name": {
                        "type": "string",
                        "description": "Name of the organization that received investment",
                        "optional": True
                    },
                    "investment_round": {
                        "type": "string",
                        "description": "Type of investment round (e.g., 'Series A', 'Seed')",
                        "optional": True
                    },
                    "investor_type": {
                        "type": "string",
                        "description": "Type of investor (e.g., 'Venture Capital', 'Angel')",
                        "optional": True
                    },
                    "lead_only": {
                        "type": "boolean",
                        "description": "Only show investments where investor was lead investor",
                        "optional": True
                    },
                    "days": {
                        "type": "integer",
                        "description": "Get investments from last N days",
                        "optional": True
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Minimum investment amount in USD",
                        "optional": True
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Filter by country code",
                        "optional": True
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by business category",
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
        """Execute the investment query"""
        try:
            investments = None
            query_type = "general"
            limit = params.get("limit", 10)

            # Query based on provided parameters
            if params.get("investor_name"):
                investments = self.investment_repo.get_by_investor_name(
                    self.db,
                    params["investor_name"],
                    lead_only=params.get("lead_only", False),
                    limit=limit
                )
                query_type = "investor_specific"
                
            elif params.get("investment_round"):
                investments = self.investment_repo.get_by_funding_round(
                    self.db,
                    params["investment_round"]
                )
                query_type = "round_specific"
                
            elif params.get("investor_type"):
                investments = self.investment_repo.get_investments_by_type(
                    self.db,
                    params["investor_type"],
                    limit=limit
                )
                query_type = "investor_type"
                
            elif params.get("days"):
                investments = self.investment_repo.get_recent_investments(
                    self.db,
                    days=params["days"],
                    limit=limit
                )
                query_type = "recent"
            
            else:
                investments = self.investment_repo.get_recent_investments(
                    self.db,
                    limit=limit
                )
                query_type = "recent"

            if not investments:
                return {
                    "status": "error",
                    "error": "No investments found matching the criteria"
                }

            # Format investment information
            formatted_investments = [{
                "investment_details": {
                    "round": investment.investment_round,
                    "announced_on": str(investment.announced_on),
                    "raised_amount": self._safe_float_convert(investment.raised_amount),
                    "total_funding": self._safe_float_convert(investment.total_funding),
                    "investor_count": investment.investor_count
                },
                "investor": {
                    "name": investment.investor_name,
                    "type": investment.investor_type,
                    "is_lead": investment.is_lead_investor
                },
                "organization": {
                    "name": investment.org_name,
                    "roles": investment.roles.split(",") if investment.roles else [],
                    "location": {
                        "country": investment.country_code,
                        "region": investment.region
                    },
                    "categories": investment.category_list.split(",") if investment.category_list else [],
                    "category_groups": investment.category_groups_list.split(",") if investment.category_groups_list else []
                },
                "metrics": {
                    "num_funding_rounds": investment.num_funding_rounds,
                    "total_funding_usd": self._safe_float_convert(investment.total_funding_usd)
                }
            } for investment in investments[:limit]]

            return {
                "status": "success",
                "data": {
                    "query_type": query_type,
                    "total_found": len(formatted_investments),
                    "investments": formatted_investments
                }
            }

        except Exception as e:
            logger.error(f"Error processing investment query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process investment query: {str(e)}"
            }
        

    def _safe_float_convert(self, value: Any) -> Optional[float]:
        """Safely convert numeric values to float"""
        if value is None:
            return None
        try:
            if isinstance(value, (Decimal, str)):
                return float(value)
            return float(value)
        except (ValueError, TypeError, InvalidOperation):
            logger.warning(f"Failed to convert value to float: {value}")
            return None
    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the investment results for context"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        try:
            context_parts = ["INVESTMENT DETAILS"]
            result_data = data.get("data", {})
            investments = result_data.get("investments", [])
            query_type = result_data.get("query_type", "unknown")

            context_parts.append(f"\nQuery Type: {query_type.replace('_', ' ').title()}")
            context_parts.append(f"Total Investments Found: {len(investments)}")

            for inv in investments:
                inv_details = inv.get("investment_details", {})
                inv_org = inv.get("organization", {})
                inv_investor = inv.get("investor", {})
                location = inv_org.get("location", {})

                context_parts.extend([
                    f"\n- Investment Round: {inv_details.get('round', 'N/A')}",
                    f"  Announced: {inv_details.get('announced_on', 'N/A')}",
                ])

                # Safe amount formatting
                amount = inv_details.get('raised_amount')
                if amount is not None:
                    context_parts.append(f"  Amount Raised: ${amount:,.2f}")
                else:
                    context_parts.append("  Amount Raised: Not disclosed")

                context_parts.extend([
                    f"  Investor: {inv_investor.get('name', 'N/A')} ({inv_investor.get('type', 'N/A')})",
                    f"  Lead Investor: {'Yes' if inv_investor.get('is_lead') else 'No'}",
                    f"  Company: {inv_org.get('name', 'N/A')}",
                    f"  Location: {location.get('region', 'N/A')}, {location.get('country', 'N/A')}",
                    f"  Categories: {', '.join(inv_org.get('categories', []))}",
                    "---"
                ])

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error formatting investment context: {str(e)}", exc_info=True)
            return "Error formatting investment details"