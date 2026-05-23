from fastapi import APIRouter, HTTPException
from typing import Dict
from core.config import settings
from models.startup_registration_models import StartupDescription
from services.startup_registration_service import StartupService
from core.forms import category_groups, country_region, categories_map

router = APIRouter()

@router.post("/extract-info/")
async def extract_startup_info(
    data: StartupDescription,
) -> Dict:
    """Extract structured information from startup description using sequential function calls"""
    try:
        service = StartupService()
        result = await service.process_startup_info(
            description=data.description,
            category_groups=category_groups,
            country_regions=country_region,
            categories_map=categories_map
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing startup information: {str(e)}"
        )