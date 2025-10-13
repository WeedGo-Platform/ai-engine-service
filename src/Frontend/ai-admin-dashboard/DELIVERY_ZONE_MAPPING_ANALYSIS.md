# Delivery Zone Mapping - Options & Best Practices
**Date:** October 13, 2025
**Feature:** Visual Geo-Fencing for Delivery Areas
**Status:** 📋 **RESEARCH & PLANNING**

---

## Executive Summary

Moving from a simple "delivery radius in km" to **visual geo-fencing** is a significant UX and operational improvement. This document analyzes industry approaches, technology options, and recommends an implementation strategy for WeedGo's admin dashboard.

**Recommendation:** Use **Mapbox GL JS** with **Mapbox Draw** for polygon-based delivery zones, stored as **GeoJSON** in the database.

---

## Current Implementation Limitations

### ❌ Current: Simple Radius (Circular)

**File:** `StoreManagement.tsx:751-755`
```typescript
<input
  type="number"
  min="0"
  max="100"
  value={formData.delivery_radius_km}
  // ...
/>
```

**Problems:**
1. **Unrealistic Coverage** - Circles don't match real delivery patterns
   - Ignores roads, rivers, highways, natural barriers
   - Includes areas that are physically unreachable
   - Doesn't account for neighborhood boundaries

2. **Inflexible** - Can't exclude specific areas
   - Can't skip high-crime neighborhoods
   - Can't exclude competitor territories
   - Can't handle non-contiguous delivery zones

3. **Poor User Experience** - No visual feedback
   - Store managers can't see what they're configuring
   - Hard to communicate delivery areas to customers
   - Difficult to optimize for driver efficiency

4. **Compliance Issues** - Cannabis regulations often have specific zones
   - Some provinces restrict delivery near schools/parks
   - Municipal boundaries matter for licensing
   - Need to exclude federal lands (airports, military bases)

---

## Industry Best Practices

### 🎯 How Leading Platforms Handle Delivery Zones

#### 1. **Uber Eats / DoorDash**
**Approach:** Polygon-based delivery zones with real-time optimization

**Features:**
- Visual map editor with polygon drawing
- Multiple zones per restaurant (e.g., "Zone 1: $2.99", "Zone 2: $4.99")
- Time-based zones (lunch vs dinner rush)
- Delivery fee tiers based on distance within zone
- Real-time adjustments based on driver availability

**Technology Stack:**
- Mapbox GL JS for mapping
- Turf.js for geospatial calculations
- GeoJSON for storage
- PostGIS for database queries

#### 2. **Instacart**
**Approach:** ZIP code + polygon hybrid

**Features:**
- Start with ZIP codes for quick setup
- Refine with polygon editing
- Exclude specific areas within ZIP codes
- Multi-store coverage optimization

#### 3. **Amazon Fresh**
**Approach:** Sophisticated multi-layer zones

**Features:**
- Same-day delivery zones (tight polygons)
- Next-day delivery zones (wider areas)
- Prime Now zones (ultra-fast, very limited)
- Dynamic pricing based on zone complexity

#### 4. **Cannabis Delivery Services (Industry-Specific)**

**Examples:** Dutchie, Jane Technologies, Leafly

**Common Features:**
- Compliance-first approach (regulatory boundaries)
- Age verification zones
- School/park buffer zones (mandatory exclusions)
- Municipal boundary alignment
- License jurisdiction enforcement

**Key Insight:** Cannabis delivery apps MUST respect:
- Provincial/state boundaries
- Municipal cannabis bylaws
- School buffer zones (typically 150-300m)
- Park/playground exclusions
- Federal property exclusions

---

## Technology Options

### Option 1: Mapbox GL JS + Mapbox Draw ⭐ **RECOMMENDED**

**Why Recommended:**
- ✅ Already using Mapbox for address autocomplete
- ✅ Same API key, no additional setup
- ✅ Excellent React integration (react-map-gl)
- ✅ Free tier: 50,000 map loads/month (plenty for admin dashboard)
- ✅ Mapbox Draw plugin for polygon editing
- ✅ GeoJSON native support
- ✅ Beautiful maps, fast rendering
- ✅ Active community, great documentation

**Pricing:**
- Free tier: 50,000 map loads/month
- Admin dashboard usage: ~500-1,000 loads/month (very low)
- **Cost:** $0/month (well within free tier)

**React Library:**
```bash
npm install react-map-gl @mapbox/mapbox-gl-draw
```

**Example Code:**
```typescript
import Map, { Source, Layer } from 'react-map-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';

<Map
  mapboxAccessToken={MAPBOX_TOKEN}
  initialViewState={{
    longitude: storeCoordinates.lng,
    latitude: storeCoordinates.lat,
    zoom: 12
  }}
  style={{ width: '100%', height: 600 }}
  mapStyle="mapbox://styles/mapbox/streets-v12"
>
  {/* Draw controls for polygon editing */}
  <DrawControl
    position="top-left"
    displayControlsDefault={false}
    controls={{
      polygon: true,
      trash: true
    }}
    defaultMode="draw_polygon"
    onCreate={handleZoneCreate}
    onUpdate={handleZoneUpdate}
    onDelete={handleZoneDelete}
  />

  {/* Existing delivery zone */}
  <Source id="delivery-zone" type="geojson" data={deliveryZoneGeoJSON}>
    <Layer
      id="delivery-zone-fill"
      type="fill"
      paint={{
        'fill-color': '#4CAF50',
        'fill-opacity': 0.3
      }}
    />
    <Layer
      id="delivery-zone-outline"
      type="line"
      paint={{
        'line-color': '#4CAF50',
        'line-width': 2
      }}
    />
  </Source>
</Map>
```

**Pros:**
- ✅ Best integration with existing stack
- ✅ Cost-effective (free)
- ✅ High-quality maps
- ✅ TypeScript support
- ✅ Mobile-friendly

**Cons:**
- ⚠️ Requires Mapbox API key (already have)
- ⚠️ Learning curve for Mapbox GL JS (moderate)

---

### Option 2: Google Maps JavaScript API

**Why Consider:**
- ✅ Familiar to most developers
- ✅ Excellent documentation
- ✅ Drawing Manager for polygons
- ✅ Street View integration
- ✅ Places API integration

**Pricing:**
- $7 per 1,000 map loads (Dynamic Maps)
- $2 per 1,000 static maps
- $200 monthly credit (includes ~28,000 map loads)
- Admin dashboard: ~$3-5/month (low usage)

**React Library:**
```bash
npm install @react-google-maps/api
```

**Pros:**
- ✅ Comprehensive features
- ✅ Familiar API
- ✅ Great satellite imagery

**Cons:**
- ❌ More expensive than Mapbox
- ❌ Requires separate API key
- ❌ Heavier bundle size
- ⚠️ Pricing can scale quickly

**Verdict:** Good option, but more expensive and redundant (already using Mapbox)

---

### Option 3: Leaflet + Leaflet.draw

**Why Consider:**
- ✅ Open source, 100% free
- ✅ Lightweight (38kb)
- ✅ Simple API
- ✅ React wrapper available (react-leaflet)

**React Library:**
```bash
npm install react-leaflet leaflet-draw
```

**Pros:**
- ✅ Completely free
- ✅ Lightweight
- ✅ Good for simple use cases

**Cons:**
- ❌ Less polished than Mapbox/Google
- ❌ Requires separate tile provider (OpenStreetMap, Mapbox, etc.)
- ❌ Smaller ecosystem
- ⚠️ Less mobile-optimized

**Verdict:** Good budget option, but we already have Mapbox

---

### Option 4: HERE Maps

**Why Consider:**
- ✅ Good for logistics/routing
- ✅ Offline map support
- ✅ Enterprise-grade

**Pricing:**
- Freemium tier exists
- More expensive at scale

**Verdict:** Overkill for this use case

---

## Recommended Solution: Mapbox GL JS + Mapbox Draw

### Architecture Overview

```
StoreManagement.tsx (Parent)
  └─ StoreFormModal
      ├─ AddressAutocomplete (existing ✅)
      ├─ DeliveryZoneMapEditor ⭐ NEW
      │   ├─ react-map-gl (Map component)
      │   ├─ @mapbox/mapbox-gl-draw (Drawing tools)
      │   ├─ Store marker (pin at store location)
      │   ├─ Delivery zone polygon (editable)
      │   └─ Zone statistics (area, perimeter)
      └─ Form submission (includes GeoJSON)
```

### Component Design

#### DeliveryZoneMapEditor Component

**Props:**
```typescript
interface DeliveryZoneMapEditorProps {
  storeCoordinates: { latitude: number; longitude: number };
  initialZone?: GeoJSON.Polygon | null;
  onChange: (zone: GeoJSON.Polygon) => void;
  onStatsChange?: (stats: ZoneStatistics) => void;
  className?: string;
  disabled?: boolean;
}

interface ZoneStatistics {
  area_km2: number;
  perimeter_km: number;
  approximate_radius_km: number;
}
```

**Features:**
1. **Initial View**
   - Center map on store coordinates
   - Show store marker with icon
   - Default zoom level: 13 (neighborhood view)

2. **Drawing Tools**
   - Polygon tool (primary)
   - Edit mode (modify existing polygon)
   - Delete tool (remove polygon)
   - Undo/redo functionality

3. **Visual Feedback**
   - Delivery zone shaded in green (#4CAF50, 30% opacity)
   - Polygon outline in green (#4CAF50, 2px)
   - Store marker in red (clearly visible)
   - Distance markers every 1km from store

4. **Zone Statistics**
   - Calculate area using Turf.js
   - Show approximate radius (for reference)
   - Display perimeter length
   - Estimate delivery time (area ÷ avg speed)

5. **Validation**
   - Minimum area: 1 km²
   - Maximum area: 100 km²
   - Polygon must contain store location
   - Maximum 50 points per polygon (performance)

6. **User Guidance**
   - Tooltip: "Click to add points, double-click to finish"
   - Helper text: "Draw around areas you can deliver to"
   - Warning if polygon is very large or very small

### Data Format: GeoJSON

**Why GeoJSON?**
- ✅ Industry standard for geographic data
- ✅ Supported by all mapping libraries
- ✅ Native support in PostGIS
- ✅ Human-readable JSON format
- ✅ Easy to validate and debug

**Example Delivery Zone:**
```json
{
  "type": "Polygon",
  "coordinates": [
    [
      [-79.3832, 43.6532],  // Point 1 (lng, lat)
      [-79.3700, 43.6532],  // Point 2
      [-79.3700, 43.6650],  // Point 3
      [-79.3832, 43.6650],  // Point 4
      [-79.3832, 43.6532]   // Close polygon
    ]
  ],
  "properties": {
    "name": "Primary Delivery Zone",
    "tier": "standard",
    "delivery_fee": 4.99,
    "delivery_time_minutes": 45
  }
}
```

**Storage in Database:**
```sql
-- Existing stores table
ALTER TABLE stores
  ADD COLUMN delivery_zone JSONB,  -- GeoJSON polygon
  ADD COLUMN delivery_zone_stats JSONB;  -- Area, perimeter, etc.

-- Example data
UPDATE stores
SET delivery_zone = '{
  "type": "Polygon",
  "coordinates": [[...]]
}'::jsonb
WHERE id = 'store-123';
```

**PostGIS Support (Optional Enhancement):**
```sql
-- If using PostGIS for advanced queries
ALTER TABLE stores
  ADD COLUMN delivery_zone_geom GEOMETRY(Polygon, 4326);

-- Convert JSONB to PostGIS geometry
UPDATE stores
SET delivery_zone_geom = ST_GeomFromGeoJSON(delivery_zone::text);

-- Query: Find stores that deliver to a customer location
SELECT id, name
FROM stores
WHERE ST_Contains(
  delivery_zone_geom,
  ST_SetSRID(ST_MakePoint(-79.3832, 43.6532), 4326)
);
```

---

## Implementation Plan

### Phase 1: Basic Map Display (2-3 hours)

**Tasks:**
1. Install dependencies
   ```bash
   npm install react-map-gl mapbox-gl @mapbox/mapbox-gl-draw
   npm install --save-dev @types/mapbox-gl
   ```

2. Create DeliveryZoneMapEditor component
   - Basic map with store marker
   - Center on store coordinates
   - No editing yet (just display)

3. Integrate into StoreFormModal
   - Replace numeric radius input
   - Show map below address fields
   - Pass store coordinates from autocomplete

4. Test
   - Map loads correctly
   - Store marker appears at correct location
   - Map is responsive

### Phase 2: Polygon Drawing (3-4 hours)

**Tasks:**
1. Add Mapbox Draw controls
   - Polygon drawing tool
   - Edit mode
   - Delete tool

2. Implement drawing handlers
   - onCreate: Save polygon to state
   - onUpdate: Update polygon in state
   - onDelete: Remove polygon from state

3. Visual styling
   - Green fill with 30% opacity
   - Green outline, 2px width
   - Store marker clearly visible

4. Validation
   - Polygon must contain store
   - Minimum/maximum area checks
   - Maximum points per polygon

5. Test
   - Draw polygon around store
   - Edit existing polygon
   - Delete polygon
   - Validation works correctly

### Phase 3: Zone Statistics (2 hours)

**Tasks:**
1. Install Turf.js
   ```bash
   npm install @turf/turf
   ```

2. Calculate statistics
   - Area in km²
   - Perimeter in km
   - Approximate radius

3. Display statistics
   - Show below map
   - Update in real-time as polygon changes

4. Test
   - Statistics are accurate
   - Updates on polygon change

### Phase 4: Database & API (3-4 hours)

**Tasks:**
1. Update database schema
   ```sql
   ALTER TABLE stores ADD COLUMN delivery_zone JSONB;
   ALTER TABLE stores ADD COLUMN delivery_zone_stats JSONB;
   ```

2. Update backend API
   - Accept GeoJSON in store creation/update
   - Validate GeoJSON format
   - Store in database

3. Update frontend service
   - Send GeoJSON in store creation
   - Parse GeoJSON from API response

4. Test
   - Create store with delivery zone
   - Edit store's delivery zone
   - Verify data persists correctly

### Phase 5: Advanced Features (Optional, 2-3 hours each)

**5.1 Multiple Zones**
- Support multiple polygons per store
- Zone tiers (e.g., "Standard", "Extended", "Premium")
- Different delivery fees per zone

**5.2 Exclusion Zones**
- Draw areas to exclude (e.g., competitor territories)
- School/park buffer zones
- Compliance-required exclusions

**5.3 Template Zones**
- Pre-defined zones (e.g., "Downtown Toronto")
- Quick-start templates for common areas
- Clone zones from existing stores

**5.4 Heatmap Overlay**
- Show order density
- Optimize zones based on data
- Identify underserved areas

**Total Estimated Time:** 12-15 hours for Phases 1-4

---

## Database Schema Changes

### Current Schema
```sql
CREATE TABLE stores (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  name VARCHAR(255),
  address JSONB,
  location JSONB,  -- {latitude, longitude}
  delivery_radius_km INTEGER,  -- OLD: Simple radius
  -- ... other fields
);
```

### Updated Schema
```sql
ALTER TABLE stores
  ADD COLUMN delivery_zone JSONB,  -- NEW: GeoJSON polygon
  ADD COLUMN delivery_zone_stats JSONB,  -- NEW: Calculated statistics
  ADD COLUMN delivery_zones JSONB;  -- FUTURE: Multiple zones array

-- Example delivery_zone value
{
  "type": "Polygon",
  "coordinates": [
    [
      [-79.3832, 43.6532],
      [-79.3700, 43.6532],
      [-79.3700, 43.6650],
      [-79.3832, 43.6650],
      [-79.3832, 43.6532]
    ]
  ]
}

-- Example delivery_zone_stats value
{
  "area_km2": 15.3,
  "perimeter_km": 18.7,
  "approximate_radius_km": 2.2,
  "point_count": 24
}

-- FUTURE: Multiple zones
{
  "zones": [
    {
      "name": "Standard Zone",
      "tier": "standard",
      "delivery_fee": 4.99,
      "polygon": { ... }
    },
    {
      "name": "Extended Zone",
      "tier": "extended",
      "delivery_fee": 7.99,
      "polygon": { ... }
    }
  ]
}
```

### Migration Strategy

**Option 1: Keep Both (Recommended for Transition)**
```sql
-- Keep delivery_radius_km for backwards compatibility
-- Add delivery_zone for new features
-- Apps can fall back to radius if polygon not available
```

**Option 2: Convert Radius to Polygon**
```sql
-- Convert existing radius to circular polygon
UPDATE stores
SET delivery_zone = jsonb_build_object(
  'type', 'Polygon',
  'coordinates', generate_circle_polygon(location, delivery_radius_km)
)
WHERE delivery_zone IS NULL;
```

---

## API Endpoints

### Create Store with Delivery Zone
```typescript
POST /api/stores
{
  "tenant_id": "...",
  "name": "Downtown Toronto Store",
  "address": { ... },
  "location": {
    "latitude": 43.6532,
    "longitude": -79.3832
  },
  "delivery_zone": {
    "type": "Polygon",
    "coordinates": [[...]]
  }
}
```

### Update Delivery Zone
```typescript
PUT /api/stores/:id/delivery-zone
{
  "delivery_zone": {
    "type": "Polygon",
    "coordinates": [[...]]
  }
}
```

### Check Delivery Availability
```typescript
POST /api/stores/check-delivery
{
  "latitude": 43.6532,
  "longitude": -79.3832
}

Response:
{
  "available": true,
  "store_id": "...",
  "store_name": "...",
  "delivery_fee": 4.99,
  "estimated_time_minutes": 45
}
```

---

## UI/UX Considerations

### Map Size & Placement

**Recommended Layout:**
```
┌─────────────────────────────────────────────┐
│  Create New Store Form                      │
├─────────────────────────────────────────────┤
│  Store Name: [__________________________]   │
│  Address:    [Autocomplete with dropdown]   │
│  Phone:      [__________________________]   │
│  Email:      [__________________________]   │
├─────────────────────────────────────────────┤
│  Delivery Zone Configuration               │
│  ┌─────────────────────────────────────┐   │
│  │                                       │   │
│  │         [  Map  600px x 400px  ]     │   │
│  │                                       │   │
│  │  Tools: [Polygon] [Edit] [Delete]    │   │
│  │                                       │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Zone Statistics:                           │
│  • Area: 15.3 km²                          │
│  • Approximate radius: 2.2 km              │
│  • Estimated delivery: 30-45 min           │
├─────────────────────────────────────────────┤
│  [Cancel]                    [Create Store] │
└─────────────────────────────────────────────┘
```

### Interaction Patterns

**Drawing Flow:**
1. User clicks "Draw Delivery Zone" button
2. Map activates polygon drawing mode
3. User clicks on map to add points
4. Tooltip shows: "Click to add points, double-click to finish"
5. Polygon appears in real-time as points are added
6. Double-click completes the polygon
7. Statistics update automatically
8. User can edit by clicking "Edit Zone"

**Visual Feedback:**
- **Drawing:** Blue outline follows cursor
- **Complete:** Green fill with 30% opacity
- **Editing:** Blue handles at each vertex
- **Invalid:** Red outline if validation fails

**Mobile Considerations:**
- Touch-friendly polygon editing
- Larger hit targets for vertices
- Pinch-to-zoom support
- Minimize map height on mobile (400px → 300px)

---

## Advanced Features (Future Enhancements)

### 1. Multi-Zone Support

**Use Case:** Different delivery fees for different areas

```typescript
interface DeliveryZoneConfig {
  zones: Array<{
    id: string;
    name: string;
    tier: 'standard' | 'extended' | 'premium';
    delivery_fee: number;
    delivery_time_minutes: number;
    polygon: GeoJSON.Polygon;
    color: string;  // Visual differentiation
  }>;
}
```

**UI:**
- Multiple polygons on same map
- Color-coded zones (green, yellow, orange)
- Zone selector dropdown
- Fee schedule table

### 2. Time-Based Zones

**Use Case:** Different zones during rush hour vs off-peak

```typescript
interface TimeBasedZones {
  lunch_rush: DeliveryZone;    // 11:30 AM - 1:30 PM
  dinner_rush: DeliveryZone;   // 5:00 PM - 8:00 PM
  off_peak: DeliveryZone;      // All other times
}
```

### 3. Dynamic Zones (AI-Powered)

**Use Case:** Automatically adjust zones based on order data

**Features:**
- Analyze order density
- Optimize for driver efficiency
- Suggest zone expansions/contractions
- A/B testing for zone configurations

### 4. Compliance Layers

**Use Case:** Cannabis-specific regulatory compliance

**Layers:**
- Schools (150m buffer required)
- Parks/playgrounds (exclusion)
- Municipal boundaries (license jurisdictions)
- Federal property (exclusion)
- Competitor territories (optional exclusion)

**Implementation:**
```typescript
interface ComplianceLayer {
  type: 'school' | 'park' | 'boundary' | 'federal';
  geometry: GeoJSON.Polygon;
  buffer_meters?: number;
  enforce: boolean;  // Block deliveries if true
}
```

---

## Cost Analysis

### Mapbox Pricing (Recommended)

**Free Tier:**
- 50,000 map loads/month
- Admin dashboard usage: ~500-1,000 loads/month
- **Projected Cost:** $0/month (well within free tier)

**If Exceeding Free Tier:**
- $5 per 1,000 additional map loads
- Admin usage unlikely to exceed free tier
- Mobile app usage separate (already accounted for)

### Google Maps Pricing (Alternative)

**Costs:**
- $7 per 1,000 dynamic map loads
- $200 monthly credit (covers ~28,000 loads)
- Admin usage: ~$3-5/month
- More expensive at scale

### Leaflet (Free Alternative)

**Costs:**
- $0 for library (open source)
- Tile provider costs vary:
  - OpenStreetMap: Free
  - Mapbox tiles: Same as above
  - Google tiles: Not recommended (TOS)

**Verdict:** Mapbox offers best value (free) with excellent features

---

## Technical Challenges & Solutions

### Challenge 1: Polygon Complexity

**Problem:** Users might draw very complex polygons (1000+ points)
**Impact:** Slow rendering, large database storage, slow queries

**Solution:**
- Limit polygon to 50 points maximum
- Simplify polygon using Turf.js simplify
- Show warning if polygon is too complex

```typescript
import { simplify } from '@turf/simplify';

const simplifiedPolygon = simplify(complexPolygon, {
  tolerance: 0.001,  // ~100m tolerance
  highQuality: true
});
```

### Challenge 2: Polygon Validation

**Problem:** Users might draw invalid polygons (self-intersecting, store outside)
**Impact:** Invalid delivery zones, incorrect calculations

**Solution:**
- Real-time validation using Turf.js
- Show error messages immediately
- Prevent form submission if invalid

```typescript
import { booleanPointInPolygon, kinks } from '@turf/turf';

// Check if polygon contains store
const storeInZone = booleanPointInPolygon(storePoint, deliveryZone);

// Check for self-intersections
const intersections = kinks(deliveryZone);
const isValid = intersections.features.length === 0;
```

### Challenge 3: Mobile Performance

**Problem:** Map rendering on mobile devices can be slow
**Impact:** Poor UX, high bounce rate

**Solution:**
- Lazy load map component
- Reduce initial zoom level
- Simplify polygon rendering
- Use lower-quality map style on mobile

```typescript
const mapStyle = isMobile
  ? 'mapbox://styles/mapbox/light-v11'  // Lighter style
  : 'mapbox://styles/mapbox/streets-v12';  // Full style
```

### Challenge 4: GeoJSON Serialization

**Problem:** PostGIS geometry format differs from GeoJSON
**Impact:** Data format mismatches, conversion overhead

**Solution:**
- Store as JSONB (works with both)
- Convert to PostGIS geometry only for spatial queries
- Use ST_GeomFromGeoJSON for conversion

```sql
-- Store as JSONB
ALTER TABLE stores ADD COLUMN delivery_zone JSONB;

-- Create computed PostGIS column (for queries)
ALTER TABLE stores ADD COLUMN delivery_zone_geom GEOMETRY
  GENERATED ALWAYS AS (ST_GeomFromGeoJSON(delivery_zone::text)) STORED;

-- Spatial index for fast queries
CREATE INDEX idx_delivery_zone_geom ON stores USING GIST(delivery_zone_geom);
```

---

## Testing Strategy

### Unit Tests
```typescript
describe('DeliveryZoneMapEditor', () => {
  it('should render map at store location', () => { /* ... */ });
  it('should enable polygon drawing on button click', () => { /* ... */ });
  it('should validate polygon contains store', () => { /* ... */ });
  it('should calculate zone statistics', () => { /* ... */ });
  it('should save GeoJSON to parent state', () => { /* ... */ });
});
```

### Integration Tests
```typescript
describe('Store Creation with Delivery Zone', () => {
  it('should create store with drawn polygon', () => { /* ... */ });
  it('should edit existing delivery zone', () => { /* ... */ });
  it('should reject invalid polygons', () => { /* ... */ });
});
```

### Manual Testing Checklist
- [ ] Map loads at correct location
- [ ] Can draw polygon around store
- [ ] Can edit existing polygon
- [ ] Can delete polygon
- [ ] Statistics update in real-time
- [ ] Validation works correctly
- [ ] GeoJSON saves to database
- [ ] Mobile touch interactions work
- [ ] Dark mode styling correct

---

## Migration Strategy

### Rollout Plan

**Week 1: Development**
- Build DeliveryZoneMapEditor component
- Integrate into StoreFormModal
- Update database schema
- Update API endpoints

**Week 2: Testing**
- Unit tests
- Integration tests
- Manual QA testing
- User acceptance testing

**Week 3: Soft Launch**
- Deploy to staging
- Train store managers
- Gather feedback
- Fix bugs

**Week 4: Full Launch**
- Deploy to production
- Monitor usage
- Support users
- Iterate based on feedback

### Backwards Compatibility

**Strategy:** Keep both radius and polygon
```typescript
interface Store {
  delivery_radius_km?: number;  // DEPRECATED: Legacy field
  delivery_zone?: GeoJSON.Polygon;  // NEW: Preferred field
}

// Delivery check logic
function canDeliver(store: Store, customerLocation: Point): boolean {
  if (store.delivery_zone) {
    // Use polygon if available (preferred)
    return booleanPointInPolygon(customerLocation, store.delivery_zone);
  } else if (store.delivery_radius_km) {
    // Fall back to radius for legacy stores
    const distance = calculateDistance(store.location, customerLocation);
    return distance <= store.delivery_radius_km;
  }
  return false;
}
```

---

`★ Insight ─────────────────────────────────────`

**Why Polygon-Based Zones are Superior:**

1. **Realism** - Delivery areas follow roads, neighborhoods, and natural boundaries. A circular radius doesn't account for rivers, highways, or geographic features that affect delivery times.

2. **Compliance** - Cannabis regulations often require exclusions (schools, parks, federal lands). Polygons allow precise compliance while circles force overly conservative coverage that hurts revenue.

3. **Optimization** - With order data, polygons can be adjusted to match actual delivery patterns. DoorDash and Uber Eats use historical data to optimize zones for driver efficiency.

4. **Pricing Flexibility** - Multi-zone support enables tiered pricing: "Zone 1: $2.99, Zone 2: $4.99". This maximizes revenue while maintaining fairness (closer = cheaper).

The upfront investment in polygon drawing pays off through better coverage, compliance, and customer experience. Simple radius inputs are developer-friendly but operationally limiting.

`─────────────────────────────────────────────────`

---

**Recommendation:** Use **Mapbox GL JS + Mapbox Draw** for polygon-based delivery zones
**Implementation Time:** 12-15 hours for core functionality
**Cost:** $0/month (within Mapbox free tier)
**ROI:** High - better compliance, coverage, and customer experience

---

*Analysis completed: October 13, 2025*
*Next step: Implement DeliveryZoneMapEditor component*
*Status: 📋 READY FOR DEVELOPMENT*
