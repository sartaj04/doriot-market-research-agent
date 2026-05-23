from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.AcquisitionRepository import AcquisitionRepository
from models.companies import Companies
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AcquisitionHandler:
    def __init__(self, db: Session):
        self.db = db
        self.acq_repo = AcquisitionRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "get_acquisition_details",
            "description": "Retrieve acquisition details for a company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string", 
                        "description": "Company name to search for"
                    },
                    "role": {
                        "type": "string", 
                        "description": "'acquirer' or 'acquired'",
                        "enum": ["acquirer", "acquired"]
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum acquisition price in USD"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    },
                    "recent_only": {
                        "type": "boolean",
                        "description": "If true, only show acquisitions from last 90 days",
                        "default": False
                    }
                },
                "required": ["company_name"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # First find the company UUID by name
            company_query = self.db.query(Companies).filter(
                Companies.name.ilike(f"%{params['company_name']}%")
            ).first()
            
            if not company_query:
                return {
                    "status": "error",
                    "error": f"Company '{params['company_name']}' not found"
                }

            # Get acquisitions with filters
            acquisitions = self.acq_repo.get_company_acquisitions(
                db=self.db,
                company_uuid=company_query.uuid,
                role=params.get("role")
            )

            # Apply additional filters
            if params.get("min_price"):
                acquisitions = [a for a in acquisitions if a.price_usd and a.price_usd >= params["min_price"]]
            
            if params.get("recent_only"):
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                acquisitions = [
                    a for a in acquisitions 
                    if a.acquired_on and datetime.strptime(a.acquired_on, '%Y-%m-%d') >= cutoff_date
                ]

            # Apply limit
            limit = params.get("limit", 10)
            acquisitions = acquisitions[:limit]

            return {"status": "success", "data": acquisitions}
            
        except Exception as e:
            logger.error(f"Error executing acquisition query: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"
        
        if not data["data"]:
            return "No acquisitions found matching the criteria."
        
        results = []
        for acq in data["data"]:
            price_str = f"${acq.price_usd:,.2f}" if acq.price_usd else "undisclosed amount"
            date_str = f" on {acq.acquired_on}" if acq.acquired_on else ""
            results.append(
                f"{acq.acquirer_name} acquired {acq.acquiree_name} for {price_str}{date_str}"
            )
        
        return "\n".join(results)