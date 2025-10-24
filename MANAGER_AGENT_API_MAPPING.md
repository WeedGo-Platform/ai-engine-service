# Manager Agent API Endpoint Mapping

## Overview
The Manager Agent must handle ALL queries that the ai-admin-dashboard makes. This document maps user queries to API endpoints, intents, and resource types.

---

## 1. DASHBOARD / ANALYTICS QUERIES

### Intent: `dashboard_stats`
**User Queries:**
- "show me dashboard stats"
- "what's our revenue today"
- "how are we performing"
- "show me today's metrics"

**API Endpoint:** `GET /analytics/dashboard`
**Query Construction:**
```json
{
  "resource_type": "analytics",
  "endpoint": "/analytics/dashboard",
  "filters": {
    "store_id": "{store_id}",
    "period": "today|week|month"
  }
}
```

**Response Data:**
- revenue.total
- revenue.trend
- orders.total
- orders.trend
- customers.total
- customers.trend
- inventory.total
- inventory.low_stock

---

## 2. INVENTORY QUERIES

### Intent: `inventory_query`
**User Queries:**
- "how many items do we have in inventory"
- "show me inventory"
- "what's in stock"
- "list all products"
- "check inventory levels"

**API Endpoint:** `GET /store-inventory/list`
**Query Construction:**
```json
{
  "resource_type": "inventory",
  "endpoint": "/store-inventory/list",
  "filters": {
    "store_id": "{store_id}",
    "category": "optional",
    "brand": "optional",
    "low_stock": "boolean",
    "search": "optional",
    "limit": 50,
    "offset": 0
  }
}
```

**Response Data:**
- items[] with: sku, product_name, quantity, price, stock_status

### Intent: `low_stock_query`
**User Queries:**
- "what items are low in stock"
- "show me low stock items"
- "inventory alerts"

**API Endpoint:** `GET /store-inventory/low-stock`
**Response Data:**
- items[] with: sku, product_name, current_quantity, reorder_point

---

## 3. ORDER QUERIES

### Intent: `order_query`
**User Queries:**
- "how many orders do we have"
- "show me pending orders"
- "list recent orders"
- "what orders came in today"
- "how much have we sold today"

**API Endpoint:** `GET /api/orders`
**Query Construction:**
```json
{
  "resource_type": "my_orders",
  "endpoint": "/api/orders",
  "filters": {
    "store_id": "{store_id}",
    "status": "pending|processing|completed|cancelled",
    "payment_status": "pending|paid|refunded",
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD",
    "limit": 50
  }
}
```

**Response Data:**
- orders[] with: order_number, customer_name, total_amount, status, payment_status, created_at

### Intent: `order_summary_query`
**User Queries:**
- "what's our order summary"
- "sales analytics"
- "order statistics"

**API Endpoint:** `GET /api/orders/analytics/summary`

---

## 4. CUSTOMER QUERIES

### Intent: `customer_query`
**User Queries:**
- "how many customers do we have"
- "list customers"
- "show me customer data"
- "who are our customers"

**API Endpoint:** `GET /api/customers`
**Query Construction:**
```json
{
  "resource_type": "customers",
  "endpoint": "/api/customers",
  "filters": {
    "tenant_id": "{tenant_id}",
    "customer_type": "optional",
    "limit": 50
  }
}
```

**Response Data:**
- customers[] with: id, name, email, phone, loyalty_points, created_at

---

## 5. DELIVERY QUERIES

### Intent: `delivery_query`
**User Queries:**
- "how many deliveries today"
- "show me active deliveries"
- "delivery status"
- "what deliveries are in progress"

**API Endpoint:** `GET /api/v1/delivery/active`
**Query Construction:**
```json
{
  "resource_type": "deliveries",
  "endpoint": "/api/v1/delivery/active",
  "filters": {
    "tenant_id": "{tenant_id}",
    "status": "pending|in_progress|delivered",
    "date": "YYYY-MM-DD"
  }
}
```

**Response Data:**
- deliveries[] with: delivery_id, order_number, customer_name, address, status, driver

---

## 6. PURCHASE ORDER QUERIES

### Intent: `purchase_order_query`
**User Queries:**
- "show me purchase orders"
- "what POs do we have"
- "incoming inventory"
- "supplier orders"

**API Endpoint:** `GET /api/inventory/purchase-orders`
**Query Construction:**
```json
{
  "resource_type": "purchase_orders",
  "endpoint": "/api/inventory/purchase-orders",
  "filters": {
    "tenant_id": "{tenant_id}",
    "status": "draft|submitted|approved|received",
    "supplier_id": "optional"
  }
}
```

**Response Data:**
- purchase_orders[] with: po_number, supplier_name, total_amount, status, expected_date

---

## 7. PRODUCT QUERIES

### Intent: `product_search_query`
**User Queries:**
- "search for [product name]"
- "find products by [brand]"
- "show me [category] products"

**API Endpoint:** `GET /api/products`
**Query Construction:**
```json
{
  "resource_type": "products",
  "endpoint": "/api/products",
  "filters": {
    "store_id": "{store_id}",
    "search": "query",
    "category": "optional",
    "brand": "optional",
    "limit": 50
  }
}
```

---

## 8. SALES/REVENUE QUERIES

### Intent: `sales_query`
**User Queries:**
- "how much did we sell today"
- "what's our revenue"
- "sales for this week"
- "total sales"

**API Endpoint:** `GET /api/orders/analytics/summary`
**Response Data:**
- total_revenue
- total_orders
- average_order_value
- period (day/week/month)

---

## 9. STORE QUERIES

### Intent: `store_query`
**User Queries:**
- "show me all stores"
- "which stores do we have"
- "store locations"

**API Endpoint:** `GET /api/stores/tenant/{tenant_id}`
**Response Data:**
- stores[] with: store_id, store_name, address, status, manager

---

## TOOL EXECUTION FLOW

```
User Query: "how many pending orders do we have"
    ↓
Intent Detection: order_query
    ↓
Template Selection: order_query template
    ↓
Tool Config: required_tools: ["query_database"]
    ↓
DynamicQueryTool Execution:
    - resource_type: "my_orders"
    - endpoint: "/api/orders"
    - filters: { status: "pending", store_id: X, limit: 50 }
    ↓
HTTP Request: GET http://localhost:5024/api/orders?status=pending&store_id=X&limit=50
    ↓
Response: { "orders": [...actual data...], "total": 25 }
    ↓
LLM Generation: "You have 25 pending orders currently."
```

---

## RESOURCE TYPE MAPPING

| Intent | Resource Type | Endpoint | Filters |
|--------|---------------|----------|---------|
| dashboard_stats | analytics | /analytics/dashboard | store_id, period |
| inventory_query | inventory | /store-inventory/list | store_id, category, search |
| low_stock_query | inventory | /store-inventory/low-stock | store_id |
| order_query | my_orders | /api/orders | store_id, status, date |
| order_summary_query | my_orders | /api/orders/analytics/summary | store_id, period |
| customer_query | customers | /api/customers | tenant_id, customer_type |
| delivery_query | deliveries | /api/v1/delivery/active | tenant_id, status |
| purchase_order_query | purchase_orders | /api/inventory/purchase-orders | tenant_id, status |
| product_search_query | products | /api/products | store_id, search, category |
| store_query | all_stores | /api/stores/tenant/{tenant_id} | tenant_id |

---

## CRITICAL RULES

1. **NEVER FABRICATE DATA**: Always call the appropriate API endpoint
2. **USE REAL NUMBERS**: Return actual counts from API responses
3. **FORMAT CLEARLY**: Present data in clear, structured format
4. **CITE SOURCE**: Mention which API/resource the data came from
5. **HANDLE ERRORS**: If API fails, say "Unable to retrieve data" not "10 items"
6. **CONTEXT AWARE**: Use store_id for store managers, tenant_id for tenant admins
7. **DATE FILTERING**: Support "today", "this week", "this month" queries
8. **AGGREGATIONS**: When asked "how many", count the actual items in response

