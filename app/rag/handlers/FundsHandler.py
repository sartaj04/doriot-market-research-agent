from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.FundRepository import FundRepository

logger = logging.getLogger(__name__)

class FundsHandler:
    def __init__(self, db: Session):
        self.db = db
        self.funds_repo = FundRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "get_fund_details",
            "description": "Retrieve details about investment funds",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "description": "Type of fund entity (optional)",
                        "optional": True
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Minimum raised amount in USD (optional)",
                        "optional": True
                    }
                },
                "required": []  # No required fields
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        funds = self.funds_repo.get_funds(
            self.db,
            entity_type=params.get("entity_type"),
            min_amount=params.get("min_amount")
        )
        return {"status": "success", "data": funds}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"
        return "\n".join([f"Fund: {f.name}, Amount: ${f.raised_amount_usd}" for f in data["data"]])