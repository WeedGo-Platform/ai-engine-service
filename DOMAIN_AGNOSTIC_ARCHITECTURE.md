# Domain-Agnostic AI Engine Architecture

## Overview
Transform the AI engine from cannabis-specific to a plugin-based, multi-domain platform that can serve any industry or role.

## Core Architecture Principles

### 1. Separation of Concerns
```
┌─────────────────────────────────────────────────┐
│                 AI Engine Core                   │
│          (Domain-Agnostic, Pure AI)              │
├─────────────────────────────────────────────────┤
│              Domain Plugin Layer                 │
│   (Budtender, Doctor, Lawyer, Teacher, etc.)    │
├─────────────────────────────────────────────────┤
│             Data Abstraction Layer               │
│    (Adapters for different data sources)         │
├─────────────────────────────────────────────────┤
│                Model Orchestra                   │
│        (Multi-model, Multi-lingual)              │
└─────────────────────────────────────────────────┘
```

### 2. Plugin Architecture
Each domain is a self-contained plugin with:
- Prompts library
- Knowledge base
- Data schema mappings
- Business logic
- Validation rules
- Response formatters

### 3. Data Abstraction
- Schema-agnostic queries
- Adapter pattern for different databases
- Semantic layer for natural language to data mapping

## Directory Structure

```
ai-engine-service/
├── core/                          # Domain-agnostic core
│   ├── engine.py                  # Main AI engine
│   ├── interfaces/                # Abstract interfaces
│   │   ├── domain_plugin.py       # Plugin interface
│   │   ├── data_adapter.py        # Data adapter interface
│   │   └── knowledge_base.py      # Knowledge interface
│   ├── orchestration/             # Model orchestration
│   └── utils/                     # Core utilities
│
├── domains/                       # Domain-specific plugins
│   ├── budtender/                # Cannabis industry
│   │   ├── prompts/              # Budtender prompts
│   │   │   ├── conversation.yaml
│   │   │   ├── product_search.yaml
│   │   │   └── recommendations.yaml
│   │   ├── knowledge/            # Cannabis knowledge
│   │   │   ├── strains.json
│   │   │   ├── effects.json
│   │   │   └── medical.json
│   │   ├── data/                 # Data mappings
│   │   │   ├── schema.yaml       # DB schema mapping
│   │   │   └── adapters.py       # Data adapters
│   │   ├── config.yaml           # Domain configuration
│   │   └── plugin.py             # Plugin implementation
│   │
│   ├── healthcare/               # Medical domain
│   │   ├── prompts/
│   │   │   ├── diagnosis.yaml
│   │   │   ├── treatment.yaml
│   │   │   └── consultation.yaml
│   │   ├── knowledge/
│   │   │   ├── conditions.json
│   │   │   ├── medications.json
│   │   │   └── protocols.json
│   │   ├── data/
│   │   │   ├── schema.yaml
│   │   │   └── adapters.py
│   │   └── plugin.py
│   │
│   ├── legal/                    # Legal domain
│   │   ├── prompts/
│   │   ├── knowledge/
│   │   ├── data/
│   │   └── plugin.py
│   │
│   └── education/                # Education domain
│       ├── prompts/
│       ├── knowledge/
│       ├── data/
│       └── plugin.py
│
├── data/                         # Data abstraction layer
│   ├── adapters/                # Database adapters
│   │   ├── postgresql.py
│   │   ├── mongodb.py
│   │   ├── elasticsearch.py
│   │   └── api_adapter.py
│   ├── schemas/                 # Schema definitions
│   └── query_builder.py         # Abstract query builder
│
└── config/                      # Configuration
    ├── domains.yaml             # Active domains config
    └── settings.yaml            # System settings
```

## Key Components

### 1. Domain Plugin Interface
```python
class DomainPlugin(ABC):
    @abstractmethod
    def get_prompts(self, task: str) -> str
    
    @abstractmethod
    def get_knowledge(self, query: str) -> Dict
    
    @abstractmethod
    def validate_response(self, response: Dict) -> bool
    
    @abstractmethod
    def format_response(self, raw: str) -> Dict
    
    @abstractmethod
    def get_tools(self) -> List[Tool]
```

### 2. Data Adapter Interface
```python
class DataAdapter(ABC):
    @abstractmethod
    def search(self, query: Dict) -> List[Dict]
    
    @abstractmethod
    def get_by_id(self, id: str) -> Dict
    
    @abstractmethod
    def map_schema(self, domain_schema: Dict) -> Dict
```

### 3. Dynamic Domain Loading
```python
class DomainManager:
    def load_domain(self, domain_name: str) -> DomainPlugin
    def switch_domain(self, domain_name: str) -> None
    def get_active_domain(self) -> DomainPlugin
```

## Implementation Benefits

1. **Scalability**: Add new domains without modifying core
2. **Maintainability**: Domain logic isolated in plugins
3. **Reusability**: Core AI capabilities shared across domains
4. **Flexibility**: Easy to switch data sources
5. **Testability**: Each domain can be tested independently

## Migration Path

1. Extract budtender-specific code to plugin
2. Create abstract interfaces
3. Implement data abstraction layer
4. Build domain manager
5. Add new domains incrementally

## Use Cases

### Budtender Mode
```python
engine = AIEngine()
engine.load_domain("budtender")
response = engine.process("I need something for pain relief")
# Returns cannabis product recommendations
```

### Healthcare Mode
```python
engine.load_domain("healthcare")
response = engine.process("I have persistent headaches")
# Returns medical consultation and treatment options
```

### Legal Mode
```python
engine.load_domain("legal")
response = engine.process("What are my rights during a traffic stop?")
# Returns legal advice and procedures
```

## Technology Stack

- **Core**: Python with async/await
- **Prompts**: YAML/JSON with Jinja2 templating
- **Knowledge**: Vector DB (Chroma/Pinecone) per domain
- **Data**: Abstract query language with adapters
- **Config**: YAML with environment overrides
- **Testing**: Pytest with domain fixtures

## Next Steps

1. Create core interfaces
2. Extract budtender to plugin
3. Implement data abstraction
4. Build domain manager
5. Create template for new domains
6. Add healthcare as proof of concept