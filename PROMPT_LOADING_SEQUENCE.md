# AI Engine Prompt Loading and Usage Sequence

## Overview
The AI Engine uses a layered prompt system that loads configuration files in a specific sequence to build the final prompt sent to the model. This document explains the loading order and how each type of configuration file is used.

## File Types and Their Purposes

### 1. **System Configuration** (`system_config.json`)
- **Location**: `config/system_config.json` (primary) or `prompts/system/config.json` (legacy)
- **Purpose**: Defines global system behavior, model settings, and infrastructure configuration
- **Contains**:
  - Model parameters (temperature, max_tokens, top_p)
  - System behavior settings
  - Tool configurations
  - Context management settings
  - Intent detection configuration

### 2. **Agent Configuration** (`agents/[agent_id]/config.json`)
- **Location**: `agents/dispensary/config.json`, etc.
- **Purpose**: Defines agent-specific behavior and capabilities
- **Contains**:
  - Agent description and capabilities
  - Available tools for the agent
  - Default personality
  - Response style preferences

### 3. **Agent Prompts** (`agents/[agent_id]/prompts.json`)
- **Location**: `agents/dispensary/prompts.json`, etc.
- **Purpose**: Agent-specific prompt templates for different scenarios
- **Contains**:
  - Greeting templates
  - Product search templates
  - Recommendation templates
  - Order assistance templates
  - Various intent-specific templates

### 4. **Personality Configuration** (`personalities/[personality_id].json`)
- **Location**: `personalities/friendly.json`, `personalities/professional.json`, etc.
- **Purpose**: Defines personality traits that modify response style
- **Contains**:
  - Personality description
  - Tone modifiers
  - Communication style
  - Behavioral traits

### 5. **Intent Detection** (`agents/[agent_id]/intent.json`)
- **Location**: `agents/dispensary/intent.json`, etc.
- **Purpose**: Maps user intents to appropriate prompt templates
- **Contains**:
  - Intent patterns and keywords
  - Prompt template mappings
  - Confidence thresholds

## Loading Sequence

### Step 1: System Initialization
```python
# In SmartAIEngineV5.__init__()
1. Load system_config.json
2. Initialize intent detector
3. Initialize tool manager
4. Initialize context manager
```

### Step 2: Agent and Personality Loading
```python
# When load_agent_personality() is called:
1. Load agent config (agents/[agent_id]/config.json)
2. Load agent prompts (agents/[agent_id]/prompts.json)
3. Load agent intent mapping (agents/[agent_id]/intent.json)
4. Load personality traits (personalities/[personality_id].json)
5. Initialize agent-specific tools
```

### Step 3: Request Processing Flow
When a user message is received:

```python
# In generate() or get_response() method:
1. Check for user context (if user_id provided)
2. Detect intent (if no prompt_type specified)
3. Select appropriate prompt template based on:
   - Explicitly provided prompt_type
   - Detected intent
   - Default template fallback
4. Build final prompt
5. Apply personality modifiers
6. Send to model
```

## Prompt Construction Hierarchy

The final prompt is constructed by layering these elements:

```
[System Instruction]
  └── From system_config.json or agent config
[Personality Modifiers]
  └── From personalities/[personality_id].json
[Agent Context]
  └── From agents/[agent_id]/config.json
[Template]
  └── From agents/[agent_id]/prompts.json
[User Context]
  └── From user profile/history (if available)
[User Message]
  └── The actual user input
```

## Example Flow

### 1. Chat Endpoint Receives Message
```python
# chat_endpoints.py
message = "What strains do you have for anxiety?"
user_id = "user_123"
session_id = "session_456"
```

### 2. Load Agent/Personality (if needed)
```python
# If not already loaded or different from current
ai_engine.load_agent_personality(
    agent_id="dispensary",
    personality_id="friendly"
)
```

### 3. Generate Response
```python
response = ai_engine.get_response(
    message=message,
    session_id=session_id,
    user_id=user_id,
    max_tokens=500
)
```

### 4. Internal Processing
```python
# Inside get_response():
1. Get user context (age verification, preferences, history)
2. Detect intent → "product_search" (anxiety-related)
3. Load template from agents/dispensary/prompts.json["product_search"]
4. Apply personality traits from personalities/friendly.json
5. Construct final prompt:
   - System: "You are a knowledgeable dispensary assistant..."
   - Personality: "Be warm and approachable..."
   - Context: "User is 21+, verified customer..."
   - Template: "Help find products for: {query}"
   - User: "What strains do you have for anxiety?"
6. Send to model with configured parameters
```

## Configuration Priority

When multiple configurations define the same setting:

1. **Template-specific settings** (highest priority)
   - Settings in individual prompt templates
2. **Agent configuration**
   - Agent-specific defaults
3. **Personality configuration**
   - Personality-based modifiers
4. **System configuration** (lowest priority)
   - Global defaults

## Key Methods in SmartAIEngineV5

- `_load_system_config()`: Loads system configuration on init
- `load_agent_personality()`: Loads agent and personality combination
- `detect_intent()`: Uses intent detector to classify user message
- `apply_prompt_template()`: Applies selected template to user message
- `get_response()`: Main entry point for chat endpoints
- `generate()`: Core generation method with all options

## Intent Detection Flow

1. User message analyzed by intent detector
2. Intent detector checks against patterns in `intent.json`
3. Returns matched intent type (e.g., "product_search", "dosage_advice")
4. System loads corresponding prompt template
5. If no match, falls back to "general_conversation" or "default"

## Tools Integration

When tools are enabled:
1. System checks if detected intent requires tools
2. Loads appropriate tools from agent configuration
3. Executes tools to gather information
4. Includes tool results in prompt context
5. Model generates response incorporating tool data

## Context Management

User context is added when available:
- User profile (name, age verification)
- Recent orders
- Preferences
- Conversation history
- Location/store information

This context is injected into the prompt to provide personalized responses.