# app/services/startup_service.py

from typing import Dict, List, Optional
from core.config import get_settings
from core.openai import get_openai_client
import logging

logger=logging.getLogger(__name__)

class StartupService:
    def __init__(self):
        # Remove client initialization from constructor
        pass
        
    async def extract_base_info(self, description: str, category_groups: List[str]) -> Dict:
        """
        First function call: Extract organization name, country code, and relevant category groups
        from the provided list
        """
        settings = get_settings()
        # Initialize a fresh client for each request
        openai_client = get_openai_client()
        
        # Log settings being used

        
        try:
            prompt = f"""Extract the following information from this startup description:
            1. Organization name
            2. Country code (3-letter ISO code)
            3. Most relevant category groups from this list: {', '.join(category_groups)}

            Description:
            {description}

            Return ONLY a JSON object with these exact keys:
            {{
                "org_name": string or null if not found,
                "country_code": string or null if not found,
                "category_groups": list of strings (up to 3 most relevant groups from the provided list) or empty list if none found
            }}

            Ensure:
            - Select category groups ONLY from the provided list
            - Use standard 3-letter country codes (e.g., USA, GBR)
            - Extract the actual company name, don't invent one if not mentioned
            - Return null for org_name or country_code if they cannot be determined from the description
            - Return an empty list for category_groups if none can be determined"""

            response = await openai_client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )
            
            # Extract the content and parse it as JSON
            content = response.choices[0].message.content
            import json
            result = json.loads(content)
            
            # Validate and clean up the response
            if result.get("org_name") == "":
                result["org_name"] = None
                
            if result.get("country_code") == "":
                result["country_code"] = None
                
            if not result.get("category_groups"):
                result["category_groups"] = []
                
            return result

        except Exception as e:
            logger.error(f"Error extracting base info: {str(e)}", exc_info=True)
            raise

    async def select_region(self, description: str, country_code: str, 
                          country_regions: Dict[str, List[str]]) -> Dict:
        """Second function call: Select the most relevant region"""
        try:
            # If country_code is None, return None for region
            if country_code is None:
                return {"region": None}
                
            settings = get_settings()
            # Initialize a fresh client for each request
            openai_client = get_openai_client()
            
            available_regions = country_regions.get(country_code, [])
            if not available_regions:
                return {"region": None}

            prompt = f"""Given this startup description, select the most relevant region from this list:
            Available regions: {', '.join(available_regions)}

            Description:
            {description}

            Return ONLY a JSON object with this exact key:
            {{
                "region": string (must be one from the provided list) or null if cannot be determined
            }}

            Choose the most likely region based on:
            1. Explicit mentions
            2. Business context
            3. Industry indicators
            If no region can be confidently determined from the description, return null."""

            response = await openai_client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Clean up empty string
            if result.get("region") == "":
                result["region"] = None
                
            return result

        except Exception as e:
            logger.error(f"Error selecting region: {str(e)}", exc_info=True)
            raise

    async def select_categories(self, description: str, category_groups: List[str], 
                              categories_map: Dict[str, List[str]]) -> Dict:
        """Third function call: Select relevant categories"""
        try:
            # If no category groups, return empty categories list
            if not category_groups:
                return {"categories": []}
                
            settings = get_settings()
            # Initialize a fresh client for each request
            openai_client = get_openai_client()
            
            available_categories = []
            for group in category_groups:
                if group in categories_map:
                    available_categories.extend(categories_map[group])
                    
            # If no available categories, return empty list
            if not available_categories:
                return {"categories": []}

            prompt = f"""Given this startup description, select the most relevant categories from this list:
            Available categories: {', '.join(available_categories)}

            Description:
            {description}

            Return ONLY a JSON object with this exact key:
            {{
                "categories": list of strings (up to 5 most relevant categories from the provided list) or empty list if none can be determined
            }}

            Ensure:
            - Select only from the provided categories list
            - Choose categories that match the company's actual business
            - Order by relevance
            - Select up to 5 categories maximum
            - Return an empty list if no categories can be confidently determined"""

            response = await openai_client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            import json
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error selecting categories: {str(e)}", exc_info=True)
            raise

    async def process_startup_info(self, description: str, 
                                 category_groups: List[str],
                                 country_regions: Dict[str, List[str]], 
                                 categories_map: Dict[str, List[str]]) -> Dict:
        """Process complete startup information using sequential function calls"""
        try:
            # First call: Get base info
            base_info = await self.extract_base_info(description, category_groups)
            
            # Second call: Get region using extracted country code
            region_info = await self.select_region(
                description,
                base_info.get("country_code"),
                country_regions
            )
            
            # Third call: Get categories using extracted category groups
            categories_info = await self.select_categories(
                description,
                base_info.get("category_groups", []),
                categories_map
            )
            
            # Combine all information
            return {
                "success": True,
                "data": {
                    **base_info,
                    **region_info,
                    **categories_info
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }