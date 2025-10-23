# OCS Integration - Technical Implementation Plan
**WeedGo Platform - Ontario Cannabis Data Reporting Integration**

**Document Version:** 1.0  
**Date:** October 22, 2025  
**Status:** Planning Phase

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Schema Design](#database-schema-design)
4. [Backend Services Implementation](#backend-services-implementation)
5. [API Endpoints](#api-endpoints)
6. [Integration Components](#integration-components)
7. [Authentication & Security](#authentication--security)
8. [Data Flow & Synchronization](#data-flow--synchronization)
9. [Error Handling & Resilience](#error-handling--resilience)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)
12. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

### Objective
Implement full OCS (Ontario Cannabis Store) compliance integration for WeedGo POS platform to enable automated regulatory reporting for Ontario-licensed cannabis retailers.

### Key Deliverables
1. **OCS Authentication Service** - OAuth 2.0 client credentials flow
2. **Inventory Position Reporting** - Daily inventory snapshots
3. **Inventory Event Streaming** - Real-time transaction reporting
4. **ASN Integration** - Advanced Shipping Notice retrieval
5. **Data Reconciliation Dashboard** - Admin UI for monitoring compliance
6. **Retry & Error Handling** - Resilient data transmission

### Compliance Requirements
- **Mandatory APIs**: POST Inventory Position, POST Inventory Event, GET ASN
- **Optional APIs**: GET Inventory Events, GET Inventory Position, GET Item Master
- **Reporting Deadline**: 15th of each month to Health Canada
- **Data Retention**: AGCO regulatory monitoring

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      WeedGo Platform                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  POS System  │───▶│  Inventory   │───▶│     OCS      │     │
│  │  (Frontend)  │    │   Service    │    │   Gateway    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                             │                     │             │
│                             ▼                     ▼             │
│                      ┌──────────────┐    ┌──────────────┐     │
│                      │  PostgreSQL  │    │  OCS Queue   │     │
│                      │  (Inventory) │    │  (Outbound)  │     │
│                      └──────────────┘    └──────────────┘     │
│                                                  │             │
│                                                  ▼             │
│                                          ┌──────────────┐     │
│                                          │ OCS Worker   │     │
│                                          │   Service    │     │
│                                          └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                        ┌────────────────────────────────────┐
                        │      OCS Data Platform (Azure)     │
                        ├────────────────────────────────────┤
                        │  - OAuth 2.0 Authentication        │
                        │  - POST Inventory Position API     │
                        │  - POST Inventory Event API        │
                        │  - GET ASN API                     │
                        └────────────────────────────────────┘
                                    │             │
                        ┌───────────┴─────────────┴──────────┐
                        ▼                                     ▼
                 ┌─────────────┐                      ┌─────────────┐
                 │    AGCO     │                      │    Health   │
                 │ (Regulatory)│                      │   Canada    │
                 └─────────────┘                      └─────────────┘
```

### Technology Stack
- **Backend**: Python 3.11+ (FastAPI, asyncio)
- **Database**: PostgreSQL 15+
- **Queue**: Redis (for async job processing)
- **HTTP Client**: httpx (async requests)
- **Scheduling**: APScheduler or Celery
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging (JSON format)

---

## Database Schema Design

### 1. OCS Configuration Tables

```sql
-- Store OCS credentials and configuration per CRSA
CREATE TABLE ocs_store_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- CRSA/CROL Information
    crsa_license VARCHAR(20) NOT NULL UNIQUE,  -- e.g., "CRSA9876543"
    crol_id VARCHAR(50),  -- Retailer company identifier
    retailer_hash_key VARCHAR(255) NOT NULL,  -- OCS-provided hash key
    
    -- OAuth Configuration
    oauth_client_id VARCHAR(255),
    oauth_client_secret_encrypted TEXT,  -- Encrypted storage
    oauth_token_url TEXT,
    oauth_scope TEXT,
    
    -- API Configuration
    api_base_url TEXT NOT NULL,  -- UAT or PROD
    pos_vendor VARCHAR(100) DEFAULT 'WeedGo',
    pos_vendor_version VARCHAR(50),
    
    -- Status & Settings
    is_active BOOLEAN DEFAULT true,
    is_uat_mode BOOLEAN DEFAULT false,
    last_sync_timestamp TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_store_crsa UNIQUE (store_id, crsa_license)
);

CREATE INDEX idx_ocs_config_store ON ocs_store_config(store_id);
CREATE INDEX idx_ocs_config_crsa ON ocs_store_config(crsa_license);
```

### 2. OCS Inventory Position Tracking

```sql
-- Track daily inventory position snapshots sent to OCS
CREATE TABLE ocs_inventory_position_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    crsa_license VARCHAR(20) NOT NULL,
    
    -- Submission Details
    position_timestamp TIMESTAMPTZ NOT NULL,  -- The snapshot time
    submission_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- OCS Response
    ocs_reference_id VARCHAR(255),  -- Reference ID from OCS
    submission_status VARCHAR(50) DEFAULT 'pending',  -- pending, success, failed, retrying
    http_status_code INT,
    
    -- Payload Data
    total_items_count INT,
    payload_json JSONB,  -- Full payload sent
    response_json JSONB,  -- OCS response
    
    -- Error Tracking
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocs_pos_store ON ocs_inventory_position_submissions(store_id);
CREATE INDEX idx_ocs_pos_status ON ocs_inventory_position_submissions(submission_status);
CREATE INDEX idx_ocs_pos_timestamp ON ocs_inventory_position_submissions(position_timestamp);
CREATE INDEX idx_ocs_pos_retry ON ocs_inventory_position_submissions(next_retry_at) 
    WHERE submission_status = 'retrying';
```

### 3. OCS Inventory Event Tracking

```sql
-- Track individual inventory events sent to OCS
CREATE TABLE ocs_inventory_event_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    crsa_license VARCHAR(20) NOT NULL,
    
    -- Link to internal transaction
    inventory_transaction_id UUID,  -- References inventory_transactions table
    pos_transaction_id UUID,  -- Our internal POS transaction ID
    pos_transaction_line_id UUID,  -- Line item ID
    
    -- Event Details
    ocs_sku VARCHAR(50) NOT NULL,
    upc_barcode VARCHAR(50),
    inventory_event_type VARCHAR(50) NOT NULL,  -- PURCHASE, TRANSFER, ADJUSTMENT, etc.
    quantity_change DECIMAL(10,2),
    value_change DECIMAL(10,2),
    sold_at_price DECIMAL(10,2),
    counter_party_crsa VARCHAR(20),  -- For transfers
    reason_category VARCHAR(255),
    
    -- Submission Details
    event_timestamp TIMESTAMPTZ NOT NULL,  -- When event occurred
    submission_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- OCS Response
    ocs_reference_id VARCHAR(255),
    submission_status VARCHAR(50) DEFAULT 'pending',
    http_status_code INT,
    
    -- Payload & Response
    payload_json JSONB,
    response_json JSONB,
    
    -- Error Handling
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocs_event_store ON ocs_inventory_event_submissions(store_id);
CREATE INDEX idx_ocs_event_status ON ocs_inventory_event_submissions(submission_status);
CREATE INDEX idx_ocs_event_transaction ON ocs_inventory_event_submissions(inventory_transaction_id);
CREATE INDEX idx_ocs_event_timestamp ON ocs_inventory_event_submissions(event_timestamp);
CREATE INDEX idx_ocs_event_retry ON ocs_inventory_event_submissions(next_retry_at) 
    WHERE submission_status = 'retrying';
```

### 4. OCS ASN (Advanced Shipping Notice) Tracking

```sql
-- Store incoming shipment notifications from OCS
CREATE TABLE ocs_asn_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    crsa_license VARCHAR(20) NOT NULL,
    
    -- ASN Details
    asn_number VARCHAR(100) NOT NULL,
    shipment_date DATE,
    expected_delivery_date DATE,
    
    -- Line Items (JSONB array)
    line_items JSONB,  -- Array of products with quantities
    
    -- Processing Status
    fetch_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'received',  -- received, processing, completed, error
    
    -- Integration with Purchase Orders
    purchase_order_id UUID,  -- Link to internal PO if created
    
    -- Metadata
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_store_asn UNIQUE (store_id, asn_number)
);

CREATE INDEX idx_ocs_asn_store ON ocs_asn_records(store_id);
CREATE INDEX idx_ocs_asn_status ON ocs_asn_records(processing_status);
CREATE INDEX idx_ocs_asn_delivery ON ocs_asn_records(expected_delivery_date);
```

### 5. OCS Product Mapping

```sql
-- Map WeedGo SKUs to OCS SKUs
CREATE TABLE ocs_product_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- WeedGo Product
    product_id UUID REFERENCES products(id),
    weedgo_sku VARCHAR(100),
    
    -- OCS Product
    ocs_sku VARCHAR(50) NOT NULL,
    upc_barcode VARCHAR(50),
    
    -- Product Info (cached from OCS Item Master)
    ocs_product_name TEXT,
    ocs_category VARCHAR(100),
    ocs_brand VARCHAR(100),
    
    -- Sync Status
    is_active BOOLEAN DEFAULT true,
    last_synced_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_ocs_sku UNIQUE (ocs_sku)
);

CREATE INDEX idx_ocs_mapping_product ON ocs_product_mapping(product_id);
CREATE INDEX idx_ocs_mapping_sku ON ocs_product_mapping(weedgo_sku);
```

### 6. OCS Audit Log

```sql
-- Comprehensive audit trail for OCS interactions
CREATE TABLE ocs_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    crsa_license VARCHAR(20),
    
    -- Event Information
    event_type VARCHAR(100) NOT NULL,  -- auth_token_refresh, inventory_position_submit, etc.
    event_category VARCHAR(50),  -- authentication, inventory, asn, configuration
    
    -- Request/Response
    request_method VARCHAR(10),  -- GET, POST
    request_url TEXT,
    request_headers JSONB,
    request_body JSONB,
    
    response_status INT,
    response_headers JSONB,
    response_body JSONB,
    
    -- Timing
    request_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMPTZ,
    duration_ms INT,
    
    -- Result
    success BOOLEAN,
    error_message TEXT,
    
    -- Metadata
    user_id UUID,  -- Admin who triggered action, if applicable
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocs_audit_store ON ocs_audit_log(store_id);
CREATE INDEX idx_ocs_audit_type ON ocs_audit_log(event_type);
CREATE INDEX idx_ocs_audit_timestamp ON ocs_audit_log(request_timestamp);
CREATE INDEX idx_ocs_audit_success ON ocs_audit_log(success);
```

---

## Backend Services Implementation

### Service Architecture

```
src/Backend/services/ocs/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── ocs_config_service.py          # Manage OCS credentials & settings
├── auth/
│   ├── __init__.py
│   └── ocs_auth_service.py            # OAuth 2.0 authentication
├── client/
│   ├── __init__.py
│   ├── ocs_http_client.py             # Base HTTP client with retry logic
│   └── ocs_api_client.py              # API-specific methods
├── inventory/
│   ├── __init__.py
│   ├── position_service.py            # Inventory position reporting
│   ├── event_service.py               # Inventory event reporting
│   └── mapping_service.py             # SKU mapping management
├── asn/
│   ├── __init__.py
│   └── asn_service.py                 # ASN retrieval and processing
├── workers/
│   ├── __init__.py
│   ├── position_worker.py             # Daily position sync worker
│   ├── event_worker.py                # Real-time event worker
│   └── retry_worker.py                # Failed submission retry worker
├── validation/
│   ├── __init__.py
│   └── payload_validator.py           # Validate payloads before submission
└── monitoring/
    ├── __init__.py
    └── compliance_monitor.py          # Track compliance metrics
```

### 1. OCS Authentication Service

```python
# src/Backend/services/ocs/auth/ocs_auth_service.py

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import asyncio
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class OCSAuthService:
    """
    Handles OAuth 2.0 authentication for OCS API
    Manages token lifecycle and automatic refresh
    """
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._token_cache: Dict[str, Dict[str, Any]] = {}  # CRSA -> token data
        self._refresh_locks: Dict[str, asyncio.Lock] = {}
    
    async def get_access_token(self, crsa_license: str) -> str:
        """
        Get valid access token for CRSA, refreshing if needed
        
        Args:
            crsa_license: CRSA license number
            
        Returns:
            Valid bearer token
        """
        # Check cache first
        cached = self._token_cache.get(crsa_license)
        if cached and datetime.utcnow() < cached['expires_at']:
            return cached['access_token']
        
        # Ensure only one refresh per CRSA at a time
        if crsa_license not in self._refresh_locks:
            self._refresh_locks[crsa_license] = asyncio.Lock()
        
        async with self._refresh_locks[crsa_license]:
            # Double-check cache after acquiring lock
            cached = self._token_cache.get(crsa_license)
            if cached and datetime.utcnow() < cached['expires_at']:
                return cached['access_token']
            
            # Fetch new token
            return await self._fetch_new_token(crsa_license)
    
    async def _fetch_new_token(self, crsa_license: str) -> str:
        """Fetch new OAuth token from OCS"""
        try:
            # Get config from database
            config = await self._get_ocs_config(crsa_license)
            
            # OAuth token request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['oauth_token_url'],
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': config['oauth_client_id'],
                        'client_secret': config['oauth_client_secret'],
                        'scope': config['oauth_scope']
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=30.0
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                # Cache token with expiry buffer (refresh 5 min before expiry)
                expires_in = token_data.get('expires_in', 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                
                self._token_cache[crsa_license] = {
                    'access_token': token_data['access_token'],
                    'expires_at': expires_at,
                    'token_type': token_data.get('token_type', 'Bearer')
                }
                
                logger.info(f"OAuth token refreshed for CRSA {crsa_license}")
                
                return token_data['access_token']
                
        except Exception as e:
            logger.error(f"Failed to fetch OAuth token for {crsa_license}: {str(e)}")
            raise
    
    async def _get_ocs_config(self, crsa_license: str) -> Dict[str, str]:
        """Retrieve OCS configuration from database"""
        async with self.db_pool.acquire() as conn:
            config = await conn.fetchrow("""
                SELECT 
                    oauth_client_id,
                    pgp_sym_decrypt(oauth_client_secret_encrypted::bytea, current_setting('app.encryption_key')) as oauth_client_secret,
                    oauth_token_url,
                    oauth_scope
                FROM ocs_store_config
                WHERE crsa_license = $1 AND is_active = true
            """, crsa_license)
            
            if not config:
                raise ValueError(f"No OCS configuration found for CRSA {crsa_license}")
            
            return dict(config)
```

### 2. OCS HTTP Client

```python
# src/Backend/services/ocs/client/ocs_http_client.py

import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class OCSHTTPClient:
    """
    Base HTTP client for OCS API with retry logic and monitoring
    """
    
    def __init__(self, auth_service, db_pool):
        self.auth_service = auth_service
        self.db_pool = db_pool
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def post(
        self,
        endpoint: str,
        crsa_license: str,
        payload: Dict[str, Any],
        query_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        POST request to OCS API with authentication and retry
        """
        start_time = datetime.utcnow()
        
        try:
            # Get access token
            token = await self.auth_service.get_access_token(crsa_license)
            
            # Build headers
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Make request
            response = await self.client.post(
                endpoint,
                json=payload,
                params=query_params,
                headers=headers
            )
            
            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Log to audit table
            await self._log_audit(
                crsa_license=crsa_license,
                method='POST',
                url=endpoint,
                request_body=payload,
                response_status=response.status_code,
                response_body=response.json() if response.status_code == 200 else None,
                duration_ms=duration_ms,
                success=response.status_code == 200
            )
            
            # Check response
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"OCS API returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise OCSAPIError(error_msg, status_code=response.status_code)
                
        except Exception as e:
            logger.error(f"OCS API request failed: {str(e)}")
            raise
    
    async def get(
        self,
        endpoint: str,
        crsa_license: str,
        query_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        GET request to OCS API with authentication
        """
        start_time = datetime.utcnow()
        
        try:
            token = await self.auth_service.get_access_token(crsa_license)
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            response = await self.client.get(
                endpoint,
                params=query_params,
                headers=headers
            )
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._log_audit(
                crsa_license=crsa_license,
                method='GET',
                url=endpoint,
                response_status=response.status_code,
                response_body=response.json() if response.status_code == 200 else None,
                duration_ms=duration_ms,
                success=response.status_code == 200
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise OCSAPIError(
                    f"OCS API returned {response.status_code}",
                    status_code=response.status_code
                )
                
        except Exception as e:
            logger.error(f"OCS GET request failed: {str(e)}")
            raise
    
    async def _log_audit(self, **kwargs):
        """Log API interaction to audit table"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ocs_audit_log
                (crsa_license, event_type, request_method, request_url,
                 request_body, response_status, response_body, duration_ms, success)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                kwargs.get('crsa_license'),
                'api_request',
                kwargs.get('method'),
                kwargs.get('url'),
                kwargs.get('request_body'),
                kwargs.get('response_status'),
                kwargs.get('response_body'),
                kwargs.get('duration_ms'),
                kwargs.get('success')
            )


class OCSAPIError(Exception):
    """Custom exception for OCS API errors"""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
```

### 3. Inventory Position Service

```python
# src/Backend/services/ocs/inventory/position_service.py

from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InventoryPositionService:
    """
    Manages inventory position snapshot reporting to OCS
    """
    
    def __init__(self, db_pool, ocs_client):
        self.db_pool = db_pool
        self.ocs_client = ocs_client
    
    async def submit_daily_position(
        self,
        store_id: UUID,
        position_timestamp: datetime = None
    ) -> Dict[str, Any]:
        """
        Submit daily inventory position snapshot to OCS
        
        Args:
            store_id: Store UUID
            position_timestamp: Snapshot timestamp (defaults to yesterday EOD)
            
        Returns:
            Submission result with OCS reference ID
        """
        if position_timestamp is None:
            # Default to yesterday at 23:59:59
            position_timestamp = (datetime.utcnow() - timedelta(days=1)).replace(
                hour=23, minute=59, second=59, microsecond=0
            )
        
        try:
            # Get store config
            config = await self._get_store_config(store_id)
            
            # Build inventory position payload
            payload = await self._build_position_payload(store_id, position_timestamp)
            
            # Submit to OCS
            api_url = f"{config['api_base_url']}/PosInventoryPositionHttpTrigger"
            query_params = {
                'posVendor': config['pos_vendor'],
                'posVendorVersion': config['pos_vendor_version'],
                'retailerCRSA': config['crsa_license'],
                'positionTimeStamp': position_timestamp.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            }
            
            response = await self.ocs_client.post(
                endpoint=api_url,
                crsa_license=config['crsa_license'],
                payload=payload,
                query_params=query_params
            )
            
            # Record submission
            submission_id = await self._record_submission(
                store_id=store_id,
                crsa_license=config['crsa_license'],
                position_timestamp=position_timestamp,
                payload=payload,
                response=response,
                status='success'
            )
            
            logger.info(f"Inventory position submitted for store {store_id}: {response}")
            
            return {
                'submission_id': submission_id,
                'ocs_reference_id': response.get('referenceId'),
                'status': 'success',
                'items_count': len(payload['inventoryPositionList'])
            }
            
        except Exception as e:
            logger.error(f"Failed to submit inventory position: {str(e)}")
            
            # Record failed submission for retry
            await self._record_submission(
                store_id=store_id,
                crsa_license=config['crsa_license'],
                position_timestamp=position_timestamp,
                payload=payload,
                status='failed',
                error=str(e)
            )
            
            raise
    
    async def _build_position_payload(
        self,
        store_id: UUID,
        position_timestamp: datetime
    ) -> Dict[str, Any]:
        """Build OCS inventory position payload"""
        async with self.db_pool.acquire() as conn:
            # Get current inventory with OCS SKU mapping
            inventory_items = await conn.fetch("""
                SELECT 
                    opm.ocs_sku,
                    opm.upc_barcode,
                    oi.quantity_on_hand::TEXT as inventory_quantity_on_hand,
                    (oi.quantity_on_hand * oi.unit_cost)::TEXT as inventory_book_value
                FROM ocs_inventory oi
                INNER JOIN ocs_product_mapping opm 
                    ON oi.sku = opm.weedgo_sku
                WHERE oi.store_id = $1 
                    AND oi.is_available = true
                    AND opm.is_active = true
                    AND oi.quantity_on_hand > 0
                ORDER BY opm.ocs_sku
            """, store_id)
            
            # Build position list
            position_list = [
                {
                    'ocsSku': item['ocs_sku'],
                    'upcAndBarcode': item['upc_barcode'] or '',
                    'inventoryQuantityOnHand': item['inventory_quantity_on_hand'],
                    'inventoryBookValue': item['inventory_book_value']
                }
                for item in inventory_items
            ]
            
            return {'inventoryPositionList': position_list}
    
    async def _get_store_config(self, store_id: UUID) -> Dict[str, Any]:
        """Get OCS configuration for store"""
        async with self.db_pool.acquire() as conn:
            config = await conn.fetchrow("""
                SELECT 
                    crsa_license,
                    api_base_url,
                    pos_vendor,
                    pos_vendor_version,
                    retailer_hash_key
                FROM ocs_store_config
                WHERE store_id = $1 AND is_active = true
            """, store_id)
            
            if not config:
                raise ValueError(f"No active OCS config for store {store_id}")
            
            return dict(config)
    
    async def _record_submission(
        self,
        store_id: UUID,
        crsa_license: str,
        position_timestamp: datetime,
        payload: Dict[str, Any],
        response: Dict[str, Any] = None,
        status: str = 'pending',
        error: str = None
    ) -> UUID:
        """Record submission to database"""
        async with self.db_pool.acquire() as conn:
            submission_id = await conn.fetchval("""
                INSERT INTO ocs_inventory_position_submissions
                (store_id, crsa_license, position_timestamp, submission_status,
                 total_items_count, payload_json, response_json, ocs_reference_id,
                 http_status_code, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
                store_id,
                crsa_license,
                position_timestamp,
                status,
                len(payload.get('inventoryPositionList', [])),
                payload,
                response,
                response.get('referenceId') if response else None,
                200 if status == 'success' else None,
                error
            )
            
            return submission_id
```

### 4. Inventory Event Service

```python
# src/Backend/services/ocs/inventory/event_service.py

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InventoryEventService:
    """
    Manages real-time inventory event reporting to OCS
    """
    
    # Map internal transaction types to OCS event types
    EVENT_TYPE_MAPPING = {
        'sale': 'PURCHASE',
        'purchase': 'RECEIVING',
        'adjustment': 'ADJUSTMENT',
        'transfer': 'TRANSFER_OUT',
        'return': 'RETURN',
        'damage': 'DESTRUCTION',
        'expire': 'DESTRUCTION'
    }
    
    def __init__(self, db_pool, ocs_client):
        self.db_pool = db_pool
        self.ocs_client = ocs_client
    
    async def submit_inventory_event(
        self,
        transaction_id: UUID,
        store_id: UUID
    ) -> Dict[str, Any]:
        """
        Submit inventory event to OCS based on internal transaction
        
        Args:
            transaction_id: Internal inventory transaction ID
            store_id: Store UUID
            
        Returns:
            Submission result
        """
        try:
            # Get store config
            config = await self._get_store_config(store_id)
            
            # Build event payload
            payload = await self._build_event_payload(transaction_id, store_id)
            
            # Submit to OCS
            api_url = f"{config['api_base_url']}/PosInventoryEventHttpTrigger"
            query_params = {
                'posVendor': config['pos_vendor'],
                'posVendorVersion': config['pos_vendor_version'],
                'retailerCRSA': config['crsa_license']
            }
            
            response = await self.ocs_client.post(
                endpoint=api_url,
                crsa_license=config['crsa_license'],
                payload=payload,
                query_params=query_params
            )
            
            # Record submission
            submission_id = await self._record_event_submission(
                transaction_id=transaction_id,
                store_id=store_id,
                crsa_license=config['crsa_license'],
                payload=payload,
                response=response,
                status='success'
            )
            
            logger.info(f"Inventory event submitted: {response}")
            
            return {
                'submission_id': submission_id,
                'ocs_reference_id': response.get('referenceId'),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to submit inventory event: {str(e)}")
            
            # Record failed submission for retry
            await self._record_event_submission(
                transaction_id=transaction_id,
                store_id=store_id,
                crsa_license=config['crsa_license'],
                payload=payload if 'payload' in locals() else {},
                status='failed',
                error=str(e)
            )
            
            raise
    
    async def _build_event_payload(
        self,
        transaction_id: UUID,
        store_id: UUID
    ) -> Dict[str, Any]:
        """Build OCS inventory event payload from transaction"""
        async with self.db_pool.acquire() as conn:
            # Get transaction details with OCS mapping
            txn = await conn.fetchrow("""
                SELECT 
                    it.id as transaction_id,
                    it.sku,
                    it.transaction_type,
                    it.quantity,
                    it.unit_price,
                    it.total_value,
                    it.reference_id,
                    it.notes,
                    it.created_at as event_timestamp,
                    opm.ocs_sku,
                    opm.upc_barcode,
                    ot.order_id,
                    ol.id as order_line_id
                FROM inventory_transactions it
                LEFT JOIN ocs_product_mapping opm ON it.sku = opm.weedgo_sku
                LEFT JOIN order_transactions ot ON it.reference_id = ot.id
                LEFT JOIN order_lines ol ON ol.order_id = ot.order_id AND ol.sku = it.sku
                WHERE it.id = $1 AND it.store_id = $2
            """, transaction_id, store_id)
            
            if not txn:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            # Map to OCS event type
            ocs_event_type = self.EVENT_TYPE_MAPPING.get(
                txn['transaction_type'],
                'ADJUSTMENT'
            )
            
            # Build event
            event = {
                'ocsSku': txn['ocs_sku'],
                'upcAndBarcode': txn['upc_barcode'] or '',
                'posTransactionTimeStamp': txn['event_timestamp'].strftime(
                    '%Y-%m-%dT%H:%M:%S+00:00'
                ),
                'posTransactionLineId': str(txn['order_line_id'] or txn['transaction_id']),
                'inventoryEventType': ocs_event_type,
                'inventoryQuantityChange': str(abs(txn['quantity'])),
                'inventoryValueChange': str(abs(txn['total_value'] or 0)),
                'posSalesTransactionId': str(txn['order_id'] or txn['transaction_id']),
                'soldAtPrice': str(txn['unit_price'] or 0),
                'counterPartyCRSA': '',  # TODO: For transfers
                'reasonCategory': txn['notes'] or ''
            }
            
            return {'inventoryEventList': [event]}
    
    async def _get_store_config(self, store_id: UUID) -> Dict[str, Any]:
        """Get OCS configuration for store"""
        async with self.db_pool.acquire() as conn:
            config = await conn.fetchrow("""
                SELECT 
                    crsa_license,
                    api_base_url,
                    pos_vendor,
                    pos_vendor_version
                FROM ocs_store_config
                WHERE store_id = $1 AND is_active = true
            """, store_id)
            
            if not config:
                raise ValueError(f"No active OCS config for store {store_id}")
            
            return dict(config)
    
    async def _record_event_submission(
        self,
        transaction_id: UUID,
        store_id: UUID,
        crsa_license: str,
        payload: Dict[str, Any],
        response: Dict[str, Any] = None,
        status: str = 'pending',
        error: str = None
    ) -> UUID:
        """Record event submission"""
        event_data = payload.get('inventoryEventList', [{}])[0]
        
        async with self.db_pool.acquire() as conn:
            submission_id = await conn.fetchval("""
                INSERT INTO ocs_inventory_event_submissions
                (store_id, crsa_license, inventory_transaction_id,
                 pos_transaction_line_id, ocs_sku, upc_barcode,
                 inventory_event_type, quantity_change, value_change,
                 sold_at_price, event_timestamp, submission_status,
                 payload_json, response_json, ocs_reference_id,
                 http_status_code, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                RETURNING id
            """,
                store_id,
                crsa_license,
                transaction_id,
                event_data.get('posTransactionLineId'),
                event_data.get('ocsSku'),
                event_data.get('upcAndBarcode'),
                event_data.get('inventoryEventType'),
                event_data.get('inventoryQuantityChange'),
                event_data.get('inventoryValueChange'),
                event_data.get('soldAtPrice'),
                datetime.utcnow(),
                status,
                payload,
                response,
                response.get('referenceId') if response else None,
                200 if status == 'success' else None,
                error
            )
            
            return submission_id
```

---

## API Endpoints

### FastAPI Router

```python
# src/Backend/api/ocs_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel
import logging

from services.ocs.auth.ocs_auth_service import OCSAuthService
from services.ocs.inventory.position_service import InventoryPositionService
from services.ocs.inventory.event_service import InventoryEventService
# ... other imports

router = APIRouter(prefix="/api/v1/ocs", tags=["OCS Integration"])
logger = logging.getLogger(__name__)


# =====================================================
# Request/Response Models
# =====================================================

class OCSConfigCreate(BaseModel):
    store_id: UUID
    crsa_license: str
    crol_id: Optional[str] = None
    retailer_hash_key: str
    oauth_client_id: str
    oauth_client_secret: str
    oauth_token_url: str
    oauth_scope: str
    api_base_url: str
    is_uat_mode: bool = False


class PositionSubmitRequest(BaseModel):
    store_id: UUID
    position_timestamp: Optional[datetime] = None


class EventSubmitRequest(BaseModel):
    transaction_id: UUID
    store_id: UUID


# =====================================================
# Configuration Endpoints
# =====================================================

@router.post("/config")
async def create_ocs_config(
    config: OCSConfigCreate,
    # Add auth dependency
):
    """
    Create or update OCS configuration for a store
    """
    # Implementation here
    pass


@router.get("/config/{store_id}")
async def get_ocs_config(store_id: UUID):
    """
    Get OCS configuration for a store
    """
    pass


# =====================================================
# Inventory Position Endpoints
# =====================================================

@router.post("/inventory/position/submit")
async def submit_inventory_position(
    request: PositionSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit daily inventory position snapshot to OCS
    """
    # Queue background task
    background_tasks.add_task(
        _submit_position_task,
        request.store_id,
        request.position_timestamp
    )
    
    return {"message": "Inventory position submission queued"}


@router.get("/inventory/position/status")
async def get_position_submission_status(
    store_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Get inventory position submission history and status
    """
    pass


# =====================================================
# Inventory Event Endpoints
# =====================================================

@router.post("/inventory/events/submit")
async def submit_inventory_event(
    request: EventSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit inventory event to OCS
    """
    background_tasks.add_task(
        _submit_event_task,
        request.transaction_id,
        request.store_id
    )
    
    return {"message": "Inventory event submission queued"}


@router.get("/inventory/events/pending")
async def get_pending_events(store_id: Optional[UUID] = None):
    """
    Get pending/failed event submissions for retry
    """
    pass


# =====================================================
# ASN Endpoints
# =====================================================

@router.post("/asn/fetch")
async def fetch_asn_records(
    store_id: UUID,
    start_date: date,
    end_date: date
):
    """
    Fetch ASN records from OCS for date range
    """
    pass


@router.get("/asn/{asn_number}")
async def get_asn_details(asn_number: str):
    """
    Get details of a specific ASN
    """
    pass


# =====================================================
# Monitoring & Compliance Endpoints
# =====================================================

@router.get("/compliance/dashboard")
async def get_compliance_dashboard(store_id: Optional[UUID] = None):
    """
    Get compliance dashboard metrics
    """
    pass


@router.get("/audit/log")
async def get_audit_log(
    store_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None
):
    """
    Get OCS API audit log
    """
    pass
```

---

## Data Flow & Synchronization

### Real-Time Event Flow

```
1. POS Transaction Occurs
   └─▶ inventory_transactions table updated
       └─▶ Database trigger OR application code
           └─▶ Queue event submission job
               └─▶ Background worker picks up job
                   └─▶ InventoryEventService.submit_inventory_event()
                       ├─▶ Build payload from transaction
                       ├─▶ Submit to OCS API
                       ├─▶ Record submission (success/failed)
                       └─▶ If failed → schedule retry
```

### Daily Position Sync Flow

```
1. Scheduled Job (Cron: 1:00 AM daily)
   └─▶ For each active OCS-enabled store:
       └─▶ InventoryPositionService.submit_daily_position()
           ├─▶ Query current inventory state
           ├─▶ Build position snapshot payload
           ├─▶ Submit to OCS API
           ├─▶ Record submission
           └─▶ If failed → schedule retry
```

### Retry Logic

```
Retry Worker (Runs every 5 minutes):
1. Query ocs_inventory_event_submissions 
   WHERE submission_status = 'retrying'
   AND next_retry_at <= NOW()

2. For each failed submission:
   ├─▶ Attempt resubmission
   ├─▶ If success → Update status to 'success'
   ├─▶ If fail:
   │   ├─▶ Increment retry_count
   │   ├─▶ If retry_count < max_retries:
   │   │   └─▶ Calculate next_retry_at (exponential backoff)
   │   └─▶ Else:
   │       └─▶ Mark as 'failed_permanent'
   │           └─▶ Send alert to admin
```

---

## Error Handling & Resilience

### Error Categories

1. **Authentication Errors (401)**
   - Token expired → Auto-refresh and retry
   - Invalid credentials → Alert admin

2. **Validation Errors (400)**
   - Invalid payload → Log error, alert admin
   - Missing required fields → Fix mapping, retry

3. **Server Errors (500, 503)**
   - Retry with exponential backoff
   - Circuit breaker pattern

4. **Network Errors**
   - Timeout → Retry up to 3 times
   - Connection refused → Alert operations

### Circuit Breaker

```python
# Implement circuit breaker for OCS API
class OCSCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if (datetime.utcnow() - self.last_failure_time).seconds > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise
```

---

## Testing Strategy

### 1. Unit Tests

```python
# tests/services/ocs/test_position_service.py

import pytest
from services.ocs.inventory.position_service import InventoryPositionService

@pytest.mark.asyncio
async def test_build_position_payload(db_pool, mock_store):
    service = InventoryPositionService(db_pool, mock_ocs_client)
    
    # Setup test data
    # ...
    
    payload = await service._build_position_payload(
        store_id=mock_store.id,
        position_timestamp=datetime.utcnow()
    )
    
    assert 'inventoryPositionList' in payload
    assert len(payload['inventoryPositionList']) > 0
    assert payload['inventoryPositionList'][0]['ocsSku']
```

### 2. Integration Tests (UAT Environment)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_submit_position_to_ocs_uat():
    """Test actual submission to OCS UAT environment"""
    # Use real UAT credentials
    # Submit test payload
    # Verify 200 response with reference ID
```

### 3. End-to-End Tests

```
1. Create test POS transaction
2. Verify event queued
3. Wait for event submission
4. Check ocs_inventory_event_submissions table
5. Verify OCS audit log entry
6. Query OCS API to confirm event received
```

---

## Deployment Plan

### Phase 1: UAT Setup (Week 1-2)
- [ ] Create OCS UAT account
- [ ] Setup database tables
- [ ] Implement authentication service
- [ ] Implement HTTP client with retry
- [ ] Deploy to staging environment
- [ ] Test with OCS UAT API

### Phase 2: Core Services (Week 3-4)
- [ ] Implement inventory position service
- [ ] Implement inventory event service
- [ ] Implement ASN service
- [ ] Setup background workers
- [ ] Implement retry mechanism

### Phase 3: Integration (Week 5-6)
- [ ] Hook into existing inventory transactions
- [ ] Setup daily position sync cron job
- [ ] Implement admin dashboard UI
- [ ] Complete UAT checklist

### Phase 4: Pilot (Week 7-8)
- [ ] Select 2-3 pilot stores
- [ ] Configure production credentials
- [ ] Monitor submissions for 2 weeks
- [ ] Fix any issues

### Phase 5: Rollout (Week 9+)
- [ ] Onboard remaining stores
- [ ] Train support staff
- [ ] Monitor compliance metrics
- [ ] Document procedures

---

## Timeline & Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Database schema complete | Week 1 | Pending |
| Authentication service live | Week 2 | Pending |
| Position service UAT tested | Week 3 | Pending |
| Event service UAT tested | Week 4 | Pending |
| Background workers deployed | Week 5 | Pending |
| Admin UI complete | Week 6 | Pending |
| UAT checklist approved | Week 7 | Pending |
| Pilot stores onboarded | Week 8 | Pending |
| Production rollout complete | Week 12 | Pending |

---

## Monitoring & Alerting

### Key Metrics

1. **Submission Success Rate**
   - Target: > 99.5%
   - Alert if < 95% over 1 hour

2. **Average Submission Latency**
   - Target: < 2 seconds
   - Alert if > 5 seconds

3. **Failed Submissions**
   - Alert immediately on permanent failure
   - Daily report of retry queue depth

4. **Daily Position Coverage**
   - Alert if any store misses daily submission
   - Send reminder at 2 AM if 1 AM job failed

### Grafana Dashboards

```
OCS Compliance Dashboard:
├─ Submission Metrics (24h)
│  ├─ Total submissions
│  ├─ Success rate
│  ├─ Average latency
│  └─ Error breakdown
├─ Store Coverage
│  ├─ Stores with active config
│  ├─ Daily position submission status
│  └─ Last submission timestamp per store
├─ Event Queue
│  ├─ Pending events
│  ├─ Retry queue depth
│  └─ Permanent failures
└─ API Health
   ├─ OCS API response times
   ├─ OAuth token refresh rate
   └─ Circuit breaker status
```

---

## Security Considerations

### Credential Management
- OAuth secrets encrypted at rest (pgcrypto)
- Secrets retrieved only when needed
- Audit trail for all secret access

### API Security
- TLS 1.3 for all OCS API calls
- Certificate pinning (if supported)
- Request signing (if required by OCS)

### Data Privacy
- No PII in OCS submissions (SKUs and quantities only)
- Audit logs retention policy (90 days)
- Compliance with PIPEDA

---

## Appendix

### A. OCS API Endpoints Reference

**UAT Base URL**: `https://apim-posdata-uat-cencan-001.azure-api.net`
**Production Base URL**: TBD (provided by OCS)

| API | Method | Endpoint | Purpose |
|-----|--------|----------|---------|
| Inventory Position | POST | `/func-inventoryposition-.../PosInventoryPositionHttpTrigger` | Submit daily snapshot |
| Inventory Event | POST | `/func-inventoryposition-.../PosInventoryEventHttpTrigger` | Submit transactions |
| ASN | GET | `/func-inventoryposition-.../RetailerASNHttpTrigger` | Get shipment notices |
| Get Events | GET | `/func-inventory-position-.../POSInventoryEventFunction` | Query events |
| Get Position | GET | `/func-inventory-position-.../POSInventoryPositionFunction` | Query positions |
| Item Master | GET | `/func-inventoryposition-.../RetailerItemCatalogueHttpTrigger` | Get product catalog |

### B. Environment Variables

```bash
# OCS Integration
OCS_UAT_MODE=true
OCS_API_BASE_URL=https://apim-posdata-uat-cencan-001.azure-api.net
OCS_OAUTH_TOKEN_URL=https://login.microsoftonline.com/.../oauth2/v2.0/token
OCS_POS_VENDOR=WeedGo
OCS_POS_VENDOR_VERSION=1.0.0

# Encryption
APP_ENCRYPTION_KEY=<strong-encryption-key>

# Workers
OCS_POSITION_SYNC_CRON=0 1 * * *  # Daily at 1 AM
OCS_RETRY_WORKER_INTERVAL=300  # Every 5 minutes
OCS_EVENT_WORKER_CONCURRENCY=10
```

### C. Support Contacts

- **OCS Support**: OntarioCannabisDataReporting@ocs.ca
- **Integration Portal**: https://ocs-uat.powerappsportals.com
- **Technical Questions**: dataplatform@ocs.ca

---

**Document End**
