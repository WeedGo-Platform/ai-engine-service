"""
POS Transaction API Endpoints
Uses unified orders system - all POS transactions create orders with order_source='pos'
No separate pos_transactions table needed
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import asyncpg
import os
import json
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["pos-transactions"])

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
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=1,
            max_size=10
        )
    return db_pool


# Pydantic Models for POS
class BatchInfo(BaseModel):
    """Batch/lot information for inventory tracking"""
    batch_lot: str
    quantity_remaining: Optional[int] = None
    case_gtin: Optional[str] = None
    each_gtin: Optional[str] = None
    packaged_on_date: Optional[str] = None
    location_code: Optional[str] = None


class POSCartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int
    discount: Optional[float] = 0
    discount_type: Optional[str] = 'percentage'
    promotion: Optional[str] = None
    batch: Optional[BatchInfo] = None  # Batch tracking support


class POSPaymentDetails(BaseModel):
    cash_amount: Optional[float] = None
    card_amount: Optional[float] = None
    change_given: Optional[float] = None
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None


class POSTransactionCreate(BaseModel):
    store_id: str
    cashier_id: str
    customer_id: Optional[str] = None
    items: List[POSCartItem]
    subtotal: float
    discounts: float
    tax: float
    total: float
    payment_method: str
    payment_details: Optional[POSPaymentDetails] = None
    status: str = 'completed'
    receipt_number: str
    notes: Optional[str] = None



@router.post("/pos/transactions")
async def create_pos_transaction(transaction: POSTransactionCreate):
    """Create a new POS transaction (now creates an order)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():  # Ensure atomicity - rollback on any failure
                # Parse store_id and customer_id as UUIDs
                store_uuid = None
                try:
                    store_uuid = uuid.UUID(transaction.store_id)
                except:
                    logger.warning(f"Invalid store UUID: {transaction.store_id}")

                customer_uuid = None
                if transaction.customer_id and transaction.customer_id not in ['anonymous', 'anon']:
                    try:
                        customer_uuid = uuid.UUID(transaction.customer_id)
                    except:
                        pass

                # Get user_id from customer if exists
                user_id = None
                if customer_uuid:
                    user_row = await conn.fetchrow(
                        "SELECT user_id FROM profiles WHERE id = $1",
                        customer_uuid
                    )
                    if user_row:
                        user_id = user_row['user_id']

                # Prepare items in the format expected by orders table
                order_items = [item.dict() for item in transaction.items]

                # Create order using the unified system
                order_number = transaction.receipt_number or f"POS-{int(datetime.now().timestamp())}"

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
                        'pos', $13, TRUE, $14, $15::jsonb
                    )
                    RETURNING id::text as id, created_at as timestamp
                """
    
                pos_metadata = {
                    'cashier_id': transaction.cashier_id,
                    'store_id_text': transaction.store_id,
                    'notes': transaction.notes,
                    'created_via': 'pos_terminal'
                }
    
                payment_status = 'paid' if transaction.status == 'completed' else 'pending'
    
                row = await conn.fetchrow(
                    query,
                    order_number,  # 1
                    user_id,  # 2
                    customer_uuid,  # 3
                    store_uuid,  # 4
                    json.dumps(order_items),  # 5
                    Decimal(str(transaction.subtotal)),  # 6
                    Decimal(str(transaction.tax)),  # 7
                    Decimal(str(transaction.discounts)),  # 8
                    Decimal(str(transaction.total)),  # 9
                    payment_status,  # 10
                    transaction.payment_method,  # 11
                    json.dumps(transaction.payment_details.dict() if transaction.payment_details else {}),  # 12
                    transaction.status,  # 13
                    transaction.receipt_number,  # 14
                    json.dumps(pos_metadata)  # 15
                )
    
                # Build result from transaction data
                result = {
                    'id': row['id'],
                    'store_id': transaction.store_id,
                    'cashier_id': transaction.cashier_id,
                    'customer_id': transaction.customer_id,
                    'items': order_items,
                    'subtotal': transaction.subtotal,
                    'discounts': transaction.discounts,
                    'tax': transaction.tax,
                    'total': transaction.total,
                    'payment_method': transaction.payment_method,
                    'payment_details': transaction.payment_details.dict() if transaction.payment_details else {},
                    'status': transaction.status,
                    'receipt_number': transaction.receipt_number,
                    'notes': transaction.notes,
                    'timestamp': row['timestamp'].isoformat()
                }
    
                # STEP 1: Validate inventory availability BEFORE processing (Strict Mode)
                inventory_validation_failures = []
    
                for item in transaction.items:
                    sku = item.product.get('sku') or item.product.get('id')
    
                    if not sku:
                        inventory_validation_failures.append({
                            'product': item.product.get('name', 'Unknown'),
                            'reason': 'Missing SKU in product data'
                        })
                        continue
    
                    # Check if inventory record exists with sufficient quantity (SKU-level check only)
                    # Use case-insensitive comparison with LOWER() to match SKU variations
                    check_query = """
                        SELECT id, sku, quantity_available, quantity_on_hand
                        FROM ocs_inventory
                        WHERE store_id = $1 AND LOWER(TRIM(sku)) = LOWER(TRIM($2))
                    """
                    check_params = [store_uuid, sku]

                    inventory_record = await conn.fetchrow(check_query, *check_params)
    
                    if not inventory_record:
                        inventory_validation_failures.append({
                            'sku': sku,
                            'quantity_requested': item.quantity,
                            'reason': f'Inventory record not found for SKU {sku}'
                        })
                    elif inventory_record['quantity_available'] < item.quantity:
                        inventory_validation_failures.append({
                            'sku': sku,
                            'quantity_requested': item.quantity,
                            'quantity_available': inventory_record['quantity_available'],
                            'reason': f'Insufficient stock (requested {item.quantity}, available {inventory_record["quantity_available"]})'
                        })
    
                # STRICT MODE: Fail transaction if ANY inventory validation fails
                if inventory_validation_failures:
                    logger.error(f"Transaction validation failed for {transaction.receipt_number}: {inventory_validation_failures}")
                    raise HTTPException(
                        status_code=400,
                        detail={
                            'error': 'Insufficient inventory',
                            'validation_failures': inventory_validation_failures,
                            'message': f'{len(inventory_validation_failures)} item(s) have insufficient stock or missing inventory records'
                        }
                    )
    
                # STEP 2: Update inventory for each item (SKU-level) and consume batches (FIFO)
                inventory_updates_successful = []
                inventory_update_failures = []
                order_id = uuid.UUID(row['id'])
    
                for item in transaction.items:
                    sku = item.product.get('sku') or item.product.get('id')
    
                    if not sku:
                        continue  # Already caught in validation
    
                    try:
                        # Update ocs_inventory (SKU-level aggregate)
                        # Use case-insensitive comparison with LOWER() to match SKU variations
                        update_query = """
                            UPDATE ocs_inventory
                            SET quantity_available = quantity_available - $3,
                                quantity_on_hand = quantity_on_hand - $3,
                                last_sold = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE store_id = $1 AND LOWER(TRIM(sku)) = LOWER(TRIM($2)) AND quantity_available >= $3
                            RETURNING id, sku, quantity_available, quantity_on_hand
                        """

                        result_row = await conn.fetchrow(update_query, store_uuid, sku, item.quantity)
    
                        if not result_row:
                            # This should not happen due to validation, but handle it anyway
                            error_msg = f"Inventory update returned no rows for SKU={sku} (insufficient stock or concurrent update)"
                            logger.error(error_msg)
                            inventory_update_failures.append({
                                'sku': sku,
                                'reason': 'Update returned no rows (insufficient stock or concurrent update)'
                            })
                            continue
    
                        # BATCH TRACKING: Every POS sale MUST have a batch (from barcode scan)
                        # No FIFO/LIFO - exact batch is required
                        scanned_batch_lot = item.batch.batch_lot if item.batch else None
    
                        if not scanned_batch_lot:
                            error_msg = f"No batch specified for SKU={sku}. POS sales require batch tracking via barcode scanning."
                            logger.error(f"POS ERROR: {error_msg}")
                            inventory_update_failures.append({
                                'sku': sku,
                                'reason': error_msg
                            })
                            continue
    
                        # Get the exact scanned batch
                        logger.info(f"POS: Processing scanned batch {scanned_batch_lot} for SKU {sku}")

                        # Use case-insensitive comparison for SKU matching
                        batch_query = """
                            SELECT id, batch_lot, quantity_remaining, unit_cost
                            FROM batch_tracking
                            WHERE store_id = $1 AND LOWER(TRIM(sku)) = LOWER(TRIM($2)) AND batch_lot = $3
                              AND is_active = TRUE AND quantity_remaining > 0
                        """
                        exact_batch = await conn.fetchrow(batch_query, store_uuid, sku, scanned_batch_lot)
    
                        if not exact_batch:
                            error_msg = f"Scanned batch {scanned_batch_lot} not found or has no remaining quantity"
                            logger.error(f"POS ERROR: {error_msg}")
                            inventory_update_failures.append({
                                'sku': sku,
                                'batch': scanned_batch_lot,
                                'reason': error_msg
                            })
                            continue
    
                        if exact_batch['quantity_remaining'] < item.quantity:
                            error_msg = f"Scanned batch {scanned_batch_lot} has insufficient quantity (need {item.quantity}, have {exact_batch['quantity_remaining']})"
                            logger.error(f"POS ERROR: {error_msg}")
                            inventory_update_failures.append({
                                'sku': sku,
                                'batch': scanned_batch_lot,
                                'quantity_requested': item.quantity,
                                'quantity_available': exact_batch['quantity_remaining'],
                                'reason': error_msg
                            })
                            continue
    
                        # Consume from exact batch
                        new_quantity = exact_batch['quantity_remaining'] - item.quantity
                        is_depleted = new_quantity == 0
    
                        await conn.execute(
                            """
                            UPDATE batch_tracking
                            SET quantity_remaining = $2,
                                is_active = $3,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = $1
                            """,
                            exact_batch['id'],
                            new_quantity,
                            not is_depleted
                        )
    
                        batches_consumed = [{
                            'batch_lot': exact_batch['batch_lot'],
                            'consumed': item.quantity,
                            'remaining': new_quantity
                        }]
    
                        logger.info(f"✅ Consumed {item.quantity} from scanned batch {scanned_batch_lot}, remaining: {new_quantity}")

                        # Log the inventory transaction with required columns
                        quantity_before = result_row['quantity_on_hand'] + item.quantity  # Before the deduction
                        quantity_after = result_row['quantity_on_hand']  # After the deduction

                        await conn.execute(
                            """
                            INSERT INTO ocs_inventory_transactions (
                                store_id, sku, transaction_type, quantity, quantity_change,
                                quantity_before, quantity_after, batch_lot,
                                reference_id, reference_type, notes, created_at
                            ) VALUES ($1, $2, 'sale', $3, $4, $5, $6, $7, $8, 'pos_transaction', $9, CURRENT_TIMESTAMP)
                            """,
                            store_uuid,
                            sku,
                            -item.quantity,  # Negative for deduction
                            -item.quantity,  # quantity_change (same as quantity for backward compatibility)
                            quantity_before,
                            quantity_after,
                            scanned_batch_lot,
                            order_id,
                            f"POS sale - Receipt: {transaction.receipt_number}, Batch: {scanned_batch_lot}"
                        )
    
                        inventory_updates_successful.append({
                            'sku': sku,
                            'quantity_deducted': item.quantity,
                            'quantity_remaining': result_row['quantity_available'],
                            'batches_consumed': batches_consumed
                        })
    
                        logger.info(
                            f"✅ Inventory updated: SKU={sku}, "
                            f"Deducted={item.quantity}, Remaining={result_row['quantity_available']}, "
                            f"Batches consumed={len(batches_consumed)}"
                        )
    
                    except Exception as e:
                        logger.error(f"❌ Failed to update inventory for SKU={sku}: {e}")
                        inventory_update_failures.append({
                            'sku': sku,
                            'error': str(e)
                        })
    
                # STRICT MODE: Fail entire transaction if ANY inventory update failed
                if inventory_update_failures:
                    logger.critical(
                        f"CRITICAL: Inventory update failed for transaction {order_id}. "
                        f"Failures: {inventory_update_failures}. Rolling back transaction."
                    )
                    # Rollback by raising exception (transaction will be aborted)
                    raise HTTPException(
                        status_code=500,
                        detail={
                            'error': 'Inventory update failed',
                            'failures': inventory_update_failures,
                            'message': 'Transaction aborted due to inventory update failure'
                        }
                    )
    
                # STEP 3: Update customer loyalty points AFTER successful inventory update
                if user_id:
                    try:
                        points_earned = int(transaction.total)  # 1 point per dollar
                        await conn.execute(
                            "UPDATE profiles SET loyalty_points = COALESCE(loyalty_points, 0) + $1 WHERE user_id = $2",
                            points_earned,
                            user_id
                        )
                        logger.info(f"Loyalty points awarded: {points_earned} points to user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to update loyalty points: {e}")
    
                # Add inventory update status to response
                result['inventory_updates'] = {
                    'successful': inventory_updates_successful,
                    'total_items': len(transaction.items),
                    'updated_count': len(inventory_updates_successful)
                }
    
                logger.info(
                    f"✅ Transaction {order_id} completed successfully. "
                    f"Inventory updates: {len(inventory_updates_successful)}/{len(transaction.items)}"
                )
    
                return result
    except HTTPException:
        # Re-raise HTTPExceptions (400, 404, etc.) without modification
        raise
    except Exception as e:
        logger.error(f"Error creating POS transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pos/transactions")
async def get_pos_transactions(
    store_id: str,
    status: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 100
):
    """Get POS transactions (orders) for a store"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            conditions = ["order_source IN ('pos', 'kiosk')"]
            params = []
            param_num = 1

            # Handle store_id - could be UUID or text stored in metadata
            try:
                store_uuid = uuid.UUID(store_id)
                conditions.append(f"store_id = ${param_num}")
                params.append(store_uuid)
                param_num += 1
            except:
                conditions.append(f"pos_metadata->>'store_id_text' = ${param_num}")
                params.append(store_id)
                param_num += 1

            if status:
                conditions.append(f"order_status = ${param_num}")
                params.append(status)
                param_num += 1

            if date:
                conditions.append(f"DATE(created_at) = ${param_num}")
                params.append(datetime.strptime(date, '%Y-%m-%d').date())
                param_num += 1

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT
                    id::text as id,
                    order_number,
                    items,
                    subtotal,
                    tax_amount as tax,
                    discount_amount as discounts,
                    total_amount as total,
                    payment_method,
                    payment_details,
                    order_status as status,
                    receipt_number,
                    pos_metadata,
                    created_at as timestamp
                FROM orders
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_num}
            """
            params.append(limit)

            rows = await conn.fetch(query, *params)
            
            transactions = []
            for row in rows:
                pos_metadata = json.loads(row['pos_metadata']) if row['pos_metadata'] else {}
                trans = {
                    'id': row['id'],
                    'store_id': store_id,
                    'cashier_id': pos_metadata.get('cashier_id', 'unknown'),
                    'items': json.loads(row['items']) if row['items'] else [],
                    'subtotal': float(row['subtotal']),
                    'tax': float(row['tax']),
                    'discounts': float(row['discounts']),
                    'total': float(row['total']),
                    'payment_method': row['payment_method'],
                    'payment_details': json.loads(row['payment_details']) if row['payment_details'] else {},
                    'status': row['status'],
                    'receipt_number': row['receipt_number'],
                    'notes': pos_metadata.get('notes'),
                    'timestamp': row['timestamp'].isoformat()
                }
                transactions.append(trans)
            
            return transactions
    except Exception as e:
        logger.error(f"Error getting POS transactions: {str(e)}")
        return []


@router.post("/pos/transactions/park")
async def park_pos_transaction(transaction: POSTransactionCreate):
    """Park a POS transaction for later"""
    transaction.status = 'parked'
    return await create_pos_transaction(transaction)


@router.get("/pos/transactions/parked")
async def get_parked_transactions(store_id: str):
    """Get all parked transactions for a store"""
    return await get_pos_transactions(store_id, status='parked')


@router.put("/pos/transactions/{transaction_id}/resume")
async def resume_pos_transaction(transaction_id: str):
    """Resume a parked transaction (order)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT
                    id::text as id,
                    items,
                    subtotal,
                    tax_amount as tax,
                    discount_amount as discounts,
                    total_amount as total,
                    payment_method,
                    payment_details,
                    receipt_number,
                    pos_metadata
                FROM orders
                WHERE id = $1::uuid AND order_status = 'parked' AND order_source IN ('pos', 'kiosk')
            """

            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Parked transaction not found")

            # Mark as pending (resumed)
            await conn.execute(
                "UPDATE orders SET order_status = 'pending', updated_at = NOW() WHERE id = $1::uuid",
                transaction_id
            )

            pos_metadata = json.loads(row['pos_metadata']) if row['pos_metadata'] else {}
            transaction = {
                'id': transaction_id,
                'store_id': pos_metadata.get('store_id_text'),
                'cashier_id': pos_metadata.get('cashier_id'),
                'items': json.loads(row['items']) if row['items'] else [],
                'subtotal': float(row['subtotal']),
                'tax': float(row['tax']),
                'discounts': float(row['discounts']),
                'total': float(row['total']),
                'payment_method': row['payment_method'],
                'payment_details': json.loads(row['payment_details']) if row['payment_details'] else {},
                'receipt_number': row['receipt_number'],
                'notes': pos_metadata.get('notes')
            }
            return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pos/transactions/{transaction_id}/refund")
async def refund_pos_transaction(transaction_id: str):
    """Process a refund for a POS transaction (order)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get original order
            query = """
                SELECT items, total_amount, user_id, customer_id
                FROM orders
                WHERE id = $1::uuid AND order_status = 'completed' AND order_source = 'pos'
            """

            row = await conn.fetchrow(query, transaction_id)
            if not row:
                raise HTTPException(status_code=404, detail="Transaction not found")

            items = json.loads(row['items']) if row['items'] else []
            total_amount = row['total_amount']
            user_id = row['user_id']

            # Update status to refunded
            await conn.execute(
                "UPDATE orders SET order_status = 'refunded', payment_status = 'refunded', updated_at = NOW() WHERE id = $1::uuid",
                transaction_id
            )
            
            # Restore inventory
            for item in items:
                product_id = item.get('product', {}).get('id')
                if product_id:
                    try:
                        await conn.execute(
                            """
                            UPDATE products
                            SET available_quantity = available_quantity + $1
                            WHERE id = $2::uuid
                            """,
                            item.get('quantity', 0),
                            product_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to restore inventory for product {product_id}: {e}")

            # Deduct loyalty points if applicable
            if user_id:
                try:
                    points_to_deduct = int(total_amount)
                    await conn.execute(
                        "UPDATE profiles SET loyalty_points = GREATEST(0, loyalty_points - $1) WHERE user_id = $2",
                        points_to_deduct,
                        user_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to deduct loyalty points: {e}")
            
            return {"success": True, "message": f"Transaction {transaction_id} refunded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))