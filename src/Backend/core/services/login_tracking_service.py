"""
Login Tracking Service
Provides IP geolocation and login tracking functionality
"""

import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import asyncpg
from uuid import UUID

logger = logging.getLogger(__name__)


class LoginTrackingService:
    """Service for IP geolocation and login tracking"""
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        # Using ipapi.co free tier (1000 requests/day)
        self.api_url = "https://ipapi.co/{ip}/json/"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_ip_location(self, ip_address: str) -> Dict[str, Any]:
        """
        Get geolocation information for an IP address
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            Location data dictionary
        """
        # Handle localhost/private IPs
        if ip_address in ['127.0.0.1', 'localhost', '::1', 'unknown'] or ip_address.startswith('192.168.'):
            return {
                'ip': ip_address,
                'country': 'Local',
                'country_code': 'XX',
                'region': 'Local',
                'city': 'Localhost',
                'postal_code': None,
                'latitude': None,
                'longitude': None,
                'timezone': 'UTC',
                'isp': 'Local Network',
                'is_local': True
            }
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = self.api_url.format(ip=ip_address)
            
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for error in response
                    if data.get('error'):
                        logger.warning(f"IP lookup error for {ip_address}: {data.get('reason')}")
                        return self._default_location(ip_address)
                    
                    return {
                        'ip': ip_address,
                        'country': data.get('country_name'),
                        'country_code': data.get('country_code'),
                        'region': data.get('region'),
                        'city': data.get('city'),
                        'postal_code': data.get('postal'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('org'),
                        'is_local': False
                    }
                else:
                    logger.warning(f"IP lookup failed with status {response.status}")
                    return self._default_location(ip_address)
                    
        except asyncio.TimeoutError:
            logger.warning(f"IP lookup timeout for {ip_address}")
            return self._default_location(ip_address)
        except Exception as e:
            logger.error(f"IP lookup error for {ip_address}: {e}")
            return self._default_location(ip_address)
    
    def _default_location(self, ip_address: str) -> Dict[str, Any]:
        """Return default location data when lookup fails"""
        return {
            'ip': ip_address,
            'country': None,
            'country_code': None,
            'region': None,
            'city': None,
            'postal_code': None,
            'latitude': None,
            'longitude': None,
            'timezone': None,
            'isp': None,
            'is_local': False
        }
    
    async def track_login(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID],
        ip_address: str,
        user_agent: str,
        login_successful: bool = True,
        login_method: str = 'password',
        session_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Track user login with location information
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID (if applicable)
            ip_address: Client IP address
            user_agent: User agent string
            login_successful: Whether login was successful
            login_method: Method of login (password, oauth, sso, api_key)
            session_id: Session identifier
            device_fingerprint: Device fingerprint
            metadata: Additional metadata
        
        Returns:
            Login log ID if successful
        """
        if not self.db_pool:
            logger.warning("No database pool available for login tracking")
            return None
        
        try:
            # Get location data
            location = await self.get_ip_location(ip_address)
            
            async with self.db_pool.acquire() as conn:
                # Insert login log
                log_id = await conn.fetchval("""
                    INSERT INTO user_login_logs (
                        user_id,
                        tenant_id,
                        login_timestamp,
                        login_successful,
                        login_method,
                        ip_address,
                        user_agent,
                        country,
                        region,
                        city,
                        postal_code,
                        latitude,
                        longitude,
                        timezone,
                        isp,
                        device_fingerprint,
                        session_id,
                        metadata,
                        created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19
                    )
                    RETURNING id
                """,
                    user_id,
                    tenant_id,
                    datetime.now(timezone.utc),
                    login_successful,
                    login_method,
                    ip_address,
                    user_agent,
                    location.get('country'),
                    location.get('region'),
                    location.get('city'),
                    location.get('postal_code'),
                    location.get('latitude'),
                    location.get('longitude'),
                    location.get('timezone'),
                    location.get('isp'),
                    device_fingerprint,
                    session_id,
                    json.dumps(metadata) if metadata else '{}',
                    datetime.now(timezone.utc)
                )
                
                logger.info(f"Login tracked for user {user_id} from {ip_address} ({location.get('city')}, {location.get('country')})")
                return log_id
                
        except Exception as e:
            logger.error(f"Failed to track login: {e}")
            return None
    
    async def get_user_login_history(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> list:
        """
        Get user's login history
        
        Args:
            user_id: User ID
            limit: Number of records to return
            offset: Offset for pagination
        
        Returns:
            List of login records
        """
        if not self.db_pool:
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id,
                        login_timestamp,
                        login_successful,
                        login_method,
                        ip_address,
                        country,
                        city,
                        user_agent,
                        device_fingerprint
                    FROM user_login_logs
                    WHERE user_id = $1
                    ORDER BY login_timestamp DESC
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get login history: {e}")
            return []
    
    async def detect_suspicious_login(
        self,
        user_id: UUID,
        ip_address: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect potentially suspicious login attempts
        
        Args:
            user_id: User ID
            ip_address: Current IP address
            country: Current country
        
        Returns:
            Dictionary with suspicion indicators
        """
        if not self.db_pool:
            return {'suspicious': False}
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get user's typical login patterns
                patterns = await conn.fetchrow("""
                    SELECT 
                        COUNT(DISTINCT ip_address) as unique_ips,
                        COUNT(DISTINCT country) as unique_countries,
                        array_agg(DISTINCT country) FILTER (WHERE country IS NOT NULL) as countries,
                        array_agg(DISTINCT ip_address) as recent_ips
                    FROM (
                        SELECT ip_address, country
                        FROM user_login_logs
                        WHERE user_id = $1 
                        AND login_successful = true
                        AND login_timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
                        ORDER BY login_timestamp DESC
                        LIMIT 20
                    ) recent_logins
                """, user_id)
                
                suspicious_indicators = []
                
                if patterns:
                    # Check for new country
                    if country and patterns['countries'] and country not in patterns['countries']:
                        suspicious_indicators.append('new_country')
                    
                    # Check for new IP
                    if ip_address not in (patterns['recent_ips'] or []):
                        suspicious_indicators.append('new_ip')
                    
                    # Check for rapid country changes
                    last_login = await conn.fetchrow("""
                        SELECT country, login_timestamp
                        FROM user_login_logs
                        WHERE user_id = $1 
                        AND login_successful = true
                        ORDER BY login_timestamp DESC
                        LIMIT 1
                    """, user_id)
                    
                    if last_login and last_login['country'] != country:
                        time_diff = datetime.now(timezone.utc) - last_login['login_timestamp']
                        if time_diff.total_seconds() < 3600:  # Less than 1 hour
                            suspicious_indicators.append('rapid_location_change')
                
                return {
                    'suspicious': len(suspicious_indicators) > 0,
                    'indicators': suspicious_indicators,
                    'risk_level': 'high' if len(suspicious_indicators) > 1 else 'medium' if suspicious_indicators else 'low'
                }
                
        except Exception as e:
            logger.error(f"Failed to detect suspicious login: {e}")
            return {'suspicious': False, 'error': str(e)}


# Singleton instance
_login_tracking_service = None

def get_login_tracking_service(db_pool: asyncpg.Pool = None) -> LoginTrackingService:
    """Get or create login tracking service instance"""
    global _login_tracking_service
    if _login_tracking_service is None:
        _login_tracking_service = LoginTrackingService(db_pool)
    elif db_pool and not _login_tracking_service.db_pool:
        _login_tracking_service.db_pool = db_pool
    return _login_tracking_service