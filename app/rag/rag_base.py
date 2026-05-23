from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
import json
import pathlib
import spacy
import logging
from openai.types.chat import ChatCompletionMessageParam
from typing import List, Tuple, Any, Optional, Dict

from models.api_models import (
    ChatParams,
    ChatRequestOverrides,
    RetrievalResponse,
    RetrievalResponseDelta,
    ThoughtStep,
    Intent,
    DataSource
)

logger = logging.getLogger(__name__)

class RAGChatBase(ABC):
    """Base class for RAG-based chat implementations"""
    
    current_dir = pathlib.Path(__file__).parent
    parent_dir = current_dir.parent
    
    # Load base prompts
    unified_prompt = open(current_dir / "prompts/query.txt").read()
    


    def __init__(self, intent_model_path: str = None):
        """Initialize with spaCy intent model"""
        # Use parent_dir to resolve the model path
        default_model_path = str(self.parent_dir / "classifier_model/intent_model")
        model_path = intent_model_path or default_model_path
        
        logger.debug(f"Loading intent model from {model_path}")
        try:
            self.nlp = spacy.load(model_path)
        except Exception as e:
            logger.error(f"Failed to load spaCy model from {model_path}: {str(e)}")
            raise RuntimeError(f"Could not load spaCy model: {str(e)}")
        
    def get_intent_prompt(self, intent: Intent) -> str:
        """Get intent-specific prompt template - now always returns unified prompt"""
        return self.unified_prompt

    async def detect_intent(self, query: str) -> Tuple[Intent, float]:
        """Detect intent from query using spaCy model"""
        doc = self.nlp(query)
        scores = doc.cats
        top_intent = max(scores.items(), key=lambda x: x[1])
        return Intent(top_intent[0]), top_intent[1]

    def get_data_source(self, intent: Intent) -> DataSource:
        """Determine if intent needs structured or unstructured data"""
        if intent in {
            Intent.COMPANY_PROFILE,
            Intent.FUNDING_ROUND,
            Intent.ACQUISITION,
            Intent.IPO,
            Intent.INVESTOR,
            Intent.INVESTMENT_DETAILS,
            Intent.ORGANIZATION_RELATIONSHIP,
            Intent.INVESTMENT_PARTNER,
            Intent.COMPETITOR_LOOKUP,
            Intent.LEAD_GENERATION,
            Intent.MARKET_ANALYSIS,
            Intent.EVENT,
            Intent.FUNDS,
            Intent.JOBS,
            Intent.PEOPLE_PROFILE,
            Intent.EDUCATION
        }:
            return DataSource.STRUCTURED
        return DataSource.UNSTRUCTURED

    def get_prompt_template(self, intent: Intent) -> str:
        """Return unified prompt regardless of intent"""
        return self.unified_prompt

    async def get_params(
        self, 
        messages: list[ChatCompletionMessageParam], 
        overrides: ChatRequestOverrides,
        user_context: Optional[Dict[str, Any]] = None  # Add user_context parameter
    ) -> ChatParams:
        """Get chat parameters with intent detection"""
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            original_user_query = last_message.content
        elif isinstance(last_message, dict):
            original_user_query = last_message.get("content")
        else:
            raise ValueError("Invalid message format - cannot extract content")

        if not isinstance(original_user_query, str):
            raise ValueError("The most recent message content must be a string.")
        
            
        # Detect intent and get confidence
        intent, confidence = await self.detect_intent(original_user_query)
        
        # Get intent-specific prompt
        prompt_template = self.get_intent_prompt(intent)
        
        enable_text_search = overrides.retrieval_mode in ["text", "hybrid", None]
        enable_vector_search = overrides.retrieval_mode in ["vectors", "hybrid", None]

        past_messages = messages[:-1]

        return ChatParams(
            top=overrides.top,
            temperature=overrides.temperature,
            seed=overrides.seed,
            retrieval_mode=overrides.retrieval_mode,
            use_advanced_flow=overrides.use_advanced_flow,
            response_token_limit=1024,
            prompt_template=prompt_template,
            enable_text_search=enable_text_search,
            enable_vector_search=enable_vector_search,
            original_user_query=original_user_query,
            past_messages=past_messages,
            intent=intent,
            confidence=confidence,
            user_context=user_context  # Add user_context to return value
        )

    @abstractmethod
    async def prepare_context(
        self, chat_params: ChatParams
    ) -> tuple[list[ChatCompletionMessageParam], list[Any], list[ThoughtStep]]:
        """Prepare context based on intent and data source"""
        raise NotImplementedError

    @abstractmethod
    async def answer(
        self,
        chat_params: ChatParams,
        contextual_messages: list[ChatCompletionMessageParam],
        results: list[Any],
        earlier_thoughts: list[ThoughtStep],
    ) -> RetrievalResponse:
        """Generate answer based on context and intent"""
        raise NotImplementedError

    @abstractmethod
    async def answer_stream(
        self,
        chat_params: ChatParams,
        contextual_messages: list[ChatCompletionMessageParam],
        results: list[Any],
        earlier_thoughts: list[ThoughtStep],
    ) -> AsyncGenerator[RetrievalResponseDelta, None]:
        """Stream answer based on context and intent"""
        raise NotImplementedError