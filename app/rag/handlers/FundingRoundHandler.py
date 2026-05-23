from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from repositories.FundingRoundsRepository import FundingRoundsRepository
from models.companies import Companies

logger = logging.getLogger(__name__)

class FundingRoundHandler:
    def __init__(self, db: Session):
        self.db = db
        self.funding_repo = FundingRoundsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Function definition for funding round queries."""
        return {
            "name": "get_funding_round_details",
            "description": "Retrieve details about company funding rounds",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name for which funding rounds are to be fetched",
                        "optional": True
                    },
                    "investment_type": {
                        "type": "string",
                        "description": "Type of investment (e.g., 'seed', 'series a', 'series b', 'private_equity')",
                        "enum": ["seed", "angel", "series_a", "series_b", "series_c", "series_d", "private_equity"],
                        "optional": True
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Minimum raised amount in USD",
                        "optional": True
                    },
                    "recent_only": {
                        "type": "boolean",
                        "description": "If true, only show rounds from last 90 days",
                        "default": False
                    },
                    "include_investors": {
                        "type": "boolean",
                        "description": "Include investor details in the results",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rounds to return",
                        "default": 10
                    }
                },
                "required": ["company_name"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute funding round query with flexible filtering."""
        try:
            limit = params.get("limit", 10)
            
            # Start with base query
            if params.get("company_name"):
                # Company-specific query
                company = self.db.query(Companies).filter(
                    Companies.name.ilike(f"%{params['company_name']}%")
                ).first()
                
                if not company:
                    return {
                        "status": "error",
                        "error": f"Company '{params['company_name']}' not found"
                    }
                    
                rounds = self.funding_repo.get_company_rounds(
                    db=self.db,
                    company_uuid=company.uuid,
                    limit=limit
                )
            else:
                # General funding rounds query
                rounds = self.funding_repo.get_funding_rounds(
                    db=self.db,
                    investment_type=params.get("investment_type"),
                    min_amount=params.get("min_amount"),
                    recent_only=params.get("recent_only"),
                    sort_by=params.get("sort_by", "date"),
                    limit=limit
                )

            if not rounds:
                return {
                    "status": "success",
                    "data": [],
                    "total_rounds": 0,
                    "message": "No funding rounds found matching the criteria"
                }

            # Process investor details if requested
            if params.get("include_investors"):
                rounds_with_investors = []
                for round in rounds:
                    round_data = self.funding_repo.get_rounds_with_investors(
                        self.db, 
                        round.uuid
                    )
                    if round_data:
                        rounds_with_investors.append(round_data)
                
                return {
                    "status": "success",
                    "data": rounds_with_investors,
                    "total_rounds": len(rounds_with_investors)
                }

            return {
                "status": "success",
                "data": rounds,
                "total_rounds": len(rounds)
            }

        except Exception as e:
            logger.error(f"Error executing funding round query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process funding round query: {str(e)}"
            }
    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format query results for context."""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        if not data["data"]:
            return "No funding rounds found matching the criteria."

        results = []
        for round in data["data"]:
            amount_str = f"${round.raised_amount_usd:,.2f}" if round.raised_amount_usd else "undisclosed amount"
            date_str = f" on {round.announced_on}" if round.announced_on else ""
            
            round_info = f"- {round.investment_type} round raised {amount_str}{date_str}"
            
            if hasattr(round, 'investors'):
                investors = [f"  • {inv['name']} ({inv['type']})" + (" (Lead)" if inv['is_lead'] else "")
                           for inv in round.investors]
                round_info += "\n" + "\n".join(investors)
            
            results.append(round_info)

        return "\n".join(results)