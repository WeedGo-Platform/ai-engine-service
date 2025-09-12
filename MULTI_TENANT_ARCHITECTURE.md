# Multi-Tenant Architecture Documentation

## Executive Summary

This document describes the comprehensive multi-tenant architecture implementation for the WeedGo platform, enabling multiple branded storefronts (tenants) to operate independently while sharing the same infrastructure. Each tenant can have their own domain/subdomain, branding, template, and store locations.

## Architecture Overview

### Core Components

1. **Tenant Resolution System**
   - Subdomain-based tenant identification (production)
   - Port-based tenant mapping (development)
   - Header-based tenant propagation
   - Query parameter fallback

2. **Store Location Services**
   - PostGIS spatial database capabilities
   - Haversine distance calculations
   - Nearest store discovery
   - Delivery zone management

3. **Template System**
   - Multiple UI templates per tenant
   - Dynamic template switching
   - Custom CSS and branding
   - Theme color customization

4. **API Infrastructure**
   - Automatic tenant header injection
   - Store context propagation
   - Multi-tenant data isolation
   - Location-based services

## Implementation Details

### 1. Database Schema

#### Spatial Extensions
```sql
-- File: migrations/015_spatial_store_locations.sql
-- Enables PostGIS for geographic queries
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

#### Core Tables
- `tenants` - Tenant configurations
- `stores` - Store locations with spatial data
- `tenant_templates` - Template assignments
- `store_hours` - Operating hours
- `delivery_zones` - Delivery areas and fees

### 2. Backend Services

#### Tenant Resolution Middleware
**File:** `core/middleware/tenant_resolution.py`
- **Pattern:** Chain of Responsibility
- **Resolvers:**
  - SubdomainTenantResolver
  - HeaderTenantResolver
  - PortMappingTenantResolver
  - QueryParamTenantResolver

#### Location Service
**File:** `core/services/location_service.py`
- **Components:**
  - HaversineCalculator - Distance calculations
  - GeocodingService - Address to coordinates
  - LocationService - Orchestrator

#### Store Availability Service
**File:** `services/store_availability_service.py`
- **Features:**
  - Hours validation
  - Delivery radius checking
  - Minimum order validation
  - Holiday hours support

#### Tenant Template Service
**File:** `core/services/tenant_template_service.py`
- **Capabilities:**
  - Template assignment
  - Configuration management
  - Default template handling
  - Template cloning

### 3. Frontend Architecture

#### Vite Configuration Factory
**File:** `vite.config.factory.ts`
- **Features:**
  - Multi-port development servers
  - Automatic tenant header injection
  - Environment-specific configuration
  - Build output isolation

#### Tenant Context Provider
**File:** `src/contexts/TenantContext.tsx`
- **Responsibilities:**
  - Tenant resolution
  - Store selection
  - Location management
  - API client configuration

#### API Client
**File:** `src/services/api-client.ts`
- **Features:**
  - Automatic tenant headers
  - Request/response interceptors
  - Retry logic
  - Error transformation

#### Store Components
**Files:** `src/components/store/`
- **StoreSelector:** Full store selection interface
- **CompactStoreSelector:** Header/inline version

## Development Setup

### 1. Port Mapping (Development)

```javascript
// Default port assignments
5173: 'default'     // Modern Minimal template
5174: 'pot-palace'  // Pot Palace template
5175: 'dark-tech'   // Dark Tech template
5176: 'rasta-vibes' // Rasta Vibes template
5177: 'weedgo'      // WeedGo Professional
5178: 'vintage'     // Vintage Classic
5179: 'dirty'       // Dirty Grunge
5180: 'metal'       // Metal Industrial
```

### 2. Running Multiple Tenants

```bash
# Run specific tenant
npm run dev:pot-palace

# Run multiple tenants
npm run dev:main  # Runs first 3 tenants
npm run dev:all   # Runs all configured tenants

# Build for production
npm run build:pot-palace
npm run build:all
```

### 3. Environment Variables

```env
# Backend
BASE_DOMAIN=weedgo.com
ENVIRONMENT=development
TENANT_PORT_MAPPING='{"5173":"default","5174":"pot-palace"}'

# Frontend
VITE_TENANT_ID=00000000-0000-0000-0000-000000000001
VITE_TENANT_CODE=default
VITE_TEMPLATE_ID=modern-minimal
VITE_API_URL=http://localhost:5024
```

## Production Deployment

### 1. Subdomain Configuration

Each tenant gets a unique subdomain:
- `default.weedgo.com`
- `pot-palace.weedgo.com`
- `dark-tech.weedgo.com`

### 2. Nginx Configuration

```nginx
# Subdomain routing example
server {
    server_name *.weedgo.com;
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Tenant-Host $host;
    }
}
```

### 3. Docker Deployment

```yaml
# docker-compose.yml example
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      args:
        TENANT_ID: ${TENANT_ID}
        TEMPLATE_ID: ${TEMPLATE_ID}
    environment:
      - VITE_API_URL=${API_URL}
    
  backend:
    build: ./backend
    environment:
      - BASE_DOMAIN=${BASE_DOMAIN}
      - DATABASE_URL=${DATABASE_URL}
    
  postgres:
    image: postgis/postgis:14-3.2
    environment:
      - POSTGRES_DB=weedgo
```

## API Endpoints

### Store Management
- `POST /api/stores/nearest` - Find nearest stores
- `GET /api/stores/{store_id}/availability` - Check availability
- `POST /api/stores/{store_id}/select` - Select store
- `POST /api/stores/geocode` - Geocode address

### Tenant Management
- `GET /api/tenants/resolve` - Resolve current tenant
- `GET /api/tenants/{tenant_id}/templates` - Get templates
- `POST /api/tenants/{tenant_id}/template` - Set template

## Data Isolation

### Row-Level Security (RLS)
```sql
-- Enable RLS on tables
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation ON stores
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

### Application-Level Isolation
- All queries filtered by tenant_id
- Tenant context propagated through middleware
- API responses scoped to tenant

## Testing

### Unit Tests
```python
# Test tenant resolution
def test_subdomain_resolution():
    resolver = SubdomainTenantResolver(db_pool)
    request = Mock(headers={'host': 'pot-palace.weedgo.com'})
    tenant = await resolver.resolve(request)
    assert tenant.tenant_code == 'pot-palace'
```

### Integration Tests
```javascript
// Test store selection flow
describe('Store Selection', () => {
  it('should find nearest stores', async () => {
    const { nearbyStores } = useTenant();
    await findNearestStores({ lat: 37.7749, lng: -122.4194 });
    expect(nearbyStores.length).toBeGreaterThan(0);
  });
});
```

## Performance Considerations

### Spatial Indexing
```sql
-- Spatial indexes for fast geographic queries
CREATE INDEX idx_stores_location 
ON stores USING GIST (geography(location));

-- B-tree indexes for tenant filtering
CREATE INDEX idx_stores_tenant_id 
ON stores(tenant_id);
```

### Caching Strategy
- Geocoding results cached
- Store hours cached per session
- Tenant configuration cached

### Query Optimization
- Use PostGIS functions for distance calculations
- Limit search radius for nearest store queries
- Batch API requests where possible

## Security Considerations

### Tenant Isolation
- Strict tenant_id filtering at database level
- Middleware validates tenant context
- API endpoints verify tenant access

### Input Validation
- Location coordinates validated
- Address inputs sanitized
- Template IDs whitelisted

### Rate Limiting
- Per-tenant rate limits
- Geocoding API throttling
- Store selection limits

## Monitoring & Observability

### Key Metrics
- Tenant resolution success rate
- Store availability check latency
- Geocoding API usage
- Template load times

### Logging
```python
logger.info(f"Tenant resolved: {tenant.tenant_code} using {resolver.__class__.__name__}")
logger.error(f"Store availability check failed for {store_id}: {error}")
```

### Health Checks
- Database connectivity
- PostGIS extension status
- Geocoding service availability
- Template accessibility

## Future Enhancements

### Planned Features
1. **Advanced Delivery Zones**
   - Polygon-based zones
   - Dynamic pricing tiers
   - Time-based availability

2. **Template Marketplace**
   - Third-party templates
   - Template versioning
   - A/B testing support

3. **Analytics Dashboard**
   - Per-tenant metrics
   - Store performance
   - User behavior tracking

4. **Multi-language Support**
   - Template translations
   - Store content localization
   - API response translation

## Troubleshooting

### Common Issues

#### Tenant Not Resolved
```bash
# Check headers
curl -H "X-Tenant-Id: tenant-uuid" http://api.weedgo.com/api/test

# Verify subdomain
nslookup pot-palace.weedgo.com
```

#### Store Not Found
```sql
-- Check store exists for tenant
SELECT * FROM stores WHERE tenant_id = 'tenant-uuid';

-- Verify spatial data
SELECT ST_AsText(location) FROM stores WHERE id = 'store-id';
```

#### Template Not Loading
```javascript
// Check configuration
console.log(__TENANT_CONFIG__);

// Verify template exists
ls src/templates/pot-palace/
```

## Support & Maintenance

### Database Maintenance
```sql
-- Update spatial statistics
VACUUM ANALYZE stores;

-- Reindex spatial indexes
REINDEX INDEX idx_stores_location;
```

### Template Updates
```bash
# Update specific template
npm run build:pot-palace

# Deploy to CDN
aws s3 sync dist-pot-palace/ s3://cdn/templates/pot-palace/
```

## Conclusion

This multi-tenant architecture provides a robust, scalable foundation for operating multiple branded storefronts. It follows industry best practices including:

- **SOLID Principles** - Single responsibility, dependency injection
- **Design Patterns** - Factory, Repository, Chain of Responsibility
- **Clean Architecture** - Clear separation of concerns
- **Production Ready** - Error handling, logging, monitoring

The system is designed to scale horizontally and can handle thousands of tenants with millions of users while maintaining data isolation and performance.