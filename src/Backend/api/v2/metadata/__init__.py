"""
Metadata Management V2 API

DDD-powered dynamic schema and custom field management using the Metadata bounded context.

Features:
- Custom field schema management
- Field validation rules
- Dynamic entity metadata
- Schema versioning
- Publish workflow (draft → published)
- Field types: string, integer, decimal, boolean, date, datetime, json, list
- Validation rules: required, min/max length, min/max value, regex, enum
- UI hints (help text, placeholder)
- Entity type support (product, customer, order, etc.)

Use Cases:
- Add custom product attributes
- Customer profile extensions
- Order metadata
- Flexible data models without database changes
"""

from .metadata_endpoints import router

__all__ = ["router"]
