from collections.abc import AsyncGenerator
from typing import Optional, Union, List, Any, Dict
import json
import logging
from datetime import datetime

from openai import AsyncAzureOpenAI, AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessageParam
from openai_messages_token_helper import build_messages, get_token_limit

from models.api_models import (
    AIChatRoles,
    Message,
    RAGContext,
    RetrievalResponse,
    RetrievalResponseDelta,
    ThoughtStep,
    Intent,
    DataSource,
    StructuredDataPoint,
    ArticleSource
)
from .postgres_searcher import MarketResearchSearcher
from .rag_base import ChatParams, RAGChatBase

from .handlers.CompanyProfileHandler import CompanyProfileHandler
from .handlers.TechNewsHandler import TechNewsHandler
from .handlers.FundingNewsHandler import FundingNewsHandler
from .handlers.MarketTrendsHandler import MarketTrendsHandler
from .handlers.FundingRoundHandler import FundingRoundHandler
from .handlers.AcquisitionHandler import AcquisitionHandler
from .handlers.IpoHandler import IpoHandler
from .handlers.FundsHandler import FundsHandler
from .handlers.PeopleProfileHandler import PeopleProfileHandler
from .handlers.JobsHandler import JobsHandler
from .handlers.EducationHandler import EducationHandler
from .handlers.OrganizationRelationshipHandler import OrganizationRelationshipHandler
from .handlers.InvestmentPartnerHandler import InvestmentPartnerHandler
from .handlers.CompetitorHandler import CompetitorHandler
from .handlers.LeadGenerationHandler import LeadGenerationHandler
from .handlers.MarketAnalysisHandler import MarketAnalysisHandler
from .handlers.EventHandler import EventHandler
from .handlers.InvestorHandler import InvestorHandler
from .handlers.InvestmentDetailsHandler import InvestmentDetailsHandler
from .IntentCoordinator import IntentCoordinator
from .backup_handler import BackupModelHandler
from .handlers.MyStartupHandler import MyStartupHandler
from .handlers.RecommendInvestorsHandler import RecommendInvestorsHandler
from .handlers.InvestorNetworkHandler import InvestorNetworkHandler
from .handlers.GreetingHandler import GreetingHandler
from core.config import get_settings

settings = get_settings()


logger = logging.getLogger(__name__)

class AdvancedRAGChat(RAGChatBase):
    def __init__(
        self,
        *,
        searcher: MarketResearchSearcher,
        openai_client: Union[AsyncOpenAI, AsyncAzureOpenAI],
        chat_model: str,
        chat_deployment: Optional[str],
        user_context: Optional[Dict[str, Any]] = None,
        intent_model_path: str = None
    ):
        super().__init__(intent_model_path)
        self.searcher = searcher
        self.openai_client = openai_client
        self.chat_model = chat_model
        self.chat_deployment = chat_deployment
        self.user_context = user_context
        self.chat_token_limit = get_token_limit(chat_model, default_to_minimum=True)
        
        # Initialize intent coordinator
        self.intent_coordinator = IntentCoordinator(
            openai_client=openai_client,
            chat_model=chat_model,
            chat_deployment=chat_deployment
        )
        
        # Initialize handlers
        self.handlers = self._initialize_handlers(searcher, openai_client)

    # async def prepare_context(
    #     self, 
    #     chat_params: ChatParams
    # ) -> tuple[list[ChatCompletionMessageParam], list[Any], list[ThoughtStep]]:
    #     """Prepare context based on multiple intents"""
    #     thoughts = []
    async def prepare_context(
        self, 
        chat_params: ChatParams
    ) -> tuple[list[ChatCompletionMessageParam], list[Any], list[ThoughtStep]]:
        """Prepare context based on multiple intents"""
        thoughts = []
        
        try:
            # user_context_str = ""
            # if self.user_context:
            #     user_context_str = (
            #         f"Organization: {self.user_context.get('org_name', 'N/A')}\n"
            #         f"Industry: {', '.join(self.user_context.get('category_list', []))}\n"
            #         f"Description: {self.user_context.get('description', 'N/A')}\n"
            #         f"Location: {self.user_context.get('org_region', 'N/A')+', '+self.user_context.get('org_country_code', 'N/A')}\n"
            #     )

            startup_context = None
            if self.user_context:
                startup_context = {
                    'org_name': self.user_context.get('org_name'),
                    'category_list': self.user_context.get('category_list', []),
                    'description': self.user_context.get('description')
                }

            # Use LLM to determine intents first
            selected_intents = await self.intent_coordinator.determine_intents(
                chat_params.original_user_query,
                startup_context=startup_context
            )
                    # Update chat_params with the detected intent from coordinator
            if selected_intents and selected_intents.get("intents"):
                primary_intent = selected_intents["intents"][0]
                # Update the chat_params intent and confidence
                chat_params.intent = Intent(primary_intent["intent"])
                chat_params.confidence = 1.0  # High confidence for LLM-based detection
            
            thoughts.append(
                ThoughtStep(
                    title="Intent Analysis",
                    description=f"Selected intents: {json.dumps(selected_intents, indent=2)}"
                )
            )

            # Fallback to spaCy if LLM intent detection fails
            if not selected_intents or not selected_intents.get("intents"):
                spacy_intent, confidence = await self.detect_intent(
                    chat_params.original_user_query
                )
                selected_intents = {
                    "intents": [{
                        "intent": spacy_intent.value,
                        "priority": 1,
                        "reasoning": "Fallback to spaCy model"
                    }],
                    "strategy": "sequential"
                }
                
                thoughts.append(
                    ThoughtStep(
                        title="Fallback Intent",
                        description=f"Used spaCy fallback: {spacy_intent.value} ({confidence:.2f})"
                    )
                )

            # Coordinate handlers and get results
            results = await self.intent_coordinator.coordinate_handlers(
                handlers=self.handlers,
                selected_intents=selected_intents,
                query=chat_params.original_user_query,
                params=self._extract_params(chat_params)
            )
            
            thoughts.append(
                ThoughtStep(
                    title="Handler Execution",
                    description=f"Executed {len(results)} handlers"
                )
            )

            # Combine results
            combined_results = await self.intent_coordinator.combine_results(
                results=results,
                selected_intents=selected_intents
            )

            # Format context from combined results
            formatted_context = await self._format_combined_context(
                combined_results,
                selected_intents
            )

            # Build messages for response generation
            # Add information about any failed handlers
            failed_intents = [
                intent_info["intent"] 
                for intent_info in selected_intents["intents"] 
                if intent_info["intent"] not in combined_results.get("data", {})
            ]
            
            context_note = ""
            if failed_intents:
                context_note = "\nNote: Some requested information could not be retrieved. " + \
                             "The response will be based on available data only.\n"
            
            contextual_messages = build_messages(
                model=self.chat_model,
                system_prompt=self._get_combined_prompt(selected_intents),
                new_user_content=(
                    # f"User Startup Profile:\n{user_context_str}\n\n" if user_context_str else ""
                    f"{chat_params.original_user_query}\n\n"
                    f"{context_note}"
                    f"Available Sources:\n{formatted_context}\n\n"
                    "Analyze the provided sources above. For each point in your response, "
                    "cite the specific sources you are referencing. "
                    "If some information is not available, acknowledge this and provide "
                    "the best possible response with the available data."
                ),
                past_messages=chat_params.past_messages,
                max_tokens=self.chat_token_limit - chat_params.response_token_limit,
                fallback_to_default=True,
            )

            return contextual_messages, combined_results, thoughts

        except Exception as e:
            logger.error(f"Error in prepare_context: {str(e)}", exc_info=True)
            thoughts.append(
                ThoughtStep(
                    title="Error",
                    description=f"Failed to prepare context: {str(e)}"
                )
            )
            raise

    def _get_combined_prompt(self, selected_intents: Dict[str, Any]) -> str:
        """Return unified prompt regardless of selected intents"""
        return self.unified_prompt

    async def _format_combined_context(
        self,
        combined_results: Dict[str, Any],
        selected_intents: Dict[str, Any]
    ) -> str:
        """Format combined results for context"""
        context_parts = []
        
        for intent_info in selected_intents["intents"]:
            intent_name = intent_info["intent"]
            if intent_name in combined_results["data"]:
                result_data = combined_results["data"][intent_name]
                handler = self.handlers.get(Intent(intent_name))
                if handler:
                    formatted = await handler.format_for_context({
                        "status": "success",
                        "data": result_data["result"]
                    })
                    context_parts.append(formatted)

        return "\n\n".join(context_parts)

    def _extract_params(self, chat_params: ChatParams) -> Dict[str, Any]:
        """Extract parameters from chat params for handlers"""
        return {
            "query": chat_params.original_user_query,
            "top": chat_params.top,
            "temperature": chat_params.temperature,
            "enable_text_search": chat_params.enable_text_search,
            "enable_vector_search": chat_params.enable_vector_search
        }
    
    def _should_use_backup_model(self, results: Dict[str, Any], structured_data: List[Any], articles: List[Any]) -> bool:
        """Determine if backup model should be used based on results and data"""
        if not settings.ENABLE_BACKUP_MODEL:
            return False
            
        # Check if all handlers failed
        all_handlers_failed = all(
            data.get("status") == "error" 
            for data in results.get("data", {}).values()
        ) if results.get("data") else True
        
        # Check if we have no data
        no_data = not structured_data and not articles
        
        # Check if data is insufficient
        insufficient_data = False
        if structured_data:
            # Check if structured data has meaningful content
            for data in structured_data:
                if isinstance(data, dict):
                    # Handle dictionary format
                    data_dict = data.get("data", {})
                    records = data_dict.get("records", [])
                    if not records:
                        # Check for alternative data formats
                        has_valid_data = any(
                            k != "error" and v and not (isinstance(v, dict) and v.get("value") == "")
                            for k, v in data_dict.items()
                        )
                        if not has_valid_data:
                            insufficient_data = True
                            break
                elif hasattr(data, "data"):
                    # Handle StructuredDataPoint object
                    data_dict = data.data
                    records = data_dict.get("records", [])
                    if not records:
                        # Check for alternative data formats
                        has_valid_data = any(
                            k != "error" and v and not (isinstance(v, dict) and v.get("value") == "")
                            for k, v in data_dict.items()
                        )
                        if not has_valid_data:
                            insufficient_data = True
                            break
                else:
                    insufficient_data = True
                    break
        
        # Check if articles are insufficient
        if articles and not insufficient_data:
            # If we have articles but they're too old or irrelevant
            current_time = datetime.utcnow()
            recent_articles = [
                article for article in articles
                if article.published_at and 
                (current_time - article.published_at).days <= 365  # Within last year
            ]
            if not recent_articles:
                insufficient_data = True
        
        # Use backup if any condition is true
        return all_handlers_failed or no_data or insufficient_data

    async def answer(
        self,
        chat_params: ChatParams,
        contextual_messages: list[ChatCompletionMessageParam],
        results: Dict[str, Any],
        earlier_thoughts: list[ThoughtStep],
    ) -> RetrievalResponse:
        """Generate answer using provided context or fallback to backup model"""
        try:
            is_greeting = False
            is_greeting = "GREETING_QUERY" in results.get("data", {})

            if is_greeting:
                # Get greeting handler
                greeting_handler = self.handlers.get(Intent.GREETING)
                if greeting_handler:
                    greeting_result = await greeting_handler.execute_query({})
                    if greeting_result["status"] == "success":
                        detected_intent = Intent.GREETING
                        return RetrievalResponse(
                            message=Message(
                                content=await greeting_handler.format_for_context(greeting_result),
                                role=AIChatRoles.ASSISTANT
                            ),
                            context=RAGContext(
                                thoughts=earlier_thoughts + [
                                    ThoughtStep(
                                        title="Greeting",
                                        description="Provided standard greeting response"
                                    )
                                ]
                            ),
                            intent=detected_intent,
                            confidence=1.0
                        )
            # Process structured and unstructured data from results
            structured_data = []
            articles = []
            
            for intent_name, data in results.get("data", {}).items():
                intent = Intent(intent_name)
                if self.get_data_source(intent) == DataSource.STRUCTURED:
                    if data.get("result"):
                        # Convert SQLAlchemy models to dictionaries if needed
                        result_data = data["result"]
                        
                        # Wrap the data in a dictionary structure
                        if isinstance(result_data, list):
                            result_dict = {
                                "records": [
                                    {k: v for k, v in (item.__dict__ if hasattr(item, '__dict__') else item).items() 
                                    if not k.startswith('_')}
                                    for item in result_data
                                ]
                            }
                        elif hasattr(result_data, '__dict__'):
                            result_dict = {
                                "record": {k: v for k, v in (result_data.__dict__).items() 
                                        if not k.startswith('_')}
                            }
                        elif isinstance(result_data, dict):
                            # Already a dict - ensure scalar values are properly wrapped
                            result_dict = {}
                            for k, v in result_data.items():
                                if not isinstance(v, (dict, list)) and k not in ('id', 'name'):
                                    # Wrap scalar values in value dict
                                    result_dict[k] = {"value": v}
                                elif isinstance(v, dict):
                                    result_dict[k] = v
                                elif isinstance(v, list):
                                    result_dict[k] = {"records": v}
                                else:
                                    result_dict[k] = v
                        else:
                            # Other data type
                            result_dict = {"data": result_data}

                        # Only wrap problematic fields that cause validation errors
                        def wrap_problematic_fields(data):
                            if isinstance(data, dict):
                                wrapped = {}
                                for k, v in data.items():
                                    if k in ['query_type', 'total_found'] or (not isinstance(v, (dict, list)) and k not in ('id', 'name')):  
                                        # Wrap scalar values and known problematic fields
                                        wrapped[k] = {"value": v}
                                    else:
                                        wrapped[k] = wrap_problematic_fields(v) if isinstance(v, (dict, list)) else v
                                return wrapped
                            elif isinstance(data, list):
                                return [wrap_problematic_fields(item) for item in data]
                            return data

                        # Apply selective wrapping
                        wrapped_dict = wrap_problematic_fields(result_dict)

                        try:
                            structured_data.append(StructuredDataPoint(
                                table=intent_name.lower().replace("_query", ""),
                                data=wrapped_dict
                            ))
                        except Exception as e:
                            logger.error(f"Failed to create StructuredDataPoint for {intent_name}: {str(e)}")
                            logger.debug(f"Original data: {result_dict}")
                            # Fallback to simpler structure if validation fails
                            structured_data.append({
                                "table": intent_name.lower().replace("_query", ""),
                                "data": result_dict
                            })
                else:  # DataSource.UNSTRUCTURED
                    if data.get("result"):
                        # Ensure articles are proper ArticleSource instances
                        for article in data["result"]:
                            if isinstance(article, dict):
                                articles.append(ArticleSource(**article))
                            elif isinstance(article, ArticleSource):
                                articles.append(article)

            # Check if we should use backup model
            if self._should_use_backup_model(results, structured_data, articles):
                try:
                    # Initialize backup handler
                    backup_handler = BackupModelHandler()
                    
                    earlier_thoughts.append(
                        ThoughtStep(
                            title="Backup Research",
                            description="No relevant documents found. Using DeepSeek-R1 for research-based analysis."
                        )
                    )
                    
                    backup_response = await backup_handler.get_backup_response(
                        chat_params.original_user_query,
                        self.user_context
                    )
                    
                    if backup_response["status"] == "success":
                        return RetrievalResponse(
                            message=Message(
                                content=backup_response["data"]["content"],
                                role=AIChatRoles.ASSISTANT
                            ),
                            context=RAGContext(
                                thoughts=earlier_thoughts + [
                                    ThoughtStep(
                                        title="Analysis Source",
                                        description="Analysis provided by Azure DeepSeek-R1 Research Model"
                                    )
                                ]
                            ),
                            intent=chat_params.intent,
                            confidence=chat_params.confidence
                        )
                    
                except Exception as e:
                    logger.error(f"Error using backup model: {str(e)}")
                    # If backup model fails, return standard no-data message
                    return RetrievalResponse(
                        message=Message(
                            content="I encountered some issues retrieving the requested information. " +
                                    "However, I can try a different approach if you'd like to rephrase your query.",
                            role=AIChatRoles.ASSISTANT
                        ),
                        context=RAGContext(thoughts=earlier_thoughts),
                        intent=None,
                        confidence=None
                    )

            # If we have data or backup model is disabled, proceed with normal RAG response
            chat_completion_response = await self.openai_client.chat.completions.create(
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=contextual_messages,
                temperature=chat_params.temperature,
                max_tokens=chat_params.response_token_limit,
                n=1,
                stream=False,
                seed=chat_params.seed,
            )

            return RetrievalResponse(
                message=Message(
                    content=str(chat_completion_response.choices[0].message.content),
                    role=AIChatRoles.ASSISTANT
                ),
                context=RAGContext(
                    articles=articles if articles else None,
                    structured_data=structured_data if structured_data else None,
                    thoughts=earlier_thoughts
                ),
                intent=chat_params.intent,
                confidence=chat_params.confidence
            )

        except Exception as e:
            logger.error(f"Error in answer: {str(e)}")
            raise

    async def answer_stream(
        self,
        chat_params: ChatParams,
        contextual_messages: list[ChatCompletionMessageParam],
        results: Dict[str, Any],
        earlier_thoughts: list[ThoughtStep],
    ) -> AsyncGenerator[RetrievalResponseDelta, None]:
        """Stream the answer generation"""
        try:
            # Check if this is a greeting query
            is_greeting = "GREETING_QUERY" in results.get("data", {})

            if is_greeting:
                # Get greeting handler
                greeting_handler = self.handlers.get(Intent.GREETING)
                if greeting_handler:
                    greeting_result = await greeting_handler.execute_query({})
                    if greeting_result["status"] == "success":
                        # Yield as RetrievalResponseDelta for streaming
                        yield RetrievalResponseDelta(
                            delta=Message(
                                content=await greeting_handler.format_for_context(greeting_result),
                                role=AIChatRoles.ASSISTANT
                            ),
                            context=RAGContext(
                                thoughts=earlier_thoughts + [
                                    ThoughtStep(
                                        title="Greeting",
                                        description="Provided standard greeting response"
                                    )
                                ]
                            )
                        )
                        return

            # Check if all handlers failed or returned no data
            all_handlers_failed = all(
                data.get("status") == "error" 
                for data in results.get("data", {}).values()
            ) if results.get("data") else True

            if all_handlers_failed and settings.ENABLE_BACKUP_MODEL:
                try:
                    backup_handler = BackupModelHandler()
                    earlier_thoughts.append(
                        ThoughtStep(
                            title="Backup Research",
                            description="Primary handlers failed. Using DeepSeek-R1 for research-based analysis."
                        )
                    )
                    
                    # Stream directly from backup handler
                    async for chunk in backup_handler.get_backup_response_stream(
                        chat_params.original_user_query,
                        self.user_context
                    ):
                        yield RetrievalResponseDelta(
                            delta=Message(
                                content=chunk["data"]["content"],
                                role=AIChatRoles.ASSISTANT
                            )
                        )
                    return
                except Exception as e:
                    logger.error(f"Backup model error: {str(e)}")
                    yield RetrievalResponseDelta(
                        delta=Message(
                            content="I encountered an error processing your request. Please try rephrasing your query.",
                            role=AIChatRoles.ASSISTANT
                        )
                    )
                    return

            # Process structured and unstructured data from results
            structured_data = []
            articles = []
            
            for intent_name, data in results.get("data", {}).items():
                intent = Intent(intent_name)
                logger.debug(f"Processing intent {intent_name} with data: {data}")
                
                if data.get("status") == "error":
                    logger.warning(f"Handler {intent_name} failed: {data.get('error')}")
                    continue

                if self.get_data_source(intent) == DataSource.STRUCTURED:
                    if data.get("result"):
                        # Convert SQLAlchemy models to dictionaries if needed
                        result_data = data["result"]
                        
                        # Wrap the data in a dictionary structure
                        if isinstance(result_data, list):
                            result_dict = {
                                "records": [
                                    {k: v for k, v in (item.__dict__ if hasattr(item, '__dict__') else item).items() 
                                    if not k.startswith('_')}
                                    for item in result_data
                                ]
                            }
                        elif hasattr(result_data, '__dict__'):
                            result_dict = {
                                "record": {k: v for k, v in (result_data.__dict__).items() 
                                        if not k.startswith('_')}
                            }
                        elif isinstance(result_data, dict):
                            # Already a dict - ensure scalar values are properly wrapped
                            result_dict = {}
                            for k, v in result_data.items():
                                if not isinstance(v, (dict, list)) and k not in ('id', 'name'):
                                    # Wrap scalar values in value dict
                                    result_dict[k] = {"value": v}
                                elif isinstance(v, dict):
                                    result_dict[k] = v
                                elif isinstance(v, list):
                                    result_dict[k] = {"records": v}
                                else:
                                    result_dict[k] = v
                        else:
                            # Other data type
                            result_dict = {"data": result_data}

                        # Only wrap problematic fields that cause validation errors
                        def wrap_problematic_fields(data):
                            if isinstance(data, dict):
                                wrapped = {}
                                for k, v in data.items():
                                    if k in ['query_type', 'total_found'] or (not isinstance(v, (dict, list)) and k not in ('id', 'name')):  
                                        # Wrap scalar values and known problematic fields
                                        wrapped[k] = {"value": v}
                                    else:
                                        wrapped[k] = wrap_problematic_fields(v) if isinstance(v, (dict, list)) else v
                                return wrapped
                            elif isinstance(data, list):
                                return [wrap_problematic_fields(item) for item in data]
                            return data

                        # Apply selective wrapping
                        wrapped_dict = wrap_problematic_fields(result_dict)

                        try:
                            structured_data.append(StructuredDataPoint(
                                table=intent_name.lower().replace("_query", ""),
                                data=wrapped_dict
                            ))
                        except Exception as e:
                            logger.error(f"Failed to create StructuredDataPoint for {intent_name}: {str(e)}")
                            logger.debug(f"Original data: {result_dict}")
                            # Fallback to simpler structure if validation fails
                            structured_data.append({
                                "table": intent_name.lower().replace("_query", ""),
                                "data": result_dict
                            })
                else:  # DataSource.UNSTRUCTURED
                    if data.get("result"):
                        # Convert article data to proper ArticleSource objects
                        for article in data["result"]:
                            # logger.debug(f"Article: {article}")
                            if isinstance(article, str):
                                continue  # Skip string values
                            if isinstance(article, dict):
                                try:
                                    articles.append(ArticleSource(
                                        url=article.get('url', ''),
                                        title=article.get('title', ''),
                                        content=article.get('content', ''),
                                        published_at=article.get('published_at', None),
                                        source=article.get('source', '')
                                    ))
                                except Exception as e:
                                    logger.warning(f"Skipping invalid article data: {e}")
                            elif isinstance(article, ArticleSource):
                                articles.append(article)


            # First yield context
            yield RetrievalResponseDelta(
                context=RAGContext(
                    structured_data=structured_data if structured_data else None,
                    articles=articles if articles else None,
                    thoughts=earlier_thoughts
                )
            )

            print(settings.ENABLE_BACKUP_MODEL)

            # Check if we should use backup model
            if self._should_use_backup_model(results, structured_data, articles):
                try:
                    backup_handler = BackupModelHandler()
                    earlier_thoughts.append(
                        ThoughtStep(
                            title="Backup Research",
                            description="Using DeepSeek-R1 for research-based analysis."
                        )
                    )
                    
                    # Stream directly from backup handler
                    async for chunk in backup_handler.get_backup_response_stream(
                        chat_params.original_user_query,
                        self.user_context
                    ):
                        yield RetrievalResponseDelta(
                            delta=Message(
                                content=chunk["data"]["content"],
                                role=AIChatRoles.ASSISTANT
                            )
                        )
                    return
                except Exception as e:
                    logger.error(f"Backup model error: {str(e)}")
                    yield RetrievalResponseDelta(
                        delta=Message(
                            content="Please try rephrasing your query.",
                            role=AIChatRoles.ASSISTANT
                        )
                    )
                    return

            # Get streaming chat completion
            chat_completion_stream = await self.openai_client.chat.completions.create(
                model=self.chat_deployment if self.chat_deployment else self.chat_model,
                messages=contextual_messages,
                temperature=chat_params.temperature,
                max_tokens=chat_params.response_token_limit,
                n=1,
                stream=True,
                seed=chat_params.seed,
            )

            # Then stream the response chunks
            async for chunk in chat_completion_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield RetrievalResponseDelta(
                        delta=Message(
                            content=str(chunk.choices[0].delta.content),
                            role=AIChatRoles.ASSISTANT
                        )
                    )

        except Exception as e:
            logger.error(f"Error in answer_stream: {str(e)}")
            yield RetrievalResponseDelta(
                delta=Message(
                    content=f"Error generating response: {str(e)}",
                    role=AIChatRoles.ASSISTANT
                )
            )


    def _initialize_handlers(
        self,
        searcher: MarketResearchSearcher,
        openai_client: Union[AsyncOpenAI, AsyncAzureOpenAI]
    ) -> Dict[str, Any]:
        """Initialize all handlers with proper configurations"""
        return {
            Intent.COMPANY_PROFILE: CompanyProfileHandler(
                searcher.db_session,
                openai_client=openai_client,
            ),
            Intent.TECH_NEWS: TechNewsHandler(
                db=searcher.db_session,
                openai_embed_client=openai_client,
                embed_model=searcher.embed_model,
                embed_deployment=searcher.embed_deployment,
                embed_dimensions=searcher.embed_dimensions
            ),
            Intent.FUNDING_NEWS: FundingNewsHandler(
                db=searcher.db_session,
                openai_embed_client=openai_client,
                embed_model=searcher.embed_model,
                embed_deployment=searcher.embed_deployment,
                embed_dimensions=searcher.embed_dimensions
            ),
            Intent.MARKET_TRENDS: MarketTrendsHandler(
                db=searcher.db_session,
                openai_embed_client=openai_client,
                embed_model=searcher.embed_model,
                embed_deployment=searcher.embed_deployment,
                embed_dimensions=searcher.embed_dimensions
            ),
            Intent.FUNDING_ROUND: FundingRoundHandler(
                searcher.db_session
            ),
            Intent.ACQUISITION: AcquisitionHandler(
                searcher.db_session
            ),
            Intent.IPO: IpoHandler(
                searcher.db_session
            ),
            Intent.FUNDS: FundsHandler(
                searcher.db_session
            ),
            Intent.JOBS: JobsHandler(
                searcher.db_session
            ),
            Intent.PEOPLE_PROFILE: PeopleProfileHandler(
                searcher.db_session
            ),
            Intent.EDUCATION: EducationHandler(
                searcher.db_session
            ),
            Intent.INVESTOR: InvestorHandler(
                searcher.db_session
            ),
            Intent.INVESTMENT_DETAILS: InvestmentDetailsHandler(
                searcher.db_session
            ),
            Intent.ORGANIZATION_RELATIONSHIP: OrganizationRelationshipHandler(
                searcher.db_session
            ),
            Intent.INVESTMENT_PARTNER: InvestmentPartnerHandler(
                searcher.db_session
            ),
            Intent.COMPETITOR_LOOKUP: CompetitorHandler(
                searcher.db_session,
                openai_client=openai_client,
            ),
            Intent.LEAD_GENERATION: LeadGenerationHandler(
                searcher.db_session
            ),
            Intent.MARKET_ANALYSIS: MarketAnalysisHandler(
                db=searcher.db_session
            ),
            Intent.EVENT: EventHandler(
                db=searcher.db_session,
                openai_embed_client=openai_client,
                embed_model=searcher.embed_model,
                embed_deployment=searcher.embed_deployment,
                embed_dimensions=searcher.embed_dimensions
            ),
            Intent.MY_STARTUP: MyStartupHandler(
                searcher.db_session,
                openai_client=openai_client
            ),
            Intent.RECOMMEND_INVESTORS: RecommendInvestorsHandler(
                searcher.db_session,
                openai_client=openai_client
            ),
            Intent.INVESTOR_NETWORK: InvestorNetworkHandler(
                searcher.db_session,
                openai_client=openai_client
            ),
            Intent.GREETING: GreetingHandler(
                client=openai_client,
                model=self.chat_model
            )
        }