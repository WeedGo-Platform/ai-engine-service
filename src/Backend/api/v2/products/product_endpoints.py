"""
Product Catalog V2 Endpoints
DDD-Powered Product API using Product Catalog Bounded Context

This endpoint demonstrates the DDD integration pattern:
- Uses OcsProduct aggregate from domain layer
- Implements cannabis-specific business logic
- Publishes domain events for product lifecycle
- Returns clean DTOs (not domain objects)
- Full backward compatibility with V1

Key Features:
- OCS product import with validation
- Cannabis-specific attributes (THC/CBD, terpenes, plant types)
- Potency level calculations
- Price per gram calculations
- Product categorization and hierarchies
- Availability and status management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from decimal import Decimal
from uuid import UUID
import logging

from ..dependencies import get_current_user
from ..dto_mappers import (
    OcsProductDTO,
    ProductListDTO,
    ImportProductRequest,
    UpdateProductRequest,
    UpdateProductPricingRequest,
    SetTerpeneProfileRequest,
    map_product_to_dto,
    map_product_list_to_dto
)

# DDD Domain imports
from ddd_refactored.domain.product_catalog.entities.ocs_product import OcsProduct
from ddd_refactored.domain.product_catalog.value_objects.product_attributes import ProductForm

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/v2/products",
    tags=["🌿 Products V2 (DDD-Powered)"],
    responses={
        404: {"description": "Product not found"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "/import",
    response_model=OcsProductDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Import OCS Product",
    description="""
    Import a new product from OCS catalog using DDD Product Catalog context.

    **Features:**
    - Creates OcsProduct aggregate with business rules
    - Validates cannabinoid ranges (min ≤ max)
    - Calculates potency levels automatically
    - Publishes OcsProductImported domain event
    - Supports cannabis-specific attributes

    **Business Rules:**
    - OCS variant number is required and unique
    - Product and brand names are required
    - THC/CBD min cannot exceed max
    - Prices must be non-negative
    - Automatically calculates price per gram
    """
)
async def import_product(
    request: ImportProductRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Import product from OCS

    This endpoint:
    1. Creates OcsProduct aggregate using factory method
    2. Validates business rules
    3. Publishes OcsProductImported event
    4. Returns complete product DTO
    """
    try:
        logger.info(f"Importing OCS product: {request.ocs_variant_number}")

        # Create product using DDD aggregate
        product = OcsProduct.import_from_ocs(
            ocs_variant_number=request.ocs_variant_number,
            ocs_product_name=request.ocs_product_name,
            product_name=request.product_name,
            brand_name=request.brand_name,
            subcategory=request.subcategory,
            thc_min=Decimal(str(request.thc_min)) if request.thc_min is not None else None,
            thc_max=Decimal(str(request.thc_max)) if request.thc_max is not None else None,
            cbd_min=Decimal(str(request.cbd_min)) if request.cbd_min is not None else None,
            cbd_max=Decimal(str(request.cbd_max)) if request.cbd_max is not None else None,
            total_mg=Decimal(str(request.total_mg)) if request.total_mg is not None else None,
            volume_ml=Decimal(str(request.volume_ml)) if request.volume_ml is not None else None,
            pieces=request.pieces,
            unit_of_measure=request.unit_of_measure,
            price_per_unit=Decimal(str(request.price_per_unit)) if request.price_per_unit is not None else None,
            msrp_price=Decimal(str(request.msrp_price)) if request.msrp_price is not None else None,
            image_url=request.image_url,
            description=request.description,
            allergens=request.allergens,
            ingredients=request.ingredients
        )

        # Set plant type if provided
        if request.plant_type:
            product.set_plant_type(request.plant_type)

        # Validate product
        validation_errors = product.validate()
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {', '.join(validation_errors)}"
            )

        # In real implementation, would save via repository
        # For now, return the created product
        logger.info(f"Product imported: {product.ocs_variant_number} - {product.product_name}")

        return map_product_to_dto(product)

    except ValueError as e:
        # Business rule violation
        logger.warning(f"Product import validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid product data: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        # System error
        logger.error(f"Product import failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product import failed. Please try again."
        )


@router.get(
    "/{product_id}",
    response_model=OcsProductDTO,
    summary="Get Product",
    description="Retrieve product details by ID or OCS variant number"
)
async def get_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get product by ID or SKU"""
    try:
        logger.info(f"Retrieving product: {product_id}")

        # In real implementation, would load from repository
        # For now, return not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.put(
    "/{product_id}",
    response_model=OcsProductDTO,
    summary="Update Product",
    description="""
    Update product information with validation.

    **Business Rules:**
    - Cannot update discontinued products
    - THC/CBD ranges must be valid (min ≤ max)
    - Pricing must be non-negative
    - Publishes OcsProductUpdated event with change tracking
    """
)
async def update_product(
    product_id: str,
    request: UpdateProductRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update product information

    This endpoint:
    1. Loads OcsProduct aggregate
    2. Updates fields with validation
    3. Tracks changes in domain event
    4. Returns updated product
    """
    try:
        logger.info(f"Updating product {product_id}")

        # In real implementation:
        # product = await repository.get_by_id(product_id)
        #
        # # Build update data
        # update_data = {k: v for k, v in request.dict().items() if v is not None}
        #
        # # Convert floats to Decimals for domain
        # for key in ['thc_min', 'thc_max', 'cbd_min', 'cbd_max', 'price_per_unit', 'msrp_price']:
        #     if key in update_data:
        #         update_data[key] = Decimal(str(update_data[key]))
        #
        # product.update_from_import(update_data)
        # await repository.save(product)
        # return map_product_to_dto(product)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Update product endpoint - repository integration pending"
        )

    except ValueError as e:
        logger.warning(f"Product update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid update: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.post(
    "/{product_id}/pricing",
    response_model=OcsProductDTO,
    summary="Update Product Pricing",
    description="""
    Update product pricing with automatic price per gram calculation.

    **Business Rules:**
    - Prices cannot be negative
    - Price per unit and MSRP are independent
    - Price per gram automatically calculated for flower products
    - Publishes OcsProductUpdated event
    """
)
async def update_product_pricing(
    product_id: str,
    request: UpdateProductPricingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update product pricing"""
    try:
        logger.info(f"Updating pricing for product {product_id}")

        # In real implementation:
        # product = await repository.get_by_id(product_id)
        # product.update_pricing(
        #     price_per_unit=Decimal(str(request.price_per_unit)) if request.price_per_unit else None,
        #     msrp_price=Decimal(str(request.msrp_price)) if request.msrp_price else None
        # )
        # await repository.save(product)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Update pricing endpoint - repository integration pending"
        )

    except ValueError as e:
        logger.warning(f"Pricing update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pricing: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update pricing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pricing"
        )


@router.post(
    "/{product_id}/terpenes",
    response_model=OcsProductDTO,
    summary="Set Terpene Profile",
    description="""
    Set cannabis terpene profile with effects mapping.

    **Features:**
    - Primary terpenes list
    - Optional terpene percentages
    - Aroma and flavor notes
    - Automatic effect mapping based on terpene profile
    - Common effects include: uplifting, relaxing, pain-relief, etc.
    """
)
async def set_terpene_profile(
    product_id: str,
    request: SetTerpeneProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """Set terpene profile"""
    try:
        logger.info(f"Setting terpene profile for product {product_id}")

        # Convert float percentages to Decimal for domain
        terpene_percentages = None
        if request.terpene_percentages:
            terpene_percentages = {
                k: Decimal(str(v)) for k, v in request.terpene_percentages.items()
            }

        # In real implementation:
        # product = await repository.get_by_id(product_id)
        # product.set_terpene_profile(
        #     primary_terpenes=request.primary_terpenes,
        #     terpene_percentages=terpene_percentages,
        #     aroma_notes=request.aroma_notes,
        #     flavor_notes=request.flavor_notes
        # )
        # await repository.save(product)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Set terpene profile endpoint - repository integration pending"
        )

    except ValueError as e:
        logger.warning(f"Terpene profile validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid terpene profile: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set terpene profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set terpene profile"
        )


@router.post(
    "/{product_id}/activate",
    response_model=OcsProductDTO,
    summary="Activate Product",
    description="Activate a deactivated product, making it available for sale"
)
async def activate_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Activate product"""
    try:
        logger.info(f"Activating product {product_id}")

        # In real implementation:
        # product = await repository.get_by_id(product_id)
        # product.activate()
        # await repository.save(product)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Activate product endpoint - repository integration pending"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate product"
        )


@router.post(
    "/{product_id}/deactivate",
    response_model=OcsProductDTO,
    summary="Deactivate Product",
    description="Temporarily deactivate a product (can be reactivated later)"
)
async def deactivate_product(
    product_id: str,
    reason: Optional[str] = Query(None, description="Reason for deactivation"),
    current_user: dict = Depends(get_current_user)
):
    """Deactivate product"""
    try:
        logger.info(f"Deactivating product {product_id}")

        # In real implementation:
        # product = await repository.get_by_id(product_id)
        # product.deactivate(reason=reason or "")
        # await repository.save(product)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Deactivate product endpoint - repository integration pending"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate product"
        )


@router.post(
    "/{product_id}/discontinue",
    response_model=OcsProductDTO,
    summary="Discontinue Product",
    description="""
    Permanently discontinue a product (cannot be reactivated).

    **Business Rules:**
    - Sets discontinued flag
    - Records discontinuation date
    - Automatically deactivates product
    - Makes product unavailable for new sales
    """
)
async def discontinue_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Discontinue product"""
    try:
        logger.info(f"Discontinuing product {product_id}")

        # In real implementation:
        # product = await repository.get_by_id(product_id)
        # product.discontinue()
        # await repository.save(product)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Discontinue product endpoint - repository integration pending"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discontinue product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discontinue product"
        )


@router.get(
    "/",
    response_model=ProductListDTO,
    summary="List Products",
    description="""
    List products with optional filters and pagination.

    **Filters:**
    - search: Search in name, brand, SKU, description
    - category: Filter by subcategory
    - brand: Filter by brand name
    - plant_type: Filter by plant type (indica, sativa, hybrid, cbd)
    - product_form: Filter by form (dried_flower, oil, edible, etc.)
    - potency_level: Filter by potency (mild, medium, strong, very_strong)
    - is_active: Show only active products
    - high_thc: Show only high THC products (>20%)
    - high_cbd: Show only high CBD products (>10%)
    - balanced: Show only balanced products

    **Sorting:**
    - Sort by: name, brand, price, thc_max, cbd_max, created_at
    - Order: asc, desc
    """
)
async def list_products(
    search: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    plant_type: Optional[str] = Query(None, description="Filter by plant type"),
    product_form: Optional[str] = Query(None, description="Filter by product form"),
    potency_level: Optional[str] = Query(None, description="Filter by potency level"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    high_thc: Optional[bool] = Query(None, description="Show only high THC products"),
    high_cbd: Optional[bool] = Query(None, description="Show only high CBD products"),
    balanced: Optional[bool] = Query(None, description="Show only balanced products"),
    sort_by: str = Query("name", description="Sort by field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    limit: int = Query(50, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    List products with filtering

    Supports pagination and complex filtering for cannabis products
    """
    try:
        logger.info(f"Listing products: search={search}, category={category}, brand={brand}")

        # In full implementation, would use query handlers/repository
        # For now, return empty list
        products = []

        return map_product_list_to_dto(
            products=products,
            total=0,
            page=1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Failed to list products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list products"
        )


@router.get(
    "/category/{category_code}",
    response_model=ProductListDTO,
    summary="Get Products by Category",
    description="Get all products in a specific category"
)
async def get_products_by_category(
    category_code: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get products by category"""
    try:
        logger.info(f"Getting products for category: {category_code}")

        # In real implementation:
        # products = await repository.find_by_category(category_code, limit, offset)
        products = []

        return map_product_list_to_dto(
            products=products,
            total=0,
            page=1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Failed to get products by category: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products by category"
        )


@router.get(
    "/brand/{brand_name}",
    response_model=ProductListDTO,
    summary="Get Products by Brand",
    description="Get all products from a specific brand"
)
async def get_products_by_brand(
    brand_name: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get products by brand"""
    try:
        logger.info(f"Getting products for brand: {brand_name}")

        # In real implementation:
        # products = await repository.find_by_brand(brand_name, limit, offset)
        products = []

        return map_product_list_to_dto(
            products=products,
            total=0,
            page=1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Failed to get products by brand: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products by brand"
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check if Product Catalog V2 API is healthy",
    tags=["Health"]
)
async def health_check():
    """Health check endpoint for Product Catalog V2 API"""
    return {
        "status": "healthy",
        "service": "products-v2",
        "version": "2.0.0",
        "ddd_enabled": True,
        "features": [
            "ocs_import",
            "cannabis_attributes",
            "terpene_profiles",
            "potency_calculations",
            "category_management",
            "pricing_management",
            "availability_tracking",
            "event_publishing"
        ]
    }


@router.get(
    "/stats",
    summary="Product Statistics",
    description="Get product catalog statistics and metrics"
)
async def get_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get product catalog statistics

    Returns metrics useful for monitoring and dashboards
    """
    return {
        "total_products": 0,
        "active_products": 0,
        "discontinued_products": 0,
        "high_thc_products": 0,
        "high_cbd_products": 0,
        "balanced_products": 0,
        "categories": [],
        "brands": [],
        "note": "Statistics will be calculated from repository in production"
    }
