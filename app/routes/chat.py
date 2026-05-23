from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette.responses import StreamingResponse, JSONResponse
from typing import Optional, Union
from datetime import timedelta
from services.rag_service import RAGService
from services.chat_service import ChatService
from services.token_service import TokenService
from services.conversation_service import ConversationService
from models.api_models import (
    ChatRequest,
    RetrievalResponse,
    ErrorResponse,
    Message,
    AIChatRoles,
    ChatRequestContext,
    ChatRequestOverrides,
    RetrievalMode
)
from models.conversation import Chat, ChatMessage 
from models.conversation_schema import (
    ConversationCreate,
    ConversationRead,
    ConversationList,
    ConversationDetail,
    MessageFeedback
)
from core.openai import get_openai_client
from dependencies import get_redis_client, get_current_user, get_db
from core.config import get_settings
from rag.postgres_searcher import MarketResearchSearcher
import logging
import json
from models.auth_models import User
from redis import Redis

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

settings = get_settings()

class CommonDeps:
    def __init__(self):
        self.openai_embed_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        self.openai_embed_model = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        self.openai_chat_deployment = settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        self.openai_chat_model = settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        self.embedding_column = "embedding_ada002"
        self.embed_dimensions = 1536

common_deps = CommonDeps()
router = APIRouter()

@router.post("/conversations", response_model=ConversationRead)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    # Initialize services
    conversation_service = ConversationService(db, redis_client)
    chat_service = ChatService(redis_client, db)
    
    
    # Create conversation first
    conversation = await conversation_service.create_conversation(current_user.uuid, data)
    
    # Initialize chat session
    await chat_service.create_session(conversation.id, current_user.uuid)
    
    return conversation

@router.post("/conversations/{conversation_id}/chat")
async def chat_handler(
    conversation_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client),
    redis_client = Depends(get_redis_client)
) -> Union[RetrievalResponse, ErrorResponse]:
    try:
        # Initialize services
        conversation_service = ConversationService(db, redis_client)
        chat_service = ChatService(redis_client, db)
        
        # Get or create chat session
        session = await chat_service.get_or_create_session(conversation_id, current_user.uuid)
        if not session:
            raise HTTPException(status_code=404, detail="Could not create chat session")
        
        if not chat_request.messages:
            logger.error("No messages provided in request")
            raise HTTPException(
                status_code=422,
                detail="No messages provided in the request"
            )

        # Create user context
        user_context = {
            "uuid": current_user.uuid,
            "org_name": current_user.org_name,
            "org_country_code": current_user.org_country_code,
            "org_region": current_user.org_region,
            "category_list": current_user.category_list,
            "category_groups_list": current_user.category_groups_list,
            "description": current_user.description,
            "investment_round": current_user.investment_round,
            "is_verified": current_user.is_verified,
            "investors_simple_list": current_user.investors_simple_list
        }

        # Initialize RAG services
        searcher = MarketResearchSearcher(
            db_session=db,
            openai_embed_client=openai_client,
            embed_deployment=common_deps.openai_embed_deployment,
            embed_model=common_deps.openai_embed_model,
            embed_dimensions=common_deps.embed_dimensions,
            embedding_column=common_deps.embedding_column
        )
        
        rag_service = RAGService(
            searcher=searcher,
            openai_chat_client=openai_client,
            chat_model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            user_context=user_context
        )
        
        token_service = TokenService(
            redis_client,
            settings.DAILY_TOKEN_LIMIT,
            settings.TOTAL_TOKEN_LIMIT,
            current_user
        )

        # Check token limits
        if not await token_service.check_limits(current_user.uuid):
            raise HTTPException(status_code=429, detail="Token limit exceeded")

        # Ensure context exists
        if not hasattr(chat_request, 'context'):
            chat_request.context = ChatRequestContext(
                overrides=ChatRequestOverrides(
                    top=3,
                    temperature=0.3,
                    retrieval_mode=RetrievalMode.HYBRID,
                    use_advanced_flow=True
                )
            )

        # Add user context to chat request
        chat_request.context.user_context = user_context

        last_message = chat_request.messages[-1]
        content = last_message.get("content") if isinstance(last_message, dict) else getattr(last_message, "content", None)
        if not content:
            raise HTTPException(
                status_code=422,
                detail="Message content cannot be empty"
            )

        user_message = Message(
            role=AIChatRoles.USER,
            content=content,
            user_context=user_context
        )

        context_messages = await chat_service.get_context_messages(
            conversation_id,
            Message(**chat_request.messages[-1])
        )
        
        # Convert Message objects to dictionaries before updating chat_request
        chat_request.messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "user_context": msg.user_context.dict() if msg.user_context else None
            } 
            for msg in context_messages
        ]


        # Process chat request
        response, token_count = await rag_service.process_chat(chat_request)
        
        # Save messages and update conversation
        await chat_service.add_message(
            conversation_id,
            Message(
                role=AIChatRoles.USER,
                content=user_message.content,
                user_context=user_context
            )
        )
        
        await chat_service.add_message(
            conversation_id,
            Message(
                role=AIChatRoles.ASSISTANT,
                content=response.message.content
            )
        )

        await conversation_service.update_message_count(conversation_id)
        await token_service.update_usage(current_user.uuid, token_count)

        return response

    except Exception as e:
        logger.error(f"Chat handler error: {str(e)}", exc_info=True)
        db.rollback()
        return ErrorResponse(error=str(e))

@router.post("/conversations/{conversation_id}/chat/stream")
async def chat_stream_handler(
    conversation_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client),
    redis_client = Depends(get_redis_client)
):
    try:
        # Initialize services
        conversation_service = ConversationService(db, redis_client)
        chat_service = ChatService(redis_client, db)
        
        # Verify conversation exists and belongs to user
        conversation = await conversation_service.get_conversation(current_user.uuid, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Create user context
        user_context = {
            "uuid": current_user.uuid,
            "org_name": current_user.org_name,
            "org_country_code": current_user.org_country_code,
            "org_region": current_user.org_region,
            "category_list": current_user.category_list,
            "category_groups_list": current_user.category_groups_list,
            "description": current_user.description,
            "investment_round": current_user.investment_round,
            "is_verified": current_user.is_verified,
            "investors_simple_list": current_user.investors_simple_list
        }

        # Initialize services
        searcher = MarketResearchSearcher(
            db_session=db,
            openai_embed_client=openai_client,
            embed_deployment=common_deps.openai_embed_deployment,
            embed_model=common_deps.openai_embed_model,
            embed_dimensions=common_deps.embed_dimensions,
            embedding_column=common_deps.embedding_column
        )
        
        rag_service = RAGService(
            searcher=searcher,
            openai_chat_client=openai_client,
            chat_model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            user_context=user_context
        )

        # Check token limits
        token_service = TokenService(
            redis_client,
            settings.DAILY_TOKEN_LIMIT,
            settings.TOTAL_TOKEN_LIMIT,
            current_user
        )
        if not await token_service.check_limits(current_user.uuid):
            raise HTTPException(status_code=429, detail="Token limit exceeded")

        # Ensure context exists
        if not hasattr(chat_request, 'context'):
            chat_request.context = ChatRequestContext(
                overrides=ChatRequestOverrides(
                    top=3,
                    temperature=0.3,
                    retrieval_mode=RetrievalMode.HYBRID,
                    use_advanced_flow=True
                )
            )

        # Add user context
        chat_request.context.user_context = user_context

        # Get context messages

        # Get context messages
        context_messages = await chat_service.get_context_messages(
            conversation_id,
            Message(**chat_request.messages[-1])
        )
        # Convert Message objects to dictionaries
        chat_request.messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "user_context": msg.user_context.dict() if msg.user_context else None
            } 
            for msg in context_messages
        ]


        complete_response = {"content": "", "context": None}

        async def generate():
            try:
                yield "data: {\"type\": \"start\"}\n\n"

                async for chunk in rag_service.process_chat_stream(chat_request):
                    if chunk:
                        # Handle content updates
                        if chunk.delta and chunk.delta.content:
                            complete_response["content"] += chunk.delta.content
                            yield f"data: {json.dumps({'type': 'content', 'content': chunk.delta.content})}\n\n"
                        # Handle context updates
                        elif chunk.context:
                            complete_response["context"] = chunk.context.dict()
                            yield f"data: {json.dumps({'type': 'context', 'context': chunk.context.dict()})}\n\n"


                await chat_service.add_message(
                    conversation_id,
                    Message(
                        role=AIChatRoles.USER,
                        content=chat_request.messages[-1]["content"],
                        user_context=user_context
                    )
                )
                
                await chat_service.add_message(
                    conversation_id,
                    Message(
                        role=AIChatRoles.ASSISTANT,
                        content=complete_response["content"],
                        context=complete_response["context"]
                    )
                )

                # Update conversation metadata
                await conversation_service.update_message_count(conversation_id)


                # Send end message
                yield "data: {\"type\": \"end\"}\n\n"
            except Exception as e:
                logger.error(f"Error in generate: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Chat stream handler error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
@router.get("/conversations", response_model=ConversationList)
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    conversation_service = ConversationService(db, redis_client)
    return await conversation_service.list_conversations(current_user.uuid, skip, limit)

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    conversation_service = ConversationService(db, redis_client)
    return await conversation_service.get_conversation(current_user.uuid, conversation_id)

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    conversation_service = ConversationService(db, redis_client)
    chat_service = ChatService(redis_client, db)
    
    # Verify conversation exists and belongs to user
    conversation = await conversation_service.get_conversation(current_user.uuid, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = await chat_service.get_messages_for_display(conversation_id, limit)
    return {"messages": messages}

@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    token_service = TokenService(
        redis_client,
        settings.DAILY_TOKEN_LIMIT,
        settings.TOTAL_TOKEN_LIMIT
    )
    return await token_service.get_usage_stats(current_user.uuid)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    conversation_service = ConversationService(db, redis_client)
    await conversation_service.delete_conversation(current_user.uuid, conversation_id)
    return {"message": "Conversation deleted successfully"}

@router.post("/conversations/{conversation_id}/messages/{message_id}/feedback")
async def give_message_feedback(
    conversation_id: str,
    message_id: str,
    feedback: MessageFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
):
    try:
        conversation_service = ConversationService(db, redis_client)
        chat_service = ChatService(redis_client, db)
        
        # Verify conversation exists and belongs to user
        conversation = await conversation_service.get_conversation(current_user.uuid, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Get message and verify it belongs to the conversation
        message = db.scalar(
            select(ChatMessage)
            .join(Chat)
            .where(
                ChatMessage.id == message_id,
                Chat.conversation_id == conversation_id
            )
        )
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
            
        # Update feedback
        message.feedback = feedback.feedback
        db.commit()
        
        return {"message": "Feedback saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error saving feedback")



RATE_LIMIT_DURATION = 60  # seconds
RATE_LIMIT_REQUESTS = 20  # requests per duration

async def check_rate_limit(
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis_client)
):
    key = f"rate_limit:{user.uuid}"
    current = await redis.get(key)
    
    if current and int(current) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
        
    async with redis.pipeline() as pipe:
        await pipe.incr(key)
        await pipe.expire(key, RATE_LIMIT_DURATION)
        await pipe.execute()