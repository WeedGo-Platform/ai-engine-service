"""
Inventory Management Service
Handles inventory tracking, purchase orders, and stock management
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID, uuid4
import asyncpg
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for managing inventory and purchase orders"""
    
    def __init__(self, db_connection):
        """Initialize inventory service with database connection"""
        self.db = db_connection
    
    async def get_inventory_status(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get current inventory status for a SKU"""
        try:
            query = """
                SELECT 
                    sku,
                    quantity_on_hand,
                    quantity_available,
                    quantity_reserved,
                    unit_cost,
                    retail_price,
                    reorder_point,
                    reorder_quantity,
                    last_restock_date
                FROM ocs_inventory
                WHERE sku = $1
            """
            
            result = await self.db.fetchrow(query, sku)
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting inventory status: {str(e)}")
            raise
    
    async def update_inventory(self, sku: str, quantity_change: int, 
                             transaction_type: str, reference_id: Optional[UUID] = None,
                             notes: Optional[str] = None) -> bool:
        """Update inventory levels and record transaction"""
        try:
            async with self.db.transaction():
                # Update inventory levels
                if transaction_type == 'sale':
                    update_query = """
                        UPDATE ocs_inventory
                        SET quantity_available = quantity_available - $2,
                            quantity_on_hand = quantity_on_hand - $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE sku = $1 AND quantity_available >= $2
                        RETURNING quantity_on_hand
                    """
                elif transaction_type == 'purchase':
                    update_query = """
                        UPDATE ocs_inventory
                        SET quantity_available = quantity_available + $2,
                            quantity_on_hand = quantity_on_hand + $2,
                            last_restock_date = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE sku = $1
                        RETURNING quantity_on_hand
                    """
                elif transaction_type == 'adjustment':
                    update_query = """
                        UPDATE ocs_inventory
                        SET quantity_available = quantity_available + $2,
                            quantity_on_hand = quantity_on_hand + $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE sku = $1
                        RETURNING quantity_on_hand
                    """
                else:
                    raise ValueError(f"Invalid transaction type: {transaction_type}")
                
                result = await self.db.fetchval(update_query, sku, abs(quantity_change))
                
                if result is None:
                    # If SKU doesn't exist or insufficient stock, create new record
                    if transaction_type == 'purchase':
                        insert_query = """
                            INSERT INTO ocs_inventory (sku, quantity_on_hand, quantity_available, 
                                                 last_restock_date)
                            VALUES ($1, $2, $2, CURRENT_TIMESTAMP)
                            RETURNING quantity_on_hand
                        """
                        result = await self.db.fetchval(insert_query, sku, abs(quantity_change))
                    else:
                        return False
                
                # Record transaction
                transaction_query = """
                    INSERT INTO ocs_inventory_transactions
                    (sku, transaction_type, reference_id, quantity, running_balance, notes)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """
                
                await self.db.execute(
                    transaction_query,
                    sku, transaction_type, reference_id, quantity_change, result, notes
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
            raise
    
    async def create_purchase_order(self, supplier_id: UUID, items: List[Dict[str, Any]],
                                   expected_date: date,
                                   notes: Optional[str] = None,
                                   excel_filename: str = None,
                                   store_id: UUID = None,
                                   shipment_id: Optional[str] = None,
                                   container_id: Optional[str] = None,
                                   vendor: Optional[str] = None,
                                   ocs_order_number: Optional[str] = None,
                                   tenant_id: Optional[UUID] = None,
                                   created_by: Optional[UUID] = None,
                                   shipment_date: Optional[date] = None) -> UUID:
        """Create a new purchase order"""
        try:
            async with self.db.transaction():
                # Generate PO number using Excel filename
                # Clean up the filename: remove ASN_ prefix and .xlsx extension
                clean_filename = excel_filename
                if clean_filename and clean_filename.startswith('ASN_'):
                    clean_filename = clean_filename[4:]  # Remove 'ASN_' prefix
                if clean_filename and clean_filename.endswith('.xlsx'):
                    clean_filename = clean_filename[:-5]  # Remove '.xlsx' extension
                elif clean_filename and clean_filename.endswith('.xls'):
                    clean_filename = clean_filename[:-4]  # Remove '.xls' extension

                po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{clean_filename}"

                # Check if PO with this number already exists
                existing_po = await self.db.fetchval(
                    "SELECT id FROM purchase_orders WHERE po_number = $1",
                    po_number
                )

                if existing_po:
                    raise ValueError(
                        f"Purchase order already exists for file: {clean_filename}. This file has already been imported."
                    )
                
                # Calculate total amount
                total_amount = sum(
                    Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
                    for item in items
                )
                
                # Create purchase order
                po_query = """
                    INSERT INTO purchase_orders
                    (po_number, supplier_id, order_date, expected_date, status, total_amount, notes, store_id,
                     shipment_id, container_id, vendor, created_by)
                    VALUES ($1, $2, CURRENT_DATE, $3, 'pending', $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """

                po_id = await self.db.fetchval(
                    po_query,
                    po_number, supplier_id, expected_date, total_amount, notes, store_id,
                    shipment_id, container_id, vendor, created_by
                )
                
                # Add items to purchase order
                for item in items:
                    # Log the gtin_barcode value for debugging
                    gtin_barcode_value = item.get('gtin_barcode')
                    logger.info(f"Processing item {item['sku']}: gtin_barcode={gtin_barcode_value}, case_gtin={item.get('case_gtin')}")

                    item_query = """
                        INSERT INTO purchase_order_items
                        (purchase_order_id, sku, item_name, batch_lot, quantity_ordered,
                         unit_cost, case_gtin, gtin_barcode, each_gtin,
                         vendor, brand, packaged_on_date,
                         shipped_qty, uom, uom_conversion, uom_conversion_qty)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    """

                    await self.db.execute(
                        item_query,
                        po_id,
                        item['sku'],  # SKU from Excel
                        item.get('item_name'),  # From Excel ItemName column
                        item['batch_lot'],  # Required from Excel
                        item['quantity'],
                        Decimal(str(item['unit_cost'])),
                        item['case_gtin'],  # Required from Excel
                        gtin_barcode_value,  # From Excel GTINBarcode column
                        item['each_gtin'],  # Required from Excel
                        item['vendor'],  # Required from Excel
                        item['brand'],  # Required from Excel
                        item['packaged_on_date'],  # Required from Excel
                        item['shipped_qty'],  # Required from Excel
                        item['uom'],  # Required from Excel
                        Decimal(str(item['uom_conversion'])),  # Required from Excel
                        item['uom_conversion_qty']  # Required from Excel
                    )
                
                logger.info(f"Created purchase order {po_number} with {len(items)} items")
                return po_id
                
        except Exception as e:
            logger.error(f"Error creating purchase order: {str(e)}")
            raise
    
    async def _get_applicable_markup(
        self,
        store_id: UUID,
        category: Optional[str],
        sub_category: Optional[str],
        sub_sub_category: Optional[str]
    ) -> Optional[float]:
        """
        Get applicable markup percentage for a product

        Follows hierarchy: sub_sub_category > sub_category > category > store default
        Returns None if no pricing configuration is found (fail-fast approach)
        """
        # Check for specific pricing rule (most specific first)
        query = """
            SELECT markup_percentage
            FROM pricing_rules
            WHERE store_id = $1
            AND ($2::text IS NULL OR category = $2 OR category IS NULL)
            AND ($3::text IS NULL OR sub_category = $3 OR sub_category IS NULL)
            AND ($4::text IS NULL OR sub_sub_category = $4 OR sub_sub_category IS NULL)
            AND is_active = true
            ORDER BY
                CASE
                    WHEN sub_sub_category IS NOT NULL THEN 3
                    WHEN sub_category IS NOT NULL THEN 2
                    WHEN category IS NOT NULL THEN 1
                    ELSE 0
                END DESC
            LIMIT 1
        """

        result = await self.db.fetchrow(query, store_id, category, sub_category, sub_sub_category)

        if result:
            return float(result['markup_percentage'])

        # Fall back to store default markup from store_settings
        settings_query = """
            SELECT value->>'default_markup_percentage' as markup
            FROM store_settings
            WHERE store_id = $1 AND category = 'pricing' AND key = 'default_markup'
        """

        settings = await self.db.fetchrow(settings_query, store_id)
        if settings and settings['markup']:
            return float(settings['markup'])

        # No pricing configuration found - return None to trigger validation error
        return None

    async def receive_purchase_order(self, po_id: UUID,
                                    received_items: List[Dict[str, Any]],
                                    received_by: Optional[UUID] = None) -> bool:
        """Process receipt of purchase order items"""
        try:
            # Get store_id from purchase order (before transaction)
            store_query = """
                SELECT store_id FROM purchase_orders WHERE id = $1
            """
            store_id = await self.db.fetchval(store_query, po_id)

            if not store_id:
                raise ValueError(f"Purchase order {po_id} does not have a store_id. Cannot receive items without a store assignment.")

            # PRE-VALIDATE: Check pricing configuration for all items BEFORE starting transaction
            items_missing_pricing = []

            for item in received_items:
                # Get product category for pricing rule lookup
                category_query = """
                    SELECT category, sub_category, sub_sub_category
                    FROM ocs_product_catalog
                    WHERE LOWER(TRIM(ocs_variant_number)) = LOWER(TRIM($1))
                    LIMIT 1
                """
                product_cat = await self.db.fetchrow(category_query, item['sku'])

                # Check if markup is available
                markup_percentage = await self._get_applicable_markup(
                    store_id,
                    product_cat.get('category') if product_cat else None,
                    product_cat.get('sub_category') if product_cat else None,
                    product_cat.get('sub_sub_category') if product_cat else None
                )

                if markup_percentage is None:
                    # Pricing configuration missing for this item
                    items_missing_pricing.append({
                        'sku': item['sku'],
                        'item_name': item.get('item_name', 'Unknown'),
                        'category': product_cat.get('category') if product_cat else None,
                        'sub_category': product_cat.get('sub_category') if product_cat else None,
                        'sub_sub_category': product_cat.get('sub_sub_category') if product_cat else None
                    })

            # If any items are missing pricing configuration, fail fast with clear error
            if items_missing_pricing:
                error_details = {
                    'error': 'pricing_configuration_required',
                    'message': f'Cannot receive purchase order: {len(items_missing_pricing)} item(s) missing pricing configuration',
                    'affected_items': items_missing_pricing,
                    'remediation': {
                        'required_action': 'Configure pricing before receiving this purchase order',
                        'options': [
                            {
                                'option': 'Set store-wide default markup',
                                'description': 'Navigate to Store Settings → Default Price Configuration and set a store-wide default markup percentage',
                                'applies_to': 'All items in this store without category-specific rules'
                            },
                            {
                                'option': 'Set category-specific markup',
                                'description': 'Navigate to Store Settings → Default Price Configuration and configure markup for affected categories',
                                'applies_to': 'Items in specific categories/subcategories'
                            }
                        ]
                    }
                }

                logger.warning(
                    f"Purchase order {po_id} cannot be received - missing pricing config for {len(items_missing_pricing)} items. "
                    f"Store ID: {store_id}"
                )

                # Raise ValueError with structured error details
                raise ValueError(str(error_details))

            # All items have pricing configuration - proceed with transaction
            async with self.db.transaction():
                # Update PO status - also set received_by and approved_by (auto-approve)
                status_query = """
                    UPDATE purchase_orders
                    SET status = 'received',
                        received_date = CURRENT_TIMESTAMP,
                        received_by = $2,
                        approved_by = $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """
                await self.db.execute(status_query, po_id, received_by)

                # Process each received item
                for item in received_items:
                    # Update PO item
                    item_query = """
                        UPDATE purchase_order_items
                        SET quantity_received = $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE purchase_order_id = $1 AND sku = $3
                    """
                    
                    await self.db.execute(
                        item_query,
                        po_id,
                        item['quantity_received'],
                        item['sku']
                    )
                    
                    # Get product category for pricing rule lookup
                    category_query = """
                        SELECT category, sub_category, sub_sub_category
                        FROM ocs_product_catalog
                        WHERE LOWER(TRIM(ocs_variant_number)) = LOWER(TRIM($1))
                        LIMIT 1
                    """
                    product_cat = await self.db.fetchrow(category_query, item['sku'])

                    # Calculate retail price using pricing rules
                    unit_cost = Decimal(str(item['unit_cost']))
                    markup_percentage = await self._get_applicable_markup(
                        store_id,
                        product_cat.get('category') if product_cat else None,
                        product_cat.get('sub_category') if product_cat else None,
                        product_cat.get('sub_sub_category') if product_cat else None
                    )

                    # Calculate: retail_price = unit_cost × (1 + markup%)
                    calculated_retail_price = unit_cost * (1 + Decimal(str(markup_percentage)) / 100)

                    # Update or create inventory record with calculated retail price
                    inv_query = """
                        INSERT INTO ocs_inventory (store_id, sku, quantity_on_hand, quantity_available,
                                             unit_cost, retail_price, last_restock_date)
                        VALUES ($1, $2, $3, $3, $4, $5, CURRENT_TIMESTAMP)
                        ON CONFLICT (store_id, sku) DO UPDATE
                        SET quantity_on_hand = ocs_inventory.quantity_on_hand + $3,
                            quantity_available = ocs_inventory.quantity_available + $3,
                            unit_cost = ((ocs_inventory.quantity_on_hand * ocs_inventory.unit_cost) +
                                        ($3 * $4)) / (ocs_inventory.quantity_on_hand + $3),
                            retail_price = COALESCE(ocs_inventory.retail_price, $5),
                            last_restock_date = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING quantity_on_hand
                    """

                    new_balance = await self.db.fetchval(
                        inv_query,
                        store_id,
                        item['sku'],
                        item['quantity_received'],
                        unit_cost,
                        calculated_retail_price  # Calculated using markup rules
                    )
                    
                    # Record inventory transaction with audit trail
                    # Calculate before/after quantities for legacy columns
                    quantity_received = item['quantity_received']
                    quantity_after = new_balance  # Balance after adding items
                    quantity_before = quantity_after - quantity_received  # Balance before adding

                    trans_query = """
                        INSERT INTO ocs_inventory_transactions
                        (store_id, sku, transaction_type, reference_id, reference_type,
                         quantity_change, quantity_before, quantity_after,
                         batch_lot, quantity, unit_cost, running_balance)
                        VALUES ($1, $2, 'purchase', $3, 'purchase_order', $4, $5, $6, $7, $8, $9, $10)
                    """

                    await self.db.execute(
                        trans_query,
                        store_id,
                        item['sku'],
                        po_id,
                        quantity_received,  # quantity_change (positive delta)
                        quantity_before,    # inventory level before
                        quantity_after,     # inventory level after
                        item.get('batch_lot'),
                        quantity_received,  # quantity (duplicate for compatibility)
                        Decimal(str(item['unit_cost'])),
                        new_balance         # running_balance (duplicate for compatibility)
                    )
                    
                    # Track batch (with optional GTIN fields)
                    batch_query = """
                            INSERT INTO batch_tracking
                            (store_id, batch_lot, sku, purchase_order_id, quantity_received,
                             quantity_remaining, unit_cost, received_date,
                             case_gtin, packaged_on_date, gtin_barcode, each_gtin)
                            VALUES ($1, $2, $3, $4, $5, $5, $6, CURRENT_DATE, $7, $8, $9, $10)
                            ON CONFLICT (batch_lot) DO UPDATE
                            SET quantity_received = batch_tracking.quantity_received + $5,
                                quantity_remaining = batch_tracking.quantity_remaining + $5,
                                unit_cost = ((batch_tracking.quantity_remaining * batch_tracking.unit_cost) +
                                            ($5 * $6)) / (batch_tracking.quantity_remaining + $5),
                                case_gtin = COALESCE(NULLIF($7, ''), batch_tracking.case_gtin),
                                packaged_on_date = COALESCE($8, batch_tracking.packaged_on_date),
                                gtin_barcode = COALESCE(NULLIF($9, ''), batch_tracking.gtin_barcode),
                                each_gtin = COALESCE(NULLIF($10, ''), batch_tracking.each_gtin)
                        """

                    await self.db.execute(
                        batch_query,
                        store_id,  # Store ID from purchase order
                        item['batch_lot'],  # batch_lot from Excel
                        item['sku'],  # SKU (ocs_sku column removed)
                        po_id,
                        item['quantity_received'],
                        Decimal(str(item['unit_cost'])),
                        item['case_gtin'],  # Required from Excel
                        item['packaged_on_date'],  # Required from Excel
                        item.get('gtin_barcode'),  # From Excel Barcode column
                        item['each_gtin']  # Required from Excel
                    )
                
                logger.info(f"Received purchase order {po_id} with {len(received_items)} items")
                return True
                
        except Exception as e:
            logger.error(f"Error receiving purchase order: {str(e)}")
            raise
    
    async def get_low_stock_items(self, threshold_multiplier: float = 1.0) -> List[Dict[str, Any]]:
        """Get items that are at or below reorder point"""
        try:
            query = """
                SELECT 
                    i.sku,
                    pc.product_name as name,
                    i.quantity_available,
                    i.reorder_point,
                    i.reorder_quantity,
                    s.name as last_supplier
                FROM ocs_inventory i
                JOIN ocs_product_catalog pc ON i.sku = pc.ocs_variant_number
                LEFT JOIN (
                    SELECT DISTINCT ON (poi.sku)
                        poi.sku,
                        s.name
                    FROM purchase_order_items poi
                    JOIN purchase_orders po ON poi.purchase_order_id = po.id
                    JOIN suppliers s ON po.supplier_id = s.id
                    ORDER BY poi.sku, po.order_date DESC
                ) s ON i.sku = s.sku
                WHERE i.quantity_available <= (i.reorder_point * $1)
                ORDER BY i.quantity_available ASC
            """
            
            results = await self.db.fetch(query, threshold_multiplier)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting low stock items: {str(e)}")
            raise
    
    async def get_inventory_value_report(self) -> Dict[str, Any]:
        """Get inventory valuation report"""
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT sku) as total_skus,
                    SUM(quantity_on_hand) as total_units,
                    SUM(quantity_on_hand * unit_cost) as total_cost_value,
                    SUM(quantity_on_hand * retail_price) as total_retail_value,
                    AVG(quantity_on_hand * retail_price - quantity_on_hand * unit_cost) as avg_margin
                FROM ocs_inventory
                WHERE quantity_on_hand > 0
            """
            
            result = await self.db.fetchrow(query)
            
            category_query = """
                SELECT 
                    pc.category,
                    COUNT(DISTINCT i.sku) as sku_count,
                    SUM(i.quantity_on_hand) as units,
                    SUM(i.quantity_on_hand * i.unit_cost) as cost_value,
                    SUM(i.quantity_on_hand * i.retail_price) as retail_value
                FROM ocs_inventory i
                JOIN ocs_product_catalog pc ON i.sku = pc.ocs_variant_number
                WHERE i.quantity_on_hand > 0
                GROUP BY pc.category
                ORDER BY retail_value DESC
            """
            
            categories = await self.db.fetch(category_query)
            
            return {
                'summary': dict(result),
                'by_category': [dict(row) for row in categories]
            }
            
        except Exception as e:
            logger.error(f"Error getting inventory value report: {str(e)}")
            raise
    
    async def search_inventory_products(self, search_term: str = None,
                                       category: str = None,
                                       in_stock_only: bool = True,
                                       limit: int = 50) -> List[Dict[str, Any]]:
        """Search products with inventory information including batch details"""
        try:
            query = """
                SELECT 
                    ipv.id,
                    ipv.name,
                    ipv.sku,
                    ipv.category,
                    ipv.strain_type,
                    ipv.thc_percentage,
                    ipv.cbd_percentage,
                    ipv.description,
                    ipv.brand,
                    ipv.quantity_available,
                    ipv.price,
                    ipv.stock_status,
                    bt.batch_lot,
                    bt.case_gtin,
                    bt.packaged_on_date,
                    bt.gtin_barcode,
                    bt.each_gtin,
                    bt.quantity_remaining as batch_quantity,
                    s.name as supplier_name
                FROM inventory_products_view ipv
                LEFT JOIN batch_tracking bt ON ipv.sku = bt.sku AND bt.quantity_remaining > 0
                LEFT JOIN purchase_orders po ON bt.purchase_order_id = po.id
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            if search_term:
                param_count += 1
                query += f" AND (ipv.name ILIKE ${param_count} OR ipv.description ILIKE ${param_count} OR ipv.brand ILIKE ${param_count} OR bt.batch_lot ILIKE ${param_count})"
                params.append(f"%{search_term}%")
            
            if category:
                param_count += 1
                query += f" AND category = ${param_count}"
                params.append(category)
            
            if in_stock_only:
                query += " AND quantity_available > 0"
            
            query += f" ORDER BY quantity_available DESC LIMIT ${param_count + 1}"
            params.append(limit)
            
            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error searching inventory products: {str(e)}")
            raise