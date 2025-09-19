"""
Store Availability Service
Comprehensive service for checking store availability, hours, and delivery constraints
Follows Domain-Driven Design with proper separation of concerns
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
import asyncpg
import pytz
from decimal import Decimal

logger = logging.getLogger(__name__)


class DayOfWeek(Enum):
    """Enumeration for days of the week"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
    
    @classmethod
    def from_name(cls, name: str) -> 'DayOfWeek':
        """Get enum from day name"""
        day_map = {
            'monday': cls.MONDAY,
            'tuesday': cls.TUESDAY,
            'wednesday': cls.WEDNESDAY,
            'thursday': cls.THURSDAY,
            'friday': cls.FRIDAY,
            'saturday': cls.SATURDAY,
            'sunday': cls.SUNDAY
        }
        return day_map.get(name.lower(), cls.MONDAY)
    
    def to_name(self) -> str:
        """Get day name from enum"""
        return self.name.capitalize()


class AvailabilityType(Enum):
    """Types of availability checks"""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    BOTH = "both"


@dataclass
class StoreHours:
    """Value object for store hours"""
    day_of_week: DayOfWeek
    open_time: time
    close_time: time
    is_closed: bool = False
    
    def is_open_at(self, check_time: time) -> bool:
        """Check if store is open at specific time"""
        if self.is_closed:
            return False
        
        # Handle overnight hours (e.g., 10 PM - 2 AM)
        if self.close_time < self.open_time:
            return check_time >= self.open_time or check_time <= self.close_time
        
        return self.open_time <= check_time <= self.close_time
    
    def get_next_open_time(self, from_time: datetime) -> Optional[datetime]:
        """Get next opening time from given datetime"""
        if self.is_closed:
            return None
        
        # Calculate next occurrence of this day
        days_ahead = self.day_of_week.value - from_time.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_date = from_time.date() + timedelta(days=days_ahead)
        return datetime.combine(next_date, self.open_time, from_time.tzinfo)


@dataclass
class DeliveryZone:
    """Value object for delivery zones"""
    zone_id: str
    zone_name: str
    radius_km: float
    delivery_fee: Decimal
    minimum_order: Decimal
    estimated_time_minutes: int
    is_active: bool = True
    
    def calculate_fee(self, order_total: Decimal, distance_km: float) -> Decimal:
        """Calculate delivery fee based on order total and distance"""
        if order_total < self.minimum_order:
            return Decimal('-1')  # Invalid order
        
        # Could implement distance-based pricing tiers here
        return self.delivery_fee


@dataclass
class AvailabilityResult:
    """Result of availability check"""
    is_available: bool
    availability_type: AvailabilityType
    message: str
    details: Dict[str, Any]
    
    @property
    def pickup_available(self) -> bool:
        """Check if pickup is available"""
        return self.is_available and self.availability_type in [AvailabilityType.PICKUP, AvailabilityType.BOTH]
    
    @property
    def delivery_available(self) -> bool:
        """Check if delivery is available"""
        return self.is_available and self.availability_type in [AvailabilityType.DELIVERY, AvailabilityType.BOTH]


class StoreAvailabilityService:
    """Service for checking store availability"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def check_availability(
        self,
        store_id: str,
        check_time: Optional[datetime] = None,
        customer_location: Optional[Tuple[float, float]] = None,
        order_total: Optional[Decimal] = None,
        tenant_id: Optional[str] = None
    ) -> AvailabilityResult:
        """
        Comprehensive availability check for a store
        
        Args:
            store_id: Store identifier
            check_time: Time to check availability (defaults to now)
            customer_location: (latitude, longitude) tuple for delivery checks
            order_total: Order total for minimum order validation
            tenant_id: Tenant ID for multi-tenant filtering
        
        Returns:
            AvailabilityResult with detailed availability information
        """
        try:
            check_time = check_time or datetime.now()
            
            # Get store information
            store = await self._get_store_info(store_id, tenant_id)
            if not store:
                return AvailabilityResult(
                    is_available=False,
                    availability_type=AvailabilityType.BOTH,
                    message="Store not found",
                    details={"error": "store_not_found"}
                )
            
            # Check if store is active
            if not store['is_active']:
                return AvailabilityResult(
                    is_available=False,
                    availability_type=AvailabilityType.BOTH,
                    message="Store is currently inactive",
                    details={"store_status": "inactive"}
                )
            
            # Check store hours
            hours_check = await self._check_store_hours(store_id, check_time)
            if not hours_check['is_open']:
                return AvailabilityResult(
                    is_available=False,
                    availability_type=AvailabilityType.BOTH,
                    message=hours_check['message'],
                    details=hours_check
                )
            
            # Determine availability types
            pickup_available = store.get('pickup_available', True)
            delivery_available = store.get('delivery_available', False)
            
            # Check delivery constraints if applicable
            if delivery_available and customer_location:
                delivery_check = await self._check_delivery_availability(
                    store_id,
                    customer_location,
                    order_total
                )
                if not delivery_check['is_available']:
                    delivery_available = False
                    details = {**hours_check, "delivery": delivery_check}
                else:
                    details = {**hours_check, "delivery": delivery_check}
            else:
                details = hours_check
            
            # Determine final availability
            if pickup_available and delivery_available:
                availability_type = AvailabilityType.BOTH
                message = "Store is open for pickup and delivery"
            elif pickup_available:
                availability_type = AvailabilityType.PICKUP
                message = "Store is open for pickup only"
            elif delivery_available:
                availability_type = AvailabilityType.DELIVERY
                message = "Store is open for delivery only"
            else:
                return AvailabilityResult(
                    is_available=False,
                    availability_type=AvailabilityType.BOTH,
                    message="Store is not available for orders",
                    details=details
                )
            
            return AvailabilityResult(
                is_available=True,
                availability_type=availability_type,
                message=message,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error checking store availability: {e}")
            return AvailabilityResult(
                is_available=False,
                availability_type=AvailabilityType.BOTH,
                message="Error checking availability",
                details={"error": str(e)}
            )
    
    async def _get_store_info(self, store_id: str, tenant_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get store information from database"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT 
                        id, name, code, address, city, state, zip_code,
                        latitude, longitude, phone_number, email,
                        is_active, pickup_available, delivery_available,
                        delivery_radius_km, minimum_order_amount,
                        timezone, tenant_id
                    FROM stores
                    WHERE id = $1
                """
                params = [store_id]
                
                # Add tenant filter if provided
                if tenant_id:
                    query += " AND tenant_id = $2"
                    params.append(tenant_id)
                
                row = await conn.fetchrow(query, *params)
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return None
    
    async def _check_store_hours(self, store_id: str, check_time: datetime) -> Dict[str, Any]:
        """Check if store is open at given time"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get store hours for the current day
                day_name = check_time.strftime('%A')
                
                # Get store hours from consolidated settings
                hours_data = await conn.fetchval("""
                    SELECT value->lower($2)
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'regular_hours'
                """, store_id, day_name.lower())

                if not hours_data:
                    row = None
                else:
                    row = {
                        'day_of_week': day_name,
                        'open_time': time.fromisoformat(hours_data['open']) if hours_data.get('open') else None,
                        'close_time': time.fromisoformat(hours_data['close']) if hours_data.get('close') else None,
                        'is_closed': hours_data.get('is_closed', False)
                    }
                
                if not row:
                    return {
                        "is_open": False,
                        "message": "No hours defined for this day",
                        "day": day_name
                    }
                
                if row['is_closed']:
                    return {
                        "is_open": False,
                        "message": f"Store is closed on {day_name}",
                        "day": day_name,
                        "next_open": await self._get_next_open_time(store_id, check_time)
                    }
                
                current_time = check_time.time()
                open_time = row['open_time']
                close_time = row['close_time']
                
                # Handle overnight hours
                if close_time < open_time:
                    is_open = current_time >= open_time or current_time <= close_time
                else:
                    is_open = open_time <= current_time <= close_time
                
                if is_open:
                    return {
                        "is_open": True,
                        "message": f"Store is open until {close_time.strftime('%I:%M %p')}",
                        "day": day_name,
                        "open_time": open_time.isoformat(),
                        "close_time": close_time.isoformat()
                    }
                else:
                    return {
                        "is_open": False,
                        "message": f"Store is closed. Opens at {open_time.strftime('%I:%M %p')}",
                        "day": day_name,
                        "next_open": await self._get_next_open_time(store_id, check_time)
                    }
                    
        except Exception as e:
            logger.error(f"Error checking store hours: {e}")
            return {
                "is_open": False,
                "message": "Unable to check store hours",
                "error": str(e)
            }
    
    async def _get_next_open_time(self, store_id: str, from_time: datetime) -> Optional[str]:
        """Get the next time the store opens"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get all store hours from consolidated settings
                hours_json = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'regular_hours'
                """, store_id)

                rows = []
                if hours_json:
                    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    for day in days_order:
                        if day in hours_json and not hours_json[day].get('is_closed', False):
                            rows.append({
                                'day_of_week': day.capitalize(),
                                'open_time': time.fromisoformat(hours_json[day]['open']),
                                'close_time': time.fromisoformat(hours_json[day]['close']),
                                'is_closed': False
                            })
                
                if not rows:
                    return None
                
                # Find next open time
                for _ in range(7):  # Check next 7 days
                    for row in rows:
                        day_enum = DayOfWeek.from_name(row['day_of_week'])
                        store_hours = StoreHours(
                            day_of_week=day_enum,
                            open_time=row['open_time'],
                            close_time=row['close_time'],
                            is_closed=row['is_closed']
                        )
                        
                        next_open = store_hours.get_next_open_time(from_time)
                        if next_open and next_open > from_time:
                            return next_open.isoformat()
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting next open time: {e}")
            return None
    
    async def _check_delivery_availability(
        self,
        store_id: str,
        customer_location: Tuple[float, float],
        order_total: Optional[Decimal]
    ) -> Dict[str, Any]:
        """Check if delivery is available to customer location"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get store location and delivery radius
                store = await conn.fetchrow("""
                    SELECT 
                        latitude, longitude, 
                        delivery_radius_km, 
                        minimum_order_amount
                    FROM stores
                    WHERE id = $1
                """, store_id)
                
                if not store:
                    return {
                        "is_available": False,
                        "message": "Store not found"
                    }
                
                # Calculate distance using PostGIS
                distance_km = await conn.fetchval("""
                    SELECT ST_Distance(
                        ST_MakePoint($1, $2)::geography,
                        ST_MakePoint($3, $4)::geography
                    ) / 1000.0 as distance_km
                """, store['longitude'], store['latitude'],
                    customer_location[1], customer_location[0])
                
                # Check if within delivery radius
                if distance_km > store['delivery_radius_km']:
                    return {
                        "is_available": False,
                        "message": f"Location is outside delivery area ({distance_km:.1f}km away)",
                        "distance_km": float(distance_km),
                        "max_radius_km": float(store['delivery_radius_km'])
                    }
                
                # Check minimum order
                if order_total and store['minimum_order_amount']:
                    if order_total < store['minimum_order_amount']:
                        return {
                            "is_available": False,
                            "message": f"Minimum order amount is ${store['minimum_order_amount']}",
                            "minimum_order": float(store['minimum_order_amount']),
                            "current_order": float(order_total)
                        }
                
                # Get delivery fee and time estimate
                delivery_info = await self._get_delivery_info(store_id, distance_km)
                
                return {
                    "is_available": True,
                    "message": "Delivery available",
                    "distance_km": float(distance_km),
                    "delivery_fee": delivery_info['fee'],
                    "estimated_time": delivery_info['time'],
                    "minimum_order": float(store['minimum_order_amount']) if store['minimum_order_amount'] else 0
                }
                
        except Exception as e:
            logger.error(f"Error checking delivery availability: {e}")
            return {
                "is_available": False,
                "message": "Unable to check delivery availability",
                "error": str(e)
            }
    
    async def _get_delivery_info(self, store_id: str, distance_km: float) -> Dict[str, Any]:
        """Get delivery fee and time estimate based on distance"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check for delivery zones
                zone = await conn.fetchrow("""
                    SELECT 
                        delivery_fee, estimated_minutes
                    FROM delivery_zones
                    WHERE store_id = $1 
                      AND min_distance_km <= $2 
                      AND max_distance_km >= $2
                      AND is_active = true
                    ORDER BY min_distance_km
                    LIMIT 1
                """, store_id, distance_km)
                
                if zone:
                    return {
                        "fee": float(zone['delivery_fee']),
                        "time": f"{zone['estimated_minutes']} minutes"
                    }
                
                # Default calculation if no zones defined
                base_fee = 5.00
                per_km_fee = 1.00
                fee = base_fee + (distance_km * per_km_fee)
                
                # Estimate time (15 min base + 2 min per km)
                time_minutes = int(15 + (distance_km * 2))
                
                return {
                    "fee": round(fee, 2),
                    "time": f"{time_minutes} minutes"
                }
                
        except Exception as e:
            logger.error(f"Error getting delivery info: {e}")
            return {"fee": 0, "time": "Unknown"}
    
    async def get_store_schedule(
        self,
        store_id: str,
        include_holidays: bool = False
    ) -> List[Dict[str, Any]]:
        """Get complete store schedule"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get all store hours from consolidated settings
                hours_json = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'regular_hours'
                """, store_id)

                rows = []
                if hours_json:
                    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    for day in days_order:
                        if day in hours_json:
                            day_data = hours_json[day]
                            rows.append({
                                'day_of_week': day.capitalize(),
                                'open_time': time.fromisoformat(day_data['open']) if day_data.get('open') else None,
                                'close_time': time.fromisoformat(day_data['close']) if day_data.get('close') else None,
                                'is_closed': day_data.get('is_closed', False)
                            })
                
                schedule = []
                for row in rows:
                    schedule.append({
                        "day": row['day_of_week'],
                        "open_time": row['open_time'].isoformat() if row['open_time'] else None,
                        "close_time": row['close_time'].isoformat() if row['close_time'] else None,
                        "is_closed": row['is_closed']
                    })
                
                # Add holiday hours if requested
                if include_holidays:
                    holidays = await self._get_holiday_hours(store_id)
                    schedule.append({"holidays": holidays})
                
                return schedule
                
        except Exception as e:
            logger.error(f"Error getting store schedule: {e}")
            return []
    
    async def _get_holiday_hours(self, store_id: str) -> List[Dict[str, Any]]:
        """Get holiday hours for store"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get holiday hours from consolidated settings
                holidays_json = await conn.fetchval("""
                    SELECT value
                    FROM store_settings
                    WHERE store_id = $1 AND category = 'hours' AND key = 'holiday_hours'
                """, store_id)

                rows = []
                if holidays_json and isinstance(holidays_json, list):
                    from datetime import date
                    today = date.today()
                    for holiday in holidays_json:
                        holiday_date = date.fromisoformat(holiday['date']) if 'date' in holiday else None
                        if holiday_date and holiday_date >= today:
                            rows.append({
                                'holiday_date': holiday_date,
                                'holiday_name': holiday.get('name', 'Holiday'),
                                'open_time': time.fromisoformat(holiday['open']) if holiday.get('open') else None,
                                'close_time': time.fromisoformat(holiday['close']) if holiday.get('close') else None,
                                'is_closed': holiday.get('is_closed', False)
                            })
                    rows.sort(key=lambda x: x['holiday_date'])
                
                holidays = []
                for row in rows:
                    holidays.append({
                        "date": row['holiday_date'].isoformat(),
                        "name": row['holiday_name'],
                        "open_time": row['open_time'].isoformat() if row['open_time'] else None,
                        "close_time": row['close_time'].isoformat() if row['close_time'] else None,
                        "is_closed": row['is_closed']
                    })
                
                return holidays
                
        except Exception as e:
            logger.error(f"Error getting holiday hours: {e}")
            return []