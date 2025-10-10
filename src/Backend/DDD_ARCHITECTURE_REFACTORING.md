# Domain-Driven Design Architecture Refactoring Plan
## Based on Actual Database Schema

## IMPLEMENTATION STATUS

### ✅ Completed (Updated: Real-time)
- **Base Infrastructure**: Domain base classes (Entity, ValueObject, AggregateRoot), Specification pattern, Repository interfaces
- **Shared Value Objects**: Address, GeoLocation, TaxInfo, Money, DateRange, ContactInfo
- **Tenant Management Context**:
  - Tenant (Root Entity) ✅
  - Store (Root Entity) ✅
  - ProvinceTerritory (Entity) ✅
  - Remaining: TenantUser, StoreUser, TenantSubscription, StoreCompliance

### 🚧 In Progress
- Tenant Management Context (remaining entities)
- Identity & Access Context

### 📋 Pending
- Product Catalog Context (0/6 entities)
- Inventory Management Context (0/7 entities)
- Purchase Order Context (0/3 entities)
- Order Management Context (0/3 entities)
- Pricing & Promotions Context (0/7 entities)
- Payment Processing Context (0/6 entities)
- Delivery Management Context (0/6 entities)
- Customer Engagement Context (0/5 entities)
- Communication Context (0/5 entities)
- AI & Conversation Context (0/6 entities)
- Analytics & Audit Context (read models)
- Localization Context (0/4 entities)
- Metadata Context (0/2 entities)

### 📊 Overall Progress: ~10% Complete

---

## 1. ARCHITECTURAL PRINCIPLES

### Core Design Patterns
- **Domain-Driven Design (DDD)**: Bounded contexts, aggregates, entities, value objects
- **Clean Architecture**: Separation of concerns, dependency inversion
- **CQRS**: Command Query Responsibility Segregation for read/write optimization
- **Event Sourcing**: For audit trails and state transitions
- **Repository Pattern**: Abstract data access
- **Unit of Work**: Transactional consistency

### Multi-Tenancy Strategy
- Tenant isolation at application layer
- Store-level data partitioning
- Shared database with row-level security
- Tenant context propagation through all layers

## 2. BOUNDED CONTEXTS

### 2.1 Tenant Management Context
**Purpose**: Multi-tenant infrastructure and store management

**Tables**:
- `tenants` (aggregate root)
- `stores` (aggregate root)
- `provinces_territories` (reference data)
- `store_settings` (value object)

**Domain Models**:
```python
class Tenant:  # Root Entity
    id: UUID
    name: str
    code: str  # Unique tenant code
    company_name: Optional[str]
    business_number: Optional[str]
    gst_hst_number: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    website: Optional[str]
    logo_url: Optional[str]
    status: TenantStatus  # active, suspended, cancelled, trial
    subscription_tier: str
    max_stores: int
    billing_info: Dict[str, Any]
    payment_provider_settings: Dict[str, Any]
    currency: str = "CAD"
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class Store:  # Root Entity
    id: UUID
    tenant_id: UUID
    province_territory_id: UUID
    store_code: str  # Unique store identifier
    name: str
    phone: Optional[str]
    email: Optional[str]
    hours: Dict[str, Any]  # Operating hours
    timezone: str = "America/Toronto"
    license_number: Optional[str]
    license_expiry: Optional[date]
    tax_rate: Decimal
    delivery_radius_km: int
    delivery_enabled: bool
    pickup_enabled: bool
    kiosk_enabled: bool
    pos_enabled: bool
    ecommerce_enabled: bool
    status: StoreStatus  # active, inactive, suspended
    settings: Dict[str, Any]
    pos_integration: Dict[str, Any]
    pos_payment_terminal_settings: Dict[str, Any]
    seo_config: Dict[str, Any]
    location: Optional[GeoLocation]
    created_at: datetime
    updated_at: datetime

class StoreSettings:  # Value Object
    store_id: UUID
    key: str
    value: Any
    category: str
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime

class Address:  # Value Object
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"

class GeoLocation:  # Value Object
    latitude: Decimal
    longitude: Decimal

TenantAggregate:
  - Root: Tenant (tenants)
  - Value Objects: Address
  - Commands: CreateTenant, UpdateTenant, SuspendTenant
  - Events: TenantCreated, TenantUpdated, TenantSuspended

StoreAggregate:
  - Root: Store (stores)
  - Value Objects: StoreSettings, GeoLocation
  - Commands: CreateStore, UpdateStore, ActivateStore, DeactivateStore
  - Events: StoreCreated, StoreUpdated, StoreActivated
```

### 2.2 Identity & Access Management Context
**Purpose**: User authentication, authorization, and session management

**Tables**:
- `users` (aggregate root)
- `profiles`
- `auth_tokens`
- `api_keys`
- `token_blacklist`
- `otp_codes`, `otp_rate_limits`
- `user_sessions`, `user_login_logs`
- `user_addresses`
- `role_permissions`

**Domain Models**:
```python
class User:  # Root Entity
    id: UUID
    email: str
    phone: Optional[str]
    password_hash: str
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    is_active: bool
    is_verified: bool
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    last_login: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class Profile:  # Entity
    id: UUID
    user_id: UUID
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    preferences: Dict[str, Any]
    loyalty_points: int
    tier_level: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class UserAddress:  # Entity
    id: UUID
    user_id: UUID
    address_type: str  # billing, shipping
    is_default: bool
    street_address: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    created_at: datetime
    updated_at: datetime

class AuthToken:  # Root Entity
    id: UUID
    user_id: UUID
    token_hash: str
    token_type: str  # access, refresh
    expires_at: datetime
    last_used: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_revoked: bool
    created_at: datetime

class ApiKey:  # Entity
    id: UUID
    user_id: Optional[UUID]
    store_id: Optional[UUID]
    key_hash: str
    name: str
    permissions: List[str]
    rate_limit: Optional[int]
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class OtpCode:  # Entity
    id: UUID
    user_id: UUID
    code_hash: str
    purpose: str  # login, verification, password_reset
    expires_at: datetime
    attempts: int
    verified_at: Optional[datetime]
    created_at: datetime

class Permission:  # Value Object
    resource: str
    action: str
    scope: Optional[str]

UserAggregate:
  - Root: User (users)
  - Entities: Profile (profiles), UserAddress (user_addresses)
  - Value Objects: Permission
  - Commands: RegisterUser, UpdateProfile, AddAddress, VerifyOTP
  - Events: UserRegistered, ProfileUpdated, AddressAdded, LoginAttempted

AuthenticationAggregate:
  - Root: AuthToken (auth_tokens)
  - Entities: ApiKey (api_keys), OtpCode (otp_codes)
  - Commands: GenerateToken, RevokeToken, CreateApiKey
  - Events: TokenGenerated, TokenRevoked, ApiKeyCreated
```

### 2.3 Product Catalog Context
**Purpose**: Provincial product catalog and accessories management

**Tables**:
- `ocs_product_catalog` (aggregate root)
- `accessories_catalog` (aggregate root)
- `accessory_categories`

**Domain Models**:

```python
class OcsProduct:  # Root Entity
    id: UUID
    ocs_variant_number: str  # Primary SKU
    ocs_product_name: str
    product_name: str
    brand_name: str
    subcategory: Optional[str]
    plant_type: Optional[str]  # Sativa, Indica, Hybrid
    product_form: Optional[str]
    total_mg: Optional[Decimal]
    cbd_min: Optional[Decimal]
    cbd_max: Optional[Decimal]
    thc_min: Optional[Decimal]
    thc_max: Optional[Decimal]
    terpene_profile: Optional[str]
    volume_ml: Optional[Decimal]
    pieces: Optional[int]
    price_per_unit: Optional[Decimal]
    msrp_price: Optional[Decimal]
    unit_of_measure: Optional[str]
    image_url: Optional[str]
    description: Optional[str]
    allergens: Optional[str]
    ingredients: Optional[str]
    created_at: datetime
    updated_at: datetime

class Accessory:  # Root Entity
    id: UUID
    sku: str
    name: str
    category_id: UUID
    brand: Optional[str]
    description: Optional[str]
    unit_cost: Decimal
    retail_price: Decimal
    barcode: Optional[str]
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class AccessoryCategory:  # Entity
    id: UUID
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]  # For hierarchical categories
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

CannabisProductAggregate:
  - Root: OcsProduct (ocs_product_catalog)
  - Value Objects: ProductAttributes, PlantType, Category, SubCategory, SubSubCategory
  - Commands: ImportCatalog, UpdateProduct
  - Events: CatalogImported, ProductUpdated

AccessoryAggregate:
  - Root: Accessory (accessories_catalog)
  - Entities: Category (accessory_categories)
  - Commands: CreateAccessory, UpdateAccessory, CategorizeAccessory
  - Events: AccessoryCreated, AccessoryCategorized
```

### 2.4 Inventory Management Context
**Purpose**: Stock management, batch tracking, and inventory movements

**Tables**:
- `ocs_inventory` (aggregate root)
- `ocs_inventory_logs`
- `ocs_inventory_movements`
- `ocs_inventory_reservations`
- `ocs_inventory_snapshots`
- `ocs_inventory_transactions`
- `accessories_inventory`
- `batch_tracking`
- `shelf_locations`
- `inventory_shelf_assignments`  # Junction table linking inventory to shelf locations

**Domain Models**:

```python
class Inventory:  # Root Entity (ocs_inventory)
    id: UUID
    store_id: UUID
    sku: str  # Product SKU
    quantity_on_hand: int
    quantity_available: int
    quantity_reserved: int
    unit_cost: Decimal
    retail_price: Decimal  # Generated or override
    retail_price_dynamic: Optional[Decimal]
    override_price: Optional[Decimal]
    reorder_point: int
    reorder_quantity: int
    min_stock_level: int
    max_stock_level: int
    is_available: bool
    case_gtin: Optional[str]  # Global Trade Item Number for case
    each_gtin: Optional[str]  # GTIN for individual units
    product_name: Optional[str]
    last_restock_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class BatchTracking:  # Entity
    id: UUID
    store_id: UUID
    sku: str
    batch_lot: str  # Lot/batch number
    gtin: Optional[str]
    quantity_received: int
    quantity_remaining: int
    unit_cost: Decimal
    received_date: datetime
    purchase_order_id: Optional[UUID]
    supplier_id: Optional[UUID]
    location_id: Optional[UUID]  # Current shelf location
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ShelfLocation:  # Entity
    id: UUID
    store_id: UUID
    zone: Optional[str]  # Warehouse zone
    aisle: Optional[str]
    shelf: Optional[str]
    bin: Optional[str]
    location_code: str  # Generated: "ZONE-AISLE-SHELF-BIN"
    location_type: str  # standard, cold_storage, secure, bulk, display
    max_weight_kg: Optional[Decimal]
    max_volume_m3: Optional[Decimal]
    temperature_range: Optional[str]
    is_active: bool
    is_available: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class InventoryShelfAssignment:  # Entity (inventory_shelf_assignments)
    id: UUID
    store_id: UUID
    sku: str
    location_id: UUID  # References shelf_locations.id
    quantity: int
    batch_lot: Optional[str]
    is_primary: bool  # Primary picking location
    assigned_at: datetime
    assigned_by: Optional[UUID]
    notes: Optional[str]

class InventoryReservation:  # Entity
    id: UUID
    store_id: UUID
    sku: str
    order_id: Optional[UUID]
    cart_session_id: Optional[str]
    quantity: int
    reserved_until: datetime
    reserved_at: datetime
    released_at: Optional[datetime]
    status: str  # active, released, expired
    created_at: datetime

InventoryAggregate:
  - Root: Inventory (ocs_inventory)
  - Entities:
    - BatchTracking (batch_tracking)
    - ShelfLocation (shelf_locations)
    - Reservation (ocs_inventory_reservations)
  - Value Objects: StockLevel, GTIN
  - Commands: AdjustStock, ReserveStock, ReleaseStock, MoveInventory
  - Events: StockAdjusted, StockReserved, StockMoved, LowStockAlert

InventoryTransactionAggregate:
  - Root: Transaction (ocs_inventory_transactions)
  - Entities: Movement (ocs_inventory_movements)
  - Commands: RecordTransaction, RecordMovement
  - Events: TransactionRecorded, MovementRecorded
```

### 2.5 Purchase Order Context
**Purpose**: Supplier orders and receiving

**Tables**:
- `purchase_orders` (aggregate root)
- `purchase_order_items`
- `provincial_suppliers`

**Domain Models**:

```python
class PurchaseOrder:  # Root Entity
    id: UUID
    po_number: str
    supplier_id: Optional[UUID]
    store_id: UUID
    tenant_id: UUID
    order_date: datetime
    expected_date: Optional[date]
    received_date: Optional[datetime]
    status: str  # pending, ordered, shipped, received, cancelled
    total_amount: Decimal
    notes: Optional[str]
    created_by: UUID
    shipment_id: Optional[str]
    container_id: Optional[str]
    vendor: Optional[str]
    ocs_order_number: Optional[str]  # Ontario Cannabis Store order number
    created_at: datetime
    updated_at: datetime

class PurchaseOrderItem:  # Entity
    id: UUID
    purchase_order_id: UUID
    sku: str
    product_name: str
    quantity_ordered: int
    quantity_received: int
    unit_cost: Decimal
    total_cost: Decimal
    batch_lot: Optional[str]
    gtin: Optional[str]
    status: str  # pending, received, cancelled
    received_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class ProvincialSupplier:  # Entity
    id: UUID
    name: str
    code: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    province: str
    license_number: Optional[str]
    is_active: bool
    payment_terms: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

PurchaseOrderAggregate:
  - Root: PurchaseOrder (purchase_orders)
  - Entities: PurchaseOrderItem (purchase_order_items)
  - Value Objects: PONumber, ShipmentId, ContainerId
  - Commands: CreatePO, AddItems, ReceivePO, UpdatePOStatus
  - Events: POCreated, POReceived, ItemsReceived

SupplierAggregate:
  - Root: Supplier (provincial_suppliers)
```

### 2.6 Order Management Context
**Purpose**: Customer orders and cart management

**Tables**:
- `orders` (aggregate root)
- `order_status_history`
- `cart_sessions`

**Domain Models**:

```python
class Order:  # Root Entity
    id: UUID
    order_number: str
    store_id: UUID
    customer_id: Optional[UUID]
    status: str  # pending, confirmed, processing, ready, completed, cancelled
    order_type: str  # online, in-store, kiosk, phone
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    payment_status: str  # pending, paid, refunded, partial_refund
    payment_method: Optional[str]
    delivery_method: str  # pickup, delivery
    delivery_address: Optional[Dict[str, Any]]
    pickup_time: Optional[datetime]
    notes: Optional[str]
    items: List[Dict[str, Any]]  # Order line items
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

class OrderStatusHistory:  # Entity
    id: UUID
    order_id: UUID
    status: str
    changed_by: Optional[UUID]
    notes: Optional[str]
    created_at: datetime

class CartSession:  # Root Entity
    id: UUID
    session_id: str
    store_id: UUID
    customer_id: Optional[UUID]
    status: str  # active, abandoned, converted
    items: Dict[str, Any]  # Cart items as JSON
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    expires_at: datetime
    converted_to_order_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

OrderAggregate:
  - Root: Order (orders)
  - Entities: StatusHistory (order_status_history)
  - Commands: CreateOrder, UpdateOrderStatus, CancelOrder
  - Events: OrderCreated, OrderStatusChanged, OrderCancelled

CartAggregate:
  - Root: CartSession (cart_sessions)
  - Value Objects: CartItem, CartTotal
  - Commands: CreateCart, AddToCart, RemoveFromCart, ConvertToOrder
  - Events: CartCreated, ItemAdded, ItemRemoved, CartConverted
```

### 2.7 Pricing & Promotions Context
**Purpose**: Dynamic pricing, discounts, and promotional campaigns

**Tables**:
- `pricing_rules`
- `customer_pricing_rules`
- `dynamic_pricing_rules`
- `price_tiers`
- `price_history`
- `promotions`
- `promotion_usage`
- `discount_codes`
- `discount_usage`
- `bundle_deals`

**Domain Models**:

```python
class PricingRule:  # Root Entity
    id: UUID
    store_id: UUID
    name: str
    rule_type: str  # markup, discount, tiered, volume
    priority: int
    conditions: Dict[str, Any]  # Rule conditions as JSON
    actions: Dict[str, Any]  # Price actions as JSON
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class Promotion:  # Root Entity
    id: UUID
    store_id: UUID
    name: str
    description: Optional[str]
    promo_type: str  # percentage, fixed, bogo, bundle
    value: Decimal
    conditions: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int]
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DiscountCode:  # Entity
    id: UUID
    store_id: UUID
    code: str
    description: Optional[str]
    discount_type: str  # percentage, fixed
    discount_value: Decimal
    minimum_purchase: Optional[Decimal]
    usage_limit: Optional[int]
    usage_count: int
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

PricingAggregate:
  - Root: PricingRule (pricing_rules)
  - Entities:
    - CustomerPricing (customer_pricing_rules)
    - DynamicPricing (dynamic_pricing_rules)
    - PriceTier (price_tiers)
  - Commands: CreateRule, ApplyPricing, UpdateTier
  - Events: RuleCreated, PricingApplied, TierUpdated

PromotionAggregate:
  - Root: Promotion (promotions)
  - Entities:
    - DiscountCode (discount_codes)
    - BundleDeal (bundle_deals)
  - Value Objects: DiscountUsage, PromotionUsage
  - Commands: CreatePromotion, ApplyDiscount, ValidateCode
  - Events: PromotionCreated, DiscountApplied, CodeUsed
```

### 2.8 Payment Processing Context
**Purpose**: Payment transactions, settlements, and provider management

**Tables**:
- `payment_transactions` (aggregate root)
- `payment_providers`
- `payment_methods`
- `payment_refunds`
- `payment_settlements`
- `payment_disputes`
- `payment_webhooks`
- `payment_webhook_routes`
- `payment_credentials`
- `payment_audit_log`
- `payment_metrics`
- `payment_provider_health_metrics`
- `payment_fee_splits`
- `payment_idempotency_keys`
- `payment_subscriptions`

**Domain Models**:

```python
class PaymentTransaction:  # Root Entity
    id: UUID
    store_id: UUID
    order_id: UUID
    transaction_id: str  # External payment ID
    provider: str  # moneris, clover, interac, nuvei
    amount: Decimal
    currency: str = "CAD"
    status: str  # pending, authorized, captured, failed, refunded
    payment_method: str  # credit, debit, cash, interac
    card_last_four: Optional[str]
    authorization_code: Optional[str]
    response_data: Dict[str, Any]
    refund_amount: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

class PaymentProvider:  # Entity
    id: UUID
    name: str
    provider_type: str  # moneris, clover, interac, nuvei, paybright
    api_endpoint: str
    is_active: bool
    supported_methods: List[str]
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

PaymentTransactionAggregate:
  - Root: Transaction (payment_transactions)
  - Entities:
    - Refund (payment_refunds)
    - Dispute (payment_disputes)
  - Commands: ProcessPayment, RefundPayment, DisputeCharge
  - Events: PaymentProcessed, PaymentRefunded, DisputeRaised

PaymentProviderAggregate:
  - Root: Provider (payment_providers)
  - Entities:
    - PaymentMethod (payment_methods)
    - Credential (payment_credentials)
  - Commands: ConfigureProvider, UpdateCredentials
  - Events: ProviderConfigured, CredentialsUpdated

SettlementAggregate:
  - Root: Settlement (payment_settlements)
  - Entities: FeeSplit (payment_fee_splits)
  - Commands: CreateSettlement, ProcessSettlement
  - Events: SettlementCreated, SettlementProcessed
```

### 2.9 Delivery Management Context
**Purpose**: Delivery operations and tracking

**Tables**:
- `deliveries` (aggregate root)
- `delivery_batches`
- `delivery_tracking`
- `delivery_zones`
- `delivery_events`
- `delivery_geofences`
- `staff_delivery_status`

**Domain Models**:

```python
class Delivery:  # Root Entity
    id: UUID
    order_id: UUID
    store_id: UUID
    driver_id: Optional[UUID]
    status: str  # pending, assigned, en_route, delivered, cancelled
    delivery_address: Dict[str, Any]
    delivery_notes: Optional[str]
    scheduled_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]
    signature_url: Optional[str]
    tracking_number: Optional[str]
    distance_km: Optional[Decimal]
    delivery_fee: Decimal
    created_at: datetime
    updated_at: datetime

class DeliveryZone:  # Entity
    id: UUID
    store_id: UUID
    name: str
    postal_codes: List[str]
    delivery_fee: Decimal
    minimum_order: Decimal
    estimated_time_minutes: int
    is_active: bool
    polygon: Optional[Dict[str, Any]]  # GeoJSON polygon
    created_at: datetime
    updated_at: datetime

DeliveryAggregate:
  - Root: Delivery (deliveries)
  - Entities:
    - Tracking (delivery_tracking)
    - Event (delivery_events)
    - StaffStatus (staff_delivery_status)
  - Commands: CreateDelivery, UpdateLocation, CompleteDelivery
  - Events: DeliveryCreated, LocationUpdated, DeliveryCompleted

DeliveryZoneAggregate:
  - Root: Zone (delivery_zones)
  - Entities: Geofence (delivery_geofences)
  - Commands: CreateZone, UpdateBoundaries
  - Events: ZoneCreated, BoundariesUpdated

DeliveryBatchAggregate:
  - Root: Batch (delivery_batches)
  - Commands: CreateBatch, OptimizeRoute
  - Events: BatchCreated, RouteOptimized
```

### 2.10 Customer Engagement Context
**Purpose**: Reviews, ratings, and recommendations

**Tables**:
- `customer_reviews`
- `product_ratings`
- `review_attributes`
- `review_media`
- `review_votes`
- `product_recommendations`
- `recommendation_metrics`
- `wishlist`

**Domain Models**:

```python
class CustomerReview:  # Root Entity
    id: UUID
    store_id: UUID
    customer_id: UUID
    product_sku: str
    order_id: Optional[UUID]
    rating: int  # 1-5
    title: Optional[str]
    comment: Optional[str]
    is_verified_purchase: bool
    is_published: bool
    helpful_count: int
    unhelpful_count: int
    response: Optional[str]  # Store response
    response_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class ProductRating:  # Entity
    id: UUID
    product_sku: str
    store_id: UUID
    average_rating: Decimal
    total_reviews: int
    rating_distribution: Dict[str, int]  # {1: count, 2: count, ...}
    last_calculated: datetime
    created_at: datetime
    updated_at: datetime

class Wishlist:  # Entity
    id: UUID
    customer_id: UUID
    store_id: UUID
    product_sku: str
    notes: Optional[str]
    created_at: datetime

ReviewAggregate:
  - Root: Review (customer_reviews)
  - Entities:
    - Rating (product_ratings)
    - Media (review_media)
    - Attribute (review_attributes)
  - Value Objects: Vote
  - Commands: CreateReview, UpdateRating, AddMedia, VoteReview
  - Events: ReviewCreated, RatingUpdated, MediaAdded, ReviewVoted

RecommendationAggregate:
  - Root: Recommendation (product_recommendations)
  - Entities: Metric (recommendation_metrics)
  - Commands: GenerateRecommendation, TrackInteraction
  - Events: RecommendationGenerated, InteractionTracked

WishlistAggregate:
  - Root: Wishlist (wishlist)
  - Commands: AddToWishlist, RemoveFromWishlist
  - Events: ItemWishlisted, ItemRemoved
```

### 2.11 Communication Context
**Purpose**: Broadcast messaging and communication preferences

**Tables**:
- `broadcasts`
- `broadcast_messages`
- `broadcast_recipients`
- `broadcast_segments`
- `broadcast_audit_logs`
- `communication_logs`
- `communication_preferences`
- `communication_analytics`
- `message_templates`
- `push_subscriptions`
- `unsubscribe_list`

**Domain Models**:

```python
class Broadcast:  # Root Entity
    id: UUID
    store_id: UUID
    name: str
    message_type: str  # sms, email, push
    subject: Optional[str]
    content: str
    segment_id: Optional[UUID]
    status: str  # draft, scheduled, sending, sent, cancelled
    scheduled_time: Optional[datetime]
    sent_time: Optional[datetime]
    total_recipients: int
    successful_sends: int
    failed_sends: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

class CommunicationPreference:  # Entity
    id: UUID
    customer_id: UUID
    channel: str  # email, sms, push
    is_opted_in: bool
    opt_in_date: Optional[datetime]
    opt_out_date: Optional[datetime]
    categories: List[str]  # promotional, transactional, alerts
    created_at: datetime
    updated_at: datetime

BroadcastAggregate:
  - Root: Broadcast (broadcasts)
  - Entities:
    - Message (broadcast_messages)
    - Recipient (broadcast_recipients)
    - Segment (broadcast_segments)
  - Commands: CreateBroadcast, SendMessage, SegmentAudience
  - Events: BroadcastCreated, MessageSent, AudienceSegmented

CommunicationPreferenceAggregate:
  - Root: Preference (communication_preferences)
  - Entities: Subscription (push_subscriptions)
  - Commands: UpdatePreferences, Subscribe, Unsubscribe
  - Events: PreferencesUpdated, Subscribed, Unsubscribed
```

### 2.12 AI & Conversation Context
**Purpose**: AI-powered conversations and training

**Tables**:
- `ai_conversations`
- `ai_personalities`
- `chat_interactions`
- `conversation_states`
- `ai_training_data`
- `training_examples`
- `training_sessions`
- `voice_profiles`
- `voice_auth_logs`

**Domain Models**:

```python
class AIConversation:  # Root Entity
    id: UUID
    session_id: str
    store_id: UUID
    customer_id: Optional[UUID]
    personality_id: Optional[UUID]
    channel: str  # web, mobile, kiosk, voice
    status: str  # active, ended, timeout
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    started_at: datetime
    ended_at: Optional[datetime]

class AIPersonality:  # Entity
    id: UUID
    tenant_id: UUID
    store_id: Optional[UUID]
    name: str
    personality_type: Optional[str]
    avatar_url: Optional[str]
    voice_config: Dict[str, Any]
    traits: Dict[str, Any]
    greeting_message: Optional[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

class ChatInteraction:  # Entity
    id: UUID
    conversation_id: UUID
    message_type: str  # user, assistant, system
    content: str
    intent: Optional[str]
    confidence: Optional[Decimal]
    metadata: Dict[str, Any]
    created_at: datetime

ConversationAggregate:
  - Root: Conversation (ai_conversations)
  - Entities:
    - Interaction (chat_interactions)
    - State (conversation_states)
  - Commands: StartConversation, SendMessage, EndConversation
  - Events: ConversationStarted, MessageSent, ConversationEnded

AIPersonalityAggregate:
  - Root: Personality (ai_personalities)
  - Entities: VoiceProfile (voice_profiles)
  - Commands: CreatePersonality, UpdateTraits, ConfigureVoice
  - Events: PersonalityCreated, TraitsUpdated, VoiceConfigured

TrainingAggregate:
  - Root: TrainingSession (training_sessions)
  - Entities: Example (training_examples)
  - Commands: StartTraining, AddExample, CompleteTraining
  - Events: TrainingStarted, ExampleAdded, TrainingCompleted
```

### 2.13 Analytics & Audit Context
**Purpose**: System monitoring and compliance

**Tables**:
- `conversion_metrics`
- `parameter_accuracy`
- `audit_log`
- `agi_audit_logs`
- `agi_audit_aggregates`
- `agi_audit_alerts`
- `agi_rate_limit_buckets`
- `agi_rate_limit_rules`
- `agi_rate_limit_violations`
- `age_verification_logs`
- `location_access_log`
- `location_assignments_log`

**Read Models**: All tables in this context are treated as read models for reporting

### 2.14 Localization Context
**Purpose**: Multi-language support

**Tables**:
- `translations`
- `translation_batches`
- `translation_batch_items`
- `translation_overrides`
- `supported_languages`
- `skip_words`

**Aggregates**:
```python
TranslationAggregate:
  - Root: Translation (translations)
  - Entities:
    - Batch (translation_batches)
    - Override (translation_overrides)
  - Commands: CreateTranslation, BatchTranslate, OverrideTranslation
  - Events: TranslationCreated, BatchProcessed, OverrideApplied
```

### 2.15 Tax & Compliance Context
**Purpose**: Tax calculations and holiday management

**Tables**:
- `tax_rates`
- `holidays`

**Value Objects**: These tables represent configuration data

## 3. REPOSITORY INTERFACES

### Base Repository Pattern
```python
class IRepository[T]:
    async def get(id: UUID) -> T
    async def get_by_tenant(tenant_id: UUID) -> List[T]
    async def get_by_store(store_id: UUID) -> List[T]
    async def save(entity: T) -> T
    async def update(entity: T) -> T
    async def delete(id: UUID) -> bool

class IUnitOfWork:
    async def begin() -> None
    async def commit() -> None
    async def rollback() -> None
```

### Specific Repositories
```python
# Tenant Context
ITenantRepository(IRepository[Tenant])
IStoreRepository(IRepository[Store])

# Product Context
IOcsProductRepository(IRepository[OcsProduct])
IAccessoryRepository(IRepository[Accessory])

# Inventory Context
IInventoryRepository(IRepository[Inventory])
IBatchTrackingRepository(IRepository[BatchTracking])

# Purchase Order Context
IPurchaseOrderRepository(IRepository[PurchaseOrder])
ISupplierRepository(IRepository[Supplier])

# Order Context
IOrderRepository(IRepository[Order])
ICartRepository(IRepository[CartSession])

# Payment Context
IPaymentTransactionRepository(IRepository[PaymentTransaction])
IPaymentProviderRepository(IRepository[PaymentProvider])

# Delivery Context
IDeliveryRepository(IRepository[Delivery])
IDeliveryZoneRepository(IRepository[DeliveryZone])

# Review Context
IReviewRepository(IRepository[Review])
IRecommendationRepository(IRepository[Recommendation])

# Communication Context
IBroadcastRepository(IRepository[Broadcast])
ICommunicationPreferenceRepository(IRepository[CommunicationPreference])

# AI Context
IConversationRepository(IRepository[Conversation])
IAIPersonalityRepository(IRepository[AIPersonality])
```

## 4. SERVICE LAYER ARCHITECTURE

### Application Services
```python
# Tenant Management
class TenantService:
    - create_tenant(command: CreateTenantCommand) -> TenantDTO
    - update_tenant(command: UpdateTenantCommand) -> TenantDTO
    - get_tenant_hierarchy(tenant_id: UUID) -> TenantHierarchyDTO

class StoreService:
    - create_store(command: CreateStoreCommand) -> StoreDTO
    - update_store_settings(command: UpdateSettingsCommand) -> StoreDTO
    - activate_store(store_id: UUID) -> StoreDTO

# Inventory Management
class InventoryService:
    - adjust_stock(command: AdjustStockCommand) -> InventoryDTO
    - reserve_stock(command: ReserveStockCommand) -> ReservationDTO
    - process_po_receipt(command: ReceivePOCommand) -> List[InventoryDTO]
    - get_low_stock_items(store_id: UUID) -> List[InventoryDTO]

# Order Processing
class OrderService:
    - create_order(command: CreateOrderCommand) -> OrderDTO
    - update_order_status(command: UpdateStatusCommand) -> OrderDTO
    - calculate_order_total(order_id: UUID) -> OrderTotalDTO

# Payment Processing
class PaymentService:
    - process_payment(command: ProcessPaymentCommand) -> TransactionDTO
    - refund_payment(command: RefundCommand) -> RefundDTO
    - get_settlement_batch(date: datetime) -> SettlementDTO
```

### Domain Services
```python
# Pricing Domain Service
class PricingDomainService:
    - calculate_price(product: Product, rules: List[PricingRule]) -> Price
    - apply_discounts(order: Order, promotions: List[Promotion]) -> DiscountResult
    - validate_promotion_eligibility(promotion: Promotion, order: Order) -> bool

# Inventory Domain Service
class InventoryDomainService:
    - allocate_stock(items: List[OrderItem], inventory: List[Inventory]) -> AllocationResult
    - calculate_reorder_point(product: Product, history: List[Sale]) -> int
    - suggest_batch_for_fulfillment(sku: str, quantity: int) -> BatchSuggestion

# Delivery Domain Service
class DeliveryDomainService:
    - calculate_delivery_fee(zone: Zone, items: List[OrderItem]) -> Decimal
    - optimize_delivery_route(deliveries: List[Delivery]) -> RouteOptimization
    - validate_delivery_eligibility(address: Address, zone: Zone) -> bool
```

## 5. API ENDPOINT MAPPING

### RESTful API Structure
```
/api/v1/
├── tenants/
│   ├── GET    /                       # List tenants
│   ├── POST   /                       # Create tenant
│   ├── GET    /{id}                   # Get tenant
│   ├── PUT    /{id}                   # Update tenant
│   └── DELETE /{id}                   # Delete tenant
│
├── stores/
│   ├── GET    /                       # List stores
│   ├── POST   /                       # Create store
│   ├── GET    /{id}                   # Get store
│   ├── PUT    /{id}                   # Update store
│   ├── POST   /{id}/activate          # Activate store
│   └── POST   /{id}/deactivate        # Deactivate store
│
├── inventory/
│   ├── GET    /                       # List inventory
│   ├── GET    /{sku}                  # Get by SKU
│   ├── POST   /adjust                 # Adjust stock
│   ├── POST   /reserve                # Reserve stock
│   ├── POST   /release                # Release reservation
│   └── GET    /low-stock              # Get low stock items
│
├── purchase-orders/
│   ├── GET    /                       # List POs
│   ├── POST   /                       # Create PO
│   ├── GET    /{id}                   # Get PO
│   ├── POST   /{id}/receive           # Receive PO
│   └── POST   /{id}/cancel            # Cancel PO
│
├── orders/
│   ├── GET    /                       # List orders
│   ├── POST   /                       # Create order
│   ├── GET    /{id}                   # Get order
│   ├── PUT    /{id}/status            # Update status
│   └── POST   /{id}/cancel            # Cancel order
│
├── cart/
│   ├── POST   /sessions               # Create session
│   ├── GET    /sessions/{id}          # Get cart
│   ├── POST   /sessions/{id}/items    # Add item
│   ├── DELETE /sessions/{id}/items/{item_id} # Remove item
│   └── POST   /sessions/{id}/checkout # Convert to order
│
├── payments/
│   ├── POST   /process                # Process payment
│   ├── POST   /refund                 # Refund payment
│   ├── GET    /transactions/{id}      # Get transaction
│   └── GET    /settlements            # List settlements
│
├── deliveries/
│   ├── GET    /                       # List deliveries
│   ├── POST   /                       # Create delivery
│   ├── GET    /{id}                   # Get delivery
│   ├── PUT    /{id}/location          # Update location
│   └── POST   /{id}/complete          # Complete delivery
│
├── products/
│   ├── GET    /cannabis               # List cannabis products
│   ├── GET    /cannabis/{sku}         # Get cannabis product
│   ├── GET    /accessories             # List accessories
│   └── GET    /accessories/{id}       # Get accessory
│
├── reviews/
│   ├── GET    /                       # List reviews
│   ├── POST   /                       # Create review
│   ├── GET    /{id}                   # Get review
│   └── POST   /{id}/vote              # Vote on review
│
└── communications/
    ├── POST   /broadcasts             # Create broadcast
    ├── POST   /broadcasts/{id}/send   # Send broadcast
    ├── GET    /preferences/{user_id}  # Get preferences
    └── PUT    /preferences/{user_id}  # Update preferences
```

## 6. EVENT-DRIVEN ARCHITECTURE

### Domain Events
```python
@dataclass
class DomainEvent:
    event_id: UUID
    aggregate_id: UUID
    aggregate_type: str
    event_type: str
    event_data: Dict[str, Any]
    occurred_at: datetime
    tenant_id: UUID
    store_id: Optional[UUID]

# Event Bus Interface
class IEventBus:
    async def publish(event: DomainEvent) -> None
    async def subscribe(event_type: str, handler: Callable) -> None
```

### Event Handlers
```python
# Inventory Events → Update Search Index
class InventoryEventHandler:
    async def handle_stock_adjusted(event: StockAdjustedEvent):
        # Update search index
        # Notify low stock alerts
        # Update analytics

# Order Events → Trigger Workflows
class OrderEventHandler:
    async def handle_order_created(event: OrderCreatedEvent):
        # Reserve inventory
        # Process payment
        # Create delivery
        # Send confirmation email

# Payment Events → Update Order Status
class PaymentEventHandler:
    async def handle_payment_processed(event: PaymentProcessedEvent):
        # Update order status
        # Release cart session
        # Track conversion metrics
```

## 7. IMPLEMENTATION PHASES

### Phase 1: Core Domain Models (Week 1-2)
- [ ] Create domain models for all aggregates
- [ ] Implement value objects
- [ ] Define domain events
- [ ] Setup repository interfaces

### Phase 2: Infrastructure Layer (Week 3-4)
- [ ] Implement PostgreSQL repositories
- [ ] Setup Redis caching
- [ ] Configure message bus
- [ ] Implement unit of work

### Phase 3: Application Services (Week 5-6)
- [ ] Implement application services
- [ ] Create DTOs and mappers
- [ ] Setup command handlers
- [ ] Implement query handlers

### Phase 4: API Layer (Week 7-8)
- [ ] Migrate existing endpoints
- [ ] Implement new RESTful APIs
- [ ] Add GraphQL support
- [ ] Setup API versioning

### Phase 5: Event Handlers (Week 9-10)
- [ ] Implement event handlers
- [ ] Setup event sourcing
- [ ] Configure workflows
- [ ] Add compensating transactions

### Phase 6: Testing & Migration (Week 11-12)
- [ ] Unit tests for domain
- [ ] Integration tests for repositories
- [ ] API tests
- [ ] Data migration scripts

## 8. FILES IMPACTED

### To Be Refactored (Core Services)
```
/services/
├── inventory_service.py → /application/inventory/
├── order_service.py → /application/orders/
├── payment_service.py → /application/payments/
├── delivery_service.py → /application/delivery/
├── pricing_service.py → /domain/pricing/
├── recommendation_service.py → /application/recommendations/
└── communication/ → /application/communication/
```

### To Be Created (New Structure)
```
/src/Backend/
├── domain/
│   ├── aggregates/
│   ├── entities/
│   ├── value_objects/
│   ├── events/
│   └── services/
├── application/
│   ├── commands/
│   ├── queries/
│   ├── dtos/
│   └── services/
├── infrastructure/
│   ├── repositories/
│   ├── persistence/
│   ├── messaging/
│   └── caching/
└── api/
    ├── rest/
    ├── graphql/
    └── websocket/
```

### API Endpoints to Migrate
- All existing endpoints in `/api/` will be reorganized
- New versioning structure `/api/v1/`
- GraphQL endpoint at `/graphql`
- WebSocket endpoint at `/ws`

## 9. MONITORING & OBSERVABILITY

### Metrics to Track
- Aggregate creation/update rates
- Command success/failure rates
- Event processing latency
- Repository query performance
- Cache hit ratios

### Logging Strategy
- Structured logging with correlation IDs
- Domain event audit trail
- Command execution logs
- Error tracking with context

## 10. SECURITY CONSIDERATIONS

### Multi-Tenant Security
- Tenant context validation at every layer
- Row-level security in repositories
- API key scoping by tenant
- Audit all cross-tenant operations

### Data Protection
- Encrypt sensitive value objects
- PII handling in accordance with regulations
- Secure event storage
- API rate limiting per tenant

## CONCLUSION

This architecture refactoring plan provides a comprehensive roadmap for transforming the current system into a well-structured, domain-driven design. The plan is based on actual database tables and follows established patterns for scalability, maintainability, and testability.

Key Benefits:
- Clear separation of concerns
- Improved testability
- Better scalability
- Easier maintenance
- Domain knowledge preservation
- Event-driven extensibility

The implementation should be done incrementally, with each phase building upon the previous one, ensuring continuous delivery of value while maintaining system stability.