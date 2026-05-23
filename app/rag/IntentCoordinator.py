from typing import List, Dict, Any, Optional, Union
from openai import AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion
import json
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IntentCoordinator:
    """Coordinates multiple intents and handlers for comprehensive responses"""
    
    def __init__(self, openai_client: Union[AsyncOpenAI, AsyncAzureOpenAI], chat_model: str, chat_deployment: Optional[str] = None):
        self.openai_client = openai_client
        self.chat_model = chat_model
        self.chat_deployment = chat_deployment

    async def determine_intents(self, query: str, startup_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.debug(f"Startup Context: {startup_context}")
        """Use LLM to determine relevant intents and their priorities"""
        
        function_def = {
            "name": "select_intents",
            "description": "Select relevant intents for processing a user query",
            "parameters": {
                "type": "object",
                "properties": {
                    "intents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "description": """Choose from these handlers based on their capabilities:
                            GREETING_QUERY: Handle greetings, introductions, and basic agent capabilities
                            MY_STARTUP_QUERY: Analysis of user's startup profile, competitors, and market position
                            RECOMMEND_INVESTORS: Personalized investor recommendations based on startup profile
                            INVESTOR_NETWORK: Investment networks, co-investors, and competitor analysis
                            COMPANY_PROFILE_QUERY: Basic company info, financials, metrics, history
                            FUNDING_ROUND_QUERY: Funding round details, amounts, investors, dates
                            ACQUISITION_QUERY: M&A details, deal values, acquirer/acquiree info
                            IPO_QUERY: IPO details, valuations, stock info, timeline
                            INVESTOR_QUERY: Investor profiles, portfolios, history, strategies
                            INVESTMENT_DETAILS_QUERY: Detailed investment data, terms, participation
                            ORGANIZATION_RELATIONSHIP_QUERY: Corporate structures, parent-subsidiary info
                            INVESTMENT_PARTNER_QUERY: VC partner profiles, track records, expertise
                            FUNDS_QUERY: Fund details, sizes, focus areas, performance
                            JOBS_QUERY: Employment data, job postings, team info
                            PEOPLE_PROFILE_QUERY: Professional backgrounds, roles, achievements
                            EDUCATION_QUERY: Educational backgrounds, degrees, certifications
                            COMPETITOR_LOOKUP: Competitive analysis, market positions
                            LEAD_GENERATION_QUERY: Business opportunities, target companies
                            MARKET_ANALYSIS_QUERY: Market size, growth, industry trends
                            TECH_NEWS_QUERY: Latest tech news, product launches, developments
                            FUNDING_NEWS_QUERY: Recent funding announcements, investment trends
                            EVENT_QUERY: Industry events, conferences, meetups
                            MARKET_TRENDS_QUERY: Industry trends, patterns, future predictions""",
                            "properties": {
                                "intent": {
                                    "type": "string",
                                    "enum": [
                                        "GREETING_QUERY",
                                        "MY_STARTUP_QUERY",
                                        "RECOMMEND_INVESTORS",
                                        "INVESTOR_NETWORK",
                                        "COMPANY_PROFILE_QUERY",
                                        "FUNDING_ROUND_QUERY",
                                        "ACQUISITION_QUERY",
                                        "IPO_QUERY",
                                        "INVESTOR_QUERY",
                                        "INVESTMENT_DETAILS_QUERY",
                                        "ORGANIZATION_RELATIONSHIP_QUERY",
                                        "INVESTMENT_PARTNER_QUERY",
                                        "FUNDS_QUERY",
                                        "JOBS_QUERY",
                                        "PEOPLE_PROFILE_QUERY",
                                        "EDUCATION_QUERY",
                                        "COMPETITOR_LOOKUP",
                                        "LEAD_GENERATION_QUERY",
                                        "MARKET_ANALYSIS_QUERY",
                                        "TECH_NEWS_QUERY",
                                        "FUNDING_NEWS_QUERY",
                                        "EVENT_QUERY",
                                        "MARKET_TRENDS_QUERY"
                                    ]
                                },
                                "priority": {
                                    "type": "integer",
                                    "description": "Priority level (1-5, where 1 is highest)",
                                    "minimum": 1,
                                    "maximum": 5
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Reasoning for selecting this intent"
                                }
                            },
                            "required": ["intent", "priority", "reasoning"]
                        }
                    },
                    "strategy": {
                        "type": "string",
                        "description": "Strategy for combining information from multiple intents",
                        "enum": ["sequential", "parallel", "hierarchical"]
                    }
                },
                "required": ["intents", "strategy"]
            }
        }
        startup_context_prompt = ""
        if startup_context and startup_context.get('org_name'):
            startup_context_prompt = f"""
            IMPORTANT - Startup Context Priority Rules:
            Current Startup: {startup_context.get('org_name')}
            
            ALWAYS follow these rules in order:
            
            1. HIGHEST PRIORITY - Use MY_STARTUP_QUERY when:
            - Query contains ANY of these patterns:
            - "my startup", "my company", "my business", "our startup"
            - "{startup_context.get('org_name')}" (exact company name)
            - ANY possessive words ("my", "our", "us", "we") in business context
            - Even indirect references to user's business
            DO NOT use COMPANY_PROFILE_QUERY for these cases
            
            2. HIGH PRIORITY - Use RECOMMEND_INVESTORS when:
            - ANY mention of "investors", "funding", "investment"
            - Phrases like "who should invest", "find investors"
            - Questions about fundraising or getting investment
            
            3. OVERRIDE RULE:
            - If query matches rules for MY_STARTUP_QUERY, ALWAYS use it instead of COMPANY_PROFILE_QUERY
            - When in doubt between MY_STARTUP_QUERY and another intent, choose MY_STARTUP_QUERY
            
            4. Query Examples and Correct Intents:
            - "Tell me about my business" → MY_STARTUP_QUERY
            - "What's {startup_context.get('org_name')}'s profile" → MY_STARTUP_QUERY
            - "Find investors for my startup" → RECOMMEND_INVESTORS + MY_STARTUP_QUERY
            - "Who should invest in us?" → RECOMMEND_INVESTORS
            """

        messages = [
            {
                "role": "system",
                "content": f"""You are an AI trained to analyze user queries and determine the most appropriate intents.
                {startup_context_prompt}
                
                Key Rules:
                1. Startup context ALWAYS takes precedence over general company queries
                2. MY_STARTUP_QUERY has highest priority when ANY startup context matches
                3. Never use COMPANY_PROFILE_QUERY when query could refer to user's startup
                
                Strategy Selection:
                - Use "hierarchical" when combining MY_STARTUP_QUERY with other intents
                - MY_STARTUP_QUERY should always have priority=1 when selected
                """
            },
            {
                "role": "user",
                "content": f"Analyze this query and select relevant intents: {query}"
            }
        ]
        

        try:
            completion = await self.openai_client.chat.completions.create(
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                tools=[{"type": "function", "function": function_def}],
                tool_choice={"type": "function", "function": {"name": "select_intents"}}
            )

            tool_call = completion.choices[0].message.tool_calls[0]
            return json.loads(tool_call.function.arguments)
        except Exception as e:
            logger.error(f"Error in intent determination: {str(e)}")
            return {"intents": [], "strategy": "sequential"}

    async def coordinate_handlers(
        self, 
        handlers: Dict[str, Any],
        selected_intents: Dict[str, Any],
        query: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        results = []
        strategy = selected_intents["strategy"]
        
        try:
            # First, get all handler definitions
            handler_defs = {}
            for intent_info in selected_intents["intents"]:
                intent_name = intent_info["intent"]
                if intent_name in handlers:
                    handler = handlers[intent_name]
                    try:
                        handler_defs[intent_name] = await handler.get_function_def()
                    except Exception as e:
                        logger.error(f"Error getting function def for {intent_name}: {str(e)}")

            # Extract parameters using handler definitions
            intent_params = await self._extract_intent_params(
                query=query,
                selected_intents=selected_intents,
                handler_defs=handler_defs
            )

            # Helper function to prepare parameters for a specific handler
            def prepare_handler_params(intent_name: str, base_params: Dict[str, Any]) -> Dict[str, Any]:
                # Get handler's function definition
                handler_def = handler_defs.get(intent_name, {})
                expected_params = handler_def.get("parameters", {}).get("properties", {})
                
                # Get intent-specific parameters
                specific_params = intent_params.get(intent_name, {})
                
                # Create a new params dict with only the parameters the handler expects
                handler_params = {}
                
                # Special handling for MY_STARTUP_QUERY
                if intent_name == "MY_STARTUP_QUERY":
                    handler_params["analysis_type"] = "full_analysis"  # Default to full analysis
                    handler_params["user_context"] = base_params.get("user_context", {})
                    handler_params["priority"] = 1
                elif intent_name == "RECOMMEND_INVESTORS":
                    handler_params["user_context"] = base_params.get("user_context", {})
                    handler_params["priority"] = 1
                
                # Add only the base params that the handler expects
                for param_name in expected_params:
                    if param_name in base_params and param_name != "user_context":
                        handler_params[param_name] = base_params[param_name]
                
                # Add the intent-specific params
                for param_name, value in specific_params.items():
                    if param_name in expected_params:
                        handler_params[param_name] = value
                
                return handler_params
        
            if strategy == "parallel":
                tasks = []
                for intent_info in selected_intents["intents"]:
                    intent_name = intent_info["intent"]
                    if intent_name in handlers:
                        handler = handlers[intent_name]
                        handler_params = prepare_handler_params(intent_name, params)
                        if intent_name in ["MY_STARTUP_QUERY", "RECOMMEND_INVESTORS"]:
                            tasks.append(handler.execute_query(handler_params, user_context=params.get("user_context", {})))
                        else:
                            tasks.append(handler.execute_query(handler_params))
                
                raw_results = await asyncio.gather(*tasks, return_exceptions=True)
                results = [r for r in raw_results if not isinstance(r, Exception)]
                
            elif strategy == "hierarchical":
                sorted_intents = sorted(selected_intents["intents"], key=lambda x: x["priority"])
                context = {}
                
                for intent_info in sorted_intents:
                    intent_name = intent_info["intent"]
                    if intent_name in handlers:
                        handler = handlers[intent_name]
                        try:
                            handler_params = prepare_handler_params(intent_name, params)
                            handler_params["context"] = context  # Add context for hierarchical
                            if intent_name in ["MY_STARTUP_QUERY", "RECOMMEND_INVESTORS"]:
                                result = await handler.execute_query(handler_params, user_context=params.get("user_context", {}))
                            else:
                                result = await handler.execute_query(handler_params)
                            results.append(result)
                            if result.get("status") == "success":
                                context[intent_name] = result["data"]
                        except Exception as e:
                            logger.error(f"Error executing handler {intent_name}: {str(e)}")
                        
            else:  # sequential
                for intent_info in selected_intents["intents"]:
                    intent_name = intent_info["intent"]
                    if intent_name in handlers:
                        handler = handlers[intent_name]
                        try:
                            handler_params = prepare_handler_params(intent_name, params)
                            if intent_name in ["MY_STARTUP_QUERY", "RECOMMEND_INVESTORS"]:
                                result = await handler.execute_query(handler_params, user_context=params.get("user_context", {}))
                            else:
                                result = await handler.execute_query(handler_params)
                            results.append(result)
                        except Exception as e:
                            logger.error(f"Error executing handler {intent_name}: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Error in handler coordination: {str(e)}")
            return []
    async def _extract_intent_params(
        self,
        query: str,
        selected_intents: Dict[str, Any],
        handler_defs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract parameters for each intent using their function definitions"""
        try:
            # Build combined function definition using all handler parameter definitions
            function_def = {
                "name": "extract_intent_parameters",
                "description": "Extract specific parameters for each intent from the query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "intent_params": {
                            "type": "object",
                            "properties": {
                                intent_name: {
                                    "type": "object",
                                    "properties": handler_def["parameters"]["properties"],
                                    "description": handler_def.get("description", "")
                                }
                                for intent_name, handler_def in handler_defs.items()
                            }
                        }
                    },
                    "required": ["intent_params"]
                }
            }

            messages = [
                {
                    "role": "system",
                    "content": """Extract specific parameters for each intent based on their handler definitions.
                    Only extract parameters that are explicitly mentioned or clearly implied in the query.
                    Each handler has its own parameter requirements - ensure parameters match the handler's schema."""
                },
                {
                    "role": "user",
                    "content": f"Extract parameters from query: {query}\nFor intents: {list(handler_defs.keys())}"
                }
            ]

            completion = await self.openai_client.chat.completions.create(
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=messages,
                tools=[{"type": "function", "function": function_def}],
                tool_choice={"type": "function", "function": {"name": "extract_intent_parameters"}}
            )

            tool_call = completion.choices[0].message.tool_calls[0]
            params = json.loads(tool_call.function.arguments)
            return params.get("intent_params", {})
            
        except Exception as e:
            logger.error(f"Error extracting intent parameters: {str(e)}")
            return {}


    async def combine_results(
        self,
        results: List[Dict[str, Any]],
        selected_intents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine results from multiple handlers into a coherent response"""
        
        combined_data = {
            "meta": {
                "strategy": selected_intents["strategy"],
                "intents_used": [i["intent"] for i in selected_intents["intents"]],
                "timestamp": datetime.utcnow().isoformat()
            },
            "data": {}
        }

        try:
            # Convert list of results to a dictionary keyed by intent
            results_dict = {}
            for i, result in enumerate(results):
                if i < len(selected_intents["intents"]):
                    intent_name = selected_intents["intents"][i]["intent"]
                    results_dict[intent_name] = result

            # Process each intent's results
            for intent_info in selected_intents["intents"]:
                intent_name = intent_info["intent"]
                result = results_dict.get(intent_name)
                
                if result and isinstance(result, dict):
                    if result.get("status") == "success":
                        combined_data["data"][intent_name] = {
                            "priority": intent_info["priority"],
                            "reasoning": intent_info["reasoning"],
                            "result": result.get("data", {})
                        }
                    else:
                        logger.warning(f"Failed result for intent {intent_name}: {result.get('error', 'Unknown error')}")
                elif result:  # If result is a list or other type
                    combined_data["data"][intent_name] = {
                        "priority": intent_info["priority"],
                        "reasoning": intent_info["reasoning"],
                        "result": result
                    }

            return combined_data

        except Exception as e:
            logger.error(f"Error combining results: {str(e)}")
            return {
                "meta": {"error": str(e)},
                "data": {}
            }