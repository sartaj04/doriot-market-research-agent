from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.DegreeRepository import DegreesRepository
from models.people import People  # Add this import

logger = logging.getLogger(__name__)


class EducationHandler:
    def __init__(self, db: Session):
        self.db = db
        self.degrees_repo = DegreesRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "get_education_details",
            "description": "Retrieve education history of a person",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {
                        "type": "string",
                        "description": "Name of the person to search for"
                    },
                    "institution": {
                        "type": "string",
                        "description": "Filter by institution name",
                        "optional": True
                    },
                    "degree_type": {
                        "type": "string",
                        "description": "Filter by degree type (e.g., 'BS', 'MS', 'PhD')",
                        "optional": True
                    },
                    "completed_only": {
                        "type": "boolean",
                        "description": "If true, only show completed degrees",
                        "default": False
                    }
                },
                "required": ["person_name"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # First find the person by name
            person_query = self.db.query(People).filter(
                People.name.ilike(f"%{params['person_name']}%")
            ).first()
            
            if not person_query:
                return {
                    "status": "error",
                    "error": f"Person '{params['person_name']}' not found"
                }

            # Get degrees based on completion status
            if params.get("completed_only"):
                degrees = self.degrees_repo.get_completed_degrees(
                    db=self.db,
                    person_uuid=person_query.uuid
                )
            else:
                degrees = self.degrees_repo.get_person_degrees(
                    db=self.db,
                    person_uuid=person_query.uuid
                )

            # Apply additional filters
            if params.get("institution"):
                degrees = [
                    d for d in degrees 
                    if params["institution"].lower() in d.institution_name.lower()
                ]
                
            if params.get("degree_type"):
                degrees = [
                    d for d in degrees 
                    if params["degree_type"].lower() in d.degree_type.lower()
                ]

            return {
                "status": "success",
                "data": degrees,
                "person_name": person_query.name
            }

        except Exception as e:
            logger.error(f"Error executing education query: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"
        
        if not data["data"]:
            return f"No education history found for {data.get('person_name', 'the person')}."
        
        results = []
        results.append(f"Education history for {data['person_name']}:")
        
        for degree in data["data"]:
            status = "completed" if degree.is_completed else "in progress"
            date_str = f" ({degree.completed_on})" if degree.completed_on else ""
            results.append(
                f"- {degree.degree_type} in {degree.subject} from {degree.institution_name} - {status}{date_str}"
            )
        
        return "\n".join(results)