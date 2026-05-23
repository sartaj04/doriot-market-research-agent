from core.config import get_settings
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from typing import Dict, Any, Optional, AsyncGenerator, Tuple
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.pipeline.transport import RequestsTransport
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()


class BackupModelConfig:
    """Configuration for backup model access"""
    
    @staticmethod
    def is_enabled() -> bool:
        return settings.ENABLE_BACKUP_MODEL
    
    @staticmethod
    def get_model() -> str:
        return settings.AZURE_DEEPSEEK_MODEL
        
    @staticmethod
    def get_credentials() -> Dict[str, str]:
        return {
            "api_key": settings.AZURE_DEEPSEEK_KEY,
            "api_version": settings.AZURE_DEEPSEEK_API_VERSION,
            "azure_endpoint": settings.AZURE_DEEPSEEK_ENDPOINT
        }
    

class BackupModelHandler:
    """Handles queries when no documents are retrieved, using DeepSeek-R1 via Azure"""
    
    def __init__(self):
        credentials = BackupModelConfig.get_credentials()
        base_endpoint = "https://sarta-m79kr3c2-eastus2.services.ai.azure.com/models"
            
        self.client = ChatCompletionsClient(
            endpoint=base_endpoint,
            credential=AzureKeyCredential(credentials["api_key"]),
            transport=RequestsTransport(read_timeout=300)
        )
        self.model = BackupModelConfig.get_model()

    def _format_investor_list(self, investors: list) -> str:
        logger.debug(f"Formatting investor list: {investors}")
        """Format investor list to string, extracting names from dictionaries"""
        if not investors:
            return "N/A"
        
        investor_names = []
        for investor in investors:
            if isinstance(investor, dict):
                name = investor.get('name')
                if name:
                    investor_names.append(name)
            elif isinstance(investor, str):
                investor_names.append(investor)
                
        return ', '.join(investor_names) if investor_names else "N/A"

    def _is_startup_related_query(self, query: str, startup_name: Optional[str]) -> Tuple[bool, str]:
        """Check if query is related to user's startup by checking patterns"""
        if not startup_name:
            return False, "No startup name provided"
            
        query_lower = query.lower()
        startup_lower = startup_name.lower()
        
        logger.debug(f"Checking query '{query_lower}' for startup name '{startup_lower}'")
        
        # Check for direct startup name mention
        if startup_lower in query_lower:
            logger.debug(f"Found direct startup name mention: {startup_lower}")
            return True, "Direct startup name match"
            
        # Personal reference patterns
        personal_patterns = [
            'my startup', 'my company', 'our startup', 'our company',
            'for me', 'for us', 'my business', 'our business',
            'recommend me', 'suggest me', 'help me find', 'for my', 'for our',
            'my competitors', 'our competitors', 'my market', 'our market',
            'my industry', 'our industry', 'my sector', 'our sector',
            'my target', 'our target', 'my customers', 'our customers',
            'my users', 'our users', 'my audience', 'our audience',
            'my product', 'our product', 'my service', 'our service',
            'my offering', 'our offering', 'my solution', 'our solution'
        ]
        
        for pattern in personal_patterns:
            if pattern in query_lower:
                logger.debug(f"Found personal reference pattern: {pattern}")
                return True, f"Personal reference match: {pattern}"
                
        # Additional checks for personal queries
        personal_pronouns = ['i ', 'me', 'my', 'we', 'us', 'our']
        business_terms = [
            'competitor', 'competition', 'market', 'industry', 'sector',
            'customer', 'user', 'audience', 'product', 'service',
            'offering', 'solution', 'strategy', 'positioning',
            'differentiation', 'advantage', 'edge', 'strength',
            'weakness', 'opportunity', 'threat', 'challenge'
        ]
        
        # Check for personal pronouns combined with business terms
        if any(term in query_lower for term in business_terms):
            if any(pron in query_lower for pron in personal_pronouns):
                logger.debug("Found personal business query pattern")
                return True, "Personal business query match"
        
        # Check for comparative queries
        comparative_terms = ['compare', 'versus', 'vs', 'against', 'relative to']
        if any(term in query_lower for term in comparative_terms):
            if any(pron in query_lower for pron in personal_pronouns):
                logger.debug("Found comparative query pattern")
                return True, "Comparative query match"
        
        logger.debug("No startup reference found")
        return False, "No match found"


    async def _determine_query_type(self, query: str, startup_name: Optional[str] = None) -> Dict[str, Any]:
        """Determine query type and appropriate response format"""
        try:
            # First check if query mentions the startup
            is_startup_related, match_reason = self._is_startup_related_query(query, startup_name)
            logger.debug(f"Startup relation check: {is_startup_related} - {match_reason}")
            
            # Always include startup name in context if available
            contextualized_query = f"[Startup: {startup_name}] {query}" if startup_name else query
            
            # If startup is mentioned, force it to be a personal query
            if is_startup_related:
                logger.debug("Forcing personal query due to startup mention")
                return {
                    "query_type": "PERSONAL_INVESTOR_REQUEST" if "investor" in query.lower() else "STARTUP_SPECIFIC",
                    "needs_context": True,
                    "reasoning": f"Startup reference found: {match_reason}",
                    "structured_response": True
                }
            
            # Only use LLM classification if not already determined by startup name check
            if not is_startup_related:
                response = self.client.complete(
                    stream=False,
                    model=self.model,
                    messages=[
                        SystemMessage(content=f"""Classify the query type and determine if startup context is needed.
                        
                        Context: The user's startup name is "{startup_name if startup_name else 'N/A'}"
                        Current query: {query}
                        
                        Types:
                        1. STARTUP_SPECIFIC - Query about the user's specific startup (needs profile)
                        2. PERSONAL_INVESTOR_REQUEST - Request for personalized investor recommendations (needs context)
                        3. GENERAL_INVESTOR_QUERY - General investor research queries (no context needed)
                        4. MARKET_ANALYSIS - General market analysis query
                        5. GENERAL_QUESTION - Other general questions
                    
                    Examples:
                    - "Recommend investors for my startup" -> PERSONAL_INVESTOR_REQUEST (needs_context: true)
                    - "Who are investors for {startup_name if startup_name else 'XYZ'}" -> PERSONAL_INVESTOR_REQUEST (needs_context: true)
                    - "Find healthcare investors in UK" -> GENERAL_INVESTOR_QUERY (needs_context: false)
                    - "Analyze {startup_name if startup_name else 'XYZ'}'s market fit" -> STARTUP_SPECIFIC (needs_context: true)
                    - "What's the AI market size" -> MARKET_ANALYSIS (needs_context: false)
                    
                    If query mentions the startup name or terms like 'my startup', treat it as a personal query needing context."""),
                    UserMessage(content=f"""Analyze this query: {contextualized_query}
                    Return format: {{
                        "query_type": "STARTUP_SPECIFIC|PERSONAL_INVESTOR_REQUEST|GENERAL_INVESTOR_QUERY|MARKET_ANALYSIS|GENERAL_QUESTION",
                        "needs_context": bool,
                        "reasoning": "brief explanation",
                        "structured_response": bool
                    }}""")
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Query type determination failed: {str(e)}")
            return {
                "query_type": "GENERAL_QUESTION",
                "needs_context": False,
                "reasoning": "Default due to error",
                "structured_response": False
            }

    def _get_system_prompt(self, query_type: str) -> str:
        """Get appropriate system prompt based on query type"""
        prompts = {
            "STARTUP_SPECIFIC": """You are an AI startup advisor. Analyze the provided startup profile 
            and provide specific, actionable insights based on the profile details. Focus on the unique 
            aspects of this startup and provide targeted recommendations.""",
            
            "PERSONAL_INVESTOR_REQUEST": """You are an AI investment advisor. Analyze the provided list 
            of recommended investors in the context of the startup's profile. Explain why these investors 
            might be interested based on their focus areas and the startup's characteristics.""",
            
            "GENERAL_INVESTOR_QUERY": """You are an AI investment researcher. Provide detailed information 
            about investors based on the specified criteria (industry, region, etc.). Include typical 
            investment sizes, focus areas, and notable portfolio companies where relevant.""",
            
            "MARKET_ANALYSIS": """You are a market research analyst. Provide detailed market insights 
            and analysis based on comprehensive industry knowledge. Include market size, growth trends, 
            key players, and important market dynamics.""",
            
            "GENERAL_QUESTION": """You are a knowledgeable AI assistant with expertise in business, 
            technology, and entrepreneurship. Provide clear, accurate, and actionable information 
            backed by reliable sources and industry knowledge."""
        }
        
        # Add a base prompt section to all responses
        base_prompt = """
        Remember to:
        - Provide factual, specific information rather than generic advice
        - Back claims with data or clear reasoning where possible
        - Focus on actionable insights
        - Be concise but comprehensive
        - Highlight any assumptions or limitations in your response
        """
        
        return prompts.get(query_type, prompts["GENERAL_QUESTION"]) + base_prompt
        return prompts.get(query_type, prompts["GENERAL_QUESTION"])

    def _get_response_limits(self, query_type: str) -> Dict[str, int]:
        """Get word/section limits based on query type"""
        limits = {
            "STARTUP_SPECIFIC": {
                "total_words": 800,
                "section_words": 160  # For 5 sections
            },
            "PERSONAL_INVESTOR_REQUEST": {
                "total_words": 400,
                "section_words": 100  # For investor descriptions
            },
            "GENERAL_INVESTOR_QUERY": {
                "total_words": 600,
                "section_words": 120
            },
            "MARKET_ANALYSIS": {
                "total_words": 750,
                "section_words": 150
            },
            "GENERAL_QUESTION": {
                "total_words": 300,
                "section_words": None
            }
        }
        return limits.get(query_type, {"total_words": 300, "section_words": None})

    def _get_query_prompt(self, query: str, query_type: str, needs_structured: bool) -> str:
        """Get appropriate query prompt based on type and structure needs"""
        limits = self._get_response_limits(query_type)
        
        base_prompt = f"""Answer this query: {query}

        Keep your total response within {limits['total_words']} words.
        Be concise and focused while providing valuable insights.
        """
        
        if needs_structured and query_type in ["STARTUP_SPECIFIC", "MARKET_ANALYSIS"]:
            base_prompt += f"""
            Structure your analysis to cover these sections, with approximately {limits['section_words']} words per section:
            1. Market Overview
            2. Competitive Landscape
            3. Growth Opportunities
            4. Risk Analysis
            5. Strategic Recommendations"""
        elif query_type == "PERSONAL_INVESTOR_REQUEST":
            base_prompt += f"""
            For each recommended investor, provide a concise analysis (max {limits['section_words']} words) covering:
            - Investment focus alignment
            - Why they might be interested
            - Typical investment parameters"""
        elif query_type == "GENERAL_INVESTOR_QUERY":
            base_prompt += f"""
            For each relevant investor or investor category, provide:
            - Focus areas and preferences
            - Investment criteria
            - Notable investments
            Limit each investor/category description to {limits['section_words']} words."""
        
        return base_prompt

    async def get_backup_response(self, query: str, user_context: Optional[Dict[str, Any]] = None):
        if not BackupModelConfig.is_enabled():
            return {"status": "error", "error": "Backup model is disabled"}
                
        query_analysis = await self._determine_query_type(
            query, 
            startup_name=user_context.get('org_name') if user_context else None
        )
        
        context_str = ""
        if query_analysis["needs_context"] and user_context:
            # Log the user context for debugging
            logger.debug(f"User context received: {user_context}")
            
            # Ensure we have the correct startup information
            if not user_context.get('org_name'):
                logger.warning("No startup name found in user context")
                return {"status": "error", "error": "No startup information available"}
            
            context_str = f"""
            Startup Profile Context:
            Organization: {user_context.get('org_name', 'N/A')}
            Industry: {', '.join(user_context.get('category_list', []))}
            Description: {user_context.get('description', 'N/A')}
            Location: {user_context.get('org_region', 'N/A')}, {user_context.get('org_country_code', 'N/A')}
            Recommended Investors: {self._format_investor_list(user_context.get('investors_simple_list', []))}
            """
            
            logger.debug(f"Using context for query: {query}")
            logger.debug(f"Context details: {context_str}")

        try:
            system_prompt = self._get_system_prompt(query_analysis["query_type"])
            query_prompt = self._get_query_prompt(
                query, 
                query_analysis["query_type"],
                query_analysis["structured_response"]
            )

            response = self.client.complete(
                stream=True,
                model=self.model,
                messages=[
                    SystemMessage(content=system_prompt),
                    UserMessage(content=f"{context_str}\n\n{query_prompt}")
                ],
                temperature=0.3,
                max_tokens=self._get_response_limits(query_analysis["query_type"])["total_words"] * 4  # Approximate tokens
            )

            # Process streaming response
            full_content = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_content += chunk.choices[0].delta.content
            
            return {
                "status": "success",
                "source": "backup_model",
                "data": {
                    "content": full_content,
                    "model_used": "Azure DeepSeek-R1",
                    "query_type": query_analysis["query_type"]
                }
            }
                    
        except Exception as e:
            logger.error(f"Error using DeepSeek-R1: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def get_backup_response_stream(
        self, 
        query: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream responses directly from the backup model"""
        
        if not BackupModelConfig.is_enabled():
            yield {"status": "error", "error": "Backup model is disabled"}
            return

        query_analysis = await self._determine_query_type(
            query, 
            startup_name=user_context.get('org_name') if user_context else None
        )
        
        context_str = ""
        if query_analysis["needs_context"] and user_context:
            context_str = f"""
            Startup Profile Context:
            Organization: {user_context.get('org_name', 'N/A')}
            Industry: {', '.join(user_context.get('category_list', []))}
            Description: {user_context.get('description', 'N/A')}
            Location: {user_context.get('org_region', 'N/A')}, {user_context.get('org_country_code', 'N/A')}
            Recommended Investors: {self._format_investor_list(user_context.get('investors_simple_list', []))}
            """

            logger.debug(f"Context: {context_str}")

        try:
            system_prompt = self._get_system_prompt(query_analysis["query_type"])
            query_prompt = self._get_query_prompt(
                query, 
                query_analysis["query_type"],
                query_analysis["structured_response"]
            )

            response = self.client.complete(
                stream=True,
                model=self.model,
                messages=[
                    SystemMessage(content=system_prompt),
                    UserMessage(content=f"{context_str}\n\n{query_prompt}")
                ],
                temperature=0.3,
                max_tokens=4000
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "status": "success",
                        "data": {
                            "content": chunk.choices[0].delta.content,
                            "model_used": "Azure DeepSeek-R1",
                            "query_type": query_analysis["query_type"]
                        }
                    }

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield {"status": "error", "error": str(e)}