from typing import Dict, Any, Optional
from openai import AsyncAzureOpenAI
import logging

logger = logging.getLogger(__name__)

class GreetingHandler:
    """Handler for generating dynamic and contextual greetings using Azure OpenAI"""
    
    def __init__(self, client: AsyncAzureOpenAI, model: str):
        self.client = client
        self.model = model

    async def get_function_def(self) -> Dict[str, Any]:
        return {
            "name": "handle_greeting",
            "description": "Handle user greetings and introductions",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }

    async def execute_query(self, params: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the greeting query using Azure OpenAI for dynamic response generation"""
        try:
            # Prepare context for LLM
            context_str = ""
            if user_context:
                context_str = f"""
                Company: {user_context.get('org_name', '')}
                Industry: {', '.join(user_context.get('category_list', []))}
                Stage: {user_context.get('funding_stage', '')}
                Region: {user_context.get('org_region', '')}
                """

            # Generate dynamic greeting using Azure OpenAI
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are Doriot AI, an advanced startup intelligence copilot powered by comprehensive market data and AI. Generate an engaging greeting with exactly this structure:

                        SECTION 1 - Introduction (2-3 sentences):
                        - Start with "👋 Hi! I'm Doriot AI"
                        - Briefly explain you're an AI-powered copilot for startups
                        - If company context provided, acknowledge their industry/focus naturally

                        SECTION 2 - Quick Insight (1 sentence):
                        - Share ONE specific, data-backed startup fact relevant to their industry
                        - If no industry context, share a general startup success insight
                        - Must include a specific statistic or metric

                        SECTION 3 - Core Capabilities (exactly 4 bullet points):
                        - Investment Intelligence: Finding investors, funding opportunities
                        - Market Analysis: Industry trends, competitive landscape
                        - Growth Strategy: Business planning, pitch optimization
                        - Data-Driven Insights: Real-time market monitoring
                        (Customize these based on company context if provided)

                        SECTION 4 - Closing:
                        End with a specific, context-aware question about their startup needs"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a greeting with this context:\n{context_str}"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Extract content from response
            generated_content = completion.choices[0].message.content

            # Parse the response into our expected format
            sections = [s.strip() for s in generated_content.split('\n\n') if s.strip()]
            
            # Extract sections based on content
            introduction_parts = []
            capabilities = []
            closing = ""

            for section in sections:
                if section.startswith('👋'):
                    introduction_parts.append(section)
                elif '💡' in section or '%' in section or any(c.isdigit() for c in section):
                    introduction_parts.append(section)
                elif section.startswith('-') or section.startswith('•'):
                    capabilities.extend([cap.strip('- •').strip() 
                                      for cap in section.split('\n') 
                                      if cap.strip().startswith(('-', '•'))])
                elif '?' in section:
                    closing = section.strip()

            greeting_response = {
                "introduction": "\n\n".join(introduction_parts),
                "capabilities": capabilities[:4],  # Ensure exactly 4 capabilities
                "usage": closing if closing else "What aspect of your startup would you like to explore?"
            }

            return {
                "status": "success",
                "data": greeting_response
            }

        except Exception as e:
            logger.error(f"Error in greeting handler: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def format_for_context(self, result: Dict[str, Any]) -> str:
        """Format greeting response for context"""
        if result["status"] != "success":
            return "Error in greeting handler"
            
        data = result["data"]
        # Format capabilities as bullet points
        capabilities_formatted = "\n".join(f"- {cap}" for cap in data['capabilities'])
        
        return f"{data['introduction']}\n\n{capabilities_formatted}\n\n{data['usage']}"