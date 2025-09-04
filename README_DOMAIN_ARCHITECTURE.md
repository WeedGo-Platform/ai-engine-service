# Domain-Agnostic AI Engine

## 🎯 Overview

The AI Engine has been redesigned as a **domain-agnostic, plugin-based platform** that can serve any industry or use case. Instead of being tied to cannabis/budtender functionality, the system now uses **domain plugins** that can be easily swapped or extended.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│             AI Engine Core                       │
│         (Domain-Agnostic, Pure AI)              │
├─────────────────────────────────────────────────┤
│            Domain Plugin Layer                   │
│  (Budtender, Healthcare, Legal, Education, etc.) │
├─────────────────────────────────────────────────┤
│           Data Abstraction Layer                 │
│      (PostgreSQL, MongoDB, APIs, etc.)          │
├─────────────────────────────────────────────────┤
│             Model Orchestra                      │
│        (Multi-model, Multi-lingual)             │
└─────────────────────────────────────────────────┘
```

## 🔌 Domain Plugins

Each domain is a self-contained plugin with:
- **Prompts Library**: Domain-specific prompts for different tasks
- **Knowledge Base**: Domain expertise and information
- **Data Schema**: Mappings to different data sources
- **Validation Rules**: Domain-specific input/output validation
- **Tools**: Specialized functions the AI can use
- **Response Formatting**: Domain-appropriate output structure

### Current Domains

1. **Budtender** (`domains/budtender/`)
   - Cannabis product recommendations
   - Strain information
   - Effects and medical benefits
   - Dosage guidance
   - Compliance and safety

2. **Healthcare** (`domains/healthcare/`)
   - Health information
   - Wellness tips
   - Symptom checking
   - Provider recommendations
   - Emergency detection

### Adding New Domains

To add a new domain (e.g., "legal"):

1. Create domain folder:
```
domains/legal/
├── config.yaml          # Domain configuration
├── plugin.py           # Plugin implementation
├── prompts/           # Prompt templates
│   └── *.yaml
├── knowledge/         # Knowledge base
│   └── *.json
└── data/             # Data schema
    └── schema.yaml
```

2. Implement the `DomainPlugin` interface:
```python
from core.interfaces.domain_plugin import DomainPlugin

class LegalPlugin(DomainPlugin):
    def get_prompt(self, task, **kwargs):
        # Return legal-specific prompts
    
    def validate_input(self, input_text, task):
        # Validate for legal compliance
    
    def format_response(self, response, task, context):
        # Format legal responses
```

3. Enable in `config/domains.yaml`:
```yaml
enabled_domains:
  - budtender
  - healthcare
  - legal  # New domain
```

## 🚀 Usage

### Basic Usage

```python
from core.ai_engine import DomainAgnosticAIEngine

# Initialize engine
engine = DomainAgnosticAIEngine()
await engine.initialize()

# Switch to budtender domain
await engine.switch_domain("budtender")
response = await engine.process("I need something for pain relief")

# Switch to healthcare domain
await engine.switch_domain("healthcare")
response = await engine.process("What are symptoms of flu?")

# Switch to legal domain
await engine.switch_domain("legal")
response = await engine.process("What are my rights during a traffic stop?")
```

### Domain Discovery

```python
# List all available domains
domains = engine.list_domains()
for domain in domains:
    print(f"{domain['name']}: {domain['description']}")

# Get domain capabilities
capabilities = engine.get_domain_capabilities("budtender")
print(f"Supported tasks: {capabilities['tasks']}")
print(f"Supported languages: {capabilities['languages']}")
```

### Multi-Language Support

```python
# Process in different languages
response = await engine.process(
    "Hola, necesito algo para dormir",
    metadata={"language": "es"}
)

response = await engine.process(
    "Bonjour, je cherche des informations",
    metadata={"language": "fr"}
)
```

### Knowledge Search

```python
# Search domain knowledge
results = await engine.search_knowledge(
    "pain relief",
    domain="budtender",
    limit=5
)
```

## 📊 Data Abstraction

The system uses a **data abstraction layer** that allows domains to work with different data sources:

### Schema Mapping

Each domain defines how its concepts map to database tables:

```yaml
# domains/budtender/data/schema.yaml
entities:
  product:
    db_table: products
    fields:
      name: product_name
      type: plant_type
      thc: thc_percentage
      cbd: cbd_percentage
```

### Data Adapters

Implement different data sources:
- PostgreSQL (`data/adapters/postgresql.py`)
- MongoDB (`data/adapters/mongodb.py`)
- REST APIs (`data/adapters/api.py`)
- Vector Databases (`data/adapters/chromadb.py`)

## 🧪 Testing

Run the domain switching test:

```bash
python test_domain_switching.py
```

This demonstrates:
- Domain switching
- Multi-language support
- Knowledge search
- Session context
- Domain-specific responses

## 🎨 Key Benefits

1. **Extensibility**: Add new domains without changing core code
2. **Maintainability**: Domain logic isolated in plugins
3. **Reusability**: Core AI capabilities shared across domains
4. **Flexibility**: Easy to switch data sources
5. **Scalability**: Domains can be loaded/unloaded dynamically
6. **Testability**: Each domain tested independently

## 📁 Directory Structure

```
ai-engine-service/
├── core/                      # Domain-agnostic core
│   ├── ai_engine.py          # Main engine
│   ├── domain_manager.py     # Domain management
│   └── interfaces/           # Abstract interfaces
│       ├── domain_plugin.py
│       └── data_adapter.py
│
├── domains/                  # Domain plugins
│   ├── budtender/           # Cannabis domain
│   ├── healthcare/          # Medical domain
│   ├── legal/              # Legal domain
│   └── education/          # Education domain
│
├── data/                    # Data layer
│   └── adapters/           # Database adapters
│
├── config/                 # Configuration
│   └── domains.yaml       # Domain settings
│
└── services/              # AI services
    ├── unified_model_interface.py
    └── multi_model_orchestrator.py
```

## 🔮 Future Enhancements

1. **Dynamic Domain Loading**: Load domains from external packages
2. **Domain Marketplace**: Share and download domain plugins
3. **Cross-Domain Integration**: Domains can call each other
4. **Domain Templates**: Scaffolding for new domains
5. **Visual Domain Builder**: GUI for creating domains
6. **Domain Versioning**: Support multiple versions
7. **A/B Testing**: Test different domain implementations
8. **Analytics**: Track domain usage and performance

## 🤝 Contributing

To contribute a new domain:

1. Fork the repository
2. Create your domain in `domains/your_domain/`
3. Implement the `DomainPlugin` interface
4. Add tests in `tests/domains/your_domain/`
5. Submit a pull request

## 📝 Industry Standards

This architecture follows industry best practices:

- **Plugin Architecture**: Similar to WordPress, Jenkins, VS Code
- **Domain-Driven Design**: Bounded contexts for each domain
- **Hexagonal Architecture**: Core isolated from infrastructure
- **Strategy Pattern**: Swappable domain implementations
- **Repository Pattern**: Abstract data access
- **Dependency Injection**: Loose coupling between components

## 🚦 Migration from Old System

The cannabis-specific code has been moved to the `budtender` domain plugin:
- Prompts → `domains/budtender/prompts/`
- Knowledge → `domains/budtender/knowledge/`
- Business Logic → `domains/budtender/plugin.py`
- Data Schema → `domains/budtender/data/schema.yaml`

The core engine is now completely domain-agnostic and can serve any industry!