# Dynamic Query Tool - Quick Reference Guide

## For AI Agent Developers

### Tool Name
`query_database`

### Purpose
Query operational data (orders, inventory, customers, etc.) with automatic access control and row-level filtering. **Prevents hallucinations by returning real data.**

### When to Use
- User asks about inventory quantities: "How many [product] do we have?"
- User asks about orders: "What orders do I have?" or "Show me today's orders"
- User asks about customers: "How many customers do we have?"
- User needs real-time data from the database
- **Instead of guessing/fabricating numbers**

### Function Signature
```python
await query_database(
    resource_type: str,      # Required: What to query (see Available Resources below)
    user_role: str,          # Optional: Defaults to "customer" (from session)
    customer_id: str,        # Optional: For customer-level filtering (from session)
    store_id: str,           # Optional: For store-level filtering (from session)  
    tenant_id: str,          # Optional: For tenant-level filtering (from session)
    filters: dict,           # Optional: Additional filters (category, status, date_range, etc.)
    limit: int              # Optional: Max results (default 50, max 100)
)
```

### Available Resources by Role

**Customer** can access:
- `my_orders` - Their own orders
- `my_profile` - Their own profile

**Staff** can access:
- `products` - Product catalog (their store only)
- `inventory` - Stock levels (their store only) ⭐ **USE THIS FOR INVENTORY QUESTIONS**
- `store_orders` - Orders (their store only)

**Store Manager** can also access:
- `customers` - Customer information (their store)
- `promotions` - Store promotions

**Tenant Admin** can also access:
- `all_stores` - All stores in their tenant
- `all_orders` - All orders in their tenant
- `purchase_orders` - Purchase orders
- `deliveries` - Delivery information

**Super Admin** can also access:
- `admin_users` - System users
- `all_tenants` - All tenants

### Example: Agent Handling Inventory Question

**User**: "How many grams of Blue Dream do we have in stock?"

**Agent Thinking**:
1. User asking about inventory quantity
2. Need to use `query_database` tool with `resource_type="inventory"`
3. Filter by product name

**Agent Tool Call**:
```json
{
  "name": "query_database",
  "arguments": {
    "resource_type": "inventory",
    "filters": {
      "product_name": "Blue Dream"
    },
    "limit": 10
  }
}
```

**Tool Response**:
```json
{
  "success": true,
  "data": [
    {
      "product_name": "Blue Dream",
      "category": "flower",
      "quantity_grams": 128.5,
      "unit": "grams",
      "last_updated": "2025-10-23T10:30:00Z"
    }
  ],
  "count": 1,
  "message": "Retrieved 1 inventory records",
  "access_level": "staff"
}
```

**Agent Response**:
"We currently have 128.5 grams of Blue Dream in stock, last updated today at 10:30 AM."

### Common Filter Examples

```python
# By category
filters={"category": "flower"}

# By status
filters={"status": "pending"}

# By date range
filters={
    "date_from": "2025-10-01",
    "date_to": "2025-10-23"
}

# Text search
filters={"search": "Blue Dream"}

# Combine multiple filters
filters={
    "category": "flower",
    "status": "in_stock",
    "search": "indica"
}
```

### Error Handling

**Access Denied**:
```json
{
  "success": false,
  "data": [],
  "count": 0,
  "message": "Access denied: customer role cannot access inventory",
  "access_level": "customer"
}
```

**Agent Response**: "I don't have permission to access inventory information. Please contact a staff member for stock availability."

**No Results**:
```json
{
  "success": true,
  "data": [],
  "count": 0,
  "message": "Retrieved 0 inventory records",
  "access_level": "staff"
}
```

**Agent Response**: "I couldn't find any inventory records for that product. It may be out of stock or not in our catalog."

### Security Notes

1. **Automatic Filtering**: Tool automatically applies row-level filters based on user_role
   - Customers only see their own data (filtered by customer_id)
   - Staff only see their store's data (filtered by store_id)
   - Tenant admins only see their tenant's data (filtered by tenant_id)

2. **Access Denied is Good**: If you get "Access denied", the security is working correctly. Don't try to work around it - guide the user to contact someone with appropriate permissions.

3. **Don't Hardcode IDs**: Let the system pass customer_id, store_id, tenant_id from the session. Don't hardcode these values.

### Integration with Agent Prompts

Add to agent system prompt:
```
You have access to the `query_database` tool for retrieving real-time operational data.

**CRITICAL**: 
- ALWAYS use this tool for inventory quantities - NEVER guess or fabricate numbers
- Use this tool for order status, customer information, and other operational data
- If access is denied, politely inform the user they need appropriate permissions

Available resources depend on user's role:
- All users: my_orders, my_profile  
- Staff+: products, inventory, store_orders
- Manager+: customers, promotions
- Tenant Admin+: all_stores, all_orders, purchase_orders, deliveries
- Super Admin: admin_users, all_tenants
```

### Testing Checklist

Before deploying:
- [ ] Test inventory query: "How many [product] do we have?"
- [ ] Test order query: "Show me my orders"
- [ ] Test access control: Customer shouldn't access inventory
- [ ] Test filtering: Results should be filtered by user's store/tenant
- [ ] Test error handling: Graceful response when access denied
- [ ] Test with different roles: customer, staff, manager, admin

### Troubleshooting

**Problem**: "Tool not found: query_database"
**Solution**: Tool is lazy-initialized on first use. Try calling it once to initialize.

**Problem**: "All connection attempts failed"
**Solution**: API server is not running. Check that the backend API is accessible.

**Problem**: "Access denied" for legitimate request
**Solution**: Check that user_role is correctly set in the session. May need to pass explicitly.

**Problem**: Agent still hallucinating numbers
**Solution**: Update agent prompt to ALWAYS use query_database for inventory. Add examples.

### Performance

- **Average Latency**: ~5-50ms (depending on API response time)
- **Caching**: Not implemented yet - every query hits the API
- **Rate Limiting**: Not implemented yet - be mindful of query frequency

### Future Enhancements

1. Response caching (TTL: 30 seconds for inventory, 5 minutes for products)
2. Batch queries (query multiple resources in one call)
3. Aggregations (sum, count, average, etc.)
4. More filter options (price range, date comparisons, etc.)
5. Export capabilities (CSV, JSON)
6. Query history and analytics
