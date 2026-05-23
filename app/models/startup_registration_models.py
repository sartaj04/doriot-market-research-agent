# app/models/startup_models.py

from pydantic import BaseModel, Field, constr, validator
from typing import List, Optional, Dict

class StartupDescription(BaseModel):
    """Request model for startup description"""
    description: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Detailed description of the startup (minimum 50 characters, maximum 5000 characters)"
    )

    @validator('description')
    def validate_description(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Description must be at least 50 characters long')
        if len(v) > 5000:
            raise ValueError('Description must not exceed 5000 characters')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "description": "TechFlow AI, based in San Francisco, is revolutionizing enterprise software development with our AI-powered code generation platform. Our solution leverages advanced machine learning algorithms to analyze code patterns and automatically generate high-quality, production-ready code, reducing development time by 60% and improving code quality by automated testing and optimization."
            }
        }

class BaseInfoResponse(BaseModel):
    """Response model for first function call"""
    org_name: str
    country_code: str
    category_groups: List[str]

class RegionResponse(BaseModel):
    """Response model for second function call"""
    region: str

class CategoriesResponse(BaseModel):
    """Response model for third function call"""
    categories: List[str]

class StartupInfoResponse(BaseModel):
    """Combined response model"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "org_name": "TechFlow AI",
                    "country_code": "USA",
                    "category_groups": ["Artificial Intelligence", "Software"],
                    "region": "California",
                    "categories": ["AI/ML", "Enterprise Software", "Developer Tools"]
                }
            }
        }