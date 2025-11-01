"""
Review and Rating System API Endpoints

⚠️ COMPATIBILITY NOTICE:
V2 Customer Engagement API is now available with DDD architecture!

**New V2 Endpoints (Recommended):**
- /api/v2/customer-engagement/reviews - Full DDD-powered review lifecycle
- /api/v2/customer-engagement/products/{sku}/reviews - Product reviews with advanced filtering
- /api/v2/customer-engagement/products/{sku}/reviews/stats - Review statistics

**Key V2 Improvements:**
✅ Domain-Driven Design with comprehensive business rules
✅ Review moderation workflow (pending → approved/rejected/flagged → published)
✅ Detailed rating breakdown (overall, quality, value, potency, flavor)
✅ Helpful vote tracking with duplicate prevention
✅ Store responses to customer reviews
✅ Reviewer badges and reputation system (Top/Frequent/Regular Reviewer)
✅ Review editing within 7-day window
✅ Cannabis-specific ratings (potency, flavor)
✅ Photo and video attachments
✅ Flag reasons for content moderation
✅ Domain events for complete audit trails

**Migration Path:**
- V1 endpoints remain functional for backward compatibility
- New integrations should use V2 endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile, Form, Header
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import uuid
import asyncpg
from enum import Enum

from database.connection import get_db_pool, get_db

# Import auth functions (handle different possible locations)
try:
    from core.auth import get_current_user, get_current_user_optional
except ImportError:
    try:
        from api.customer_auth import get_current_user, get_current_user_optional
    except ImportError:
        # Create simple auth dependencies if not available
        async def get_current_user(
            authorization: Optional[str] = Header(None),
            x_user_id: Optional[str] = Header(None, alias="X-User-Id")
        ):
            if x_user_id:
                return {"id": x_user_id}
            raise HTTPException(401, "Unauthorized")

        async def get_current_user_optional(
            authorization: Optional[str] = Header(None),
            x_user_id: Optional[str] = Header(None, alias="X-User-Id")
        ):
            if x_user_id:
                return {"id": x_user_id}
            return None

# S3 upload stub - replace with actual implementation if needed
async def upload_to_s3(file_data, key: str, content_type: str):
    # Stub implementation - would upload to S3 in production
    return f"https://s3.amazonaws.com/weedgo-reviews/{key}"

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

# =============================================
# Pydantic Models
# =============================================

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"

class VoteType(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"

class ReviewAttributeName(str, Enum):
    EFFECTS = "effects"
    FLAVOR = "flavor"
    POTENCY = "potency"
    AROMA = "aroma"
    VALUE = "value"
    QUALITY = "quality"

class ReviewAttribute(BaseModel):
    attribute_name: ReviewAttributeName
    attribute_value: Optional[str]
    rating: int = Field(ge=1, le=5)

class ReviewSubmission(BaseModel):
    sku: str
    order_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str]
    is_recommended: bool = True
    attributes: Optional[List[ReviewAttribute]] = []

    @validator('review_text')
    def validate_review_text(cls, v):
        if v and len(v) > 5000:
            raise ValueError('Review text must be less than 5000 characters')
        return v

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str]
    is_recommended: Optional[bool]
    attributes: Optional[List[ReviewAttribute]]

class ReviewVote(BaseModel):
    review_id: str
    vote_type: VoteType

class ReviewResponse(BaseModel):
    id: str
    sku: str
    user_id: str
    user_name: str
    order_id: Optional[str]
    rating: int
    title: Optional[str]
    review_text: Optional[str]
    is_recommended: bool
    is_verified_purchase: bool
    helpful_count: int
    not_helpful_count: int
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime
    attributes: List[Dict[str, Any]]
    media: List[Dict[str, Any]]
    user_vote: Optional[str] = None

class ProductRatingResponse(BaseModel):
    sku: str
    average_rating: float
    total_reviews: int
    rating_distribution: Dict[str, int]
    verified_purchase_count: int
    recommended_percentage: float
    recent_reviews: List[ReviewResponse]

# =============================================
# Helper Functions
# =============================================

async def check_review_exists(db_or_connection, user_id: str, sku: str) -> bool:
    """Check if user has already reviewed this product"""
    query = """
        SELECT COUNT(*) FROM customer_reviews
        WHERE user_id = $1 AND sku = $2
    """
    result = await db_or_connection.fetchval(query, uuid.UUID(user_id), sku)
    return result > 0

async def get_user_display_name(pool_or_conn, user_id: str) -> str:
    """Get formatted user display name for reviews"""
    # If it's a pool, acquire a connection
    if hasattr(pool_or_conn, 'acquire'):
        async with pool_or_conn.acquire() as conn:
            query = """
                SELECT first_name, last_name
                FROM users
                WHERE id = $1
            """
            user = await conn.fetchrow(query, uuid.UUID(user_id))
            if user:
                return f"{user['first_name']} {user['last_name'][0] if user['last_name'] else ''}."
            return "Anonymous"
    else:
        # It's already a connection
        query = """
            SELECT first_name, last_name
            FROM users
            WHERE id = $1
        """
        user = await pool_or_conn.fetchrow(query, uuid.UUID(user_id))
        if user:
            return f"{user['first_name']} {user['last_name'][0] if user['last_name'] else ''}."
        return "Anonymous"

# =============================================
# Review Endpoints
# =============================================

@router.get("/products/{sku}/ratings", response_model=ProductRatingResponse)
async def get_product_ratings(
    sku: str,
    current_user=Depends(get_current_user_optional)
):
    """Get product ratings and review summary"""

    # Get database pool connection
    pool = await get_db_pool()
    async with pool.acquire() as db:
        # Get rating summary from materialized view
        query = """
        SELECT
            sku,
            average_rating,
            total_reviews,
            five_star_count,
            four_star_count,
            three_star_count,
            two_star_count,
            one_star_count,
            verified_percentage,
            recommended_percentage,
            recent_reviews,
            top_positive_review,
            top_critical_review
        FROM review_summary_view
        WHERE sku = $1
    """

        summary = await db.fetchrow(query, sku)

        if not summary:
            # Return empty rating if product hasn't been reviewed
            return ProductRatingResponse(
            sku=sku,
            average_rating=0,
            total_reviews=0,
            rating_distribution={"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
            verified_purchase_count=0,
            recommended_percentage=0,
                recent_reviews=[]
            )

        # Build rating distribution
        rating_distribution = {
        "5": summary['five_star_count'] or 0,
        "4": summary['four_star_count'] or 0,
        "3": summary['three_star_count'] or 0,
        "2": summary['two_star_count'] or 0,
        "1": summary['one_star_count'] or 0
    }

        # Parse recent reviews from JSONB
        recent_reviews = []
    if summary['recent_reviews']:
        for review_data in summary['recent_reviews']:
            recent_reviews.append(ReviewResponse(
                id=review_data['id'],
                sku=sku,
                user_id="",  # Hidden for privacy
                user_name=review_data['user_name'],
                order_id=None,  # Hidden for privacy
                rating=review_data['rating'],
                title=review_data.get('title'),
                review_text=review_data.get('review_text'),
                is_recommended=True,  # Not in summary, default
                is_verified_purchase=review_data['is_verified_purchase'],
                helpful_count=review_data['helpful_count'],
                not_helpful_count=0,  # Not in summary
                status=ReviewStatus.APPROVED,
                created_at=review_data['created_at'],
                updated_at=review_data['created_at'],
                attributes=[],
                media=[]
            ))

        return ProductRatingResponse(
            sku=sku,
            average_rating=float(summary['average_rating'] or 0),
            total_reviews=summary['total_reviews'] or 0,
            rating_distribution=rating_distribution,
            verified_purchase_count=int(summary['verified_percentage'] * summary['total_reviews'] / 100) if summary['total_reviews'] else 0,
            recommended_percentage=float(summary['recommended_percentage'] or 0),
            recent_reviews=recent_reviews
        )

@router.get("/products/{sku}/reviews", response_model=List[ReviewResponse])
async def get_product_reviews(
    sku: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    rating: Optional[int] = Query(None, ge=1, le=5),
    verified_only: bool = False,
    sort: str = Query("helpful", regex="^(helpful|recent|rating_high|rating_low)$"),
    current_user=Depends(get_current_user_optional)
):
    """Get paginated reviews for a product"""

    # Get database pool connection
    pool = await get_db_pool()
    async with pool.acquire() as db:
        offset = (page - 1) * limit

        # Build query with filters
        conditions = ["cr.sku = $1", "cr.status = 'approved'"]
        params = [sku]
        param_count = 1

        if rating:
            param_count += 1
            conditions.append(f"cr.rating = ${param_count}")
            params.append(rating)

        if verified_only:
            conditions.append("cr.is_verified_purchase = true")

        # Determine sort order
        order_by = {
            "helpful": "cr.helpful_count DESC, cr.created_at DESC",
            "recent": "cr.created_at DESC",
            "rating_high": "cr.rating DESC, cr.created_at DESC",
            "rating_low": "cr.rating ASC, cr.created_at DESC"
        }[sort]

        query = f"""
            SELECT
                cr.id,
                cr.sku,
                cr.user_id,
                cr.rating,
                cr.title,
                cr.review_text,
                cr.is_recommended,
                cr.is_verified_purchase,
                cr.helpful_count,
                cr.not_helpful_count,
                cr.status,
                cr.created_at,
                cr.updated_at,
                u.first_name,
                u.last_name,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'attribute_name', ra.attribute_name,
                            'attribute_value', ra.attribute_value,
                            'rating', ra.rating
                        )
                    ) FILTER (WHERE ra.review_id IS NOT NULL),
                    '[]'::json
                ) as attributes,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'id', rm.id,
                            'media_type', rm.media_type,
                            'media_url', rm.media_url,
                            'thumbnail_url', rm.thumbnail_url,
                            'caption', rm.caption
                        )
                    ) FILTER (WHERE rm.id IS NOT NULL),
                    '[]'::json
                ) as media
            FROM customer_reviews cr
            JOIN users u ON u.id = cr.user_id
            LEFT JOIN review_attributes ra ON ra.review_id = cr.id
            LEFT JOIN review_media rm ON rm.review_id = cr.id
            WHERE {' AND '.join(conditions)}
            GROUP BY cr.id, u.first_name, u.last_name
            ORDER BY {order_by}
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """

        params.extend([limit, offset])
        rows = await db.fetch(query, *params)

        reviews = []
        for row in rows:
            # Check if current user has voted on this review
            user_vote = None
            if current_user:
                vote_query = """
                    SELECT vote_type FROM review_votes
                    WHERE review_id = $1 AND user_id = $2
                """
                vote = await db.fetchval(vote_query, row['id'], uuid.UUID(current_user['id']))
                user_vote = vote

            reviews.append(ReviewResponse(
                id=str(row['id']),
                sku=row['sku'],
                user_id=str(row['user_id']),
                user_name=f"{row['first_name']} {row['last_name'][0] if row['last_name'] else ''}.",
                order_id=None,  # Hidden for privacy
                rating=row['rating'],
                title=row['title'],
                review_text=row['review_text'],
                is_recommended=row['is_recommended'],
                is_verified_purchase=row['is_verified_purchase'],
                helpful_count=row['helpful_count'],
                not_helpful_count=row['not_helpful_count'],
                status=row['status'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                attributes=row['attributes'],
                media=row['media'],
                user_vote=user_vote
            ))

        return reviews

@router.post("/submit", response_model=ReviewResponse)
async def submit_review(
    review: ReviewSubmission,
    current_user=Depends(get_current_user)
):
    """Submit a new product review"""

    # Get database pool connection
    pool = await get_db_pool()
    async with pool.acquire() as db:
        user_id = uuid.UUID(current_user['id'])

        # Check if user has already reviewed this product
        if await check_review_exists(db, current_user['id'], review.sku):
            raise HTTPException(400, "You have already reviewed this product")

        # Start transaction
        async with db.transaction():
            # Insert review
            review_query = """
                INSERT INTO customer_reviews (
                    sku,
                    user_id,
                    order_id,
                    rating,
                    title,
                    review_text,
                    is_recommended,
                    status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """

            review_row = await db.fetchrow(
                review_query,
                review.sku,
                user_id,
                uuid.UUID(review.order_id) if review.order_id else None,
                review.rating,
                review.title,
                review.review_text,
                review.is_recommended,
                ReviewStatus.APPROVED  # Auto-approve for now, implement moderation later
            )

            # Insert review attributes
            if review.attributes:
                for attr in review.attributes:
                    attr_query = """
                        INSERT INTO review_attributes (
                            review_id,
                            attribute_name,
                            attribute_value,
                            rating
                        ) VALUES ($1, $2, $3, $4)
                    """
                    await db.execute(
                        attr_query,
                        review_row['id'],
                        attr.attribute_name,
                        attr.attribute_value,
                        attr.rating
                    )

        # Get user display name
        pool2 = await get_db_pool()
        user_name = await get_user_display_name(pool2, current_user['id'])

        return ReviewResponse(
            id=str(review_row['id']),
            sku=review_row['sku'],
            user_id=str(review_row['user_id']),
            user_name=user_name,
            order_id=str(review_row['order_id']) if review_row['order_id'] else None,
            rating=review_row['rating'],
            title=review_row['title'],
            review_text=review_row['review_text'],
            is_recommended=review_row['is_recommended'],
            is_verified_purchase=review_row['is_verified_purchase'],
            helpful_count=0,
            not_helpful_count=0,
            status=review_row['status'],
            created_at=review_row['created_at'],
            updated_at=review_row['updated_at'],
            attributes=[attr.dict() for attr in review.attributes] if review.attributes else [],
            media=[]
        )

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    update: ReviewUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update an existing review (only by the author)"""

    user_id = uuid.UUID(current_user['id'])
    review_uuid = uuid.UUID(review_id)

    # Check if review exists and belongs to user
    check_query = """
        SELECT * FROM customer_reviews
        WHERE id = $1 AND user_id = $2
    """
    existing = await db.fetchrow(check_query, review_uuid, user_id)

    if not existing:
        raise HTTPException(404, "Review not found or you don't have permission to edit it")

    # Build update query
    updates = []
    params = []
    param_count = 0

    if update.rating is not None:
        param_count += 1
        updates.append(f"rating = ${param_count}")
        params.append(update.rating)

    if update.title is not None:
        param_count += 1
        updates.append(f"title = ${param_count}")
        params.append(update.title)

    if update.review_text is not None:
        param_count += 1
        updates.append(f"review_text = ${param_count}")
        params.append(update.review_text)

    if update.is_recommended is not None:
        param_count += 1
        updates.append(f"is_recommended = ${param_count}")
        params.append(update.is_recommended)

    if not updates:
        raise HTTPException(400, "No updates provided")

    param_count += 1
    updates.append(f"updated_at = ${param_count}")
    params.append(datetime.utcnow())

    param_count += 1
    params.append(review_uuid)

    update_query = f"""
        UPDATE customer_reviews
        SET {', '.join(updates)}
        WHERE id = ${param_count}
        RETURNING *
    """

    async with db.transaction():
        review_row = await db.fetchrow(update_query, *params)

        # Update attributes if provided
        if update.attributes is not None:
            # Delete existing attributes
            await db.execute("DELETE FROM review_attributes WHERE review_id = $1", review_uuid)

            # Insert new attributes
            for attr in update.attributes:
                attr_query = """
                    INSERT INTO review_attributes (
                        review_id,
                        attribute_name,
                        attribute_value,
                        rating
                    ) VALUES ($1, $2, $3, $4)
                """
                await db.execute(
                    attr_query,
                    review_uuid,
                    attr.attribute_name,
                    attr.attribute_value,
                    attr.rating
                )

    # Get updated data
    user_name = await get_user_display_name(db, current_user['id'])

    # Get attributes
    attr_query = """
        SELECT attribute_name, attribute_value, rating
        FROM review_attributes
        WHERE review_id = $1
    """
    attributes = await db.fetch(attr_query, review_uuid)

    return ReviewResponse(
        id=str(review_row['id']),
        sku=review_row['sku'],
        user_id=str(review_row['user_id']),
        user_name=user_name,
        order_id=str(review_row['order_id']) if review_row['order_id'] else None,
        rating=review_row['rating'],
        title=review_row['title'],
        review_text=review_row['review_text'],
        is_recommended=review_row['is_recommended'],
        is_verified_purchase=review_row['is_verified_purchase'],
        helpful_count=review_row['helpful_count'],
        not_helpful_count=review_row['not_helpful_count'],
        status=review_row['status'],
        created_at=review_row['created_at'],
        updated_at=review_row['updated_at'],
        attributes=[dict(a) for a in attributes],
        media=[]
    )

@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a review (only by the author)"""

    user_id = uuid.UUID(current_user['id'])
    review_uuid = uuid.UUID(review_id)

    # Check if review exists and belongs to user
    delete_query = """
        DELETE FROM customer_reviews
        WHERE id = $1 AND user_id = $2
        RETURNING id
    """

    result = await db.fetchval(delete_query, review_uuid, user_id)

    if not result:
        raise HTTPException(404, "Review not found or you don't have permission to delete it")

    return {"message": "Review deleted successfully"}

@router.post("/reviews/{review_id}/vote")
async def vote_on_review(
    review_id: str,
    vote: ReviewVote,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Vote a review as helpful or not helpful"""

    user_id = uuid.UUID(current_user['id'])
    review_uuid = uuid.UUID(review_id)

    # Check if review exists
    review_check = await db.fetchval(
        "SELECT id FROM customer_reviews WHERE id = $1",
        review_uuid
    )
    if not review_check:
        raise HTTPException(404, "Review not found")

    # Check for existing vote
    existing_vote = await db.fetchrow(
        "SELECT id, vote_type FROM review_votes WHERE review_id = $1 AND user_id = $2",
        review_uuid, user_id
    )

    async with db.transaction():
        if existing_vote:
            if existing_vote['vote_type'] == vote.vote_type:
                # Remove vote if clicking the same button
                await db.execute(
                    "DELETE FROM review_votes WHERE id = $1",
                    existing_vote['id']
                )
                action = "removed"
            else:
                # Update vote type
                await db.execute(
                    "UPDATE review_votes SET vote_type = $1 WHERE id = $2",
                    vote.vote_type, existing_vote['id']
                )
                action = "updated"
        else:
            # Insert new vote
            await db.execute(
                "INSERT INTO review_votes (review_id, user_id, vote_type) VALUES ($1, $2, $3)",
                review_uuid, user_id, vote.vote_type
            )
            action = "added"

    # Get updated counts
    counts = await db.fetchrow(
        "SELECT helpful_count, not_helpful_count FROM customer_reviews WHERE id = $1",
        review_uuid
    )

    return {
        "action": action,
        "helpful_count": counts['helpful_count'],
        "not_helpful_count": counts['not_helpful_count']
    }

@router.post("/reviews/{review_id}/media")
async def upload_review_media(
    review_id: str,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Upload media (images/videos) for a review"""

    user_id = uuid.UUID(current_user['id'])
    review_uuid = uuid.UUID(review_id)

    # Check if review exists and belongs to user
    check_query = """
        SELECT id FROM customer_reviews
        WHERE id = $1 AND user_id = $2
    """
    review = await db.fetchval(check_query, review_uuid, user_id)

    if not review:
        raise HTTPException(404, "Review not found or you don't have permission to add media")

    # Check media count limit (max 5 per review)
    media_count = await db.fetchval(
        "SELECT COUNT(*) FROM review_media WHERE review_id = $1",
        review_uuid
    )
    if media_count >= 5:
        raise HTTPException(400, "Maximum 5 media files allowed per review")

    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4']
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"File type {file.content_type} not allowed")

    # Upload to S3
    media_type = "image" if file.content_type.startswith("image/") else "video"
    s3_key = f"reviews/{review_id}/{uuid.uuid4()}.{file.filename.split('.')[-1]}"

    try:
        media_url = await upload_to_s3(file.file, s3_key, file.content_type)
    except Exception as e:
        raise HTTPException(500, f"Failed to upload media: {str(e)}")

    # Generate thumbnail URL (would be created by a Lambda function in production)
    thumbnail_url = media_url if media_type == "image" else None

    # Insert media record
    insert_query = """
        INSERT INTO review_media (
            review_id,
            media_type,
            media_url,
            thumbnail_url,
            caption,
            display_order
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    media_row = await db.fetchrow(
        insert_query,
        review_uuid,
        media_type,
        media_url,
        thumbnail_url,
        caption,
        media_count + 1
    )

    return {
        "id": str(media_row['id']),
        "media_type": media_row['media_type'],
        "media_url": media_row['media_url'],
        "thumbnail_url": media_row['thumbnail_url'],
        "caption": media_row['caption']
    }

@router.get("/user/reviews", response_model=List[ReviewResponse])
async def get_user_reviews(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all reviews by the current user"""

    user_id = uuid.UUID(current_user['id'])
    offset = (page - 1) * limit

    query = """
        SELECT
            cr.*,
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'attribute_name', ra.attribute_name,
                        'attribute_value', ra.attribute_value,
                        'rating', ra.rating
                    )
                ) FILTER (WHERE ra.review_id IS NOT NULL),
                '[]'::json
            ) as attributes,
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'id', rm.id,
                        'media_type', rm.media_type,
                        'media_url', rm.media_url,
                        'thumbnail_url', rm.thumbnail_url,
                        'caption', rm.caption
                    )
                ) FILTER (WHERE rm.id IS NOT NULL),
                '[]'::json
            ) as media
        FROM customer_reviews cr
        LEFT JOIN review_attributes ra ON ra.review_id = cr.id
        LEFT JOIN review_media rm ON rm.review_id = cr.id
        WHERE cr.user_id = $1
        GROUP BY cr.id
        ORDER BY cr.created_at DESC
        LIMIT $2 OFFSET $3
    """

    rows = await db.fetch(query, user_id, limit, offset)
    user_name = await get_user_display_name(db, current_user['id'])

    reviews = []
    for row in rows:
        reviews.append(ReviewResponse(
            id=str(row['id']),
            sku=row['sku'],
            user_id=str(row['user_id']),
            user_name=user_name,
            order_id=str(row['order_id']) if row['order_id'] else None,
            rating=row['rating'],
            title=row['title'],
            review_text=row['review_text'],
            is_recommended=row['is_recommended'],
            is_verified_purchase=row['is_verified_purchase'],
            helpful_count=row['helpful_count'],
            not_helpful_count=row['not_helpful_count'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            attributes=row['attributes'],
            media=row['media']
        ))

    return reviews