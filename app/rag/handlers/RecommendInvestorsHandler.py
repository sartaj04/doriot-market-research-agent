from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.InvestorRepository import InvestorsRepository
from models.investors import Investors
import json
from core.openai import AsyncAzureOpenAI 


logger = logging.getLogger(__name__)



class RecommendInvestorsHandler:
    """Handles detailed investor recommendations"""
    
    def __init__(self, db: Session, openai_client: AsyncAzureOpenAI):
        self.db = db
        self.openai_client = openai_client
        self.investor_repo = InvestorsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "recommend_investors",
            "description": "Get detailed investor recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_area": {
                        "type": "string",
                        "enum": ["all", "technical", "strategic", "financial"],
                        "description": "Type of investors to focus on"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["brief", "detailed", "comprehensive"],
                        "default": "detailed"
                    }
                }
            }
        }

    async def execute_query(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute investor recommendation query"""
        try:
            investor_list = user_context.get('investor_simple_list', [])
            if not investor_list:
                return {
                    "status": "error",
                    "error": "No recommended investors found in your profile"
                }

            recommended_investors = []
            for investor in investor_list:
                # Add type validation for investor_list items
                if not isinstance(investor.get('uuid'), str):
                    continue
                investor_data = await self.investor_repo.get_investor_stats(
                    self.db,
                    investor['uuid']
                )
                
                if not investor_data:
                    continue

                # Calculate match reasons
                reasons = []
                
                # Category match
                if investor_data.get('investment_analysis', {}).get('top_categories'):
                    matching_categories = set(investor_data['investment_analysis']['top_categories'].keys()) & \
                                       set(user_context.get('category_list', []))
                    if matching_categories:
                        reasons.append(f"Invests in {', '.join(matching_categories)}")

                # Investment stage match
                if investor_data.get('investment_analysis', {}).get('top_investment_rounds'):
                    user_funding = user_context.get('total_funding_usd', 0)
                    if user_funding < 1000000 and 'seed' in investor_data['investment_analysis']['top_investment_rounds']:
                        reasons.append("Active in seed-stage investments")
                    elif user_funding < 5000000 and 'series_a' in investor_data['investment_analysis']['top_investment_rounds']:
                        reasons.append("Active in Series A investments")

                # Recent activity
                if investor_data.get('investment_metrics', {}).get('investment_count'):
                    reasons.append(f"Made {investor_data['investment_metrics']['investment_count']} recent investments")

                recommended_investors.append({
                    "uuid": investor['uuid'],
                    "name": investor_data.get('basic_info', {}).get('name'),
                    "description": investor_data.get('basic_info', {}).get('description'),
                    "investment_focus": investor_data.get('investment_analysis', {}).get('top_categories', {}),
                    "recent_investments": investor_data.get('investment_metrics', {}),
                    "network": investor_data.get('co_investment_network', {}),
                    "contact": {
                        "website": investor_data.get('social_presence', {}).get('domain'),
                        "linkedin": investor_data.get('social_presence', {}).get('linkedin')
                    },
                    "match_reasons": reasons
                })

            return {
                "status": "success",
                "data": {
                    "recommendations": recommended_investors,
                    "startup_context": {
                        "name": user_context.get('org_name'),
                        "categories": user_context.get('category_list', []),
                        "funding": user_context.get('total_funding_usd')
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error getting investor recommendations: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the investor recommendations"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        startup = data["data"]["startup_context"]
        recommendations = data["data"]["recommendations"]

        sections = [
            f"# Investor Recommendations for {startup['name']}",
            "\nBased on your profile:",
            f"- Industry: {', '.join(startup['categories'])}",
            f"- Current Funding: ${startup['funding']:,.2f}",
            "\n## Recommended Investors\n"
        ]

        for investor in recommendations:
            sections.extend([
                f"### {investor['name']}",
                f"\n{investor['description']}",
                "\n**Why This Investor Matches:**",
                *[f"- {reason}" for reason in investor['match_reasons']],
                "\n**Investment Focus:**",
                *[f"- {category}: {count} investments" 
                  for category, count in investor['investment_focus'].items()],
                "\n**Recent Investment Activity:**",
                f"- Total Investments: {investor['recent_investments'].get('investment_count', 'N/A')}",
                f"- Total Funding Deployed: ${investor['recent_investments'].get('total_funding_usd', 0):,.2f}",
                "\n**Network:**",
                f"- Co-investors: {len(investor['network'].get('co_investors', []))}",
                "\n**Contact:**",
                f"- Website: {investor['contact']['website']}",
                f"- LinkedIn: {investor['contact']['linkedin']}",
                "\n---\n"
            ])

        return "\n".join(sections)
