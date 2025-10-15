"""
Store-Aware Inventory Management Service
Handles multi-tenant inventory tracking with store isolation
Follows SOLID principles and clean architecture patterns
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4
import asyncpg
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Inventory transaction types"""
    SALE = "sale"
    PURCHASE = "purchase"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"
    DAMAGE = "damage"
    EXPIRE = "expire"


class StoreInventoryService:
    """
    Service for managing store-specific inventory
    Implements store isolation and multi-tenant inventory operations
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize store inventory service with database connection pool
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
    
    # =====================================================
    # Store Inventory Query Methods
    # =====================================================
    
    async def get_store_inventory_status(
        self, 
        store_id: UUID, 
        sku: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current inventory status for a SKU in a specific store
        
        Args:
            store_id: UUID of the store
            sku: Product SKU
            
        Returns:
            Dict with inventory details or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT
                        si.id,
                        si.store_id,
                        si.sku,
                        si.quantity_on_hand,
                        si.quantity_available,
                        si.quantity_reserved,
                        si.unit_cost,
                        si.retail_price,
                        si.reorder_point,
                        si.reorder_quantity,
                        si.last_restock_date,
                        si.is_available as is_active,
                        p.product_name,
                        p.category,
                        p.brand,
                        s.name as store_name,
                        s.store_code
                    FROM ocs_inventory si
                    LEFT JOIN ocs_product_catalog p ON LOWER(TRIM(si.sku)) = LOWER(TRIM(p.ocs_variant_number))
                    JOIN stores s ON si.store_id = s.id
                    WHERE si.store_id = $1 AND si.sku = $2
                """
                
                result = await conn.fetchrow(query, store_id, sku)
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"Error getting store inventory status: {str(e)}")
            raise
    
    async def get_store_inventory_list(
        self,
        store_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get paginated inventory list for a store with optional filters
        
        Args:
            store_id: UUID of the store
            filters: Optional filters (category, brand, low_stock, out_of_stock)
            limit: Number of records to return
            offset: Number of records to skip
            
        Returns:
            Tuple of (inventory list, total count)
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build dynamic WHERE clause - include available filter by default for kiosk
                where_conditions = ["si.store_id = $1", "si.is_available = true"]
                params = [store_id]
                param_counter = 2
                
                if filters:
                    if filters.get('category'):
                        where_conditions.append(f"p.category = ${param_counter}")
                        params.append(filters['category'])
                        param_counter += 1

                    if filters.get('subcategory'):
                        where_conditions.append(f"p.sub_category = ${param_counter}")
                        params.append(filters['subcategory'])
                        param_counter += 1

                    if filters.get('strain_type'):
                        # Plant type/strain type filter
                        where_conditions.append(f"p.plant_type = ${param_counter}")
                        params.append(filters['strain_type'])
                        param_counter += 1

                    if filters.get('size'):
                        # Size filter - match product size/weight
                        where_conditions.append(f"p.size = ${param_counter}")
                        params.append(filters['size'])
                        param_counter += 1

                    if filters.get('quick_filter'):
                        # Handle quick filters
                        if filters['quick_filter'] == 'trending':
                            # Sort by popularity/sales - handled in ORDER BY
                            pass
                        elif filters['quick_filter'] == 'new':
                            # New arrivals - items added in last 30 days
                            where_conditions.append("si.created_at >= CURRENT_DATE - INTERVAL '30 days'")
                        elif filters['quick_filter'] == 'staff-picks':
                            # Staff picks - use rating as a proxy for featured
                            where_conditions.append("p.rating >= 4.5")

                    if filters.get('brand'):
                        where_conditions.append(f"p.brand = ${param_counter}")
                        params.append(filters['brand'])
                        param_counter += 1

                    if filters.get('low_stock'):
                        where_conditions.append("si.quantity_available <= si.reorder_point")

                    if filters.get('out_of_stock'):
                        where_conditions.append("si.quantity_available = 0")

                    if filters.get('search'):
                        where_conditions.append(
                            f"(p.product_name ILIKE ${param_counter} OR si.sku ILIKE ${param_counter})"
                        )
                        params.append(f"%{filters['search']}%")
                        param_counter += 1
                
                where_clause = " AND ".join(where_conditions)
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*)
                    FROM ocs_inventory si
                    LEFT JOIN ocs_product_catalog p ON LOWER(TRIM(si.sku)) = LOWER(TRIM(p.ocs_variant_number))
                    WHERE {where_clause}
                """
                total_count = await conn.fetchval(count_query, *params)

                # Get paginated results with batch tracking details
                params.extend([limit, offset])
                list_query = f"""
                    SELECT
                        si.*,
                        p.product_name,
                        p.category,
                        p.sub_category as subcategory,
                        p.brand,
                        p.image_url,
                        p.product_name as name,
                        p.plant_type,
                        p.size,
                        p.thc_content_per_unit as thc_content,
                        p.cbd_content_per_unit as cbd_content,
                        p.rating,
                        p.rating_count,
                        p.product_short_description as description,
                        STRING_AGG(DISTINCT bt.batch_lot, ', ' ORDER BY bt.batch_lot) as batch_lot,
                        -- Aggregate batch details as JSON array
                        COALESCE(
                            JSON_AGG(
                                CASE WHEN bt.batch_lot IS NOT NULL THEN
                                    JSON_BUILD_OBJECT(
                                        'batch_lot', bt.batch_lot,
                                        'case_gtin', bt.case_gtin,
                                        'each_gtin', bt.each_gtin,
                                        'gtin_barcode', bt.gtin_barcode,
                                        'packaged_on_date', bt.packaged_on_date,
                                        'quantity_received', bt.quantity_received,
                                        'quantity_remaining', bt.quantity_remaining,
                                        'unit_cost', bt.unit_cost,
                                        'received_date', bt.received_date,
                                        'purchase_order_id', bt.purchase_order_id,
                                        'supplier_name', s.name,
                                        'supplier_id', po.supplier_id,
                                        'vendor', poi.vendor,
                                        'brand', poi.brand,
                                        'po_number', po.po_number
                                    )
                                ELSE NULL
                                END
                            ) FILTER (WHERE bt.batch_lot IS NOT NULL),
                            '[]'::json
                        ) as batch_details
                    FROM ocs_inventory si
                    LEFT JOIN ocs_product_catalog p ON LOWER(TRIM(si.sku)) = LOWER(TRIM(p.ocs_variant_number))
                    LEFT JOIN batch_tracking bt ON si.sku = bt.sku AND si.store_id = bt.store_id AND bt.is_active = true AND bt.quantity_remaining > 0
                    LEFT JOIN purchase_orders po ON bt.purchase_order_id = po.id
                    LEFT JOIN provincial_suppliers s ON po.supplier_id = s.id
                    LEFT JOIN purchase_order_items poi ON po.id = poi.purchase_order_id AND bt.sku = poi.sku AND bt.batch_lot = poi.batch_lot
                    WHERE {where_clause}
                    GROUP BY si.id, si.store_id, si.sku, si.quantity_on_hand, si.quantity_available,
                             si.quantity_reserved, si.unit_cost, si.retail_price, si.reorder_point,
                             si.reorder_quantity, si.last_restock_date, si.is_available, si.created_at,
                             si.updated_at, p.product_name, p.category, p.sub_category, p.brand, p.image_url,
                             p.plant_type, p.size, p.thc_content_per_unit, p.cbd_content_per_unit,
                             p.rating, p.rating_count, p.product_short_description
                    ORDER BY COALESCE(p.product_name, si.sku)
                    LIMIT ${param_counter} OFFSET ${param_counter + 1}
                """

                results = await conn.fetch(list_query, *params)

                # Process results to handle JSON data properly
                inventory_items = []
                for row in results:
                    item = dict(row)
                    # Parse batch_details JSON if it's a string
                    if 'batch_details' in item and isinstance(item['batch_details'], str):
                        import json
                        item['batch_details'] = json.loads(item['batch_details'])
                    inventory_items.append(item)

                return inventory_items, total_count
                
        except Exception as e:
            logger.error(f"Error getting store inventory list: {str(e)}")
            raise
    
    # =====================================================
    # Store Inventory Update Methods
    # =====================================================
    
    async def update_store_inventory(
        self,
        store_id: UUID,
        sku: str,
        quantity_change: int,
        transaction_type: TransactionType,
        reference_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        batch_lot: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update inventory levels for a specific store and record transaction
        
        Args:
            store_id: UUID of the store
            sku: Product SKU
            quantity_change: Change in quantity (positive or negative)
            transaction_type: Type of transaction
            reference_id: Reference ID (order, transfer, etc.)
            notes: Optional transaction notes
            batch_lot: Optional batch/lot number
            
        Returns:
            Dict with updated inventory status
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Get product ID
                    product_id = await conn.fetchval(
                        "SELECT id FROM products WHERE sku = $1", sku
                    )
                    
                    if not product_id:
                        raise ValueError(f"Product with SKU {sku} not found")
                    
                    # Update inventory based on transaction type
                    if transaction_type == TransactionType.SALE:
                        update_query = """
                            UPDATE store_inventory
                            SET quantity_available = quantity_available - $3,
                                quantity_on_hand = quantity_on_hand - $3,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND sku = $2 AND quantity_available >= $3
                            RETURNING *
                        """
                    elif transaction_type == TransactionType.PURCHASE:
                        update_query = """
                            UPDATE store_inventory
                            SET quantity_available = quantity_available + $3,
                                quantity_on_hand = quantity_on_hand + $3,
                                quantity_in_transit = GREATEST(0, quantity_in_transit - $3),
                                last_restock_date = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND sku = $2
                            RETURNING *
                        """
                    elif transaction_type == TransactionType.ADJUSTMENT:
                        update_query = """
                            UPDATE store_inventory
                            SET quantity_available = quantity_available + $3,
                                quantity_on_hand = quantity_on_hand + $3,
                                last_count_date = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND sku = $2
                            RETURNING *
                        """
                    elif transaction_type == TransactionType.TRANSFER:
                        # Transfer reduces inventory in source store
                        update_query = """
                            UPDATE store_inventory
                            SET quantity_available = quantity_available - $3,
                                quantity_on_hand = quantity_on_hand - $3,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND sku = $2 AND quantity_available >= $3
                            RETURNING *
                        """
                    else:
                        update_query = """
                            UPDATE store_inventory
                            SET quantity_available = quantity_available + $3,
                                quantity_on_hand = quantity_on_hand + $3,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND sku = $2
                            RETURNING *
                        """
                    
                    result = await conn.fetchrow(
                        update_query, store_id, sku, abs(quantity_change)
                    )
                    
                    if result is None:
                        # Create new inventory record if doesn't exist
                        if transaction_type in [TransactionType.PURCHASE, TransactionType.ADJUSTMENT]:
                            insert_query = """
                                INSERT INTO store_inventory 
                                (store_id, product_id, sku, quantity_on_hand, quantity_available,
                                 quantity_reserved, quantity_in_transit, last_restock_date)
                                VALUES ($1, $2, $3, $4, $4, 0, 0, CURRENT_TIMESTAMP)
                                RETURNING *
                            """
                            result = await conn.fetchrow(
                                insert_query, store_id, product_id, sku, abs(quantity_change)
                            )
                        else:
                            raise ValueError(f"Insufficient inventory for {sku} in store")
                    
                    # Record inventory transaction
                    transaction_query = """
                        INSERT INTO inventory_transactions
                        (store_id, product_id, sku, transaction_type, quantity,
                         reference_id, batch_lot, notes, user_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                    """
                    
                    transaction_id = await conn.fetchval(
                        transaction_query,
                        store_id, product_id, sku, transaction_type.value,
                        quantity_change, reference_id, batch_lot, notes,
                        None  # TODO: Add user_id from context
                    )

                    # Handle batch tracking for PURCHASE transactions
                    if transaction_type == TransactionType.PURCHASE and batch_lot:
                        # Check if batch_tracking record exists
                        existing_batch = await conn.fetchrow("""
                            SELECT id, quantity_remaining
                            FROM batch_tracking
                            WHERE store_id = $1 AND sku = $2 AND batch_lot = $3
                        """, store_id, sku, batch_lot)

                        if existing_batch:
                            # Update existing batch quantity
                            await conn.execute("""
                                UPDATE batch_tracking
                                SET quantity_remaining = quantity_remaining + $4,
                                    quantity_received = quantity_received + $4,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE store_id = $1 AND sku = $2 AND batch_lot = $3
                            """, store_id, sku, batch_lot, abs(quantity_change))
                        else:
                            # Create new batch tracking record
                            await conn.execute("""
                                INSERT INTO batch_tracking
                                (store_id, sku, batch_lot, quantity_received,
                                 quantity_remaining, is_active, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $4, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """, store_id, sku, batch_lot, abs(quantity_change))

                    # Handle batch tracking for SALE transactions (reduce from oldest batches first - FIFO)
                    elif transaction_type == TransactionType.SALE:
                        quantity_to_reduce = abs(quantity_change)

                        # Get active batches ordered by created_at (FIFO)
                        active_batches = await conn.fetch("""
                            SELECT id, batch_lot, quantity_remaining
                            FROM batch_tracking
                            WHERE store_id = $1 AND sku = $2 AND is_active = true
                                  AND quantity_remaining > 0
                            ORDER BY created_at ASC
                        """, store_id, sku)

                        for batch in active_batches:
                            if quantity_to_reduce <= 0:
                                break

                            batch_reduction = min(batch['quantity_remaining'], quantity_to_reduce)
                            new_remaining = batch['quantity_remaining'] - batch_reduction

                            # Update batch quantity
                            await conn.execute("""
                                UPDATE batch_tracking
                                SET quantity_remaining = $3,
                                    is_active = CASE WHEN $3 = 0 THEN false ELSE true END,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = $1 AND store_id = $2
                            """, batch['id'], store_id, new_remaining)

                            quantity_to_reduce -= batch_reduction

                    return {
                        **dict(result),
                        'transaction_id': transaction_id
                    }
                    
        except Exception as e:
            logger.error(f"Error updating store inventory: {str(e)}")
            raise
    
    # =====================================================
    # Store Purchase Order Methods
    # =====================================================
    
    async def create_store_purchase_order(
        self,
        store_id: UUID,
        supplier_id: UUID,
        items: List[Dict[str, Any]],
        expected_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> UUID:
        """
        Create a new purchase order for a specific store
        
        Args:
            store_id: UUID of the store
            supplier_id: UUID of the supplier
            items: List of order items
            expected_date: Expected delivery date
            notes: Optional notes
            
        Returns:
            UUID of created purchase order
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Generate PO number with store code
                    store_code = await conn.fetchval(
                        "SELECT store_code FROM stores WHERE id = $1", store_id
                    )
                    po_number = f"PO-{store_code}-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
                    
                    # Calculate total amount
                    total_amount = sum(
                        Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
                        for item in items
                    )
                    
                    # Create purchase order with store_id
                    po_query = """
                        INSERT INTO purchase_orders
                        (po_number, store_id, supplier_id, order_date, expected_date, status, 
                         total_amount, notes)
                        VALUES ($1, $2, $3, CURRENT_DATE, $4, 'pending', $5, $6)
                        RETURNING id
                    """
                    
                    po_id = await conn.fetchval(
                        po_query,
                        po_number, store_id, supplier_id, expected_date, 
                        total_amount, notes
                    )
                    
                    # Add items to purchase order
                    for item in items:
                        # Get product ID
                        product_id = await conn.fetchval(
                            "SELECT id FROM products WHERE sku = $1", item['sku']
                        )
                        
                        item_query = """
                            INSERT INTO purchase_order_items
                            (purchase_order_id, product_id, sku, batch_lot,
                             quantity_ordered, unit_cost,
                             case_gtin, gtin_barcode, each_gtin,
                             vendor, brand, packaged_on_date, shipped_qty,
                             uom, uom_conversion, uom_conversion_qty)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9,
                                    $10, $11, $12, $13, $14, $15, $16)
                        """
                        
                        await conn.execute(
                            item_query,
                            po_id,
                            product_id,
                            item['sku'],
                            item.get('batch_lot'),
                            item['quantity'],
                            item['unit_cost'],
                            item.get('case_gtin'),
                            item.get('gtin_barcode'),
                            item.get('each_gtin'),
                            item.get('vendor'),
                            item.get('brand'),
                            item.get('packaged_on_date'),
                            item.get('shipped_qty', item['quantity']),
                            item.get('uom'),
                            item.get('uom_conversion'),
                            item.get('uom_conversion_qty')
                        )
                        
                        # Update in-transit quantity for store
                        await conn.execute("""
                            UPDATE store_inventory
                            SET quantity_in_transit = quantity_in_transit + $3,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND sku = $2
                        """, store_id, item['sku'], item['quantity'])
                        
                        # Create record if doesn't exist
                        await conn.execute("""
                            INSERT INTO store_inventory 
                            (store_id, product_id, sku, quantity_on_hand, quantity_available,
                             quantity_reserved, quantity_in_transit)
                            VALUES ($1, $2, $3, 0, 0, 0, $4)
                            ON CONFLICT (store_id, sku) DO UPDATE
                            SET quantity_in_transit = store_inventory.quantity_in_transit + $4
                        """, store_id, product_id, item['sku'], item['quantity'])
                    
                    logger.info(f"Created purchase order {po_number} for store {store_id}")
                    return po_id
                    
        except Exception as e:
            logger.error(f"Error creating store purchase order: {str(e)}")
            raise
    
    async def receive_store_purchase_order(
        self,
        store_id: UUID,
        po_id: UUID,
        received_items: List[Dict[str, Any]],
        receive_date: Optional[date] = None
    ) -> bool:
        """
        Receive items from a purchase order into store inventory
        
        Args:
            store_id: UUID of the store
            po_id: UUID of the purchase order
            received_items: List of received items with quantities
            receive_date: Date of receipt
            
        Returns:
            True if successful
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Verify PO belongs to store
                    po_store_id = await conn.fetchval(
                        "SELECT store_id FROM purchase_orders WHERE id = $1", po_id
                    )
                    
                    if po_store_id != store_id:
                        raise ValueError("Purchase order does not belong to this store")
                    
                    # Process each received item
                    for item in received_items:
                        # Update PO item received quantity
                        await conn.execute("""
                            UPDATE purchase_order_items
                            SET quantity_received = $2,
                                received_date = $3
                            WHERE purchase_order_id = $1 AND sku = $4
                        """, po_id, item['quantity_received'], 
                            receive_date or datetime.now(), item['sku'])
                        
                        # Update store inventory
                        await self.update_store_inventory(
                            store_id=store_id,
                            sku=item['sku'],
                            quantity_change=item['quantity_received'],
                            transaction_type=TransactionType.PURCHASE,
                            reference_id=po_id,
                            batch_lot=item.get('batch_lot'),
                            notes=f"Received from PO {po_id}"
                        )
                    
                    # Update PO status
                    await conn.execute("""
                        UPDATE purchase_orders
                        SET status = 'received',
                            received_date = $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """, po_id, receive_date or datetime.now())
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Error receiving store purchase order: {str(e)}")
            raise
    
    # =====================================================
    # Store Transfer Methods
    # =====================================================
    # Batch-Level Operations
    # =====================================================

    async def adjust_batch_quantity(
        self,
        store_id: UUID,
        sku: str,
        batch_lot: str,
        adjustment: int,
        reason: str
    ) -> bool:
        """
        Adjust quantity for a specific batch

        Args:
            store_id: Store UUID
            sku: Product SKU
            batch_lot: Batch lot number
            adjustment: Quantity adjustment (positive or negative)
            reason: Reason for adjustment

        Returns:
            Success status
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Update batch tracking quantity
                result = await conn.execute("""
                    UPDATE batch_tracking
                    SET quantity_remaining = quantity_remaining + $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE batch_lot = $2
                    AND sku = $3
                    AND store_id = $4
                    AND quantity_remaining + $1 >= 0
                """, adjustment, batch_lot, sku, store_id)

                if result == "UPDATE 0":
                    raise ValueError(f"Batch {batch_lot} not found or insufficient quantity")

                # Record transaction
                await conn.execute("""
                    INSERT INTO ocs_inventory_transactions
                    (sku, transaction_type, quantity, notes, batch_lot, store_id)
                    VALUES ($1, 'adjustment', $2, $3, $4, $5)
                """, sku, adjustment, f"Batch adjustment: {reason}", batch_lot, store_id)

                return True

        except Exception as e:
            logger.error(f"Error adjusting batch quantity: {str(e)}")
            raise

    async def update_inventory_settings(
        self,
        store_id: UUID,
        sku: str,
        retail_price: Optional[Decimal] = None,
        reorder_point: Optional[int] = None,
        reorder_quantity: Optional[int] = None,
        is_available: Optional[bool] = None
    ) -> bool:
        """
        Update inventory settings for a SKU in a store

        Args:
            store_id: Store UUID
            sku: Product SKU
            retail_price: Optional new retail price
            reorder_point: Optional new reorder point
            reorder_quantity: Optional new reorder quantity
            is_available: Optional availability status

        Returns:
            Success status
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build update query dynamically
                update_fields = []
                params = []
                param_counter = 1

                if retail_price is not None:
                    update_fields.append(f"retail_price = ${param_counter}")
                    params.append(retail_price)
                    param_counter += 1

                if reorder_point is not None:
                    update_fields.append(f"reorder_point = ${param_counter}")
                    params.append(reorder_point)
                    param_counter += 1

                if reorder_quantity is not None:
                    update_fields.append(f"reorder_quantity = ${param_counter}")
                    params.append(reorder_quantity)
                    param_counter += 1

                if is_available is not None:
                    update_fields.append(f"is_available = ${param_counter}")
                    params.append(is_available)
                    param_counter += 1

                if not update_fields:
                    return True  # Nothing to update

                # Add timestamp update
                update_fields.append("updated_at = CURRENT_TIMESTAMP")

                # Add WHERE clause parameters
                params.extend([store_id, sku])

                query = f"""
                    UPDATE ocs_inventory
                    SET {', '.join(update_fields)}
                    WHERE store_id = ${param_counter} AND sku = ${param_counter + 1}
                """

                result = await conn.execute(query, *params)
                return result != "UPDATE 0"

        except Exception as e:
            logger.error(f"Error updating inventory settings: {str(e)}")
            raise

    # =====================================================
    # Transfer Management
    # =====================================================

    async def create_store_transfer(
        self,
        from_store_id: UUID,
        to_store_id: UUID,
        items: List[Dict[str, Any]],
        notes: Optional[str] = None
    ) -> UUID:
        """
        Create inventory transfer between stores
        
        Args:
            from_store_id: Source store UUID
            to_store_id: Destination store UUID
            items: List of items to transfer
            notes: Optional transfer notes
            
        Returns:
            UUID of transfer record
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Create transfer record
                    transfer_id = await conn.fetchval("""
                        INSERT INTO inventory_transfers
                        (from_store_id, to_store_id, status, notes)
                        VALUES ($1, $2, 'pending', $3)
                        RETURNING id
                    """, from_store_id, to_store_id, notes)
                    
                    # Process each item
                    for item in items:
                        # Reduce inventory in source store
                        await self.update_store_inventory(
                            store_id=from_store_id,
                            sku=item['sku'],
                            quantity_change=-item['quantity'],
                            transaction_type=TransactionType.TRANSFER,
                            reference_id=transfer_id,
                            notes=f"Transfer to store {to_store_id}"
                        )
                        
                        # Add to in-transit for destination store
                        product_id = await conn.fetchval(
                            "SELECT id FROM products WHERE sku = $1", item['sku']
                        )
                        
                        await conn.execute("""
                            INSERT INTO store_inventory 
                            (store_id, product_id, sku, quantity_on_hand, quantity_available,
                             quantity_reserved, quantity_in_transit)
                            VALUES ($1, $2, $3, 0, 0, 0, $4)
                            ON CONFLICT (store_id, sku) DO UPDATE
                            SET quantity_in_transit = store_inventory.quantity_in_transit + $4
                        """, to_store_id, product_id, item['sku'], item['quantity'])
                        
                        # Record transfer item
                        await conn.execute("""
                            INSERT INTO inventory_transfer_items
                            (transfer_id, sku, quantity, batch_lot)
                            VALUES ($1, $2, $3, $4)
                        """, transfer_id, item['sku'], item['quantity'], 
                            item.get('batch_lot'))
                    
                    return transfer_id
                    
        except Exception as e:
            logger.error(f"Error creating store transfer: {str(e)}")
            raise
    
    # =====================================================
    # Store Inventory Statistics
    # =====================================================
    
    async def get_store_inventory_stats(self, store_id: UUID) -> Dict[str, Any]:
        """
        Get inventory statistics for a store
        
        Args:
            store_id: UUID of the store
            
        Returns:
            Dict with inventory statistics
        """
        try:
            async with self.db_pool.acquire() as conn:
                stats_query = """
                    SELECT 
                        COUNT(DISTINCT sku) as total_skus,
                        SUM(quantity_on_hand) as total_quantity,
                        SUM(quantity_available * unit_cost) as total_value,
                        COUNT(CASE WHEN quantity_available <= reorder_point
                              AND quantity_available > 0 THEN 1 END) as low_stock_items,
                        COUNT(CASE WHEN quantity_available = 0 THEN 1 END) as out_of_stock_items,
                        0 as items_in_transit,
                        0 as total_in_transit
                    FROM ocs_inventory
                    WHERE store_id = $1 AND is_available = true
                """
                
                result = await conn.fetchrow(stats_query, store_id)
                
                return {
                    'total_skus': result['total_skus'] or 0,
                    'total_quantity': result['total_quantity'] or 0,
                    'total_value': float(result['total_value'] or 0),
                    'low_stock_items': result['low_stock_items'] or 0,
                    'out_of_stock_items': result['out_of_stock_items'] or 0,
                    'items_in_transit': result['items_in_transit'] or 0,
                    'total_in_transit': result['total_in_transit'] or 0
                }
                
        except Exception as e:
            logger.error(f"Error getting store inventory stats: {str(e)}")
            raise


# =====================================================
# Service Factory
# =====================================================

def create_store_inventory_service(db_pool: asyncpg.Pool) -> StoreInventoryService:
    """
    Factory function to create store inventory service instance
    
    Args:
        db_pool: Database connection pool
        
    Returns:
        StoreInventoryService instance
    """
    return StoreInventoryService(db_pool)