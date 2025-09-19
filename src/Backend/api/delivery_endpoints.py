"""
Delivery API endpoints for managing deliveries
Provides REST API for delivery operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import json
import logging
import asyncio

from ..services.delivery.delivery_service import DeliveryService
from ..services.delivery.base import (
    DeliveryStatus, StaffStatus, Location,
    DeliveryNotFound, StaffNotAvailable, InvalidStatusTransition
)
from ..services.database import get_db
from ..middleware.auth import get_current_user
from ..middleware.tenant_resolution import tenant_required

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/delivery", tags=["delivery"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, List[WebSocket]] = {}
        self.staff_connections: Dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, delivery_id: UUID):
        await websocket.accept()
        if delivery_id not in self.active_connections:
            self.active_connections[delivery_id] = []
        self.active_connections[delivery_id].append(websocket)

    async def connect_staff(self, websocket: WebSocket, staff_id: UUID):
        await websocket.accept()
        self.staff_connections[staff_id] = websocket

    def disconnect(self, websocket: WebSocket, delivery_id: UUID):
        if delivery_id in self.active_connections:
            self.active_connections[delivery_id].remove(websocket)
            if not self.active_connections[delivery_id]:
                del self.active_connections[delivery_id]

    def disconnect_staff(self, staff_id: UUID):
        if staff_id in self.staff_connections:
            del self.staff_connections[staff_id]

    async def send_to_delivery(self, delivery_id: UUID, message: dict):
        if delivery_id in self.active_connections:
            for connection in self.active_connections[delivery_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

    async def send_to_staff(self, staff_id: UUID, message: dict):
        if staff_id in self.staff_connections:
            try:
                await self.staff_connections[staff_id].send_json(message)
            except:
                pass

    async def broadcast_to_store(self, store_id: UUID, message: dict):
        # Broadcast to all connections for a store
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()


@router.post("/create-from-order")
async def create_delivery_from_order(
    order_id: UUID,
    delivery_address: Dict[str, Any] = Body(...),
    customer_data: Dict[str, Any] = Body(...),
    delivery_fee: Optional[Decimal] = Body(Decimal("5.00")),
    scheduled_at: Optional[datetime] = Body(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(tenant_required)
):
    """Create a delivery from an order"""
    try:
        service = DeliveryService(db)

        delivery = await service.create_delivery_from_order(
            order_id=order_id,
            store_id=tenant.id,
            customer_data=customer_data,
            delivery_address=delivery_address,
            delivery_fee=delivery_fee,
            scheduled_at=scheduled_at
        )

        # Broadcast new delivery to store
        await manager.broadcast_to_store(tenant.id, {
            "type": "new_delivery",
            "delivery": {
                "id": str(delivery.id),
                "order_id": str(delivery.order_id),
                "status": delivery.status.value,
                "customer_name": delivery.customer_name,
                "address": delivery.delivery_address.to_dict()
            }
        })

        return {
            "success": True,
            "delivery_id": str(delivery.id),
            "status": delivery.status.value,
            "estimated_time": delivery.metrics.estimated_time.isoformat() if delivery.metrics.estimated_time else None
        }

    except Exception as e:
        logger.error(f"Error creating delivery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_deliveries(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(tenant_required)
):
    """Get all active deliveries for the store"""
    try:
        service = DeliveryService(db)
        deliveries = await service.get_active_deliveries(tenant.id)

        return {
            "success": True,
            "deliveries": [
                {
                    "id": str(d.id),
                    "order_id": str(d.order_id),
                    "status": d.status.value,
                    "customer_name": d.customer_name,
                    "customer_phone": d.customer_phone,
                    "address": d.delivery_address.to_dict(),
                    "assigned_to": str(d.assigned_to) if d.assigned_to else None,
                    "estimated_time": d.metrics.estimated_time.isoformat() if d.metrics and d.metrics.estimated_time else None,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                }
                for d in deliveries
            ]
        }

    except Exception as e:
        logger.error(f"Error getting active deliveries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{delivery_id}")
async def get_delivery(
    delivery_id: UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get delivery details"""
    try:
        service = DeliveryService(db)
        delivery = await service.get_delivery(delivery_id)

        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")

        return {
            "success": True,
            "delivery": {
                "id": str(delivery.id),
                "order_id": str(delivery.order_id),
                "status": delivery.status.value,
                "customer_name": delivery.customer_name,
                "customer_phone": delivery.customer_phone,
                "customer_email": delivery.customer_email,
                "address": delivery.delivery_address.to_dict(),
                "assigned_to": str(delivery.assigned_to) if delivery.assigned_to else None,
                "metrics": {
                    "estimated_time": delivery.metrics.estimated_time.isoformat() if delivery.metrics and delivery.metrics.estimated_time else None,
                    "actual_time": delivery.metrics.actual_time.isoformat() if delivery.metrics and delivery.metrics.actual_time else None,
                    "distance_km": delivery.metrics.distance_km if delivery.metrics else None,
                    "delivery_fee": float(delivery.metrics.delivery_fee) if delivery.metrics else 0,
                    "tip_amount": float(delivery.metrics.tip_amount) if delivery.metrics else 0
                },
                "proof": {
                    "signature": bool(delivery.proof.signature_data) if delivery.proof else False,
                    "photo": bool(delivery.proof.photo_urls) if delivery.proof else False,
                    "id_verified": delivery.proof.id_verified if delivery.proof else False,
                    "age_verified": delivery.proof.age_verified if delivery.proof else False
                } if delivery.proof else None,
                "created_at": delivery.created_at.isoformat() if delivery.created_at else None
            }
        }

    except Exception as e:
        logger.error(f"Error getting delivery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{delivery_id}/assign")
async def assign_delivery(
    delivery_id: UUID,
    staff_id: UUID = Body(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(tenant_required)
):
    """Manually assign delivery to staff member"""
    try:
        service = DeliveryService(db)

        delivery = await service.assign_to_staff(
            delivery_id=delivery_id,
            staff_id=staff_id,
            user_id=current_user.id
        )

        # Notify staff member
        await manager.send_to_staff(staff_id, {
            "type": "new_assignment",
            "delivery": {
                "id": str(delivery.id),
                "order_id": str(delivery.order_id),
                "customer_name": delivery.customer_name,
                "address": delivery.delivery_address.to_dict(),
                "estimated_time": delivery.metrics.estimated_time.isoformat() if delivery.metrics.estimated_time else None
            }
        })

        # Broadcast assignment
        await manager.send_to_delivery(delivery_id, {
            "type": "status_update",
            "status": "assigned",
            "assigned_to": str(staff_id)
        })

        return {
            "success": True,
            "message": f"Delivery assigned to staff {staff_id}",
            "estimated_time": delivery.metrics.estimated_time.isoformat() if delivery.metrics.estimated_time else None
        }

    except StaffNotAvailable as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DeliveryNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning delivery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-assign")
async def batch_assign_deliveries(
    delivery_ids: List[UUID] = Body(...),
    staff_id: UUID = Body(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(tenant_required)
):
    """Assign multiple deliveries to a staff member"""
    try:
        service = DeliveryService(db)

        assigned = await service.batch_assign(
            delivery_ids=delivery_ids,
            staff_id=staff_id,
            user_id=current_user.id
        )

        # Notify staff member
        await manager.send_to_staff(staff_id, {
            "type": "batch_assignment",
            "count": len(assigned),
            "delivery_ids": [str(d) for d in assigned]
        })

        return {
            "success": True,
            "assigned_count": len(assigned),
            "assigned_deliveries": [str(d) for d in assigned],
            "failed_count": len(delivery_ids) - len(assigned)
        }

    except Exception as e:
        logger.error(f"Error in batch assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{delivery_id}/status")
async def update_delivery_status(
    delivery_id: UUID,
    status: DeliveryStatus = Body(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update delivery status"""
    try:
        service = DeliveryService(db)

        delivery = await service.update_status(
            delivery_id=delivery_id,
            status=status,
            user_id=current_user.id
        )

        # Broadcast status update
        await manager.send_to_delivery(delivery_id, {
            "type": "status_update",
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Notify assigned staff
        if delivery.assigned_to:
            await manager.send_to_staff(delivery.assigned_to, {
                "type": "delivery_status_changed",
                "delivery_id": str(delivery_id),
                "status": status.value
            })

        return {
            "success": True,
            "status": delivery.status.value,
            "message": f"Status updated to {status.value}"
        }

    except InvalidStatusTransition as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DeliveryNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{delivery_id}/location")
async def update_delivery_location(
    delivery_id: UUID,
    latitude: float = Body(...),
    longitude: float = Body(...),
    accuracy: Optional[float] = Body(None),
    speed: Optional[float] = Body(None),
    heading: Optional[int] = Body(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update delivery GPS location"""
    try:
        service = DeliveryService(db)

        success = await service.update_location(
            delivery_id=delivery_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            heading=heading
        )

        if success:
            # Broadcast location update
            await manager.send_to_delivery(delivery_id, {
                "type": "location_update",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "accuracy": accuracy,
                    "speed": speed,
                    "heading": heading,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        return {
            "success": success,
            "message": "Location updated" if success else "Failed to update location"
        }

    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{delivery_id}/proof")
async def add_proof_of_delivery(
    delivery_id: UUID,
    signature: Optional[str] = Body(None),
    photo_urls: Optional[List[str]] = Body(None),
    id_verified: bool = Body(False),
    id_type: Optional[str] = Body(None),
    id_data: Optional[Dict] = Body(None),
    age_verified: bool = Body(False),
    notes: Optional[str] = Body(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Add proof of delivery"""
    try:
        service = DeliveryService(db)

        success = await service.add_proof_of_delivery(
            delivery_id=delivery_id,
            signature=signature,
            photo_urls=photo_urls,
            id_verified=id_verified,
            id_type=id_type,
            id_data=id_data,
            age_verified=age_verified,
            notes=notes
        )

        if success:
            # Broadcast completion
            await manager.send_to_delivery(delivery_id, {
                "type": "delivery_completed",
                "proof": {
                    "signature": bool(signature),
                    "photo": bool(photo_urls),
                    "id_verified": id_verified,
                    "age_verified": age_verified
                },
                "timestamp": datetime.utcnow().isoformat()
            })

        return {
            "success": success,
            "message": "Proof of delivery added" if success else "Failed to add proof"
        }

    except Exception as e:
        logger.error(f"Error adding proof: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{delivery_id}/tracking")
async def get_delivery_tracking(
    delivery_id: UUID,
    start_time: Optional[datetime] = Query(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get delivery tracking information"""
    try:
        service = DeliveryService(db)

        tracking = await service.get_delivery_tracking(
            delivery_id=delivery_id,
            start_time=start_time
        )

        return {
            "success": True,
            "tracking": tracking
        }

    except DeliveryNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tracking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/staff/available")
async def get_available_staff(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(tenant_required)
):
    """Get list of available staff members"""
    try:
        service = DeliveryService(db)
        staff = await service.assignment.get_available_staff(tenant.id)

        return {
            "success": True,
            "staff": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "phone": s.phone,
                    "status": s.status.value,
                    "current_deliveries": s.current_deliveries,
                    "max_deliveries": s.max_deliveries,
                    "is_available": s.is_available,
                    "can_accept": s.can_accept_delivery,
                    "location": {
                        "latitude": s.current_location.latitude,
                        "longitude": s.current_location.longitude
                    } if s.current_location else None
                }
                for s in staff
            ]
        }

    except Exception as e:
        logger.error(f"Error getting available staff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/staff/{staff_id}/deliveries")
async def get_staff_deliveries(
    staff_id: UUID,
    active_only: bool = Query(True),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get deliveries assigned to a staff member"""
    try:
        service = DeliveryService(db)
        deliveries = await service.get_staff_deliveries(staff_id, active_only)

        return {
            "success": True,
            "deliveries": [
                {
                    "id": str(d.id),
                    "order_id": str(d.order_id),
                    "status": d.status.value,
                    "customer_name": d.customer_name,
                    "address": d.delivery_address.to_dict(),
                    "estimated_time": d.metrics.estimated_time.isoformat() if d.metrics and d.metrics.estimated_time else None
                }
                for d in deliveries
            ]
        }

    except Exception as e:
        logger.error(f"Error getting staff deliveries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/staff/{staff_id}/status")
async def update_staff_status(
    staff_id: UUID,
    status: StaffStatus = Body(...),
    is_available: Optional[bool] = Body(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update staff availability status"""
    try:
        service = DeliveryService(db)

        success = await service.assignment.update_staff_status(
            staff_id=staff_id,
            status=status,
            is_available=is_available
        )

        return {
            "success": success,
            "message": f"Staff status updated to {status.value}"
        }

    except Exception as e:
        logger.error(f"Error updating staff status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoints
@router.websocket("/ws/{delivery_id}")
async def websocket_delivery_tracking(
    websocket: WebSocket,
    delivery_id: UUID,
    db=Depends(get_db)
):
    """WebSocket endpoint for real-time delivery tracking"""
    await manager.connect(websocket, delivery_id)

    try:
        service = DeliveryService(db)

        # Send initial delivery status
        delivery = await service.get_delivery(delivery_id)
        if delivery:
            await websocket.send_json({
                "type": "initial_status",
                "status": delivery.status.value,
                "assigned_to": str(delivery.assigned_to) if delivery.assigned_to else None,
                "estimated_time": delivery.metrics.estimated_time.isoformat() if delivery.metrics and delivery.metrics.estimated_time else None
            })

            # Send current location if available
            tracking = await service.get_delivery_tracking(delivery_id)
            if tracking and tracking.get('current_location'):
                await websocket.send_json({
                    "type": "current_location",
                    "location": tracking['current_location']
                })

        # Keep connection alive
        while True:
            try:
                # Wait for any messages from client (like ping)
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket, delivery_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket, delivery_id)


@router.websocket("/ws/staff/{staff_id}")
async def websocket_staff_updates(
    websocket: WebSocket,
    staff_id: UUID,
    db=Depends(get_db)
):
    """WebSocket endpoint for staff member updates"""
    await manager.connect_staff(websocket, staff_id)

    try:
        service = DeliveryService(db)

        # Send initial staff deliveries
        deliveries = await service.get_staff_deliveries(staff_id, active_only=True)
        await websocket.send_json({
            "type": "active_deliveries",
            "deliveries": [
                {
                    "id": str(d.id),
                    "status": d.status.value,
                    "customer_name": d.customer_name,
                    "address": d.delivery_address.to_dict()
                }
                for d in deliveries
            ]
        })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()

                # Handle staff location updates
                if data.startswith("location:"):
                    location_data = json.loads(data[9:])
                    # Update staff location in database
                    await service.assignment.update_staff_status(
                        staff_id=staff_id,
                        status=StaffStatus.AVAILABLE
                    )

                elif data == "ping":
                    await websocket.send_text("pong")

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        manager.disconnect_staff(staff_id)
    except Exception as e:
        logger.error(f"Staff WebSocket error: {str(e)}")
        manager.disconnect_staff(staff_id)


# Export router
__all__ = ['router', 'manager']