"""
Kiosk API Endpoints
Provides specialized endpoints for self-serve kiosk functionality
Uses existing services and database structure without modifications
"""

import asyncpg
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json
import hashlib
import secrets

from services.profile_service import ProfileService
from services.otp_service import OTPService
from services.inventory_service import InventoryService
from services.store_inventory_service import StoreInventoryService
from services.order_service import OrderService
from services.cart_service import CartService
from services.user_context_service import UserContextService
from models.api_models import (
    KioskAuthRequest,
    KioskVerifyRequest,
    KioskSessionResponse,
    KioskProductSearchRequest,
    KioskCartRequest,
    KioskOrderRequest
)
import os

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])

# In-memory session store (in production, use Redis)
kiosk_sessions = {}
qr_sessions = {}

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool

async def get_db():
    """Get database connection from pool"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn


async def get_kiosk_session(session_id: str) -> Dict[str, Any]:
    """Validate and get kiosk session"""
    session = kiosk_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Check session expiry (30 minutes)
    if datetime.now() - session.get('last_activity', datetime.now()) > timedelta(minutes=30):
        del kiosk_sessions[session_id]
        raise HTTPException(status_code=401, detail="Session expired")

    # Update last activity
    session['last_activity'] = datetime.now()
    return session


@router.post("/auth/send-code")
async def send_verification_code(
    request: Dict[str, Any],
    db: asyncpg.Connection = Depends(get_db)
):
    """Send OTP verification code to phone or email"""
    try:
        identifier = request.get('identifier')
        method = request.get('method', 'phone')  # 'phone' or 'email'

        if not identifier:
            raise HTTPException(status_code=400, detail="Identifier required")

        # Initialize OTP service
        otp_service = OTPService()

        # Check if user exists with this identifier
        if method == 'phone':
            # Validate phone number
            formatted_phone = otp_service.validate_phone_number(identifier)

            # Check if profile exists with this phone
            query = """
                SELECT p.*, u.id as user_id, u.email
                FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE p.phone = $1
                LIMIT 1
            """
            existing_user = await db.fetchrow(query, formatted_phone)

            # Send OTP via SMS
            otp_code = otp_service.generate_otp()
            success = await otp_service.send_sms_otp(formatted_phone, otp_code)

            if not success:
                raise HTTPException(status_code=500, detail="Failed to send verification code")

            # Store OTP in database
            await otp_service.store_otp(db, formatted_phone, otp_code, 'sms')

        else:  # email
            # Validate email
            formatted_email = otp_service.validate_email(identifier)

            # Check if user exists with this email
            query = """
                SELECT p.*, u.id as user_id, u.email
                FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE u.email = $1
                LIMIT 1
            """
            existing_user = await db.fetchrow(query, formatted_email)

            # Send OTP via email
            otp_code = otp_service.generate_otp()
            success = await otp_service.send_email_otp(formatted_email, otp_code)

            if not success:
                raise HTTPException(status_code=500, detail="Failed to send verification code")

            # Store OTP in database
            await otp_service.store_otp(db, formatted_email, otp_code, 'email')

        return {
            "status": "success",
            "message": f"Verification code sent to {identifier}",
            "user_exists": existing_user is not None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending verification code: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification code")


@router.post("/auth/verify")
async def verify_code(
    request: Dict[str, Any],
    db: asyncpg.Connection = Depends(get_db)
):
    """Verify OTP code and create/get user profile"""
    try:
        identifier = request.get('identifier')
        code = request.get('code')
        method = request.get('method', 'phone')

        if not identifier or not code:
            raise HTTPException(status_code=400, detail="Identifier and code required")

        # Initialize services
        otp_service = OTPService()
        profile_service = ProfileService(db)

        # Format identifier
        if method == 'phone':
            identifier = otp_service.validate_phone_number(identifier)
        else:
            identifier = otp_service.validate_email(identifier)

        # Verify OTP
        is_valid = await otp_service.verify_otp(db, identifier, code)

        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid or expired code")

        # Get or create user profile
        if method == 'phone':
            # Check if profile exists
            query = """
                SELECT p.*, u.id as user_id, u.email, u.role
                FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE p.phone = $1
                LIMIT 1
            """
            profile = await db.fetchrow(query, identifier)

            if not profile:
                # Create guest user for kiosk
                user_query = """
                    INSERT INTO users (email, role, tenant_id, active)
                    VALUES ($1, 'customer', NULL, true)
                    RETURNING id
                """
                guest_email = f"kiosk_{uuid4().hex[:8]}@weedgo.local"
                user_result = await db.fetchrow(user_query, guest_email)
                user_id = user_result['id']

                # Create profile
                profile_query = """
                    INSERT INTO profiles (user_id, phone, customer_type, language)
                    VALUES ($1, $2, 'kiosk', 'en')
                    RETURNING *
                """
                profile = await db.fetchrow(profile_query, user_id, identifier)

        else:  # email
            # Check if user exists
            query = """
                SELECT p.*, u.id as user_id, u.email, u.role
                FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE u.email = $1
                LIMIT 1
            """
            profile = await db.fetchrow(query, identifier)

            if not profile:
                # Create user
                user_query = """
                    INSERT INTO users (email, role, tenant_id, active)
                    VALUES ($1, 'customer', NULL, true)
                    RETURNING id
                """
                user_result = await db.fetchrow(user_query, identifier)
                user_id = user_result['id']

                # Create profile
                profile_query = """
                    INSERT INTO profiles (user_id, customer_type, language)
                    VALUES ($1, 'kiosk', 'en')
                    RETURNING *
                """
                profile = await db.fetchrow(profile_query, user_id)

        # Create kiosk session
        session_id = f"kiosk_{uuid4().hex}"
        kiosk_sessions[session_id] = {
            'session_id': session_id,
            'user_id': str(profile['user_id']),
            'profile_id': str(profile['id']) if 'id' in profile else None,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'language': profile.get('language', 'en')
        }

        # Return customer data for frontend
        customer = {
            'id': str(profile.get('user_id')),
            'email': profile.get('email'),
            'phone': profile.get('phone'),
            'firstName': profile.get('first_name'),
            'lastName': profile.get('last_name'),
            'language': profile.get('language', 'en'),
            'preferences': json.loads(profile.get('preferences', '{}')) if profile.get('preferences') else {}
        }

        return {
            "status": "success",
            "session_id": session_id,
            "customer": customer
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/auth/qr-generate")
async def generate_qr_session():
    """Generate a QR code session for mobile login"""
    try:
        # Generate unique session code
        session_code = f"KIOSK-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

        # Store in QR sessions
        qr_sessions[session_code] = {
            'code': session_code,
            'created_at': datetime.now(),
            'authenticated': False,
            'customer': None
        }

        # Clean up old QR sessions (older than 5 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        expired_codes = [
            code for code, session in qr_sessions.items()
            if session['created_at'] < cutoff_time
        ]
        for code in expired_codes:
            del qr_sessions[code]

        return {
            "status": "success",
            "session_code": session_code,
            "expires_in": 300  # 5 minutes
        }

    except Exception as e:
        logger.error(f"Error generating QR session: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate QR session")


@router.get("/auth/check-qr/{session_code}")
async def check_qr_session(session_code: str):
    """Check if QR session has been authenticated"""
    try:
        session = qr_sessions.get(session_code)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if session is expired (5 minutes)
        if datetime.now() - session['created_at'] > timedelta(minutes=5):
            del qr_sessions[session_code]
            raise HTTPException(status_code=410, detail="Session expired")

        return {
            "status": "success",
            "authenticated": session['authenticated'],
            "customer": session.get('customer')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking QR session: {e}")
        raise HTTPException(status_code=500, detail="Failed to check session")


@router.post("/auth/manual-code")
async def verify_manual_code(
    request: Dict[str, Any],
    db: asyncpg.Connection = Depends(get_db)
):
    """Verify a manually entered code from mobile app"""
    try:
        code = request.get('code', '').upper()

        if not code:
            raise HTTPException(status_code=400, detail="Code required")

        # In production, this would verify against codes generated by mobile app
        # For now, we'll create a mock verification

        # Create a guest session for demo
        session_id = f"kiosk_{uuid4().hex}"
        kiosk_sessions[session_id] = {
            'session_id': session_id,
            'user_id': f"guest_{uuid4().hex[:8]}",
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'language': 'en'
        }

        customer = {
            'id': kiosk_sessions[session_id]['user_id'],
            'firstName': 'Guest',
            'lastName': 'User',
            'language': 'en',
            'preferences': {}
        }

        return {
            "status": "success",
            "session_id": session_id,
            "customer": customer
        }

    except Exception as e:
        logger.error(f"Error verifying manual code: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.get("/products/browse")
async def browse_products(
    store_id: str,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    strain_type: Optional[str] = None,
    size: Optional[str] = None,
    filter: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = 'name',
    session_id: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db)
):
    """Browse products optimized for kiosk display"""
    try:
        # Validate session if provided
        user_preferences = {}
        if session_id:
            try:
                session = await get_kiosk_session(session_id)
                # Get user preferences if available
                if session.get('user_id'):
                    profile_service = ProfileService(db)
                    profile = await profile_service.get_profile_by_user_id(UUID(session['user_id']))
                    if profile and profile.get('preferences'):
                        user_preferences = json.loads(profile['preferences'])
            except:
                pass  # Continue without session

        # Get the pool instead of connection for store inventory service
        pool = await get_db_pool()
        store_inventory_service = StoreInventoryService(pool)

        # Build filters for the query
        filters = {}
        if category:
            filters['category'] = category
        if subcategory:
            filters['subcategory'] = subcategory
        if strain_type:
            # Plant type/strain type filter (Indica, Sativa, Hybrid, etc.)
            filters['strain_type'] = strain_type
        if size:
            # Size filter (1g, 3.5g, 7g, etc.)
            filters['size'] = size
        if filter:
            # Quick filter (trending, new, staff-picks)
            filters['quick_filter'] = filter
        if search:
            filters['search'] = search

        # Calculate offset from page
        offset = (page - 1) * limit

        # Get products using get_store_inventory_list with correct parameters
        products, total_count = await store_inventory_service.get_store_inventory_list(
            store_id=UUID(store_id),
            filters=filters,
            limit=limit,
            offset=offset
        )

        # Convert to expected format
        inventory_result = {
            'items': products,
            'total': total_count,
            'total_pages': (total_count + limit - 1) // limit if total_count > 0 else 1
        }
        products = inventory_result.get('items', [])

        # Apply sorting based on sort_by parameter
        if sort_by == 'price_low':
            products = sorted(products, key=lambda x: float(x.get('retail_price', 0) or x.get('price', 0)))
        elif sort_by == 'price_high':
            products = sorted(products, key=lambda x: float(x.get('retail_price', 0) or x.get('price', 0)), reverse=True)
        elif sort_by == 'thc_high':
            products = sorted(products, key=lambda x: float(x.get('thc_content', 0) or 0), reverse=True)
        elif sort_by == 'cbd_high':
            products = sorted(products, key=lambda x: float(x.get('cbd_content', 0) or 0), reverse=True)
        elif sort_by == 'size_large':
            # Sort by size (extract numeric value from size string)
            def get_size_value(product):
                size = str(product.get('size', '') or '')
                # Extract numeric value (e.g., "3.5g" -> 3.5, "14g" -> 14)
                import re
                match = re.search(r'(\d+\.?\d*)', size)
                return float(match.group(1)) if match else 0
            products = sorted(products, key=get_size_value, reverse=True)
        elif sort_by == 'popular':
            # Sort by popularity (can be based on sales_count or rating if available)
            products = sorted(products, key=lambda x: int(x.get('sales_count', 0) or 0), reverse=True)
        elif sort_by != 'name':
            # Default is name (alphabetical), already handled by the query

            pass
        # If user has preferences, apply smart sorting (override the basic sort)
        if user_preferences:
            ai_engine = SmartAIEngineV5()
            products = await ai_engine.rank_products_by_preferences(
                products,
                user_preferences
            )

        # Add kiosk-specific formatting
        for product in products:
            # Ensure images are properly formatted
            if product.get('images'):
                product['primary_image'] = product['images'][0] if isinstance(product['images'], list) else product['images']

            # Format prices
            if product.get('price'):
                product['display_price'] = f"${product['price']:.2f}"

            # Add badge for effects
            if product.get('thc_content'):
                product['thc_badge'] = f"THC {product['thc_content']}%"
            if product.get('cbd_content'):
                product['cbd_badge'] = f"CBD {product['cbd_content']}%"

        return {
            "products": products,
            "total": inventory_result.get('total', len(products)),
            "page": page,
            "page_size": limit,
            "total_pages": inventory_result.get('total_pages', 1)
        }

    except Exception as e:
        logger.error(f"Error browsing products: {e}")
        raise HTTPException(status_code=500, detail="Failed to load products")


@router.post("/products/recommendations")
async def get_recommendations(
    request: Dict[str, Any],
    db: asyncpg.Connection = Depends(get_db)
):
    """Get AI-powered product recommendations"""
    try:
        session_id = request.get('session_id')
        store_id = request.get('store_id')
        cart_items = request.get('cart_items', [])

        if not store_id:
            raise HTTPException(status_code=400, detail="Store ID required")

        # Get user context if session exists
        user_context = {}
        if session_id:
            try:
                session = await get_kiosk_session(session_id)
                if session.get('user_id'):
                    profile_service = ProfileService(db)
                    profile = await profile_service.get_profile_by_user_id(UUID(session['user_id']))
                    if profile:
                        user_context = {
                            'preferences': json.loads(profile.get('preferences', '{}')),
                            'experience_level': profile.get('experience_level'),
                            'preferred_effects': json.loads(profile.get('preferred_effects', '[]')),
                            'preferred_categories': json.loads(profile.get('preferred_categories', '[]'))
                        }
            except:
                pass

        # Get recommendations based on popular products and user context
        # Query for popular products from inventory
        query = """
            SELECT DISTINCT
                i.id::text as product_id,
                COALESCE(i.product_name, pc.product_name) as name,
                COALESCE(i.override_price, i.retail_price) as price,
                pc.category,
                pc.sub_category,
                pc.brand,
                pc.thc_range,
                pc.cbd_range,
                pc.plant_type,
                pc.image_url,
                i.quantity_available
            FROM ocs_inventory i
            INNER JOIN ocs_product_catalog pc
                ON LOWER(TRIM(i.sku)) = LOWER(TRIM(pc.ocs_variant_number))
            WHERE i.store_id = $1
                AND i.is_available = true
                AND i.quantity_available > 0
            ORDER BY i.quantity_available DESC, RANDOM()
            LIMIT $2
        """

        rows = await db.fetch(query, UUID(store_id), 6)

        recommendations = []
        for row in rows:
            recommendations.append({
                'product_id': row['product_id'],
                'name': row['name'],
                'price': float(row['price']) if row['price'] else 0.0,
                'category': row['category'],
                'sub_category': row['sub_category'],
                'brand': row['brand'],
                'thc_range': row['thc_range'],
                'cbd_range': row['cbd_range'],
                'plant_type': row['plant_type'],
                'image_url': row['image_url'],
                'reason': 'Popular in store'
            })

        return {
            "status": "success",
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.post("/cart/add")
async def add_to_cart(
    request: Dict[str, Any],
    db: asyncpg.Connection = Depends(get_db)
):
    """Add item to kiosk cart"""
    try:
        session_id = request.get('session_id')
        product_id = request.get('product_id')
        quantity = request.get('quantity', 1)
        store_id = request.get('store_id')

        if not all([product_id, store_id]):
            raise HTTPException(status_code=400, detail="Product ID and Store ID required")

        # Validate session if provided
        user_id = None
        if session_id:
            try:
                session = await get_kiosk_session(session_id)
                user_id = session.get('user_id')
            except:
                pass

        # Check product availability
        store_inventory_service = StoreInventoryService(db)
        product = await store_inventory_service.get_product_availability(
            store_id=UUID(store_id),
            product_id=UUID(product_id)
        )

        if not product or product.get('quantity_available', 0) < quantity:
            raise HTTPException(status_code=400, detail="Product not available in requested quantity")

        # Store cart in session (in production, use proper cart service)
        if session_id and session_id in kiosk_sessions:
            if 'cart' not in kiosk_sessions[session_id]:
                kiosk_sessions[session_id]['cart'] = []

            # Check if item already in cart
            cart = kiosk_sessions[session_id]['cart']
            existing_item = next((item for item in cart if item['product_id'] == product_id), None)

            if existing_item:
                existing_item['quantity'] += quantity
            else:
                cart.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': product.get('price', 0),
                    'name': product.get('name'),
                    'image': product.get('images', [None])[0] if product.get('images') else None
                })

        return {
            "status": "success",
            "message": "Item added to cart"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail="Failed to add to cart")


@router.post("/order/create")
async def create_kiosk_order(request: Dict[str, Any]):
    """
    Create order from kiosk - properly handles customer profiles
    """
    from .pos_transaction_endpoints import POSCartItem
    from decimal import Decimal
    import uuid

    try:
        # Extract kiosk request data
        store_id = request.get('store_id')
        cart_items = request.get('cart_items', [])
        customer_info = request.get('customer_info', {})
        session_id = request.get('session_id')

        if not store_id or not cart_items:
            logger.error(f"Missing required fields - store_id: {store_id}, cart_items: {cart_items}")
            raise HTTPException(status_code=400, detail="Store ID and cart items required")

        # Convert cart items to POS format
        pos_items = []
        subtotal = 0
        for item in cart_items:
            pos_item = POSCartItem(
                product={
                    'id': item['product_id'],
                    'name': item.get('name', 'Product'),
                    'price': item['price']
                },
                quantity=item['quantity'],
                discount=0,
                discount_type='percentage'
            )
            pos_items.append(pos_item)
            subtotal += item['price'] * item['quantity']

        # Calculate totals
        tax_rate = 0.13  # Ontario HST
        tax = subtotal * tax_rate
        total = subtotal + tax

        # Get database connection
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Parse store_id as UUID
            store_uuid = None
            try:
                store_uuid = uuid.UUID(store_id) if store_id else None
            except:
                logger.warning(f"Invalid store UUID: {store_id}")

            # Handle customer profile creation/update
            customer_uuid = None
            user_id = None
            customer_id = customer_info.get('customer_id', 'anonymous')

            if customer_id and customer_id not in ['anonymous', 'anon']:
                # Existing customer - look up profile
                try:
                    customer_uuid = uuid.UUID(customer_id)
                    profile_row = await conn.fetchrow(
                        "SELECT id, user_id FROM profiles WHERE id = $1",
                        customer_uuid
                    )
                    if profile_row:
                        user_id = profile_row['user_id']

                        # Update profile with new info if provided
                        updates = []
                        params = []
                        param_num = 1

                        if customer_info.get('customer_name'):
                            names = customer_info['customer_name'].split(' ', 1)
                            updates.append(f"first_name = ${param_num}")
                            params.append(names[0])
                            param_num += 1
                            if len(names) > 1:
                                updates.append(f"last_name = ${param_num}")
                                params.append(names[1])
                                param_num += 1

                        if customer_info.get('customer_email'):
                            # Update email in users table
                            await conn.execute(
                                "UPDATE users SET email = $1 WHERE id = $2",
                                customer_info['customer_email'],
                                user_id
                            )

                        if customer_info.get('customer_phone'):
                            updates.append(f"phone = ${param_num}")
                            params.append(customer_info['customer_phone'])
                            param_num += 1

                        if updates:
                            updates.append(f"updated_at = CURRENT_TIMESTAMP")
                            params.append(customer_uuid)
                            update_query = f"""
                                UPDATE profiles
                                SET {', '.join(updates)}
                                WHERE id = ${param_num}
                            """
                            await conn.execute(update_query, *params)
                except:
                    pass
            elif customer_info.get('customer_email') or customer_info.get('customer_phone'):
                # New customer with contact info - create profile
                customer_email = customer_info.get('customer_email')
                customer_phone = customer_info.get('customer_phone')
                customer_name = customer_info.get('customer_name', 'Walk-in Customer')

                # Check if user exists with this email
                if customer_email:
                    existing_user = await conn.fetchrow(
                        "SELECT id FROM users WHERE email = $1",
                        customer_email
                    )
                    if existing_user:
                        user_id = existing_user['id']
                    else:
                        # Create new user with a random password hash
                        import secrets
                        import hashlib
                        random_password = secrets.token_urlsafe(32)
                        password_hash = hashlib.sha256(random_password.encode()).hexdigest()

                        user_row = await conn.fetchrow(
                            """
                            INSERT INTO users (email, password_hash, role, active)
                            VALUES ($1, $2, 'customer', true)
                            RETURNING id
                            """,
                            customer_email,
                            password_hash
                        )
                        user_id = user_row['id']
                elif customer_phone:
                    # Check if profile exists with this phone
                    existing_profile = await conn.fetchrow(
                        """
                        SELECT p.id, p.user_id
                        FROM profiles p
                        WHERE p.phone = $1
                        LIMIT 1
                        """,
                        customer_phone
                    )
                    if existing_profile:
                        customer_uuid = existing_profile['id']
                        user_id = existing_profile['user_id']
                    else:
                        # Create user with generated email and random password
                        generated_email = f"kiosk_{uuid.uuid4().hex[:8]}@weedgo.local"
                        import secrets
                        import hashlib
                        random_password = secrets.token_urlsafe(32)
                        password_hash = hashlib.sha256(random_password.encode()).hexdigest()

                        user_row = await conn.fetchrow(
                            """
                            INSERT INTO users (email, password_hash, role, active)
                            VALUES ($1, $2, 'customer', true)
                            RETURNING id
                            """,
                            generated_email,
                            password_hash
                        )
                        user_id = user_row['id']

                # Create or update profile if we have user_id but no customer_uuid
                if user_id and not customer_uuid:
                    names = customer_name.split(' ', 1)
                    first_name = names[0] if names else None
                    last_name = names[1] if len(names) > 1 else None

                    # Check if profile exists for this user
                    existing_profile = await conn.fetchrow(
                        "SELECT id FROM profiles WHERE user_id = $1",
                        user_id
                    )

                    if existing_profile:
                        customer_uuid = existing_profile['id']
                        # Update existing profile
                        await conn.execute(
                            """
                            UPDATE profiles
                            SET first_name = COALESCE($1, first_name),
                                last_name = COALESCE($2, last_name),
                                phone = COALESCE($3, phone),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = $4
                            """,
                            first_name,
                            last_name,
                            customer_phone,
                            customer_uuid
                        )
                    else:
                        # Create new profile
                        profile_row = await conn.fetchrow(
                            """
                            INSERT INTO profiles (
                                user_id, first_name, last_name, phone,
                                customer_type, language
                            )
                            VALUES ($1, $2, $3, $4, 'kiosk', 'en')
                            RETURNING id
                            """,
                            user_id,
                            first_name,
                            last_name,
                            customer_phone
                        )
                        customer_uuid = profile_row['id']

            # Prepare items for database
            order_items = []
            for item in pos_items:
                order_items.append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'discount': item.discount,
                    'discount_type': item.discount_type
                })

            order_number = f"K{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Only store operational metadata in pos_metadata
            pos_metadata = {
                'cashier_id': 'kiosk',
                'store_id_text': store_id,
                'session_id': session_id,
                'created_via': 'kiosk'
            }

            query = """
                INSERT INTO orders (
                    order_number,
                    user_id,
                    customer_id,
                    store_id,
                    items,
                    subtotal,
                    tax_amount,
                    discount_amount,
                    total_amount,
                    payment_status,
                    payment_method,
                    payment_details,
                    order_source,
                    order_status,
                    is_pos_transaction,
                    receipt_number,
                    pos_metadata
                ) VALUES (
                    $1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, $12::jsonb,
                    'kiosk', $13, TRUE, $14, $15::jsonb
                )
                RETURNING id::text as id, created_at
            """

            row = await conn.fetchrow(
                query,
                order_number,  # 1
                user_id,  # 2
                customer_uuid,  # 3
                store_uuid,  # 4
                json.dumps(order_items),  # 5
                Decimal(str(subtotal)),  # 6
                Decimal(str(tax)),  # 7
                Decimal('0'),  # 8 - no discounts
                Decimal(str(total)),  # 9
                'pending',  # 10 - payment_status (pay at pickup)
                'pay_at_pickup',  # 11
                json.dumps({}),  # 12 - empty payment details
                'parked',  # 13 - order_status (show as parked in POS)
                order_number,  # 14 - receipt_number
                json.dumps(pos_metadata)  # 15
            )

            # Update loyalty points if customer exists
            if user_id:
                try:
                    points_earned = int(total)  # 1 point per dollar
                    await conn.execute(
                        "UPDATE profiles SET loyalty_points = COALESCE(loyalty_points, 0) + $1 WHERE user_id = $2",
                        points_earned,
                        user_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to update loyalty points: {e}")

            return {
                'order_id': row['id'],
                'order_number': order_number,
                'timestamp': row['created_at'].isoformat(),
                'total': float(total)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating kiosk order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get session information"""
    try:
        session = await get_kiosk_session(session_id)

        # Get profile info if user exists
        profile = None
        if session.get('user_id'):
            profile_service = ProfileService(db)
            profile = await profile_service.get_profile_by_user_id(UUID(session['user_id']))

        return {
            "status": "success",
            "session": {
                "id": session_id,
                "created_at": session.get('created_at'),
                "language": session.get('language', 'en'),
                "cart": session.get('cart', [])
            },
            "customer": {
                "id": session.get('user_id'),
                "firstName": profile.get('first_name') if profile else None,
                "lastName": profile.get('last_name') if profile else None,
                "email": profile.get('email') if profile else None,
                "phone": profile.get('phone') if profile else None
            } if profile else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session info")

@router.get("/categories")
async def get_categories(
    store_id: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Get all product categories with counts
    """
    try:
        query = """
            SELECT
                LOWER(REPLACE(category, ' ', '-')) as id,
                category as name,
                LOWER(REPLACE(category, ' ', '-')) as slug,
                NULL as description,
                NULL as image_url,
                COUNT(DISTINCT ocs_variant_number) as product_count,
                json_build_array() as subcategories
            FROM ocs_product_catalog
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY product_count DESC
        """

        rows = await db.fetch(query)

        categories = []
        for row in rows:
            category = dict(row)
            # Convert product_count to int
            category['product_count'] = int(category['product_count'])
            categories.append(category)

        return categories

    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brands")
async def get_brands(
    store_id: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Get all product brands with counts
    """
    try:
        query = """
            SELECT
                LOWER(REPLACE(brand, ' ', '-')) as id,
                brand as name,
                LOWER(REPLACE(brand, ' ', '-')) as slug,
                NULL as logo_url,
                NULL as description,
                NULL as website,
                COUNT(DISTINCT ocs_variant_number) as product_count
            FROM ocs_product_catalog
            WHERE brand IS NOT NULL
            GROUP BY brand
            ORDER BY product_count DESC
            LIMIT 100
        """

        rows = await db.fetch(query)

        brands = []
        for row in rows:
            brand = dict(row)
            # Convert product_count to int
            brand['product_count'] = int(brand['product_count'])
            brands.append(brand)

        return brands

    except Exception as e:
        logger.error(f"Error fetching brands: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
