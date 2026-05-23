from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.JobRepository import JobRepository

logger = logging.getLogger(__name__)

class JobsHandler:
    def __init__(self, db: Session):
        self.db = db
        self.jobs_repo = JobRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "get_jobs",
            "description": "Retrieve job information from various perspectives",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name to get jobs for a specific organization",
                        "optional": True
                    },
                    "person_name": {
                        "type": "string",
                        "description": "Person name to get job history for an individual",
                        "optional": True
                    },
                    "job_title": {
                        "type": "string",
                        "description": "Search jobs by title (e.g., 'Software Engineer')",
                        "optional": True
                    },
                    "job_type": {
                        "type": "string",
                        "description": "Filter jobs by type (e.g., 'Full-time', 'Part-time')",
                        "optional": True
                    },
                    "location": {
                        "type": "string",
                        "description": "Filter jobs by location (city or country code)",
                        "optional": True
                    },
                    "current_only": {
                        "type": "boolean",
                        "description": "Only show current positions",
                        "default": False,
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
            current_only = params.get("current_only", False)
            limit = params.get("limit", 10)
            query_type = "general"
            jobs = None

            # Person's job history
            if params.get("person_name"):
                if current_only:
                    jobs = self.jobs_repo.get_person_jobs_by_name(
                        self.db,
                        params["person_name"],
                        current_only=True,
                        limit=limit
                    )
                else:
                    jobs = self.jobs_repo.get_job_history_by_name(
                        self.db,
                        params["person_name"],
                        limit=limit
                    )
                query_type = "person_history"

            # Company jobs
            elif params.get("company_name"):
                jobs = self.jobs_repo.get_organization_jobs_by_name(
                    self.db,
                    params["company_name"],
                    current_only=current_only,
                    limit=limit
                )
                query_type = "company_jobs"

            # Search by location
            elif params.get("location"):
                jobs = self.jobs_repo.search_by_location(
                    self.db,
                    params["location"],
                    current_only=current_only,
                    limit=limit
                )
                query_type = "location_search"

            # Search by job title
            elif params.get("job_title"):
                jobs = self.jobs_repo.search_by_title(
                    self.db,
                    params["job_title"],
                    current_only=current_only,
                    limit=limit
                )
                query_type = "title_search"

            # Search by job type
            elif params.get("job_type"):
                jobs = self.jobs_repo.get_jobs_by_type(
                    self.db,
                    params["job_type"],
                    current_only=current_only,
                    limit=limit
                )
                query_type = "type_search"

            # Default: get current jobs
            else:
                jobs = self.jobs_repo.get_current_jobs(
                    self.db,
                    limit=limit
                )
                query_type = "current_jobs"

            if not jobs:
                return {
                    "status": "error",
                    "error": "No jobs found matching the criteria"
                }

            return {
                "status": "success",
                "data": {
                    "query_type": query_type,
                    "total_found": len(jobs if isinstance(jobs, list) else jobs.get("total", 0)),
                    "jobs": jobs
                }
            }

        except Exception as e:
            logger.error(f"Error processing jobs query: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        query_type = data.get("query_type", "general")
        
        if query_type == "person_history":
            jobs = data["data"]
            lines = ["JOB HISTORY:\n"]
            
            if jobs.get("current_positions"):
                lines.append("Current Positions:")
                for job in jobs["current_positions"]:
                    lines.extend([
                        f"• {job['title']} at {job['organization']}",
                        f"  Started: {job['started_on']}",
                        f"  Type: {job['type']}",
                        "---"
                    ])
            
            if jobs.get("past_positions"):
                lines.append("\nPast Positions:")
                for job in jobs["past_positions"]:
                    lines.extend([
                        f"• {job['title']} at {job['organization']}",
                        f"  Period: {job['started_on']} to {job['ended_on']}",
                        f"  Type: {job['type']}",
                        "---"
                    ])
                    
            return "\n".join(lines)
        
        else:
            jobs = data["data"]
            lines = [f"JOB LISTINGS ({query_type.replace('_', ' ').title()}):\n"]
            
            for job in jobs:
                lines.extend([
                    f"• {job.title}",
                    f"  Organization: {job.org_name}",
                    f"  Location: {job.city}, {job.country_code}",
                    f"  Type: {job.job_type}",
                    f"  Status: {'Current' if job.is_current else 'Past'}",
                    "---"
                ])
            
            return "\n".join(lines)