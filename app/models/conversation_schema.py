from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class ConversationRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    meta_data: Optional[Dict[str, Any]] = None
    message_count: int = 0 

    class Config:
        from_attributes = True

class ConversationList(BaseModel):
    conversations: List[ConversationRead]
    total: int
    
class MessageRead(BaseModel):
    role: str
    content: str
    created_at: datetime
    feedback: Optional[bool] = None

class ChatRead(BaseModel):
    id: str
    created_at: datetime
    messages: List[MessageRead]

class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    meta_data: Optional[Dict[str, Any]] = None
    chats: List[ChatRead]

    class Config:
        from_attributes = True
    
# Update ChatService to use new models
class ChatCreate(BaseModel):
    conversation_id: str
    meta_data: Optional[Dict[str, Any]] = None

class ChatUpdate(BaseModel):
    meta_data: Optional[Dict[str, Any]] = None

class ChatRead(BaseModel):
    id: str
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    meta_data: Optional[Dict[str, Any]] = None
    messages: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class MessageFeedback(BaseModel):
    feedback: bool



class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    feedback: Optional[bool] = None
    references: Optional[List[Dict[str, Any]]] = None

class MessagesResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    has_more: bool

    class Config:
        from_attributes = True

class Message(BaseModel):
    role: str
    content: str
    references: Optional[List[Dict[str, Any]]] = None