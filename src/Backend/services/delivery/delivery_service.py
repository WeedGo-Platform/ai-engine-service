"""
Main delivery service orchestrating all delivery operations
Following Single Responsibility Principle
"""

import asyncpg
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from .base import (
    Delivery, DeliveryStatus, DeliveryMetrics, Address, Location,
    StaffMember, StaffStatus, ProofOfDelivery,
    DeliveryException, DeliveryNotFound, StaffNotAvailable,
    InvalidStatusTransition
)
from .repository import DeliveryRepository
from .tracking_service import TrackingService
from .assignment_service import AssignmentService
from .eta_service import ETAService

logger = logging.getLogger(__name__)


class DeliveryService:
    """Main service for managing deliveries"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize delivery service with dependencies"""
        self.db_pool = db_pool
        self.repository = DeliveryRepository(db_pool)
        self.tracking = TrackingService(db_pool)
        self.assignment = AssignmentService(db_pool)
        self.eta_service = ETAService()

    async def create_delivery_from_order(
        self,
        order_id: UUID,
        store_id: UUID,
        customer_data: Dict[str, Any],
        delivery_address: Dict[str, Any],
        delivery_fee: Decimal = Decimal("5.00"),
        scheduled_at: Optional[datetime] = None
    ) -> Delivery:
        """Create a delivery from an order"""
        try:
            # Create address object
            address = Address.from_dict(delivery_address)

            # Geocode address if coordinates not provided
            if not address.location and delivery_address.get('latitude'):
                address.location = Location(
                    latitude=delivery_address['latitude'],
                    longitude=delivery_address['longitude']
                )

            # Create delivery metrics
            metrics = DeliveryMetrics(
                delivery_fee=delivery_fee,
                estimated_time=scheduled_at or datetime.utcnow() + timedelta(minutes=45)
            )

            # Create delivery object
            delivery = Delivery(
                id=uuid4(),
                order_id=order_id,
                store_id=store_id,
                status=DeliveryStatus.PENDING,
                customer_id=UUID(customer_data['id']) if 'id' in customer_data else uuid4(),
                customer_name=customer_data['name'],
                customer_phone=customer_data['phone'],
                customer_email=customer_data.get('email'),
                delivery_address=address,
                metrics=metrics
            )

            # Save to database
            created_delivery = await self.repository.create(delivery)

            # Create geofence for arrival detection
            if address.location:
                await self.tracking.create_geofence(
                    created_delivery.id,
                    address.location,
                    radius_meters=100
                )

            logger.info(f"Created delivery {created_delivery.id} from order {order_id}")
            return created_delivery

        except Exception as e:
            logger.error(f"Error creating delivery from order: {str(e)}")
            raise DeliveryException(f"Failed to create delivery: {str(e)}")

    async def assign_to_staff(
        self,
        delivery_id: UUID,
        staff_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Delivery:
        """Manually assign delivery to staff member"""
        try:
            # Get delivery
            delivery = await self.repository.get(delivery_id)
            if not delivery:
                raise DeliveryNotFound(f"Delivery {delivery_id} not found")

            # Check if staff is available
            staff = await self.assignment.get_staff_member(staff_id)
            if not staff or not staff.can_accept_delivery:
                raise StaffNotAvailable(f"Staff member {staff_id} is not available")

            # Validate status transition
            if delivery.status not in [DeliveryStatus.PENDING, DeliveryStatus.ASSIGNED]:
                raise InvalidStatusTransition(
                    f"Cannot assign delivery in status {delivery.status.value}"
                )

            # Assign delivery
            delivery.assigned_to = staff_id
            delivery.status = DeliveryStatus.ASSIGNED

            # Update in database
            updated = await self.repository.update(delivery)

            # Update staff delivery count
            await self.assignment.increment_staff_deliveries(staff_id)

            # Calculate ETA if location available
            if staff.current_location and delivery.delivery_address.location:
                eta, distance = await self.eta_service.calculate_eta(
                    staff.current_location,
                    delivery.delivery_address.location
                )
                updated.metrics.estimated_time = eta
                updated.metrics.distance_km = distance
                await self.repository.update(updated)

            logger.info(f"Assigned delivery {delivery_id} to staff {staff_id}")
            return updated

        except Exception as e:
            logger.error(f"Error assigning delivery: {str(e)}")
            raise

    async def update_status(
        self,
        delivery_id: UUID,
        status: DeliveryStatus,
        user_id: Optional[UUID] = None
    ) -> Delivery:
        """Update delivery status with validation"""
        try:
            # Get current delivery
            delivery = await self.repository.get(delivery_id)
            if not delivery:
                raise DeliveryNotFound(f"Delivery {delivery_id} not found")

            # Validate status transition
            if not self._is_valid_transition(delivery.status, status):
                raise InvalidStatusTransition(
                    f"Invalid transition from {delivery.status.value} to {status.value}"
                )

            # Update status
            delivery.status = status

            # Handle status-specific actions
            if status == DeliveryStatus.COMPLETED:
                delivery.metrics.actual_time = datetime.utcnow()
                # Decrement staff delivery count
                if delivery.assigned_to:
                    await self.assignment.decrement_staff_deliveries(delivery.assigned_to)

            elif status == DeliveryStatus.CANCELLED:
                # Release staff if assigned
                if delivery.assigned_to and delivery.status in DeliveryStatus.active_statuses():
                    await self.assignment.decrement_staff_deliveries(delivery.assigned_to)

            # Update in database
            updated = await self.repository.update(delivery)

            logger.info(f"Updated delivery {delivery_id} status to {status.value}")
            return updated

        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
            raise

    async def update_location(
        self,
        delivery_id: UUID,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None,
        speed: Optional[float] = None,
        heading: Optional[int] = None
    ) -> bool:
        """Update delivery GPS location"""
        try:
            location = Location(
                latitude=latitude,
                longitude=longitude,
                accuracy_meters=accuracy
            )

            # Add additional attributes
            if speed is not None:
                setattr(location, 'speed_kmh', speed)
            if heading is not None:
                setattr(location, 'heading', heading)

            # Update tracking
            success = await self.tracking.update_location(delivery_id, location)

            # Check if arrived
            delivery = await self.repository.get(delivery_id)
            if delivery and delivery.status == DeliveryStatus.EN_ROUTE:
                arrived = await self.tracking.check_arrival(location, delivery)
                if arrived:
                    await self.update_status(delivery_id, DeliveryStatus.ARRIVED)

            # Update ETA
            if delivery and delivery.delivery_address.location:
                eta, _ = await self.eta_service.calculate_eta(
                    location,
                    delivery.delivery_address.location
                )
                delivery.metrics.estimated_time = eta
                await self.repository.update(delivery)

            return success

        except Exception as e:
            logger.error(f"Error updating location: {str(e)}")
            return False

    async def add_proof_of_delivery(
        self,
        delivery_id: UUID,
        signature: Optional[str] = None,
        photo_urls: Optional[List[str]] = None,
        id_verified: bool = False,
        id_type: Optional[str] = None,
        id_data: Optional[Dict] = None,
        age_verified: bool = False,
        notes: Optional[str] = None
    ) -> bool:
        """Add proof of delivery"""
        try:
            proof = ProofOfDelivery(
                signature_data=signature,
                photo_urls=photo_urls or [],
                id_verified=id_verified,
                id_verification_type=id_type,
                id_verification_data=id_data,
                age_verified=age_verified,
                notes=notes,
                captured_at=datetime.utcnow()
            )

            success = await self.repository.add_proof_of_delivery(delivery_id, proof)

            if success:
                # Auto-complete delivery if proof is provided
                await self.update_status(delivery_id, DeliveryStatus.COMPLETED)

            return success

        except Exception as e:
            logger.error(f"Error adding proof of delivery: {str(e)}")
            return False

    async def get_active_deliveries(self, store_id: UUID) -> List[Delivery]:
        """Get all active deliveries for a store"""
        return await self.repository.list_active(store_id)

    async def get_staff_deliveries(
        self,
        staff_id: UUID,
        active_only: bool = True
    ) -> List[Delivery]:
        """Get deliveries assigned to a staff member"""
        return await self.repository.list_by_staff(staff_id, active_only)

    async def get_delivery(self, delivery_id: UUID) -> Optional[Delivery]:
        """Get delivery by ID"""
        return await self.repository.get(delivery_id)

    async def get_delivery_tracking(
        self,
        delivery_id: UUID,
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get delivery tracking information"""
        try:
            delivery = await self.repository.get(delivery_id)
            if not delivery:
                raise DeliveryNotFound(f"Delivery {delivery_id} not found")

            # Get current location
            current_location = await self.tracking.get_current_location(delivery_id)

            # Get location history
            history = await self.tracking.get_location_history(
                delivery_id,
                start_time=start_time
            )

            # Get tracking stats
            stats = await self.tracking.get_tracking_stats(delivery_id)

            return {
                'delivery_id': str(delivery_id),
                'status': delivery.status.value,
                'current_location': current_location.to_dict() if current_location else None,
                'location_history': [loc.to_dict() for loc in history],
                'stats': stats,
                'estimated_arrival': delivery.metrics.estimated_time.isoformat() if delivery.metrics.estimated_time else None
            }

        except Exception as e:
            logger.error(f"Error getting delivery tracking: {str(e)}")
            raise

    async def batch_assign(
        self,
        delivery_ids: List[UUID],
        staff_id: UUID,
        user_id: Optional[UUID] = None
    ) -> List[UUID]:
        """Assign multiple deliveries to a staff member"""
        try:
            assigned = []
            for delivery_id in delivery_ids:
                try:
                    await self.assign_to_staff(delivery_id, staff_id, user_id)
                    assigned.append(delivery_id)
                except (DeliveryNotFound, StaffNotAvailable, InvalidStatusTransition) as e:
                    logger.warning(f"Failed to assign {delivery_id}: {str(e)}")
                    continue

            logger.info(f"Batch assigned {len(assigned)} deliveries to staff {staff_id}")
            return assigned

        except Exception as e:
            logger.error(f"Error in batch assignment: {str(e)}")
            raise

    def _is_valid_transition(
        self,
        current: DeliveryStatus,
        new: DeliveryStatus
    ) -> bool:
        """Validate status transition"""
        # Define valid transitions
        valid_transitions = {
            DeliveryStatus.PENDING: [
                DeliveryStatus.ASSIGNED,
                DeliveryStatus.CANCELLED
            ],
            DeliveryStatus.ASSIGNED: [
                DeliveryStatus.ACCEPTED,
                DeliveryStatus.CANCELLED,
                DeliveryStatus.PENDING  # Unassign
            ],
            DeliveryStatus.ACCEPTED: [
                DeliveryStatus.PREPARING,
                DeliveryStatus.READY_FOR_PICKUP,
                DeliveryStatus.CANCELLED
            ],
            DeliveryStatus.PREPARING: [
                DeliveryStatus.READY_FOR_PICKUP,
                DeliveryStatus.CANCELLED
            ],
            DeliveryStatus.READY_FOR_PICKUP: [
                DeliveryStatus.PICKED_UP,
                DeliveryStatus.CANCELLED
            ],
            DeliveryStatus.PICKED_UP: [
                DeliveryStatus.EN_ROUTE,
                DeliveryStatus.CANCELLED
            ],
            DeliveryStatus.EN_ROUTE: [
                DeliveryStatus.ARRIVED,
                DeliveryStatus.CANCELLED
            ],
            DeliveryStatus.ARRIVED: [
                DeliveryStatus.DELIVERING,
                DeliveryStatus.COMPLETED,
                DeliveryStatus.FAILED
            ],
            DeliveryStatus.DELIVERING: [
                DeliveryStatus.COMPLETED,
                DeliveryStatus.FAILED
            ],
            # Terminal states - no transitions allowed
            DeliveryStatus.COMPLETED: [],
            DeliveryStatus.FAILED: [],
            DeliveryStatus.CANCELLED: []
        }

        return new in valid_transitions.get(current, [])