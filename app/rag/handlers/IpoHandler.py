from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.IpoRepository import IpoRepository

logger = logging.getLogger(__name__)

class IpoHandler:
    def __init__(self, db: Session):
        self.db = db
        self.ipo_repo = IpoRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "get_ipo_details",
            "description": "Retrieve IPO information for companies",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name to get specific IPO details",
                        "optional": True
                    },
                    "days": {
                        "type": "integer",
                        "description": "Get IPOs from last N days",
                        "optional": True
                    },
                    "min_valuation": {
                        "type": "number",
                        "description": "Minimum IPO valuation in USD",
                        "optional": True
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Stock exchange symbol (e.g., NYSE, NASDAQ)",
                        "optional": True
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Country code for IPO listings",
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
        try:
            limit = params.get("limit", 10)
            
            if params.get("company_name"):
                ipos = self.ipo_repo.get_by_company_name(
                    self.db, 
                    params["company_name"]
                )
                query_type = "company_specific"
                
            elif params.get("exchange"):
                ipos = self.ipo_repo.get_by_stock_exchange(
                    self.db,
                    params["exchange"],
                    limit=limit
                )
                query_type = "exchange_specific"
                
            else:
                ipos = self.ipo_repo.get_recent_ipos(
                    self.db,
                    days=params.get("days", 90),
                    min_valuation=params.get("min_valuation"),
                    country_code=params.get("country_code"),
                    limit=limit
                )
                query_type = "recent_ipos"

            if not ipos:
                return {
                    "status": "error", 
                    "error": "No IPOs found matching the criteria"
                }

            # Format IPO information
            formatted_ipos = [{
                "company_name": ipo.company_name,
                "went_public_on": ipo.went_public_on,
                "stock_exchange": ipo.stock_exchange_symbol,
                "stock_symbol": ipo.stock_symbol,
                "share_price_usd": ipo.share_price_usd,
                "money_raised_usd": ipo.money_raised_usd,
                "valuation_price_usd": ipo.valuation_price_usd
            } for ipo in ipos[:limit]]

            return {
                "status": "success",
                "data": {
                    "query_type": query_type,
                    "total_found": len(formatted_ipos),
                    "ipos": formatted_ipos
                }
            }

        except Exception as e:
            logger.error(f"Error processing IPO query: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        query_type = data.get("query_type", "unknown")
        
        if query_type == "company_specific":
            ipo = data["data"]
            return (
                f"IPO DETAILS:\n"
                f"• Date: {ipo['went_public_on']}\n"
                f"• Exchange: {ipo['stock_exchange']}\n"
                f"• Symbol: {ipo['stock_symbol']}\n"
                f"• Share Price: ${ipo['share_price_usd']:,.2f}\n"
                f"• Money Raised: ${ipo['money_raised_usd']:,.2f}\n"
                f"• Valuation: ${ipo['valuation_price_usd']:,.2f}"
            )
        
        # Format list of IPOs
        ipos = data["data"]
        lines = [f"IPO LISTINGS ({query_type.replace('_', ' ').title()}):\n"]
        
        for ipo in ipos:
            lines.append(
                f"• {ipo.went_public_on} - {ipo.stock_symbol} "
                f"(${ipo.share_price_usd:,.2f}/share)"
            )
            if ipo.money_raised_usd:
                lines.append(f"  Raised: ${ipo.money_raised_usd:,.2f}")
            lines.append("---")

        return "\n".join(lines)