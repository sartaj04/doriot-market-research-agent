from typing import Tuple, List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from openai.types.chat import ChatCompletionMessageParam
from models.api_models import ChatRequest, RetrievalResponse, ThoughtStep, RetrievalResponseDelta
from rag.postgres_searcher import MarketResearchSearcher
from rag.rag_advanced import AdvancedRAGChat


class RAGService:
    def __init__(
        self,
        searcher: MarketResearchSearcher,
        openai_chat_client: Any,
        chat_model: str,
        chat_deployment: Optional[str],
        user_context: Optional[Dict[str, Any]] = None,
        intent_model_path: str = None
    ):
        
        current_dir = Path(__file__).parent
        parent_dir = current_dir.parent
        default_model_path = str(parent_dir / "classifier_model/intent_model")
        model_path = intent_model_path or default_model_path
        self.searcher = searcher
        self.openai_chat_client = openai_chat_client
        self.chat_model = chat_model
        self.chat_deployment = chat_deployment
        self.rag_chat = AdvancedRAGChat(
            searcher=searcher,
            openai_client=openai_chat_client,
            chat_model=chat_model,
            chat_deployment=chat_deployment,
            user_context=user_context,
            intent_model_path=model_path
        )

    async def process_chat(
        self,
        chat_request: ChatRequest
    ) -> Tuple[RetrievalResponse, int]:
        """Process chat request and return response with token count"""
        
        # Get chat parameters - await the coroutine
        chat_params = await self.rag_chat.get_params(
            chat_request.messages,
            chat_request.context.overrides,
            user_context=chat_request.context.user_context
        )

        # Prepare context
        contextual_messages, results, thoughts = await self.rag_chat.prepare_context(
            chat_params
        )

        # Generate response
        response = await self.rag_chat.answer(
            chat_params=chat_params,
            contextual_messages=contextual_messages,
            results=results,
            earlier_thoughts=thoughts
        )

        # Estimate token usage
        token_count = self._estimate_token_count(response.message.content)

        return response, token_count

    async def process_chat_stream(
        self,
        chat_request: ChatRequest
    ) -> AsyncGenerator[RetrievalResponseDelta, None]:
        """Process chat request and return streaming response"""
        
        # Get chat parameters - await the coroutine here too
        chat_params = await self.rag_chat.get_params(
            chat_request.messages,
            chat_request.context.overrides,
            user_context=chat_request.context.user_context
        )

        # Prepare context
        contextual_messages, results, thoughts = await self.rag_chat.prepare_context(
            chat_params
        )

        # Stream the response
        async for chunk in self.rag_chat.answer_stream(
            chat_params=chat_params,
            contextual_messages=contextual_messages,
            results=results,
            earlier_thoughts=thoughts
        ):
            yield chunk

    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count from text"""
        return int(len(text.split()) * 1.3)