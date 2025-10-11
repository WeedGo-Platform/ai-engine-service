"""
Pricing & Promotions V2 API Endpoints

DDD-powered pricing and promotional campaign management using the Pricing & Promotions bounded context.

Features:
- Dynamic pricing strategies (cost-plus, competitive, value-based, tiered)
- Bulk/volume discounts with multi-tier pricing
- Time-based pricing schedules (happy hour, weekend specials)
- Promotional campaigns with discount codes
- BOGO (Buy One Get One) promotions
- Customer segmentation and targeting
- Discount code generation and tracking
- Promotion stacking controls
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from ..dependencies import get_current_user
from ..dto_mappers import (
    PricingRuleDTO, PromotionDTO,
    PricingRuleListDTO, PromotionListDTO,
    CreatePricingRuleRequest, AddProductPriceRequest, UpdateProductPriceRequest,
    AddBulkDiscountRequest, AddPriceScheduleRequest,
    CreatePromotionRequest, GenerateDiscountCodeRequest, ApplyDiscountCodeRequest,
    UpdatePromotionStatusRequest, CalculateDiscountRequest,
    map_pricing_rule_to_dto, map_pricing_rule_list_to_dto,
    map_promotion_to_dto, map_promotion_list_to_dto
)

from ddd_refactored.domain.pricing_promotions.entities.pricing_rule import (
    PricingRule, PricingStrategy
)
from ddd_refactored.domain.pricing_promotions.entities.promotion import (
    Promotion, PromotionStatus, DiscountType, ApplicableProducts, CustomerSegment
)
from ddd_refactored.domain.pricing_promotions.value_objects.pricing_types import (
    PricingTier, DiscountCondition, PriceSchedule, BulkDiscountRule
)

router = APIRouter(
    prefix="/v2/pricing-promotions",
    tags=["💰 Pricing & Promotions V2 (DDD)"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# Pricing Rule Endpoints
# ============================================================================

@router.post("/pricing-rules", response_model=PricingRuleDTO, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    request: CreatePricingRuleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new pricing rule

    Pricing strategies:
    - cost_plus: Base price = cost + (cost * markup_percentage)
    - competitive: Match or beat competitor pricing
    - value_based: Price based on perceived value
    - dynamic: Real-time price adjustments based on demand
    - tiered: Volume-based pricing with discount tiers
    """
    try:
        # Get tenant_id from user context
        tenant_id = UUID(current_user.get("tenant_id")) if current_user.get("tenant_id") else None

        strategy = PricingStrategy(request.pricing_strategy)

        pricing_rule = PricingRule.create(
            store_id=UUID(request.store_id),
            tenant_id=tenant_id,
            rule_name=request.rule_name,
            pricing_strategy=strategy,
            default_markup_percentage=Decimal(str(request.default_markup_percentage))
        )

        # TODO: Save to repository

        return map_pricing_rule_to_dto(pricing_rule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pricing strategy: {str(e)}"
        )


@router.get("/pricing-rules/{rule_id}", response_model=PricingRuleDTO)
async def get_pricing_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a pricing rule by ID"""
    # TODO: Load from repository
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Pricing rule {rule_id} not found"
    )


@router.get("/pricing-rules", response_model=PricingRuleListDTO)
async def list_pricing_rules(
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user)
):
    """List all pricing rules with optional filters"""
    # TODO: Load from repository with filters

    # Placeholder response
    return map_pricing_rule_list_to_dto(
        rules=[],
        total=0,
        page=page,
        page_size=page_size
    )


@router.post("/pricing-rules/{rule_id}/activate", response_model=PricingRuleDTO)
async def activate_pricing_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Activate a pricing rule

    Activated pricing rules will be used for calculating product prices.
    """
    # TODO: Load from repository, activate, save
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Pricing rule {rule_id} not found"
    )


@router.post("/pricing-rules/{rule_id}/deactivate", response_model=PricingRuleDTO)
async def deactivate_pricing_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deactivate a pricing rule

    Deactivated pricing rules will not be used for calculating prices.
    """
    # TODO: Load from repository, deactivate, save
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Pricing rule {rule_id} not found"
    )


@router.post("/pricing-rules/{rule_id}/products", response_model=PricingRuleDTO, status_code=status.HTTP_201_CREATED)
async def add_product_price(
    rule_id: str,
    request: AddProductPriceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add product price to pricing rule

    The base price is calculated as:
    base_price = cost_price * (1 + markup_percentage / 100)

    If markup_percentage is not provided, the rule's default markup is used.
    """
    try:
        # TODO: Load pricing rule from repository
        # pricing_rule.add_product_price(
        #     product_sku=request.product_sku,
        #     product_name=request.product_name,
        #     cost_price=Decimal(str(request.cost_price)),
        #     markup_percentage=Decimal(str(request.markup_percentage)) if request.markup_percentage else None
        # )
        # TODO: Save to repository

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/pricing-rules/{rule_id}/products/{product_sku}", response_model=PricingRuleDTO)
async def update_product_price(
    rule_id: str,
    product_sku: str,
    request: UpdateProductPriceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update product price in pricing rule

    You can update either cost_price, markup_percentage, or both.
    The base price will be recalculated automatically.
    """
    try:
        # TODO: Load pricing rule from repository
        # if request.cost_price or request.markup_percentage:
        #     pricing_rule.update_product_price(
        #         product_sku=product_sku,
        #         cost_price=Decimal(str(request.cost_price)) if request.cost_price else None,
        #         markup_percentage=Decimal(str(request.markup_percentage)) if request.markup_percentage else None
        #     )
        # TODO: Save to repository

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/pricing-rules/{rule_id}/products/{product_sku}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_price(
    rule_id: str,
    product_sku: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove product price from pricing rule"""
    # TODO: Load pricing rule, remove product price, save
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Pricing rule {rule_id} not found"
    )


@router.post("/pricing-rules/{rule_id}/products/{product_sku}/bulk-discount", response_model=PricingRuleDTO)
async def add_bulk_discount(
    rule_id: str,
    product_sku: str,
    request: AddBulkDiscountRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add bulk discount rule to product

    Bulk discounts apply when customers purchase large quantities.

    Example tiers:
    - Buy 10-24 units: 10% off
    - Buy 25-49 units: 15% off
    - Buy 50+ units: 20% off

    Each tier can have either a discount_percentage or a fixed_price.
    """
    try:
        # TODO: Load pricing rule from repository
        # Convert tier dicts to PricingTier value objects
        tiers = []
        for tier_data in request.tiers:
            tier = PricingTier(
                min_quantity=Decimal(str(tier_data.get("min_quantity"))),
                max_quantity=Decimal(str(tier_data.get("max_quantity"))) if tier_data.get("max_quantity") else None,
                discount_percentage=Decimal(str(tier_data.get("discount_percentage"))) if tier_data.get("discount_percentage") else None,
                fixed_price=Decimal(str(tier_data.get("fixed_price"))) if tier_data.get("fixed_price") else None
            )
            tiers.append(tier)

        # pricing_rule.add_bulk_discount(product_sku=product_sku, tiers=tiers)
        # TODO: Save to repository

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/pricing-rules/{rule_id}/products/{product_sku}/schedule", response_model=PricingRuleDTO)
async def add_price_schedule(
    rule_id: str,
    product_sku: str,
    request: AddPriceScheduleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add time-based price schedule to product

    Price schedules allow dynamic pricing based on time:
    - Happy Hour: 15% off from 3-6pm, Monday-Friday
    - Weekend Special: 20% off all day Saturday-Sunday
    - Flash Sale: $5 off for 24 hours

    Schedules can be:
    - One-time: Set start_time and end_time only
    - Recurring: Add days_of_week and/or start_hour/end_hour

    When a schedule is active, the discount is applied to the base price.
    """
    try:
        # TODO: Load pricing rule from repository
        # discount_type_enum = DiscountType(request.discount_type)

        # schedule = PriceSchedule(
        #     name=request.name,
        #     discount_type=discount_type_enum,
        #     discount_value=Decimal(str(request.discount_value)),
        #     start_time=request.start_time,
        #     end_time=request.end_time,
        #     days_of_week=request.days_of_week,
        #     start_hour=request.start_hour,
        #     end_hour=request.end_hour
        # )

        # pricing_rule.add_price_schedule(product_sku=product_sku, schedule=schedule)
        # TODO: Save to repository

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Promotion Endpoints
# ============================================================================

@router.post("/promotions", response_model=PromotionDTO, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    request: CreatePromotionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new promotional campaign

    Discount types:
    - percentage: % off the order (e.g., 25% off)
    - fixed_amount: Fixed $ off (e.g., $10 off)
    - bogo: Buy X get Y free (e.g., Buy 2 Get 1 Free)
    - bulk_discount: Volume-based discount
    - bundle: Special bundle pricing

    Product applicability:
    - all_products: Apply to entire order
    - specific_skus: Apply to specific products only
    - category: Apply to product category
    - brand: Apply to specific brand
    - type: Apply to product type (cannabis, accessories, etc.)

    Customer targeting:
    - all: All customers
    - new_customer: First-time customers only
    - returning: Returning customers
    - vip: VIP/loyalty members
    - medical: Medical cannabis patients
    - recreational: Recreational customers
    """
    try:
        # Get tenant_id from user context
        tenant_id = UUID(current_user.get("tenant_id")) if current_user.get("tenant_id") else None

        discount_type = DiscountType(request.discount_type)
        applicable_to = ApplicableProducts(request.applicable_to)
        customer_segment = CustomerSegment(request.customer_segment)

        # Validate BOGO configuration
        if discount_type == DiscountType.BOGO:
            if not request.bogo_buy_quantity or not request.bogo_get_quantity:
                raise ValueError("BOGO promotions require bogo_buy_quantity and bogo_get_quantity")

        promotion = Promotion.create(
            store_id=UUID(request.store_id),
            tenant_id=tenant_id,
            promotion_name=request.promotion_name,
            discount_type=discount_type,
            discount_value=Decimal(str(request.discount_value)),
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Set optional fields
        if request.description:
            promotion.description = request.description

        if request.bogo_buy_quantity and request.bogo_get_quantity:
            promotion.bogo_buy_quantity = request.bogo_buy_quantity
            promotion.bogo_get_quantity = request.bogo_get_quantity

        promotion.applicable_to = applicable_to
        if request.specific_skus:
            promotion.specific_skus = set(request.specific_skus)
        if request.category:
            promotion.category = request.category
        if request.brand:
            promotion.brand = request.brand

        promotion.customer_segment = customer_segment
        promotion.can_stack = request.can_stack
        promotion.priority = request.priority

        # Save to repository
        from ..dependencies import get_promotion_repository
        repository = await get_promotion_repository()
        saved_promotion = await repository.save(promotion)

        return map_promotion_to_dto(saved_promotion)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/promotions/{promotion_id}", response_model=PromotionDTO)
async def get_promotion(
    promotion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a promotion by ID"""
    from ..dependencies import get_promotion_repository

    repository = await get_promotion_repository()
    promotion = await repository.get_by_id(UUID(promotion_id))

    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promotion {promotion_id} not found"
        )

    return map_promotion_to_dto(promotion)


@router.get("/promotions", response_model=PromotionListDTO)
async def list_promotions(
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    status: Optional[str] = Query(None, description="Filter by status (draft, scheduled, active, paused, expired, cancelled)"),
    discount_type: Optional[str] = Query(None, description="Filter by discount type"),
    is_active_now: Optional[bool] = Query(None, description="Filter by currently active"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user)
):
    """List all promotions with optional filters"""
    from ..dependencies import get_promotion_repository

    repository = await get_promotion_repository()

    # Convert filters
    store_uuid = UUID(store_id) if store_id else None
    status_filter = PromotionStatus(status.upper()) if status else None

    # Calculate skip
    skip = (page - 1) * page_size

    # Get promotions from repository
    if is_active_now:
        # Get currently active promotions
        promotions = await repository.get_active_promotions(
            store_id=store_uuid or UUID(current_user.get("store_id", "00000000-0000-0000-0000-000000000000")),
            current_time=datetime.utcnow()
        )
        # Apply pagination manually for active promotions
        total = len(promotions)
        promotions = promotions[skip:skip + page_size]
    else:
        # Get all promotions with filters
        promotions = await repository.list_all(
            store_id=store_uuid,
            status=status_filter,
            skip=skip,
            limit=page_size
        )
        # For total count, we'd need a separate count query
        # For now, assume the list size as total (limitation)
        total = len(promotions) + skip

    return map_promotion_list_to_dto(
        promotions=promotions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/promotions/{promotion_id}/status", response_model=PromotionDTO)
async def update_promotion_status(
    promotion_id: str,
    request: UpdatePromotionStatusRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update promotion status

    Actions:
    - schedule: Move from draft to scheduled
    - activate: Start the promotion immediately
    - pause: Temporarily pause an active promotion
    - resume: Resume a paused promotion
    - expire: Mark promotion as expired
    - cancel: Cancel the promotion

    Status transitions:
    - draft → scheduled → active → expired
    - active → paused → active
    - any → cancelled
    """
    try:
        from ..dependencies import get_promotion_repository

        repository = await get_promotion_repository()
        promotion = await repository.get_by_id(UUID(promotion_id))

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Promotion {promotion_id} not found"
            )

        action = request.action.lower()

        # Map actions to domain methods
        if action == "schedule":
            promotion.schedule()
        elif action == "activate":
            promotion.activate()
        elif action == "pause":
            promotion.pause()
        elif action == "resume":
            promotion.resume()
        elif action == "expire":
            promotion.expire()
        elif action == "cancel":
            promotion.cancel()
        else:
            raise ValueError(f"Invalid action: {action}")

        # Save updated promotion
        updated_promotion = await repository.save(promotion)

        return map_promotion_to_dto(updated_promotion)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/promotions/{promotion_id}/discount-codes", response_model=PromotionDTO, status_code=status.HTTP_201_CREATED)
async def generate_discount_code(
    promotion_id: str,
    request: GenerateDiscountCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a discount code for promotion

    Discount codes allow you to:
    - Track promotion usage
    - Limit redemptions (max_uses)
    - Target specific customer segments
    - Create personalized codes for specific customers

    The code will be automatically uppercased.

    Examples:
    - WELCOME25: 25% off for new customers (max 100 uses)
    - VIP50: $50 off for VIP members (unlimited uses)
    - JOHN-SPECIAL: Personalized code for customer John
    """
    try:
        customer_segment = CustomerSegment(request.customer_segment)

        # TODO: Load promotion from repository
        # promotion.generate_discount_code(
        #     code=request.code,
        #     max_uses=request.max_uses,
        #     customer_segment=customer_segment,
        #     specific_customer_id=UUID(request.specific_customer_id) if request.specific_customer_id else None
        # )
        # TODO: Save to repository

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promotion {promotion_id} not found"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/promotions/{promotion_id}/apply-code", response_model=Dict[str, Any])
async def apply_discount_code(
    promotion_id: str,
    request: ApplyDiscountCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Apply a discount code to validate and track usage

    This endpoint:
    - Validates the discount code
    - Checks eligibility (customer segment, max uses, etc.)
    - Increments usage counter
    - Returns discount amount

    Returns:
    - valid: Whether the code is valid
    - discount_amount: Calculated discount amount
    - message: Validation message or error
    """
    try:
        # TODO: Load promotion from repository
        # TODO: Validate and apply discount code
        # discount_amount = promotion.apply_discount_code(
        #     code=request.code,
        #     customer_id=UUID(request.customer_id),
        #     order_amount=Decimal(str(request.order_amount))
        # )
        # TODO: Save to repository

        # Placeholder response
        return {
            "valid": False,
            "discount_amount": 0.0,
            "message": f"Promotion {promotion_id} not found"
        }

    except ValueError as e:
        return {
            "valid": False,
            "discount_amount": 0.0,
            "message": str(e)
        }


@router.post("/promotions/{promotion_id}/calculate", response_model=Dict[str, Any])
async def calculate_discount(
    promotion_id: str,
    request: CalculateDiscountRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate discount amount for an order

    This endpoint calculates the discount without applying it.
    Useful for showing preview/estimated savings to customers.

    Returns:
    - discount_amount: Calculated discount
    - final_amount: Order amount after discount
    - discount_percentage: Effective discount percentage
    - promotion_name: Name of the promotion
    """
    try:
        # TODO: Load promotion from repository
        # discount_amount = promotion.calculate_discount(
        #     base_amount=Decimal(str(request.order_amount)),
        #     quantity=request.quantity
        # )

        # Placeholder calculation
        discount_amount = 0.0
        order_amount = request.order_amount
        final_amount = order_amount - discount_amount
        discount_percentage = (discount_amount / order_amount * 100) if order_amount > 0 else 0

        return {
            "discount_amount": float(discount_amount),
            "final_amount": float(final_amount),
            "discount_percentage": float(discount_percentage),
            "promotion_name": "Promotion name here",
            "requires_code": False
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Pricing & Promotions V2",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats")
async def get_statistics(
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get pricing and promotions statistics

    Returns:
    - Total pricing rules (active/inactive)
    - Total promotions (by status)
    - Total discount codes generated
    - Total discount amount given
    - Average discount percentage
    """
    from ..dependencies import get_promotion_repository

    repository = await get_promotion_repository()

    # Convert store_id to UUID if provided
    store_uuid = UUID(store_id) if store_id else None

    # Get statistics from repository
    stats = await repository.get_statistics(
        store_id=store_uuid
    )

    return stats
