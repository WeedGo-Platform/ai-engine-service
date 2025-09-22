# AI Engine Service - Comprehensive Architecture Analysis

## Overview
The AI Engine Service is a sophisticated multi-tenant cannabis commerce platform backend built on FastAPI, integrating AI capabilities, inventory management, payment processing, and customer engagement features.

## Database Architecture

### Core Tables (100+ tables identified)
The database follows a comprehensive schema with proper separation of concerns:

#### Product & Inventory Management
- **ocs_product_catalog**: Provincial product catalog with detailed cannabis attributes
- **ocs_inventory**: Multi-store inventory tracking with real-time stock levels
- **accessories_catalog/inventory**: Non-cannabis product management
- **batch_tracking**: Lot tracking for compliance
- **shelf_locations**: Physical store location mapping
- **inventory_movements/transactions**: Audit trail for all inventory changes

#### Customer & Order Management
- **profiles**: Customer profiles with preferences
- **orders**: Order processing with status tracking
- **cart_sessions**: Shopping cart persistence
- **wishlist**: Customer product favorites
- **customer_reviews/ratings**: Product feedback system
- **order_status_history**: Complete order lifecycle tracking

#### Payment Infrastructure
- **payment_providers**: Multi-provider configuration
- **payment_transactions**: Transaction processing records
- **payment_methods**: Stored customer payment options
- **payment_settlements**: Financial reconciliation
- **payment_webhooks**: Async payment notifications
- **payment_disputes/refunds**: Dispute resolution tracking

#### Multi-Tenancy & Store Management
- **tenants**: Platform tenant management
- **stores**: Individual store configurations
- **store_settings**: Store-specific preferences
- **provinces_territories**: Canadian jurisdiction support
- **provincial_suppliers**: Supplier management per province

#### AI & Communication
- **ai_conversations**: Chat history persistence
- **ai_personalities**: Configurable AI personas
- **conversation_states**: Conversation context tracking
- **voice_profiles**: Voice authentication data
- **translation_batches**: Multi-language support

### Database Views (8 views)
- **comprehensive_product_inventory_view**: Unified product-inventory data
- **inventory_products_view**: Simplified inventory access
- **store_settings_view**: Aggregated store configurations
- **admin_users**: Administrative user access
- **wishlist_details**: Enhanced wishlist information
- **recent_login_activity**: Security monitoring
- **v_hot_translations**: Performance-optimized translations
- **v_translation_stats**: Translation analytics

## API Architecture

### Endpoint Categories (48+ endpoint modules)

#### Authentication & Security
- **customer_auth**: Customer authentication (JWT)
- **admin_auth**: Admin authentication with RBAC
- **auth_otp**: OTP-based authentication
- **auth_context**: Context switching for multi-tenant
- **auth_voice**: Voice biometric authentication

#### Product & Inventory
- **inventory_endpoints**: Core inventory operations
- **store_inventory_endpoints**: Store-specific inventory
- **product_endpoints**: Product management
- **product_details_endpoints**: Enhanced product info
- **product_catalog_ocs_endpoints**: Provincial catalog integration
- **accessories_endpoints**: Non-cannabis products
- **shelf_location_endpoints**: Store layout management

#### Commerce Operations
- **cart_endpoints**: Shopping cart management
- **order_endpoints**: Order processing
- **pos_endpoints**: Point-of-sale operations
- **pos_transaction_endpoints**: Transaction processing
- **wishlist_endpoints**: Customer favorites
- **promotion_endpoints**: Discount management
- **review_endpoints**: Customer feedback

#### Payment Processing
- **payment_endpoints**: Core payment operations
- **client_payment_endpoints**: Customer payment UI
- **store_payment_endpoints**: Store terminal integration
- **payment_session_endpoints**: Clover integration
- **payment_provider_endpoints**: Provider management
- **payment_settings_endpoints**: Configuration

#### Store & Tenant Management
- **tenant_endpoints**: Multi-tenant operations
- **store_endpoints**: Store management
- **store_hours_endpoints**: Operating hours
- **supplier_endpoints**: Supplier management
- **provincial_catalog_upload_endpoints**: Bulk catalog import

#### Customer Experience
- **chat_endpoints**: WebSocket chat interface
- **voice_endpoints**: Voice interaction
- **kiosk_endpoints**: Self-service kiosk
- **delivery_endpoints**: Delivery management
- **customer_endpoints**: Customer profiles
- **search_endpoints**: Product search

#### Analytics & Admin
- **analytics_endpoints**: Business intelligence
- **admin_endpoints**: Administrative functions
- **database_management**: Database operations
- **translation_endpoints**: Multi-language support
- **hardware_endpoints**: Device detection

## Core Services Architecture

### AI Engine (SmartAIEngineV5)
**Location**: `services/smart_ai_engine_v5.py`

Key Features:
- **Modular Agent System**: Supports multiple AI personalities and agents
- **Tool Integration**: Extensible tool framework for function calling
- **Context Persistence**: Maintains conversation state across sessions
- **Intent Detection**: Pattern and LLM-based intent recognition
- **Model Management**: Dynamic model loading with resource optimization

Components:
- ToolManager: Manages AI tool registration and execution
- ContextManager: Handles conversation memory and state
- IntentDetector: Classifies user intents for routing
- Multiple LLama models support with dynamic loading

### Inventory Service
**Location**: `services/store_inventory_service.py`

Key Features:
- **Multi-Store Support**: Tenant and store isolation
- **Transaction Types**: Sale, purchase, adjustment, transfer, return, damage, expire
- **Real-time Tracking**: Quantity on hand, available, reserved
- **Batch Management**: Lot tracking for compliance
- **Reorder Management**: Automatic reorder point monitoring

### Payment Service V2
**Location**: `services/payment_service_v2.py`

Key Features:
- **Multi-Provider Support**: Factory pattern for provider integration
- **Circuit Breaker**: Automatic failover for reliability
- **Idempotency**: Duplicate transaction prevention
- **Fee Splitting**: Platform and store fee management
- **Security**: PCI-compliant credential management

### Order Service
**Location**: `services/order_service.py`

Key Features:
- **Cart Conversion**: Seamless cart to order transformation
- **Inventory Integration**: Automatic stock reservation
- **Status Tracking**: Complete order lifecycle management
- **Payment Integration**: Multiple payment method support

### Customer Service
**Location**: `services/customer_service.py`

Features:
- Profile management
- Address management
- Preference tracking
- Order history

### Authentication System
**Location**: `core/authentication.py`

Security Features:
- **JWT Tokens**: Access and refresh token management
- **RBAC**: Role-based access control
- **API Keys**: Service-to-service authentication
- **Session Management**: Active session tracking
- **Multi-Factor**: OTP and voice authentication support

## Data Flow Architecture

### Customer Purchase Flow
1. **Product Discovery**
   - Search via AI chat or browse catalog
   - Real-time inventory from `comprehensive_product_inventory_view`
   - Personalized recommendations from AI engine

2. **Cart Management**
   - Session-based cart persistence
   - Real-time pricing with promotions
   - Inventory reservation on add-to-cart

3. **Checkout Process**
   - Address validation
   - Payment method selection
   - Tax calculation based on jurisdiction

4. **Payment Processing**
   - Provider routing based on tenant config
   - Idempotent transaction processing
   - Webhook-based async confirmation

5. **Order Fulfillment**
   - Inventory deduction
   - Status tracking
   - Delivery/pickup coordination

### AI Interaction Flow
1. **User Input**
   - WebSocket connection via chat endpoint
   - Voice input through STT service
   - Context enrichment from user profile

2. **Intent Processing**
   - Intent detection (pattern or LLM-based)
   - Context retrieval from conversation history
   - Tool selection based on intent

3. **Response Generation**
   - LLama model inference
   - Tool execution for data retrieval
   - Response formatting with personality traits

4. **Delivery**
   - WebSocket streaming for chat
   - TTS for voice responses
   - Context persistence for continuity

## Integration Points

### External Integrations
- **OCS (Ontario Cannabis Store)**: Provincial catalog sync
- **Clover**: POS and payment terminal
- **Multiple Payment Providers**: Via factory pattern
- **Hardware Devices**: Barcode scanners, receipt printers

### Internal Service Communication
- **Database Pool**: Async PostgreSQL connections
- **WebSocket Manager**: Real-time communication
- **Background Tasks**: Async job processing
- **Event System**: Order status updates, inventory changes

## Security Architecture

### Multi-Layer Security
1. **Authentication Layer**
   - JWT with refresh tokens
   - API key authentication
   - Voice biometric option

2. **Authorization Layer**
   - Role-based access control
   - Tenant isolation
   - Store-level permissions

3. **Data Protection**
   - Encrypted credentials storage
   - PCI compliance for payments
   - Audit logging

4. **API Security**
   - Rate limiting
   - CORS configuration
   - Security headers
   - Input validation

## Scalability Features

### Performance Optimizations
- **Connection Pooling**: Database connection reuse
- **Caching**: Hot translations view
- **Lazy Loading**: Model loading on demand
- **Circuit Breakers**: Fault tolerance
- **Idempotency**: Duplicate prevention

### Multi-Tenant Architecture
- **Tenant Isolation**: Data segregation
- **Store-Level Configuration**: Flexible settings
- **Provider Routing**: Tenant-specific integrations
- **Resource Management**: Per-tenant limits

## Key Technical Decisions

1. **FastAPI Framework**: Async support, automatic OpenAPI docs
2. **PostgreSQL Database**: ACID compliance, JSON support
3. **LLama Models**: Local AI inference without external dependencies
4. **WebSocket Chat**: Real-time bidirectional communication
5. **Factory Pattern**: Extensible payment provider integration
6. **Service Layer Architecture**: Clean separation of concerns

## Deployment Considerations

### Environment Configuration
- Database connection: PostgreSQL on port 5434
- Multiple localhost ports for different frontends
- Environment-based configuration loading
- Secure credential management

### Monitoring Points
- User login activity tracking
- Payment transaction monitoring
- Inventory level alerts
- AI conversation analytics
- System resource utilization

## Summary

The AI Engine Service represents a sophisticated, production-ready commerce platform with:
- **Comprehensive Data Model**: 100+ tables covering all business aspects
- **Modular Architecture**: Clean service separation with defined interfaces
- **AI Integration**: Embedded intelligence for customer engagement
- **Multi-Tenant Support**: Complete tenant and store isolation
- **Security First**: Multiple authentication methods and data protection
- **Scalability**: Built for high-volume commerce operations

The architecture demonstrates enterprise-grade design patterns while maintaining flexibility for cannabis industry-specific requirements.