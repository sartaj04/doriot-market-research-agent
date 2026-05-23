from enum import Enum
from typing import Any, Optional, List, Dict, Union
from datetime import datetime
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class AIChatRoles(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class DataSource(str, Enum):
    STRUCTURED = "structured"    # Crunchbase data
    UNSTRUCTURED = "unstructured"  # TechCrunch and news articles

class ErrorResponse(BaseModel):
    error: str

class Message(BaseModel):
    content: str
    role: AIChatRoles = AIChatRoles.USER
    user_context: Optional[Dict[str, Any]] = None

class ChatSession(BaseModel):
    id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    meta_data: Optional[Dict[str, Any]] = None

class Intent(str, Enum):
    # Structured Data Intents
    COMPANY_PROFILE = "COMPANY_PROFILE_QUERY"
    FUNDING_ROUND = "FUNDING_ROUND_QUERY"
    ACQUISITION = "ACQUISITION_QUERY"
    IPO = "IPO_QUERY"
    FUNDS= "FUNDS_QUERY"
    JOBS= "JOBS_QUERY"
    PEOPLE_PROFILE = "PEOPLE_PROFILE_QUERY"
    EDUCATION = "EDUCATION_QUERY"
    INVESTOR = "INVESTOR_QUERY"
    INVESTMENT_DETAILS = "INVESTMENT_DETAILS_QUERY"
    ORGANIZATION_RELATIONSHIP = "ORGANIZATION_RELATIONSHIP_QUERY"
    INVESTMENT_PARTNER = "INVESTMENT_PARTNER_QUERY"
    COMPETITOR_LOOKUP = "COMPETITOR_LOOKUP"
    LEAD_GENERATION = "LEAD_GENERATION_QUERY"
    MARKET_ANALYSIS = "MARKET_ANALYSIS_QUERY"
    EVENT = "EVENT_QUERY"
    MY_STARTUP = "MY_STARTUP_QUERY"
    RECOMMEND_INVESTORS = "RECOMMEND_INVESTORS"
    INVESTOR_NETWORK = "INVESTOR_NETWORK"
    GREETING = "GREETING_QUERY"
    # ... add other intents

    # Unstructured Data Intents
    TECH_NEWS = "TECH_NEWS_QUERY"
    FUNDING_NEWS = "FUNDING_NEWS_QUERY"
    MARKET_TRENDS = "MARKET_TRENDS_QUERY"



class RetrievalMode(str, Enum):
    TEXT = "text"
    VECTORS = "vectors"
    HYBRID = "hybrid"

class ChatRequestOverrides(BaseModel):
    top: int = 3
    temperature: float = 0.3
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    use_advanced_flow: bool = True
    prompt_template: Optional[str] = None
    seed: Optional[int] = None

class ChatRequestContext(BaseModel):
    overrides: ChatRequestOverrides
    user_context: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    messages: list[ChatCompletionMessageParam]
    context: ChatRequestContext
    sessionState: Optional[Any] = None

class ThoughtStep(BaseModel):
    title: str
    description: Any
    props: dict = {}

class ArticleSource(BaseModel):
    title: str
    url: str
    published_at: str
    source: str  # TechCrunch Startup/Venture or Funding News
    content: str

class StructuredDataPoint(BaseModel):
    table: str  # e.g., "companies", "funding_rounds"
    data: Dict[str, Union[Dict[str, Any], List[Dict[str, Any]]]]  # The actual data
    meta_data: dict = {}  # Any additional meta_data
    def get(self, key: str, default: Any = None) -> Any:
        """Allow dict-like get access to model fields"""
        return getattr(self, key, default)

class RAGContext(BaseModel):
    structured_data: Optional[List[StructuredDataPoint]] = None
    articles: Optional[List[ArticleSource]] = None
    thoughts: list[ThoughtStep]
    followup_questions: Optional[list[str]] = None

class RetrievalResponse(BaseModel):
    message: Message
    context: RAGContext
    intent: Optional[Intent] = None
    confidence: Optional[float] = None
    sessionState: Optional[Any] = None

class RetrievalResponseDelta(BaseModel):
    delta: Optional[Message] = None
    context: Optional[RAGContext] = None
    sessionState: Optional[Any] = None

class ChatParams(ChatRequestOverrides):
    prompt_template: str
    response_token_limit: int = 1024
    enable_text_search: bool
    enable_vector_search: bool
    original_user_query: str
    past_messages: list[ChatCompletionMessageParam]
    intent: Optional[Intent] = None
    confidence: Optional[float] = None
    user_context: Optional[Dict[str, Any]] = None 