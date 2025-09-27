"""
Core Interfaces for AGI System
Following SOLID principles - these are the contracts for all components
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncIterator, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid

# ============================================================================
# Base Data Structures
# ============================================================================

class MessageRole(Enum):
    """Message roles in conversations"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    """Basic message structure"""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ConversationContext:
    """Conversation context containing messages and metadata"""
    messages: List[Message]
    session_id: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# ============================================================================
# Model Interfaces
# ============================================================================

class IModel(ABC):
    """Interface for language models"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Generate text stream from prompt"""
        pass

    @abstractmethod
    def get_context_length(self) -> int:
        """Get maximum context length"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass

class IModelRegistry(ABC):
    """Interface for model registry"""

    @abstractmethod
    async def register_model(self, model_id: str, model: IModel) -> None:
        """Register a model"""
        pass

    @abstractmethod
    async def get_model(self, model_id: str) -> Optional[IModel]:
        """Get a model by ID"""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List all available models"""
        pass

    @abstractmethod
    async def unregister_model(self, model_id: str) -> None:
        """Unregister a model"""
        pass

# ============================================================================
# Memory Interfaces
# ============================================================================

class IMemory(ABC):
    """Interface for memory systems"""

    @abstractmethod
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value"""
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass

class IWorkingMemory(IMemory):
    """Interface for working memory (short-term)"""

    @abstractmethod
    async def add_message(self, session_id: str, message: Message) -> None:
        """Add message to working memory"""
        pass

    @abstractmethod
    async def get_messages(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages"""
        pass

class IEpisodicMemory(IMemory):
    """Interface for episodic memory (medium-term)"""

    @abstractmethod
    async def store_episode(self, episode_id: str, episode: Dict[str, Any]) -> None:
        """Store an episode"""
        pass

    @abstractmethod
    async def retrieve_episodes(
        self,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve episodes by query"""
        pass

class ISemanticMemory(IMemory):
    """Interface for semantic memory (long-term knowledge)"""

    @abstractmethod
    async def store_knowledge(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store knowledge and return ID"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar knowledge"""
        pass

# ============================================================================
# Tool Interfaces
# ============================================================================

@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None

@dataclass
class ToolDefinition:
    """Tool definition"""
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: str

@dataclass
class ToolResult:
    """Tool execution result"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ITool(ABC):
    """Interface for tools"""

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get tool definition"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass

    @abstractmethod
    async def validate_input(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate input parameters"""
        pass

class IToolRegistry(ABC):
    """Interface for tool registry"""

    @abstractmethod
    async def register_tool(self, tool: ITool) -> None:
        """Register a tool"""
        pass

    @abstractmethod
    async def get_tool(self, name: str) -> Optional[ITool]:
        """Get a tool by name"""
        pass

    @abstractmethod
    async def list_tools(self) -> List[ToolDefinition]:
        """List all available tools"""
        pass

# ============================================================================
# Agent Interfaces
# ============================================================================

class AgentState(Enum):
    """Agent states"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentTask:
    """Task for an agent to execute"""
    id: str
    description: str
    context: ConversationContext
    tools: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None

@dataclass
class AgentResult:
    """Result from agent execution"""
    task_id: str
    success: bool
    result: Any
    steps_taken: List[Dict[str, Any]]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IAgent(ABC):
    """Interface for agents"""

    @abstractmethod
    async def plan(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Plan how to execute the task"""
        pass

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute the task"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        pass

    @abstractmethod
    def get_state(self) -> AgentState:
        """Get current agent state"""
        pass

class IAgentOrchestrator(ABC):
    """Interface for agent orchestration"""

    @abstractmethod
    async def route_task(self, task: AgentTask) -> str:
        """Route task to appropriate agent"""
        pass

    @abstractmethod
    async def coordinate_agents(
        self,
        agents: List[IAgent],
        task: AgentTask
    ) -> AgentResult:
        """Coordinate multiple agents"""
        pass

# ============================================================================
# Knowledge Interfaces
# ============================================================================

@dataclass
class Document:
    """Document for knowledge base"""
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    embeddings: Optional[List[float]] = None
    source: Optional[str] = None
    timestamp: Optional[datetime] = None

class IKnowledgeStore(ABC):
    """Interface for knowledge storage"""

    @abstractmethod
    async def add_document(self, document: Document) -> str:
        """Add document to knowledge store"""
        pass

    @abstractmethod
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search documents"""
        pass

    @abstractmethod
    async def update_document(self, document_id: str, document: Document) -> None:
        """Update a document"""
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """Delete a document"""
        pass

class IEmbedding(ABC):
    """Interface for embedding generation"""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass

# ============================================================================
# Orchestrator Interfaces
# ============================================================================

class IOrchestrator(ABC):
    """Main orchestrator interface"""

    @abstractmethod
    async def process_request(
        self,
        request: str,
        context: ConversationContext,
        stream: bool = False
    ) -> Any:
        """Process a request"""
        pass

    @abstractmethod
    async def select_model(self, task_type: str) -> str:
        """Select appropriate model for task"""
        pass

    @abstractmethod
    async def select_agent(self, task: AgentTask) -> IAgent:
        """Select appropriate agent for task"""
        pass

    @abstractmethod
    async def handle_failure(
        self,
        error: Exception,
        context: ConversationContext
    ) -> Any:
        """Handle failure with fallback"""
        pass

# ============================================================================
# Pipeline Interfaces
# ============================================================================

class IPipeline(ABC):
    """Interface for processing pipelines"""

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input through pipeline"""
        pass

    @abstractmethod
    def add_stage(self, stage: 'IPipelineStage') -> None:
        """Add a stage to pipeline"""
        pass

    @abstractmethod
    def get_stages(self) -> List['IPipelineStage']:
        """Get all pipeline stages"""
        pass

class IPipelineStage(ABC):
    """Interface for pipeline stages"""

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get stage name"""
        pass

# ============================================================================
# Monitoring Interfaces
# ============================================================================

class IMetrics(ABC):
    """Interface for metrics collection"""

    @abstractmethod
    async def record_latency(self, operation: str, duration_ms: float) -> None:
        """Record operation latency"""
        pass

    @abstractmethod
    async def record_error(self, operation: str, error: str) -> None:
        """Record an error"""
        pass

    @abstractmethod
    async def record_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """Record token usage"""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        pass