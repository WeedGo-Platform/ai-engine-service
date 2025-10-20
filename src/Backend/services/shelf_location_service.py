"""
Shelf Location Management Service
Handles warehouse shelf locations and inventory placement
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
import asyncpg
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class LocationType(Enum):
    """Types of storage locations"""
    STANDARD = "standard"
    COLD_STORAGE = "cold_storage"
    SECURE = "secure"
    BULK = "bulk"
    DISPLAY = "display"


class MovementType(Enum):
    """Types of inventory movements"""
    RECEIVE = "receive"
    PICK = "pick"
    TRANSFER = "transfer"
    CYCLE_COUNT = "cycle_count"
    RETURN = "return"


class ShelfLocationService:
    """Service for managing shelf locations and inventory placement"""
    
    def __init__(self, db_connection):
        """Initialize shelf location service with database connection"""
        self.db = db_connection
    
    # ==================== Location Management ====================
    
    async def create_location(self, store_id: UUID, zone: str, aisle: str = None,
                            shelf: str = None, bin: str = None,
                            location_type: LocationType = LocationType.STANDARD,
                            max_weight_kg: float = None, max_volume_m3: float = None,
                            temperature_range: str = None, notes: str = None) -> UUID:
        """Create a new shelf location"""
        try:
            query = """
                INSERT INTO shelf_locations 
                (store_id, zone, aisle, shelf, bin, location_type,
                 max_weight_kg, max_volume_m3, temperature_range, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """
            
            location_id = await self.db.fetchval(
                query, store_id, zone, aisle, shelf, bin, location_type.value,
                max_weight_kg, max_volume_m3, temperature_range, notes
            )
            
            logger.info(f"Created shelf location {location_id} in store {store_id}")
            return location_id
            
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Location {zone}-{aisle}-{shelf}-{bin} already exists in store")
        except Exception as e:
            logger.error(f"Error creating shelf location: {str(e)}")
            raise
    
    async def get_location(self, location_id: UUID) -> Optional[Dict[str, Any]]:
        """Get shelf location details"""
        try:
            query = """
                SELECT 
                    id, store_id, zone, aisle, shelf, bin,
                    location_code, location_type, max_weight_kg,
                    max_volume_m3, temperature_range, is_active,
                    is_available, notes, created_at, updated_at
                FROM shelf_locations
                WHERE id = $1
            """
            
            result = await self.db.fetchrow(query, location_id)
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting location: {str(e)}")
            raise
    
    async def list_locations(self, store_id: UUID, location_type: LocationType = None,
                           is_available: bool = None, zone: str = None,
                           limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
        """List shelf locations with filters"""
        try:
            # Build query with filters
            conditions = ["store_id = $1", "is_active = true"]
            params = [store_id]
            param_count = 1
            
            if location_type:
                param_count += 1
                conditions.append(f"location_type = ${param_count}")
                params.append(location_type.value)
            
            if is_available is not None:
                param_count += 1
                conditions.append(f"is_available = ${param_count}")
                params.append(is_available)
            
            if zone:
                param_count += 1
                conditions.append(f"zone = ${param_count}")
                params.append(zone)
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) FROM shelf_locations
                WHERE {where_clause}
            """
            total = await self.db.fetchval(count_query, *params)
            
            # Get paginated results
            param_count += 1
            params.append(limit)
            param_count += 1
            params.append(offset)
            
            list_query = f"""
                SELECT 
                    id, store_id, zone, aisle, shelf, bin,
                    location_code, location_type, max_weight_kg,
                    max_volume_m3, temperature_range, is_active,
                    is_available, notes, created_at, updated_at
                FROM shelf_locations
                WHERE {where_clause}
                ORDER BY zone, aisle, shelf, bin
                LIMIT ${param_count - 1} OFFSET ${param_count}
            """
            
            results = await self.db.fetch(list_query, *params)
            return [dict(row) for row in results], total
            
        except Exception as e:
            logger.error(f"Error listing locations: {str(e)}")
            raise
    
    async def update_location_availability(self, location_id: UUID, 
                                          is_available: bool) -> bool:
        """Update location availability status"""
        try:
            query = """
                UPDATE shelf_locations
                SET is_available = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING id
            """
            
            result = await self.db.fetchval(query, location_id, is_available)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating location availability: {str(e)}")
            raise
    
    # ==================== Inventory Location Assignment ====================
    
    async def assign_inventory_to_location(self, store_id: UUID, sku: str,
                                          location_id: UUID, quantity: int,
                                          batch_lot: str = None,
                                          is_primary: bool = False,
                                          performed_by: UUID = None) -> UUID:
        """Assign inventory to a shelf location"""
        try:
            async with self.db.transaction():
                # Check if assignment already exists
                check_query = """
                    SELECT id, quantity FROM inventory_locations
                    WHERE store_id = $1 AND sku = $2 AND location_id = $3
                    AND ($4::VARCHAR IS NULL OR batch_lot = $4)
                """
                existing = await self.db.fetchrow(check_query, store_id, sku, location_id, batch_lot)
                
                if existing:
                    # Update existing assignment
                    update_query = """
                        UPDATE inventory_locations
                        SET quantity = quantity + $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING id
                    """
                    assignment_id = await self.db.fetchval(update_query, existing['id'], quantity)
                else:
                    # Create new assignment
                    insert_query = """
                        INSERT INTO inventory_locations
                        (store_id, sku, location_id, quantity, batch_lot, is_primary)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                    """
                    assignment_id = await self.db.fetchval(
                        insert_query, store_id, sku, location_id, quantity, batch_lot, is_primary
                    )
                
                # Log the movement
                log_query = """
                    INSERT INTO location_assignments_log
                    (store_id, sku, batch_lot, to_location_id, quantity_moved,
                     movement_type, performed_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                await self.db.execute(
                    log_query, store_id, sku, batch_lot, location_id, quantity,
                    MovementType.RECEIVE.value, performed_by
                )
                
                # Update batch_tracking if batch_lot is provided
                if batch_lot:
                    batch_update_query = """
                        UPDATE batch_tracking
                        SET location_id = $2
                        WHERE batch_lot = $1
                    """
                    await self.db.execute(batch_update_query, batch_lot, location_id)
                
                logger.info(f"Assigned {quantity} units of {sku} to location {location_id}")
                return assignment_id
                
        except Exception as e:
            logger.error(f"Error assigning inventory to location: {str(e)}")
            raise
    
    async def transfer_inventory(self, store_id: UUID, sku: str,
                                from_location_id: UUID, to_location_id: UUID,
                                quantity: int, batch_lot: str = None,
                                performed_by: UUID = None, notes: str = None) -> bool:
        """Transfer inventory between locations"""
        try:
            async with self.db.transaction():
                # Check source location has enough inventory
                check_query = """
                    SELECT id, quantity FROM inventory_locations
                    WHERE store_id = $1 AND sku = $2 AND location_id = $3
                    AND ($4::VARCHAR IS NULL OR batch_lot = $4)
                """
                source = await self.db.fetchrow(
                    check_query, store_id, sku, from_location_id, batch_lot
                )
                
                if not source or source['quantity'] < quantity:
                    raise ValueError(f"Insufficient inventory at source location")
                
                # Update source location
                if source['quantity'] == quantity:
                    # Remove assignment if transferring all
                    delete_query = """
                        DELETE FROM inventory_locations WHERE id = $1
                    """
                    await self.db.execute(delete_query, source['id'])
                else:
                    # Reduce quantity
                    update_query = """
                        UPDATE inventory_locations
                        SET quantity = quantity - $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """
                    await self.db.execute(update_query, source['id'], quantity)
                
                # Add to destination location
                await self.assign_inventory_to_location(
                    store_id, sku, to_location_id, quantity, batch_lot
                )
                
                # Log the transfer
                log_query = """
                    INSERT INTO location_assignments_log
                    (store_id, sku, batch_lot, from_location_id, to_location_id,
                     quantity_moved, movement_type, performed_by, notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                await self.db.execute(
                    log_query, store_id, sku, batch_lot, from_location_id,
                    to_location_id, quantity, MovementType.TRANSFER.value,
                    performed_by, notes
                )
                
                # Update batch_tracking if batch_lot is provided
                if batch_lot:
                    batch_update_query = """
                        UPDATE batch_tracking
                        SET location_id = $2
                        WHERE batch_lot = $1
                    """
                    await self.db.execute(batch_update_query, batch_lot, to_location_id)
                
                logger.info(f"Transferred {quantity} units of {sku} from {from_location_id} to {to_location_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error transferring inventory: {str(e)}")
            raise
    
    async def get_inventory_locations(self, store_id: UUID, sku: str = None,
                                     location_id: UUID = None,
                                     batch_lot: str = None) -> List[Dict[str, Any]]:
        """Get inventory location assignments"""
        try:
            conditions = ["il.store_id = $1"]
            params = [store_id]
            param_count = 1
            
            if sku:
                param_count += 1
                conditions.append(f"il.sku = ${param_count}")
                params.append(sku)
            
            if location_id:
                param_count += 1
                conditions.append(f"il.location_id = ${param_count}")
                params.append(location_id)
            
            if batch_lot:
                param_count += 1
                conditions.append(f"il.batch_lot = ${param_count}")
                params.append(batch_lot)
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT 
                    il.id,
                    il.sku,
                    il.quantity,
                    il.batch_lot,
                    il.is_primary,
                    il.assigned_at,
                    sl.location_code,
                    sl.zone,
                    sl.aisle,
                    sl.shelf,
                    sl.bin,
                    sl.location_type
                FROM inventory_locations il
                JOIN shelf_locations sl ON il.location_id = sl.id
                WHERE {where_clause}
                ORDER BY sl.location_code, il.sku
            """
            
            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting inventory locations: {str(e)}")
            raise
    
    async def pick_inventory(self, store_id: UUID, sku: str,
                           location_id: UUID, quantity: int,
                           batch_lot: str = None, reference_id: UUID = None,
                           performed_by: UUID = None) -> bool:
        """Pick inventory from a location (for orders)"""
        try:
            async with self.db.transaction():
                # Check location has enough inventory
                check_query = """
                    SELECT id, quantity FROM inventory_locations
                    WHERE store_id = $1 AND sku = $2 AND location_id = $3
                    AND ($4::VARCHAR IS NULL OR batch_lot = $4)
                """
                location_inv = await self.db.fetchrow(
                    check_query, store_id, sku, location_id, batch_lot
                )
                
                if not location_inv or location_inv['quantity'] < quantity:
                    raise ValueError(f"Insufficient inventory at location")
                
                # Update location inventory
                if location_inv['quantity'] == quantity:
                    # Remove assignment if picking all
                    delete_query = """
                        DELETE FROM inventory_locations WHERE id = $1
                    """
                    await self.db.execute(delete_query, location_inv['id'])
                else:
                    # Reduce quantity
                    update_query = """
                        UPDATE inventory_locations
                        SET quantity = quantity - $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """
                    await self.db.execute(update_query, location_inv['id'], quantity)
                
                # Log the pick
                log_query = """
                    INSERT INTO location_assignments_log
                    (store_id, sku, batch_lot, from_location_id,
                     quantity_moved, movement_type, reference_id, performed_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                await self.db.execute(
                    log_query, store_id, sku, batch_lot, location_id,
                    quantity, MovementType.PICK.value, reference_id, performed_by
                )
                
                logger.info(f"Picked {quantity} units of {sku} from location {location_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error picking inventory: {str(e)}")
            raise
    
    async def get_movement_history(self, store_id: UUID, sku: str = None,
                                  location_id: UUID = None,
                                  limit: int = 100) -> List[Dict[str, Any]]:
        """Get inventory movement history"""
        try:
            conditions = ["lal.store_id = $1"]
            params = [store_id]
            param_count = 1
            
            if sku:
                param_count += 1
                conditions.append(f"lal.sku = ${param_count}")
                params.append(sku)
            
            if location_id:
                param_count += 1
                conditions.append(f"(lal.from_location_id = ${param_count} OR lal.to_location_id = ${param_count})")
                params.append(location_id)
            
            where_clause = " AND ".join(conditions)
            
            param_count += 1
            params.append(limit)
            
            query = f"""
                SELECT 
                    lal.id,
                    lal.sku,
                    lal.batch_lot,
                    lal.quantity_moved,
                    lal.movement_type,
                    lal.reference_id,
                    lal.notes,
                    lal.created_at,
                    fl.location_code as from_location,
                    tl.location_code as to_location,
                    u.email as performed_by_email
                FROM location_assignments_log lal
                LEFT JOIN shelf_locations fl ON lal.from_location_id = fl.id
                LEFT JOIN shelf_locations tl ON lal.to_location_id = tl.id
                LEFT JOIN users u ON lal.performed_by = u.id
                WHERE {where_clause}
                ORDER BY lal.created_at DESC
                LIMIT ${param_count}
            """
            
            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting movement history: {str(e)}")
            raise
    
    async def suggest_location_for_sku(self, store_id: UUID, sku: str,
                                      quantity: int) -> Optional[UUID]:
        """Suggest best available location for storing an SKU"""
        try:
            # First check if SKU already has a primary location with space
            primary_query = """
                SELECT 
                    il.location_id,
                    sl.max_weight_kg,
                    sl.max_volume_m3
                FROM inventory_locations il
                JOIN shelf_locations sl ON il.location_id = sl.id
                WHERE il.store_id = $1 AND il.sku = $2 AND il.is_primary = true
                AND sl.is_available = true
                LIMIT 1
            """
            primary = await self.db.fetchrow(primary_query, store_id, sku)
            
            if primary:
                return primary['location_id']
            
            # Find available location of appropriate type
            # This is a simplified algorithm - can be enhanced with more rules
            available_query = """
                SELECT 
                    sl.id
                FROM shelf_locations sl
                LEFT JOIN (
                    SELECT location_id, SUM(quantity) as total_qty
                    FROM inventory_locations
                    WHERE store_id = $1
                    GROUP BY location_id
                ) il ON sl.id = il.location_id
                WHERE sl.store_id = $1
                AND sl.is_available = true
                AND sl.is_active = true
                AND sl.location_type = 'standard'
                ORDER BY 
                    COALESCE(il.total_qty, 0) ASC,  -- Least full locations first
                    sl.zone, sl.aisle, sl.shelf, sl.bin
                LIMIT 1
            """
            
            location_id = await self.db.fetchval(available_query, store_id)
            return location_id
            
        except Exception as e:
            logger.error(f"Error suggesting location: {str(e)}")
            raise


# Factory function for creating service instance
def create_shelf_location_service(db_pool) -> ShelfLocationService:
    """Create shelf location service instance"""
    return ShelfLocationService(db_pool)