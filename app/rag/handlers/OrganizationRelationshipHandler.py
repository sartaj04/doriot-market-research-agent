from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.OrgParentsRepository import OrgParentsRepository

logger = logging.getLogger(__name__)

class OrganizationRelationshipHandler:
    """Handles ORGANIZATION_RELATIONSHIP_QUERY intent operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.org_parents_repo = OrgParentsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        """Get the function definition for organization relationship queries"""
        return {
            "name": "get_organization_relationships",
            "description": "Get information about corporate relationships and structure",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to find relationships",
                        "optional": False
                    },
                    "relationship_type": {
                        "type": "string",
                        "enum": ["parent", "subsidiary", "full_structure"],
                        "description": "Type of relationship to query (parent/subsidiary/full_structure)",
                        "optional": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of relationships to return (default: 10)",
                        "optional": True
                    }
                },
                "required": ["company_name"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the organization relationship query"""
        try:
            relationship_type = params.get("relationship_type", "full_structure")
            limit = params.get("limit", 10)
            company_name = params["company_name"]
            
            if relationship_type == "full_structure":
                # Get complete organizational structure
                structure = self.org_parents_repo.get_full_org_structure_by_name(
                    self.db,
                    company_name
                )
                return {
                    "status": "success",
                    "data": {
                        "structure_type": "full",
                        "company_name": company_name,
                        "relationships": structure
                    }
                }
            else:
                # Get specific relationships (parent/subsidiary)
                relationships = self.org_parents_repo.get_company_relationships_by_name(
                    self.db,
                    company_name,
                    limit=limit
                )
                return {
                    "status": "success",
                    "data": {
                        "structure_type": relationship_type,
                        "company_name": company_name,
                        "relationships": relationships
                    }
                }

        except Exception as e:
            logger.error(f"Error processing organization relationship query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to process organization relationship query: {str(e)}"
            }
    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the query results for context injection"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        context_parts = ["ORGANIZATIONAL RELATIONSHIPS"]
        
        structure_type = data["data"]["structure_type"]
        relationships = data["data"]["relationships"]
        
        if structure_type == "full":
            context_parts.append("\nComplete Organizational Structure:")
            
            def format_structure(node: Dict[str, Any], level: int = 0):
                indent = "  " * level
                parts = [f"\n{indent}- {node['name']}"]
                for child in node.get("children", []):
                    parts.extend(format_structure(child, level + 1))
                return parts
            
            context_parts.extend(format_structure(relationships))
            
        else:
            if relationships.get("parent_companies"):
                context_parts.append("\nParent Companies:")
                for parent in relationships["parent_companies"]:
                    context_parts.append(f"- {parent['name']}")
            
            if relationships.get("subsidiaries"):
                context_parts.append("\nSubsidiaries:")
                for subsidiary in relationships["subsidiaries"]:
                    context_parts.append(f"- {subsidiary['name']}")

        return "\n".join(context_parts)