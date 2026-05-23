from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from repositories.InvestorRepository import InvestorsRepository
from models.investors import Investors
import json
from core.openai import AsyncAzureOpenAI 

logger = logging.getLogger(__name__)

class InvestorNetworkHandler:
    """Handles queries about investor networks, co-investors, and competitors"""
    
    def __init__(self, db: Session, openai_client: AsyncAzureOpenAI):
        self.db = db
        self.openai_client = openai_client
        self.investor_repo = InvestorsRepository()

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "analyze_investor_network",
            "description": "Analyze investor networks, co-investors, and competitors",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": [
                            "co_investors",
                            "competitor_investors",
                            "full_network"
                        ],
                        "description": "Type of investor network analysis"
                    },
                    "investor_uuid": {
                        "type": "string",
                        "description": "UUID of the investor to analyze"
                    }
                },
                "required": ["analysis_type", "investor_uuid"]
            }
        }

    async def execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute investor network analysis"""
        try:
            analysis_type = params["analysis_type"]
            investor_uuid = params["investor_uuid"]

            # Get investor data
            investor_stats = await self.investor_repo.get_investor_stats(
                self.db,
                investor_uuid
            )
            
            if not investor_stats:
                return {
                    "status": "error",
                    "error": f"Investor with UUID '{investor_uuid}' not found"
                }
            
            response_data = {
                "investor_info": {
                    "name": investor_stats["basic_info"]["name"],
                    "type": investor_stats["basic_info"]["type"],
                    "description": investor_stats["basic_info"]["description"],
                    "metrics": investor_stats["investment_metrics"]
                }
            }

            # Get relevant network data based on analysis type
            if analysis_type in ["co_investors", "full_network"]:
                network = await self._get_co_investor_network(investor_stats)
                response_data["co_investors"] = network

            if analysis_type in ["competitor_investors", "full_network"]:
                competitors = await self._get_competitor_analysis(investor_stats)
                response_data["competitors"] = competitors

            # Add investment focus data
            response_data["investment_focus"] = {
                "top_categories": investor_stats.get("investment_analysis", {}).get("top_categories", {}),
                "top_series": investor_stats.get("investment_analysis", {}).get("top_investment_rounds", {}),
                "top_locations": investor_stats.get("investment_analysis", {}).get("top_locations", {})
            }

            return {
                "status": "success",
                "data": response_data
            }

        except Exception as e:
            logger.error(f"Error in investor network analysis: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _get_co_investor_network(self, investor_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze co-investor network using combined_co_lead_list"""
        try:
            co_investors = []
            network_data = investor_stats.get("co_investment_network", {})
            
            for co_inv in network_data.get("co_investors", []):
                co_investor_stats = await self.investor_repo.get_investor_stats(
                    self.db,
                    co_inv.get("uuid")
                )
                
                if co_investor_stats:
                    co_investors.append({
                        "name": co_investor_stats["basic_info"]["name"],
                        "type": co_investor_stats["basic_info"]["type"],
                        "investment_count": co_investor_stats["investment_metrics"]["investment_count"],
                        "investment_focus": co_investor_stats["investment_analysis"]["top_categories"],
                        "total_funding": co_investor_stats["investment_metrics"]["total_funding_usd"],
                        "contact": {
                            "website": co_investor_stats["social_presence"]["domain"],
                            "linkedin": co_investor_stats["social_presence"]["linkedin"]
                        }
                    })

            return {
                "total_co_investors": len(co_investors),
                "co_investors": sorted(
                    co_investors,
                    key=lambda x: x["investment_count"],
                    reverse=True
                )
            }

        except Exception as e:
            logger.error(f"Error getting co-investor network: {str(e)}")
            return {"total_co_investors": 0, "co_investors": []}

    async def _get_competitor_analysis(self, investor_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitor investors using competitors_list"""
        try:
            competitors = []
            landscape_data = investor_stats.get("competitive_landscape", {})
            
            for comp in landscape_data.get("competitors", []):
                competitor_stats = await self.investor_repo.get_investor_stats(
                    self.db,
                    comp.get("uuid")
                )
                
                if competitor_stats:
                    competitors.append({
                        "name": competitor_stats["basic_info"]["name"],
                        "type": competitor_stats["basic_info"]["type"],
                        "description": competitor_stats["basic_info"]["description"],
                        "investment_metrics": {
                            "count": competitor_stats["investment_metrics"]["investment_count"],
                            "total_funding": competitor_stats["investment_metrics"]["total_funding_usd"]
                        },
                        "focus": competitor_stats["investment_analysis"]["top_categories"],
                        "social": {
                            "domain": competitor_stats["social_presence"]["domain"],
                            "linkedin": competitor_stats["social_presence"]["linkedin"]
                        }
                    })

            return {
                "total_competitors": len(competitors),
                "competitors": sorted(
                    competitors,
                    key=lambda x: x["investment_metrics"]["count"],
                    reverse=True
                )
            }

        except Exception as e:
            logger.error(f"Error getting competitor analysis: {str(e)}")
            return {"total_competitors": 0, "competitors": []}

    async def format_for_context(self, data: Dict[str, Any]) -> str:
        """Format the network analysis results"""
        if data.get("status") != "success":
            return f"Error: {data.get('error', 'Unknown error')}"

        response_data = data["data"]
        sections = [
            f"# Investor Network Analysis: {response_data['investor_info']['name']}",
            f"\n{response_data['investor_info']['description']}",
            "\n## Investment Profile",
            f"- Type: {response_data['investor_info']['type']}",
            f"- Total Investments: {response_data['investor_info']['metrics']['investment_count']}",
            f"- Total Funding Deployed: ${response_data['investor_info']['metrics']['total_funding_usd']:,.2f}"
        ]

        # Investment Focus
        focus = response_data["investment_focus"]
        if focus["top_categories"]:
            sections.extend([
                "\n### Investment Categories",
                *[f"- {category}: {count} investments" 
                  for category, count in focus["top_categories"].items()]
            ])
        
        if focus["top_series"]:
            sections.extend([
                "\n### Investment Stages",
                *[f"- {stage}: {count} rounds" 
                  for stage, count in focus["top_series"].items()]
            ])

        # Co-Investors Section
        if "co_investors" in response_data:
            network = response_data["co_investors"]
            sections.extend([
                f"\n## Co-Investor Network ({network['total_co_investors']} Partners)",
                "\nTop Co-Investment Partners:"
            ])
            
            for co_inv in network["co_investors"]:
                sections.extend([
                    f"\n### {co_inv['name']}",
                    f"- Type: {co_inv['type']}",
                    f"- Total Investments: {co_inv['investment_count']}",
                    f"- Total Funding Deployed: ${co_inv['total_funding']:,.2f}",
                    "- Investment Focus:",
                    *[f"  * {category}: {count} investments" 
                      for category, count in co_inv['investment_focus'].items()],
                    "- Contact:",
                    f"  * Website: {co_inv['contact']['website']}",
                    f"  * LinkedIn: {co_inv['contact']['linkedin']}"
                ])

        # Competitors Section
        if "competitors" in response_data:
            comp_data = response_data["competitors"]
            sections.extend([
                f"\n## Similar Investors ({comp_data['total_competitors']} Competitors)",
                "\nKey Competitors:"
            ])
            
            for comp in comp_data["competitors"]:
                sections.extend([
                    f"\n### {comp['name']}",
                    f"{comp['description']}",
                    f"\n- Type: {comp['type']}",
                    f"- Total Investments: {comp['investment_metrics']['count']}",
                    f"- Total Funding Deployed: ${comp['investment_metrics']['total_funding']:,.2f}",
                    "- Investment Focus:",
                    *[f"  * {category}: {count} investments" 
                      for category, count in comp['focus'].items()],
                    "- Contact:",
                    f"  * Website: {comp['social']['domain']}",
                    f"  * LinkedIn: {comp['social']['linkedin']}"
                ])

        return "\n".join(sections)