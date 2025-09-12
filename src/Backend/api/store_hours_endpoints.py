"""
Store Hours and Holiday Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Optional, Any
from datetime import datetime, date, time
from uuid import UUID
from pydantic import BaseModel, Field
import asyncpg
import logging
import json

from core.domain.models import StoreStatus
from api.store_endpoints import get_db_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stores", tags=["store-hours"])


# =====================================================
# PYDANTIC MODELS
# =====================================================

class TimeSlot(BaseModel):
    """Single time period"""
    open: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    close: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")


class ServiceHours(BaseModel):
    """Service-specific hours"""
    start: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")


class RegularHours(BaseModel):
    """Regular weekly hours for a day"""
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Sunday, 6=Saturday
    is_closed: bool = False
    time_slots: List[TimeSlot] = []
    delivery_hours: Optional[ServiceHours] = None
    pickup_hours: Optional[ServiceHours] = None


class HolidayHours(BaseModel):
    """Holiday-specific hours"""
    holiday_id: Optional[UUID] = None
    custom_holiday_name: Optional[str] = None
    custom_holiday_date: Optional[date] = None
    year: Optional[int] = None
    is_closed: bool = True
    open_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    close_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    eve_hours: Optional[Dict[str, str]] = None
    delivery_available: bool = False
    pickup_available: bool = False
    customer_message: Optional[str] = None


class SpecialHours(BaseModel):
    """Special/temporary hours for specific dates"""
    date: date
    reason: Optional[str] = None
    is_closed: bool = False
    open_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    close_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    delivery_available: bool = True
    pickup_available: bool = True
    customer_message: Optional[str] = None


class HoursSettings(BaseModel):
    """Store hours configuration settings"""
    observe_federal_holidays: bool = True
    observe_provincial_holidays: bool = True
    observe_municipal_holidays: bool = False
    auto_close_on_stat_holidays: bool = True
    default_holiday_hours: Optional[Dict[str, str]] = None
    notify_customers_of_changes: bool = True
    advance_notice_days: int = 7
    display_timezone: str = "America/Toronto"


class StoreHoursResponse(BaseModel):
    """Complete store hours information"""
    store_id: UUID
    regular_hours: List[RegularHours]
    holiday_hours: List[HolidayHours]
    special_hours: List[SpecialHours]
    settings: HoursSettings


class HolidayInfo(BaseModel):
    """Holiday information"""
    id: UUID
    name: str
    holiday_type: str
    date_type: str
    date: Optional[date] = None
    is_statutory: bool
    typical_business_impact: str


class StoreOpenStatus(BaseModel):
    """Current open/closed status"""
    is_open: bool
    current_time: datetime
    next_change: Optional[datetime] = None
    message: Optional[str] = None
    services: Dict[str, bool] = {"delivery": False, "pickup": False}


# =====================================================
# HOLIDAYS ENDPOINT (Must be before /{store_id} routes)
# =====================================================

@router.get("/holidays", response_model=List[HolidayInfo])
async def get_holidays(
    holiday_type: Optional[str] = Query(None),
    province_code: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get list of holidays"""
    async with pool.acquire() as conn:
        try:
            query = """
                SELECT h.*, pt.code as province_code
                FROM holidays h
                LEFT JOIN provinces_territories pt ON h.province_territory_id = pt.id
                WHERE 1=1
            """
            params = []
            param_count = 1
            
            if holiday_type:
                query += f" AND h.holiday_type = ${param_count}"
                params.append(holiday_type)
                param_count += 1
            
            if province_code:
                query += f" AND (pt.code = ${param_count} OR h.holiday_type = 'federal')"
                params.append(province_code)
                param_count += 1
            
            query += " ORDER BY h.fixed_month, h.fixed_day, h.name"
            
            rows = await conn.fetch(query, *params)
            
            holidays = []
            for row in rows:
                # Calculate date for current or specified year
                if year:
                    holiday_date = await conn.fetchval(
                        "SELECT calculate_holiday_date($1, $2)",
                        year, row['id']
                    )
                else:
                    holiday_date = None
                
                holidays.append(HolidayInfo(
                    id=row['id'],
                    name=row['name'],
                    holiday_type=row['holiday_type'],
                    date_type=row['date_type'],
                    date=holiday_date,
                    is_statutory=row['is_statutory'],
                    typical_business_impact=row['typical_business_impact']
                ))
            
            return holidays
            
        except Exception as e:
            logger.error(f"Error getting holidays: {e}")
            raise HTTPException(status_code=500, detail="Failed to get holidays")


# =====================================================
# REGULAR HOURS ENDPOINTS
# =====================================================

@router.get("/{store_id}/hours", response_model=StoreHoursResponse)
async def get_store_hours(
    store_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get all hours information for a store"""
    async with pool.acquire() as conn:
        try:
            # Get regular hours
            regular_query = """
                SELECT day_of_week, is_closed, time_slots, delivery_hours, pickup_hours
                FROM store_regular_hours
                WHERE store_id = $1
                ORDER BY day_of_week
            """
            regular_rows = await conn.fetch(regular_query, store_id)
            
            regular_hours = []
            for row in regular_rows:
                time_slots = json.loads(row['time_slots']) if isinstance(row['time_slots'], str) else row['time_slots']
                delivery_hours = json.loads(row['delivery_hours']) if isinstance(row['delivery_hours'], str) else row['delivery_hours']
                pickup_hours = json.loads(row['pickup_hours']) if isinstance(row['pickup_hours'], str) else row['pickup_hours']
                
                regular_hours.append(RegularHours(
                    day_of_week=row['day_of_week'],
                    is_closed=row['is_closed'],
                    time_slots=[TimeSlot(**slot) for slot in time_slots] if time_slots else [],
                    delivery_hours=ServiceHours(**delivery_hours) if delivery_hours else None,
                    pickup_hours=ServiceHours(**pickup_hours) if pickup_hours else None
                ))
            
            # Get holiday hours
            holiday_query = """
                SELECT shh.*, h.name as holiday_name
                FROM store_holiday_hours shh
                LEFT JOIN holidays h ON shh.holiday_id = h.id
                WHERE shh.store_id = $1
                ORDER BY shh.year DESC, shh.custom_holiday_date DESC
            """
            holiday_rows = await conn.fetch(holiday_query, store_id)
            
            holiday_hours = []
            for row in holiday_rows:
                eve_hours = json.loads(row['eve_hours']) if isinstance(row['eve_hours'], str) else row['eve_hours']
                
                holiday_hours.append(HolidayHours(
                    holiday_id=row['holiday_id'],
                    custom_holiday_name=row['custom_holiday_name'] or row['holiday_name'],
                    custom_holiday_date=row['custom_holiday_date'],
                    year=row['year'],
                    is_closed=row['is_closed'],
                    open_time=str(row['open_time']) if row['open_time'] else None,
                    close_time=str(row['close_time']) if row['close_time'] else None,
                    eve_hours=eve_hours,
                    delivery_available=row['delivery_available'],
                    pickup_available=row['pickup_available'],
                    customer_message=row['customer_message']
                ))
            
            # Get special hours
            special_query = """
                SELECT * FROM store_special_hours
                WHERE store_id = $1 AND date >= CURRENT_DATE
                ORDER BY date
            """
            special_rows = await conn.fetch(special_query, store_id)
            
            special_hours = []
            for row in special_rows:
                special_hours.append(SpecialHours(
                    date=row['date'],
                    reason=row['reason'],
                    is_closed=row['is_closed'],
                    open_time=str(row['open_time']) if row['open_time'] else None,
                    close_time=str(row['close_time']) if row['close_time'] else None,
                    delivery_available=row['delivery_available'],
                    pickup_available=row['pickup_available'],
                    customer_message=row['customer_message']
                ))
            
            # Get settings
            settings_query = """
                SELECT * FROM store_hours_settings
                WHERE store_id = $1
            """
            settings_row = await conn.fetchrow(settings_query, store_id)
            
            if settings_row:
                default_holiday_hours = json.loads(settings_row['default_holiday_hours']) if isinstance(settings_row['default_holiday_hours'], str) else settings_row['default_holiday_hours']
                
                settings = HoursSettings(
                    observe_federal_holidays=settings_row['observe_federal_holidays'],
                    observe_provincial_holidays=settings_row['observe_provincial_holidays'],
                    observe_municipal_holidays=settings_row['observe_municipal_holidays'],
                    auto_close_on_stat_holidays=settings_row['auto_close_on_stat_holidays'],
                    default_holiday_hours=default_holiday_hours,
                    notify_customers_of_changes=settings_row['notify_customers_of_changes'],
                    advance_notice_days=settings_row['advance_notice_days'],
                    display_timezone=settings_row['display_timezone']
                )
            else:
                settings = HoursSettings()
            
            return StoreHoursResponse(
                store_id=store_id,
                regular_hours=regular_hours,
                holiday_hours=holiday_hours,
                special_hours=special_hours,
                settings=settings
            )
            
        except Exception as e:
            logger.error(f"Error getting store hours: {e}")
            raise HTTPException(status_code=500, detail="Failed to get store hours")


@router.put("/{store_id}/hours/regular")
async def update_regular_hours(
    store_id: UUID,
    hours: List[RegularHours],
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update regular weekly hours for a store"""
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                # Delete existing regular hours
                await conn.execute(
                    "DELETE FROM store_regular_hours WHERE store_id = $1",
                    store_id
                )
                
                # Insert new regular hours
                for day_hours in hours:
                    time_slots_json = json.dumps([slot.dict() for slot in day_hours.time_slots])
                    delivery_json = json.dumps(day_hours.delivery_hours.dict()) if day_hours.delivery_hours else None
                    pickup_json = json.dumps(day_hours.pickup_hours.dict()) if day_hours.pickup_hours else None
                    
                    await conn.execute("""
                        INSERT INTO store_regular_hours 
                        (store_id, day_of_week, is_closed, time_slots, delivery_hours, pickup_hours)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, store_id, day_hours.day_of_week, day_hours.is_closed,
                        time_slots_json, delivery_json, pickup_json)
                
                return {"message": "Regular hours updated successfully"}
                
            except Exception as e:
                logger.error(f"Error updating regular hours: {e}")
                raise HTTPException(status_code=500, detail="Failed to update regular hours")


# =====================================================
# HOLIDAY HOURS ENDPOINTS
# =====================================================

@router.get("/{store_id}/hours/holidays", response_model=List[HolidayHours])
async def get_holiday_hours(
    store_id: UUID,
    year: Optional[int] = Query(None),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get holiday hours for a store"""
    async with pool.acquire() as conn:
        try:
            query = """
                SELECT shh.*, h.name as holiday_name
                FROM store_holiday_hours shh
                LEFT JOIN holidays h ON shh.holiday_id = h.id
                WHERE shh.store_id = $1
            """
            params = [store_id]
            
            if year:
                query += " AND (shh.year = $2 OR shh.year IS NULL)"
                params.append(year)
            
            query += " ORDER BY shh.year DESC, shh.custom_holiday_date DESC"
            
            rows = await conn.fetch(query, *params)
            
            holiday_hours = []
            for row in rows:
                eve_hours = json.loads(row['eve_hours']) if isinstance(row['eve_hours'], str) else row['eve_hours']
                
                holiday_hours.append(HolidayHours(
                    holiday_id=row['holiday_id'],
                    custom_holiday_name=row['custom_holiday_name'] or row['holiday_name'],
                    custom_holiday_date=row['custom_holiday_date'],
                    year=row['year'],
                    is_closed=row['is_closed'],
                    open_time=str(row['open_time']) if row['open_time'] else None,
                    close_time=str(row['close_time']) if row['close_time'] else None,
                    eve_hours=eve_hours,
                    delivery_available=row['delivery_available'],
                    pickup_available=row['pickup_available'],
                    customer_message=row['customer_message']
                ))
            
            return holiday_hours
            
        except Exception as e:
            logger.error(f"Error getting holiday hours: {e}")
            raise HTTPException(status_code=500, detail="Failed to get holiday hours")


@router.post("/{store_id}/hours/holidays", status_code=status.HTTP_201_CREATED)
async def add_holiday_hours(
    store_id: UUID,
    holiday_hours: HolidayHours,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Add or update holiday hours for a store"""
    async with pool.acquire() as conn:
        try:
            eve_hours_json = json.dumps(holiday_hours.eve_hours) if holiday_hours.eve_hours else None
            
            # Check if entry exists
            existing = await conn.fetchrow("""
                SELECT id FROM store_holiday_hours
                WHERE store_id = $1 AND (
                    (holiday_id = $2 AND year = $3) OR
                    (custom_holiday_date = $4)
                )
            """, store_id, holiday_hours.holiday_id, holiday_hours.year, 
                holiday_hours.custom_holiday_date)
            
            if existing:
                # Update existing
                await conn.execute("""
                    UPDATE store_holiday_hours SET
                        is_closed = $2, open_time = $3, close_time = $4,
                        eve_hours = $5, delivery_available = $6, 
                        pickup_available = $7, customer_message = $8,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, existing['id'], holiday_hours.is_closed,
                    holiday_hours.open_time, holiday_hours.close_time,
                    eve_hours_json, holiday_hours.delivery_available,
                    holiday_hours.pickup_available, holiday_hours.customer_message)
            else:
                # Insert new
                await conn.execute("""
                    INSERT INTO store_holiday_hours
                    (store_id, holiday_id, custom_holiday_name, custom_holiday_date,
                     year, is_closed, open_time, close_time, eve_hours,
                     delivery_available, pickup_available, customer_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, store_id, holiday_hours.holiday_id, holiday_hours.custom_holiday_name,
                    holiday_hours.custom_holiday_date, holiday_hours.year,
                    holiday_hours.is_closed, holiday_hours.open_time, holiday_hours.close_time,
                    eve_hours_json, holiday_hours.delivery_available,
                    holiday_hours.pickup_available, holiday_hours.customer_message)
            
            return {"message": "Holiday hours saved successfully"}
            
        except Exception as e:
            logger.error(f"Error saving holiday hours: {e}")
            raise HTTPException(status_code=500, detail="Failed to save holiday hours")


# =====================================================
# SPECIAL HOURS ENDPOINTS
# =====================================================

@router.get("/{store_id}/hours/special", response_model=List[SpecialHours])
async def get_special_hours(
    store_id: UUID,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get special/temporary hours for a store"""
    async with pool.acquire() as conn:
        try:
            query = """
                SELECT * FROM store_special_hours
                WHERE store_id = $1
            """
            params = [store_id]
            param_count = 2
            
            if from_date:
                query += f" AND date >= ${param_count}"
                params.append(from_date)
                param_count += 1
            
            if to_date:
                query += f" AND date <= ${param_count}"
                params.append(to_date)
            
            query += " ORDER BY date"
            
            rows = await conn.fetch(query, *params)
            
            return [
                SpecialHours(
                    date=row['date'],
                    reason=row['reason'],
                    is_closed=row['is_closed'],
                    open_time=str(row['open_time']) if row['open_time'] else None,
                    close_time=str(row['close_time']) if row['close_time'] else None,
                    delivery_available=row['delivery_available'],
                    pickup_available=row['pickup_available'],
                    customer_message=row['customer_message']
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting special hours: {e}")
            raise HTTPException(status_code=500, detail="Failed to get special hours")


@router.post("/{store_id}/hours/special", status_code=status.HTTP_201_CREATED)
async def add_special_hours(
    store_id: UUID,
    special_hours: SpecialHours,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Add special/temporary hours for a specific date"""
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO store_special_hours
                (store_id, date, reason, is_closed, open_time, close_time,
                 delivery_available, pickup_available, customer_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (store_id, date) DO UPDATE SET
                    reason = $3, is_closed = $4, open_time = $5, close_time = $6,
                    delivery_available = $7, pickup_available = $8, customer_message = $9,
                    updated_at = CURRENT_TIMESTAMP
            """, store_id, special_hours.date, special_hours.reason,
                special_hours.is_closed, special_hours.open_time, special_hours.close_time,
                special_hours.delivery_available, special_hours.pickup_available,
                special_hours.customer_message)
            
            return {"message": "Special hours saved successfully"}
            
        except Exception as e:
            logger.error(f"Error saving special hours: {e}")
            raise HTTPException(status_code=500, detail="Failed to save special hours")


@router.delete("/{store_id}/hours/special/{date}")
async def delete_special_hours(
    store_id: UUID,
    date: date,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Delete special hours for a specific date"""
    async with pool.acquire() as conn:
        try:
            result = await conn.execute("""
                DELETE FROM store_special_hours
                WHERE store_id = $1 AND date = $2
            """, store_id, date)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Special hours not found")
            
            return {"message": "Special hours deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting special hours: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete special hours")


# =====================================================
# SETTINGS ENDPOINTS
# =====================================================

@router.get("/{store_id}/hours/settings", response_model=HoursSettings)
async def get_hours_settings(
    store_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get hours management settings for a store"""
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow("""
                SELECT * FROM store_hours_settings
                WHERE store_id = $1
            """, store_id)
            
            if not row:
                # Return defaults if no settings exist
                return HoursSettings()
            
            default_holiday_hours = json.loads(row['default_holiday_hours']) if isinstance(row['default_holiday_hours'], str) else row['default_holiday_hours']
            
            return HoursSettings(
                observe_federal_holidays=row['observe_federal_holidays'],
                observe_provincial_holidays=row['observe_provincial_holidays'],
                observe_municipal_holidays=row['observe_municipal_holidays'],
                auto_close_on_stat_holidays=row['auto_close_on_stat_holidays'],
                default_holiday_hours=default_holiday_hours,
                notify_customers_of_changes=row['notify_customers_of_changes'],
                advance_notice_days=row['advance_notice_days'],
                display_timezone=row['display_timezone']
            )
            
        except Exception as e:
            logger.error(f"Error getting hours settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to get hours settings")


@router.put("/{store_id}/hours/settings")
async def update_hours_settings(
    store_id: UUID,
    settings: HoursSettings,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update hours management settings for a store"""
    async with pool.acquire() as conn:
        try:
            default_holiday_hours_json = json.dumps(settings.default_holiday_hours) if settings.default_holiday_hours else None
            
            await conn.execute("""
                INSERT INTO store_hours_settings
                (store_id, observe_federal_holidays, observe_provincial_holidays,
                 observe_municipal_holidays, auto_close_on_stat_holidays,
                 default_holiday_hours, notify_customers_of_changes,
                 advance_notice_days, display_timezone)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (store_id) DO UPDATE SET
                    observe_federal_holidays = $2,
                    observe_provincial_holidays = $3,
                    observe_municipal_holidays = $4,
                    auto_close_on_stat_holidays = $5,
                    default_holiday_hours = $6,
                    notify_customers_of_changes = $7,
                    advance_notice_days = $8,
                    display_timezone = $9,
                    updated_at = CURRENT_TIMESTAMP
            """, store_id, settings.observe_federal_holidays,
                settings.observe_provincial_holidays, settings.observe_municipal_holidays,
                settings.auto_close_on_stat_holidays, default_holiday_hours_json,
                settings.notify_customers_of_changes, settings.advance_notice_days,
                settings.display_timezone)
            
            return {"message": "Settings updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating hours settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to update hours settings")


# =====================================================
# STATUS AND HOLIDAYS ENDPOINTS
# =====================================================

@router.get("/{store_id}/hours/status", response_model=StoreOpenStatus)
async def get_store_status(
    store_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get current open/closed status of a store"""
    async with pool.acquire() as conn:
        try:
            # Call the helper function to check if store is open
            is_open = await conn.fetchval(
                "SELECT is_store_open($1, $2)",
                store_id,
                datetime.now()
            )
            
            return StoreOpenStatus(
                is_open=is_open or False,
                current_time=datetime.now(),
                services={
                    "delivery": is_open or False,
                    "pickup": is_open or False
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting store status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get store status")


