from sqlalchemy.orm import Session
from core.openai import AsyncAzureOpenAI 
from repositories.InvestorRepository import InvestorsRepository
from repositories.CompanyRepository import CompanyRepository
from repositories.ArticlesRepository import ArticlesRepository
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MyStartupHandler:
    """Handles comprehensive analysis of user's startup"""
    
    def __init__(self, db: Session, openai_client: AsyncAzureOpenAI):
        self.db = db
        self.openai_client = openai_client
        self.competitor_repo = CompanyRepository()
        self.article_repo = ArticlesRepository()
        self.investor_repo = InvestorsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "analyze_startup",
            "description": "Analyze different aspects of user's startup",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": [
                            "competitors",
                            "market_news",
                            "investors",
                            "profile",
                            "full_analysis"
                        ],
                        "description": "Type of analysis to perform"
                    },
                    "specific_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific metrics to analyze"
                    }
                },
                "required": ["analysis_type"]
            }
        }

    async def execute_query(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute startup analysis query"""
        try:
            analysis_type = params["analysis_type"]
            response_data = {}

            # Basic profile always included
            response_data["profile"] = {
                "name": user_context.get('org_name'),
                "categories": user_context.get('category_list', []),
                "description": user_context.get('description'),
                "location": f"{user_context.get('org_region')}, {user_context.get('org_country_code')}",
                # "metrics": {
                #     "funding": user_context.get('total_funding_usd'),
                #     "employees": user_context.get('employee_count')
                # }
            }

            # Add requested analysis
            if analysis_type in ["competitors", "full_analysis"]:
                competitors = await self.competitor_repo.get_competitors(
                    self.db,
                    user_context.get('org_uuid'),
                    self.openai_client,
                    limit=5
                )
                response_data["competitors"] = [
                    {
                        "name": comp.name,
                        "description": comp.short_description,
                        "funding": comp.total_funding_usd,
                        "categories": comp.category_list.split(",") if comp.category_list else []
                    }
                    for comp in competitors
                ]

            if analysis_type in ["market_news", "full_analysis"]:
                articles = await self.article_repo.get_articles(
                    self.db,
                    query=" OR ".join(user_context.get('category_list', [])),
                    days=30,
                    limit=5
                )
                response_data["market_news"] = [
                    {
                        "title": article.title,
                        "url": article.url,
                        "published_at": str(article.published_at),
                        "source": "Industry News"
                    }
                    for article in articles
                ]

            if analysis_type in ["investors", "full_analysis"]:
                investor_list = user_context.get('investor_simple_list', [])
                if investor_list:
                    recommended_investors = []
                    for investor in investor_list[:3]:  # Top 3 for brief overview
                        investor_data = await self.investor_repo.get_investor_stats(
                            self.db,
                            investor['uuid']
                        )
                        if investor_data:
                            recommended_investors.append({
                                "name": investor_data.get('basic_info', {}).get('name'),
                                "focus": investor_data.get('investment_analysis', {}).get('top_categories', {})
                            })
                    response_data["recommended_investors"] = recommended_investors

            return {
                "status": "success",
                "data": response_data
            }

        except Exception as e:
            logger.error(f"Error in startup analysis: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the analysis results"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        response_data = data["data"]
        sections = []

        # Profile Section
        profile = response_data["profile"]
        sections.extend([
            "## Your Startup Profile",
            f"**{profile['name']}**",
            f"\n{profile['description']}",
            "\n### Key Information",
            f"- **Industry**: {', '.join(profile['categories'])}",
            f"- **Location**: {profile['location']}",
            # f"- **Current Funding**: ${profile['metrics']['funding']:,.2f}",
            # f"- **Team Size**: {profile['metrics']['employees']}"
        ])

        # Competitors Section
        if "competitors" in response_data:
            sections.extend([
                "\n## Key Competitors",
                *[f"### {comp['name']}\n{comp['description']}\n- Funding: ${comp['funding']:,.2f}"
                  for comp in response_data["competitors"]]
            ])

        # Market News Section
        if "market_news" in response_data:
            sections.extend([
                "\n## Recent Industry News",
                *[f"- [{article['title']}]({article['url']}) - {article['published_at']}"
                  for article in response_data["market_news"]]
            ])

        # Brief Investor Overview
        if "recommended_investors" in response_data:
            sections.extend([
                "\n## Potential Investors",
                "Top matches (for detailed analysis, use the investor recommendation query):",
                *[f"- **{inv['name']}** - Focus: {', '.join(inv['focus'].keys())}"
                  for inv in response_data["recommended_investors"]]
            ])

        return "\n".join(sections)