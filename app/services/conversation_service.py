# services/conversation_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from redis.asyncio import Redis
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException

from models.conversation import Conversation as ConversationDB
from models.conversation import Chat as ChatDB
from models.conversation_schema import (
    ConversationCreate,
    ConversationRead,
    ConversationList,
    ConversationDetail
)

class ConversationService:
    def __init__(self, db: Session, redis: Redis):
        self.db = db
        self.redis = redis

    async def create_conversation(
        self,
        user_id: str,
        data: ConversationCreate
    ) -> ConversationRead:
        # Create in database
        db_conversation = ConversationDB(
            user_id=user_id,
            title=data.title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            meta_data=data.meta_data or {}
        )
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        
        # Store in Redis for quick access
        await self.redis.set(
            f"conversation:{db_conversation.id}",
            ConversationRead(
                id=db_conversation.id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                updated_at=db_conversation.updated_at,
                message_count=0,
                meta_data=db_conversation.meta_data
            ).model_dump_json()
        )
        
        # Add to user's conversation set
        await self.redis.sadd(
            f"user_conversations:{user_id}",
            db_conversation.id
        )
        
        return ConversationRead.model_validate(db_conversation)

    async def list_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> ConversationList:
        # Get total count
        total = self.db.scalar(
            select(func.count()).select_from(ConversationDB).where(
                ConversationDB.user_id == user_id
            )
        )
        
        # Get conversations from database
        db_conversations = self.db.scalars(
            select(ConversationDB)
            .where(ConversationDB.user_id == user_id)
            .order_by(ConversationDB.updated_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        
        # Convert to Pydantic models
        conversations = [
            ConversationRead.model_validate(conv)
            for conv in db_conversations
        ]
        
        return ConversationList(
            conversations=conversations,
            total=total
        )

    async def get_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> ConversationDetail:
        """Get a single conversation with its messages"""
        try:
            # Check cache first
            cached = await self.redis.get(f"conversation:{conversation_id}")
            if cached:
                conversation = ConversationRead.model_validate_json(cached)
            else:
                # Get from database
                db_conversation = self.db.scalar(
                    select(ConversationDB)
                    .where(
                        ConversationDB.id == conversation_id,
                        ConversationDB.user_id == user_id
                    )
                )
                if not db_conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                conversation = ConversationRead.model_validate(db_conversation)
                
                # Cache in Redis
                await self.redis.set(
                    f"conversation:{conversation_id}",
                    conversation.model_dump_json()
                )
            
            # Get only chats that have messages
            chats = self.db.scalars(
                select(ChatDB)
                .where(
                    ChatDB.conversation_id == conversation_id,
                    ChatDB.messages.any()  # Only get chats with messages
                )
                .order_by(ChatDB.created_at)
            ).all()
            
            return ConversationDetail(
                **conversation.model_dump(),
                chats=[{
                    "id": chat.id,
                    "created_at": chat.created_at,
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "created_at": msg.created_at,
                            "feedback": msg.feedback
                        }
                        for msg in sorted(chat.messages, key=lambda x: x.created_at)
                    ]
                } for chat in chats if chat.messages]  # Additional check for messages
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail="Conversation not found")

    async def delete_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> bool:
        # Delete from database
        result = self.db.execute(
            select(ConversationDB)
            .where(
                ConversationDB.id == conversation_id,
                ConversationDB.user_id == user_id
            )
        )
        db_conversation = result.scalar_one_or_none()
        
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        self.db.delete(db_conversation)
        self.db.commit()
        
        # Delete from Redis
        await self.redis.delete(f"conversation:{conversation_id}")
        await self.redis.srem(f"user_conversations:{user_id}", conversation_id)
        
        return True

    async def update_conversation(
        self,
        user_id: str,
        conversation_id: str,
        data: ConversationCreate
    ) -> ConversationRead:
        # Update in database
        db_conversation = self.db.scalar(
            select(ConversationDB)
            .where(
                ConversationDB.id == conversation_id,
                ConversationDB.user_id == user_id
            )
        )
        
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if data.title is not None:
            db_conversation.title = data.title
        if data.meta_data is not None:
            db_conversation.meta_data = data.meta_data
            
        db_conversation.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_conversation)
        
        # Update Redis
        conversation = ConversationRead.model_validate(db_conversation)
        await self.redis.set(
            f"conversation:{conversation_id}",
            conversation.model_dump_json()
        )
        
        return conversation

    async def update_message_count(
        self,
        conversation_id: str,
        increment: int = 1
    ) -> None:
        # Update count in Redis
        cached = await self.redis.get(f"conversation:{conversation_id}")
        if cached:
            conversation = ConversationRead.model_validate_json(cached)
            conversation.message_count += increment
            conversation.updated_at = datetime.now()
            await self.redis.set(
                f"conversation:{conversation_id}",
                conversation.model_dump_json()
            )
                
        # Update timestamp in database using the correct update syntax
        from sqlalchemy import update
        
        stmt = (
            update(ConversationDB)
            .where(ConversationDB.id == conversation_id)
            .values(updated_at=datetime.now())
        )
        self.db.execute(stmt)
        self.db.commit()

    async def get_active_conversations(
        self,
        user_id: str,
        max_age_hours: int = 24
    ) -> List[str]:
        """Get recently active conversation IDs"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        active = self.db.scalars(
            select(ConversationDB.id)
            .where(
                ConversationDB.user_id == user_id,
                ConversationDB.updated_at >= cutoff
            )
        ).all()
        return active