from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column(JSON)
    
    # Relationship with existing Chat model
    chats = relationship("Chat", back_populates="conversation")

# Update existing Chat model to include conversation relationship
class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column(JSON)
    
    messages = relationship("ChatMessage", back_populates="chat")
    conversation = relationship("Conversation", back_populates="chats")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    chat_id = Column(String, ForeignKey("chats.id"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON)
    feedback = Column(Boolean, nullable=True)  # True for positive, False for negative
    
    chat = relationship("Chat", back_populates="messages")
