"""
Data models for the unified chat service.

These Pydantic models provide validation, serialization, and type safety
for all chat-related operations.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class WebSocketMessageType(str, Enum):
    """WebSocket message types for client-server communication"""
    CONNECTION = "connection"
    MESSAGE = "message"
    TYPING = "typing"
    ERROR = "error"
    SESSION_UPDATE = "session_update"
    SESSION_UPDATED = "session_updated"
    HEARTBEAT = "heartbeat"
    TOKEN_UPDATE = "token_update"


class ChatRequest(BaseModel):
    """Request model for chat message processing"""
    message: str = Field(..., min_length=1, max_length=4000, description="User's message text")
    session_id: Optional[str] = Field(None, description="Session identifier for context")
    user_id: Optional[str] = Field(None, description="User identifier")
    store_id: Optional[str] = Field(None, description="Store context")
    language: str = Field("en", description="Message language code")
    agent_id: str = Field("dispensary", description="Agent type to use")
    personality_id: str = Field("marcel", description="Personality variant")
    use_tools: bool = Field(True, description="Enable tool usage")
    use_context: bool = Field(True, description="Include conversation context")
    max_tokens: int = Field(500, ge=50, le=2000, description="Maximum response tokens")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "I want sativa pre-rolls",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "store_id": "store456",
                "language": "en",
                "agent_id": "dispensary",
                "personality_id": "marcel"
            }
        }
    )


class ProductModel(BaseModel):
    """Model for product recommendations"""
    id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    type: str = Field(..., description="Product type (flower, pre-roll, etc.)")
    category: Optional[str] = Field(None, description="Product category")
    price: float = Field(..., ge=0, description="Product price")
    thc: Optional[float] = Field(None, description="THC percentage")
    cbd: Optional[float] = Field(None, description="CBD percentage")
    description: Optional[str] = Field(None, description="Product description")
    image_url: Optional[str] = Field(None, description="Product image URL")
    in_stock: bool = Field(True, description="Stock availability")
    quantity_available: int = Field(0, ge=0, description="Available quantity")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "prod123",
                "name": "Blue Dream Sativa",
                "sku": "BD-SAT-001",
                "type": "flower",
                "category": "sativa",
                "price": 12.99,
                "thc": 22.5,
                "cbd": 0.5,
                "in_stock": True,
                "quantity_available": 15
            }
        }
    )


class QuickActionModel(BaseModel):
    """Model for quick action buttons"""
    label: str = Field(..., description="Action button label")
    action: str = Field(..., description="Action identifier")
    data: Optional[Dict[str, Any]] = Field(None, description="Action payload")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "View more sativa",
                "action": "search",
                "data": {"category": "sativa"}
            }
        }
    )


class ResponseMetadata(BaseModel):
    """Metadata about the response generation"""
    model: str = Field(..., description="Model used for generation")
    tokens_used: int = Field(..., ge=0, description="Total tokens consumed")
    prompt_tokens: int = Field(..., ge=0, description="Prompt tokens")
    completion_tokens: int = Field(..., ge=0, description="Completion tokens")
    response_time: float = Field(..., ge=0, description="Response time in seconds")
    tool_calls: List[str] = Field(default_factory=list, description="Tools executed")
    intent: Optional[str] = Field(None, description="Detected user intent")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Intent confidence score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "claude-3-5-sonnet-20241022",
                "tokens_used": 450,
                "prompt_tokens": 350,
                "completion_tokens": 100,
                "response_time": 2.35,
                "tool_calls": ["SmartProductSearch"],
                "intent": "product_search",
                "confidence": 0.95
            }
        }
    )


class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    text: str = Field(..., description="Assistant's response text")
    products: List[ProductModel] = Field(default_factory=list, description="Product recommendations")
    quick_actions: List[QuickActionModel] = Field(default_factory=list, description="Quick action buttons")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
    session_id: str = Field(..., description="Session identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "I found some great sativa pre-rolls for you!",
                "products": [],
                "quick_actions": [],
                "metadata": {
                    "model": "claude-3-5-sonnet-20241022",
                    "tokens_used": 450,
                    "prompt_tokens": 350,
                    "completion_tokens": 100,
                    "response_time": 2.35,
                    "tool_calls": ["SmartProductSearch"],
                    "intent": "product_search",
                    "confidence": 0.95
                },
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class SessionModel(BaseModel):
    """Model for chat session data"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    agent_id: str = Field("dispensary", description="Active agent type")
    personality_id: str = Field("marcel", description="Active personality")
    store_id: Optional[str] = Field(None, description="Store context")
    language: str = Field("en", description="Session language")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    message_count: int = Field(0, ge=0, description="Total messages in session")
    is_active: bool = Field(True, description="Session active status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "agent_id": "dispensary",
                "personality_id": "marcel",
                "store_id": "store456",
                "language": "en",
                "created_at": "2025-10-02T16:00:00Z",
                "updated_at": "2025-10-02T16:30:00Z",
                "message_count": 5,
                "is_active": True,
                "metadata": {}
            }
        }
    )


class MessageModel(BaseModel):
    """Model for individual conversation messages"""
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Parent session ID")
    user_id: Optional[str] = Field(None, description="User who sent message")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message text content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    products: List[ProductModel] = Field(default_factory=list, description="Associated products")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg123",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "role": "user",
                "content": "I want sativa pre-rolls",
                "timestamp": "2025-10-02T16:30:00Z",
                "products": [],
                "metadata": {}
            }
        }
    )


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session"""
    agent_id: str = Field("dispensary", description="Initial agent type")
    personality_id: str = Field("marcel", description="Initial personality")
    user_id: Optional[str] = Field(None, description="User identifier")
    store_id: Optional[str] = Field(None, description="Store context")
    language: str = Field("en", description="Session language")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SessionUpdateRequest(BaseModel):
    """Request model for updating session settings"""
    agent_id: Optional[str] = Field(None, description="New agent type")
    personality_id: Optional[str] = Field(None, description="New personality")
    store_id: Optional[str] = Field(None, description="New store context")
    language: Optional[str] = Field(None, description="New language")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata updates")


class StreamChunk(BaseModel):
    """Model for streaming response chunks"""
    type: Literal["text", "product", "action", "metadata", "done"] = Field(..., description="Chunk type")
    content: Any = Field(..., description="Chunk content")
    session_id: str = Field(..., description="Session identifier")
    chunk_id: int = Field(..., ge=0, description="Chunk sequence number")


class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code identifier")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    session_id: Optional[str] = Field(None, description="Session identifier if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
