# Sales Conversion Pipeline Architecture

## Overview
AI-driven sales conversion system that guides users from intent discovery through purchase completion using a state-based conversation flow with configurable stages, prompts, and strategies.

## Key Integration Points

### 1. Existing Components to Leverage
- **SmartAIEngineV5**: Core conversation engine with tool calling capabilities
- **ContextManager**: Session and conversation state persistence (IContextManager)
- **IntentDetector**: Intent classification system (IIntentDetector)
- **ToolManager**: Tool execution framework (IToolManager)
- **ProductSearchTool**: Product database search capabilities
- **DatabaseConnectionManager**: Database connection pooling
- **PromptManager**: Prompt template management (IPromptManager)

### 2. New Components Required

#### 2.1 Sales State Management
- **ISalesStateManager**: Interface for managing sales conversation states
- **SalesStage**: Enum defining sales pipeline stages
- **StateTransitionRules**: Configuration-driven state transitions

#### 2.2 User Profiling
- **IUserProfiler**: Interface for user profile management
- **ProfileRepository**: Persistent storage of user profiles
- **ProgressiveDataCollector**: Gradual information gathering

#### 2.3 Sales Strategy Engine
- **ISalesStrategy**: Interface for sales approach strategies
- **IntentToActionMapper**: Maps detected intents to sales actions
- **ObjectionHandler**: Configurable objection handling

#### 2.4 Cart & Order Management
- **ICartManager**: Interface for cart operations
- **OrderService**: Order creation and management
- **SessionTracker**: Session-based cart persistence

#### 2.5 Recommendation Engine
- **IRecommendationEngine**: Interface for product recommendations
- **UpsellCrossSellRules**: Rules engine for upselling
- **PersonalizationService**: User preference-based recommendations

#### 2.6 Analytics & Metrics
- **IConversionTracker**: Interface for tracking conversions
- **MetricsCollector**: Real-time metrics collection
- **ABTestingFramework**: Response optimization testing

## Design Patterns Applied

### 1. State Pattern
- **ConversationState**: Abstract base state
- **GreetingState, DiscoveryState, RecommendationState, etc.**: Concrete states
- **StateContext**: Maintains current state and transitions

### 2. Strategy Pattern
- **SalesStrategy**: Abstract strategy interface
- **DirectSalesStrategy, ConsultativeSalesStrategy, etc.**: Concrete strategies
- **StrategySelector**: Dynamic strategy selection based on context

### 3. Repository Pattern
- **UserProfileRepository**: User profile persistence
- **ConversationRepository**: Conversation history storage
- **OrderRepository**: Order management

### 4. Factory Pattern
- **ServiceFactory**: Already exists, extend for new services
- **StrategyFactory**: Creates appropriate sales strategies
- **StateFactory**: Creates conversation states

### 5. Observer Pattern
- **EventBus**: For analytics and metrics collection
- **ConversionEventListener**: Tracks conversion events
- **MetricsAggregator**: Aggregates metrics

## Database Schema Extensions

### New Tables Required
```sql
-- User profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    preferences JSONB,
    purchase_history JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Conversation states table
CREATE TABLE conversation_states (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    current_stage VARCHAR(50),
    stage_history JSONB,
    context_data JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Cart sessions table
CREATE TABLE cart_sessions (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_profile_id UUID REFERENCES user_profiles(id),
    items JSONB,
    total_amount DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    cart_session_id UUID REFERENCES cart_sessions(id),
    user_profile_id UUID REFERENCES user_profiles(id),
    order_details JSONB,
    payment_status VARCHAR(50),
    delivery_info JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Conversion metrics table
CREATE TABLE conversion_metrics (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255),
    stage_transitions JSONB,
    conversion_events JSONB,
    duration_seconds INTEGER,
    converted BOOLEAN,
    created_at TIMESTAMP
);
```

## Configuration Structure

### Sales Pipeline Configuration
```json
{
  "sales_pipeline": {
    "stages": {
      "greeting": {
        "next_stages": ["discovery", "direct_request"],
        "timeout_seconds": 30,
        "prompts": ["greeting_new", "greeting_returning"]
      },
      "discovery": {
        "next_stages": ["recommendation", "education"],
        "data_collection": ["needs", "experience_level", "preferences"],
        "prompts": ["discovery_open", "discovery_guided"]
      },
      "recommendation": {
        "next_stages": ["consideration", "objection", "cart"],
        "strategies": ["personalized", "trending", "similar"],
        "prompts": ["recommend_single", "recommend_multiple"]
      }
    },
    "transitions": {
      "rules": [
        {
          "from": "greeting",
          "to": "discovery",
          "conditions": ["no_specific_request", "new_user"]
        }
      ]
    }
  }
}
```

## API Endpoints

### New Endpoints Required
- `POST /api/v5/sales/start-session` - Initialize sales conversation
- `POST /api/v5/sales/process-message` - Process user message in sales context
- `GET /api/v5/sales/session/{session_id}` - Get session state
- `POST /api/v5/cart/add` - Add item to cart
- `POST /api/v5/cart/update` - Update cart items
- `POST /api/v5/cart/checkout` - Initiate checkout
- `POST /api/v5/order/create` - Create order from cart
- `GET /api/v5/metrics/conversion` - Get conversion metrics

## Integration Flow

1. **Request Reception**: API endpoint receives user message
2. **Session Management**: ContextManager retrieves/creates session
3. **Intent Detection**: IntentDetector classifies user intent
4. **State Management**: SalesStateManager determines current stage
5. **Strategy Selection**: StrategySelector chooses sales approach
6. **Profile Update**: UserProfiler updates user information
7. **Action Execution**: Execute appropriate action (search, recommend, add to cart)
8. **Response Generation**: Generate response using prompt templates
9. **State Transition**: Update conversation state if needed
10. **Metrics Collection**: Track conversion events
11. **Response Delivery**: Return response to user

## File Structure
```
src/services/sales_conversion/
├── __init__.py
├── interfaces.py           # All interfaces
├── models.py              # Data models and enums
├── states/
│   ├── __init__.py
│   ├── base.py           # Base state class
│   ├── greeting.py       # Greeting state
│   ├── discovery.py      # Discovery state
│   ├── recommendation.py # Recommendation state
│   └── ...
├── strategies/
│   ├── __init__.py
│   ├── base.py           # Base strategy
│   ├── direct.py         # Direct sales strategy
│   └── consultative.py   # Consultative strategy
├── repositories/
│   ├── __init__.py
│   ├── user_profile.py   # User profile repository
│   └── conversation.py   # Conversation repository
├── services/
│   ├── __init__.py
│   ├── cart_manager.py   # Cart management
│   ├── order_service.py  # Order processing
│   └── recommendation.py # Recommendation engine
├── config/
│   ├── sales_pipeline.json
│   ├── prompts/
│   └── strategies.json
└── tests/
    ├── unit/
    └── integration/
```

## Next Steps
1. Create interface definitions
2. Implement sales stage enum and state classes
3. Build user profiling system
4. Create sales strategy implementations
5. Develop cart and order management
6. Implement recommendation engine
7. Add conversion tracking
8. Create comprehensive tests