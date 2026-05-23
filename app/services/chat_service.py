from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from redis.asyncio import Redis
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.api_models import Message, ChatSession
from fastapi import HTTPException
from models.conversation import Chat, ChatMessage, Conversation
import logging
from datetime import timedelta
logger = logging.getLogger(__name__)

CACHE_TTL = 3600 

class ChatService:
    MAX_HISTORY_MESSAGES = 10 
    DEFAULT_EXPIRE = timedelta(hours=24)
    def __init__(self, redis_client: Redis, db: Session):
        self.redis = redis_client
        self.db = db

        self.prefix = "chat_session"

    async def create_session(self, conversation_id: str, user_id: str) -> str:
        """Create a new chat session linked to conversation"""
        try:
            # Use conversation_id as session_id for consistency
            session_key = f"{self.prefix}:{conversation_id}"
            
            # Create Redis session with TTL
            session_data = ChatSession(
                id=conversation_id,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store in Redis with expiration
            await self.redis.setex(
                session_key,
                CACHE_TTL,
                session_data.model_dump_json()
            )
            
            # Create initial chat
            chat = Chat(
                conversation_id=conversation_id,
                user_id=user_id
            )
            self.db.add(chat)
            self.db.commit()
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            self.db.rollback()
            raise
    async def get_or_create_session(
        self,
        conversation_id: str,
        user_id: str,
        expire_in: timedelta = None
    ) -> Optional[ChatSession]:
        expire = expire_in or self.DEFAULT_EXPIRE
        try:
            # First verify conversation ownership
            conversation = self.db.scalar(
                select(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
            
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found or not authorized"
                )
                
            # Then get or create session
            session = await self.get_session(conversation_id)
            if session:
                return session
                    
            return await self.create_session(conversation_id, user_id)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Session error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error managing chat session"
            )
            
    async def _validate_session_owner(self, session: ChatSession, user_id: str) -> bool:
        try:
            # First check conversation ownership
            conversation = self.db.scalar(
                select(Conversation)
                .where(
                    Conversation.id == session.id,
                    Conversation.user_id == user_id
                )
            )
            
            if not conversation:
                return False
                
            # Then check chat association
            chat = self.db.scalar(
                select(Chat)
                .where(Chat.conversation_id == session.id)
            )
            
            return chat is not None
            
        except Exception as e:
            logger.error(f"Error validating session owner: {str(e)}")

# In the get_session method, modify the Redis set operation:
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        try:
            # Try Redis first
            session_key = f"{self.prefix}:{session_id}"  # Add prefix to key
            data = await self.redis.get(session_key)
            if data:
                return ChatSession.model_validate_json(data)
            
            # Fallback to DB
            conversation = self.db.scalar(
                select(Conversation)
                .where(Conversation.id == session_id)
            )
            
            if not conversation:
                return None
                
            # Get messages from DB
            chat = self.db.scalar(
                select(Chat)
                .where(Chat.conversation_id == session_id)
            )
            
            if not chat:
                return None
                
            messages = self.db.scalars(
                select(ChatMessage)
                .where(ChatMessage.chat_id == chat.id)
                .order_by(ChatMessage.created_at)
            ).all()
            
            # Create session from DB data
            session = ChatSession(
                id=session_id,
                messages=[
                    Message(
                        role=msg.role,
                        content=msg.content,
                        user_context=msg.meta_data
                    )
                    for msg in messages
                ],
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            
            # Restore Redis cache with proper expiration
            await self.redis.setex(
                name=session_key,
                time=CACHE_TTL,  # Use seconds instead of timedelta
                value=session.model_dump_json()
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return None

    # Suggested improvement
    async def add_message(self, session_id: str, message: Message) -> bool:
        try:
            # Start Redis pipeline (not a transaction yet)
            pipe = self.redis.pipeline()
            
            # Get current session
            session = await self.get_session(session_id)
            if not session:
                return False
                
            # Update session in Redis
            session.messages.append(message)
            session.updated_at = datetime.now()
            await pipe.set(session_id, session.model_dump_json())
            
            # Add to DB
            chat = self.db.scalar(
                select(Chat).where(Chat.conversation_id == session_id)
            )
            if not chat:
                return False
            
            # Store metadata - include structured and unstructured data if available
            meta_data = message.user_context or {}
            if hasattr(message, 'context') and message.context:
                if message.context.structured_data:
                    meta_data['structured_data'] = message.context.structured_data
                if message.context.articles:
                    meta_data['articles'] = message.context.articles
                
            db_message = ChatMessage(
                chat_id=chat.id,
                role=message.role,
                content=message.content,
                meta_data=meta_data
            )
            self.db.add(db_message)
            
            # Execute Redis pipeline
            await pipe.execute()
            
            # Commit DB changes
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            self.db.rollback()
            return False
    
            

    async def get_messages_for_display(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Get messages for frontend display"""
        try:
            # Query all messages for this conversation, properly ordered
            messages = self.db.scalars(
                select(ChatMessage)
                .join(Chat)
                .where(Chat.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            ).all()
            
            # Convert to display format with references preserved
            return [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "feedback": message.feedback,
                    "references": message.meta_data.get("references") if message.meta_data else None
                }
                for message in reversed(messages)  # Reverse to get chronological order
            ]
        except Exception as e:
            logger.error(f"Error getting messages for display: {str(e)}")
            return []

    async def save_chat_history(self, user_id: str, message: str) -> bool:
        """Save chat history to Redis and DB"""
        try:
            # Save to Redis for quick access
            chat_key = f"chat:{user_id}"
            await self.redis.rpush(chat_key, message)
            
            # Save to DB for persistence
            chat = self.db.scalar(
                select(Chat)
                .join(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Chat.created_at.desc())
            )
            
            if chat:
                db_message = ChatMessage(
                    chat_id=chat.id,
                    role="user",  # or determine from message
                    content=message
                )
                self.db.add(db_message)
                self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving chat history: {str(e)}")
            self.db.rollback()
            return False
        
    async def update_message_feedback(self, message_id: str, feedback: bool) -> bool:
        """Update message feedback"""
        try:
            message = self.db.scalar(
                select(ChatMessage)
                .where(ChatMessage.id == message_id)
            )
            
            if not message:
                return False
                
            message.feedback = feedback
            self.db.commit()
            
            # Update Redis cache if exists
            session_key = f"{self.prefix}:{message.chat.conversation_id}"
            session_data = await self.redis.get(session_key)
            if session_data:
                session = ChatSession.model_validate_json(session_data)
                for msg in session.messages:
                    if msg.id == message_id:
                        msg.feedback = feedback
                        break
                await self.redis.setex(
                    session_key,
                    CACHE_TTL,
                    session.model_dump_json()
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating feedback: {str(e)}")
            self.db.rollback()
            return False
        
    async def get_context_messages(
        self,
        conversation_id: str,
        new_message: Message
    ) -> List[Message]:
        """Get limited message history for RAG context"""
        messages = self.db.scalars(
            select(ChatMessage)
            .join(Chat)
            .where(Chat.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(self.MAX_HISTORY_MESSAGES - 1)  # -1 to account for new message
        ).all()
        
        history = [
            Message(
                role=msg.role,
                content=msg.content
            ) for msg in reversed(messages)  # Return in chronological order
        ]
        return history + [new_message]
        
    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions from Redis and sync with DB"""
        try:
            async for key in self.redis.scan_iter(f"{self.prefix}:*"):
                if not await self.redis.exists(key):
                    session_id = key.split(":")[-1]
                    # Ensure DB is synced
                    await self.sync_session_to_db(session_id)
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")