from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.PeopleRepository import PeopleRepository

logger = logging.getLogger(__name__)

class PeopleProfileHandler:
    def __init__(self, db: Session):
        self.db = db
        self.people_repo = PeopleRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "get_people_profiles",
            "description": "Retrieve profile details of people",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name or partial name of the person to search for",
                        "optional": True
                    },
                    "job_title": {
                        "type": "string",
                        "description": "Job title to filter people by (e.g., 'CEO', 'Software Engineer')",
                        "optional": True
                    },
                    "organization_name": {
                        "type": "string",
                        "description": "Company/organization name to find people from",
                        "optional": True
                    },
                    "location": {
                        "type": "string",
                        "description": "Location (city or country) to find people from",
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
            query_type = "general"
            people = None

            if params.get("name"):
                people = self.people_repo.search_people(
                    self.db,
                    name=params["name"],
                    limit=limit
                )
                query_type = "name_search"
                
            elif params.get("job_title"):
                people = self.people_repo.search_people(
                    self.db,
                    job_title=params["job_title"],
                    limit=limit
                )
                query_type = "job_search"
                
            elif params.get("organization_name"):
                people = self.people_repo.search_people(
                    self.db,
                    organization_name=params["organization_name"],
                    limit=limit
                )
                query_type = "organization_search"
                
            elif params.get("location"):
                people = self.people_repo.get_by_location(
                    self.db,
                    city=params["location"],
                    limit=limit
                )
                query_type = "location_search"
                
            else:
                # Default: get ranked people
                people = self.people_repo.search_people(
                    self.db,
                    limit=limit
                )
                query_type = "top_ranked"

            if not people:
                return {
                    "status": "error",
                    "error": "No people found matching the criteria"
                }

            # Format people information
            formatted_people = [{
                "name": person.name,
                "featured_job_title": person.featured_job_title,
                "organization": person.featured_job_organization_name,
                "location": f"{person.city}, {person.country_code}" if person.city else person.country_code,
                "linkedin_url": person.linkedin_url,
                "rank": person.rank
            } for person in people]

            return {
                "status": "success",
                "data": {
                    "query_type": query_type,
                    "total_found": len(formatted_people),
                    "people": formatted_people
                }
            }

        except Exception as e:
            logger.error(f"Error processing people profile query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process people profile query: {str(e)}"
            }

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        query_type = data["data"]["query_type"]
        people = data["data"]["people"]
        
        context_parts = [f"PEOPLE PROFILES ({query_type.replace('_', ' ').title()})"]
        context_parts.append(f"Total Found: {len(people)}")
        
        for person in people:
            context_parts.extend([
                f"\n- Name: {person['name']}",
                f"  Role: {person['featured_job_title'] or 'Not specified'}",
                f"  Organization: {person['organization'] or 'Not specified'}",
                f"  Location: {person['location'] or 'Not specified'}",
                f"  LinkedIn: {person['linkedin_url'] or 'Not available'}",
                "---"
            ])

        return "\n".join(context_parts)