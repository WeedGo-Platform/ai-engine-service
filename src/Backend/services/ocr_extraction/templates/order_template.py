"""
Order Template

Pre-built template for extracting purchase order information from documents.

Use Case:
- Processing vendor purchase orders
- Extracting line items from order documents
- Automating order entry

Fields Extracted:
- order_number: Purchase order number
- vendor: Vendor/supplier name
- order_date: Date of order
- line_items: List of items ordered (table extraction)
- subtotal: Subtotal amount
- tax: Tax amount
- total: Total amount
- shipping: Shipping cost
- payment_terms: Payment terms (Net 30, etc.)
"""

from ..domain.value_objects import Template, Field
from ..domain.enums import TemplateType, FieldType


def create_order_template() -> Template:
    """
    Create template for purchase order extraction

    Returns:
        Template configured for order documents
    """

    # Define fields to extract
    fields = (
        Field(
            name="order_number",
            field_type=FieldType.TEXT,
            description="Purchase order number or reference ID",
            required=True,
            example="PO-2025-001234",
        ),
        Field(
            name="vendor",
            field_type=FieldType.TEXT,
            description="Vendor or supplier company name",
            required=True,
            example="One Wholesale Distribution",
        ),
        Field(
            name="vendor_contact",
            field_type=FieldType.TEXT,
            description="Vendor contact person name",
            required=False,
            example="John Smith",
        ),
        Field(
            name="order_date",
            field_type=FieldType.DATE,
            description="Date when order was placed (YYYY-MM-DD format)",
            required=True,
            example="2025-10-20",
            validation_pattern=r"^\d{4}-\d{2}-\d{2}$",
        ),
        Field(
            name="expected_delivery",
            field_type=FieldType.DATE,
            description="Expected delivery date (YYYY-MM-DD format)",
            required=False,
            example="2025-10-25",
            validation_pattern=r"^\d{4}-\d{2}-\d{2}$",
        ),
        Field(
            name="line_items",
            field_type=FieldType.TABLE,
            description="List of items in the order with SKU, description, quantity, unit price, total",
            required=True,
            example='[{"sku": "RAW-KSS-32", "description": "RAW King Size Slim", "quantity": "50", "unit_price": "1.50", "total": "75.00"}]',
        ),
        Field(
            name="subtotal",
            field_type=FieldType.PRICE,
            description="Subtotal amount before tax (numbers only)",
            required=True,
            example="1250.00",
            validation_pattern=r"^\d+(\.\d{2})?$",
        ),
        Field(
            name="tax",
            field_type=FieldType.PRICE,
            description="Tax amount (numbers only)",
            required=False,
            example="162.50",
            validation_pattern=r"^\d+(\.\d{2})?$",
        ),
        Field(
            name="shipping",
            field_type=FieldType.PRICE,
            description="Shipping cost (numbers only)",
            required=False,
            example="25.00",
            validation_pattern=r"^\d+(\.\d{2})?$",
        ),
        Field(
            name="total",
            field_type=FieldType.PRICE,
            description="Total amount including tax and shipping (numbers only)",
            required=True,
            example="1437.50",
            validation_pattern=r"^\d+(\.\d{2})?$",
        ),
        Field(
            name="payment_terms",
            field_type=FieldType.TEXT,
            description="Payment terms (Net 30, COD, Prepaid, etc.)",
            required=False,
            example="Net 30",
        ),
        Field(
            name="currency",
            field_type=FieldType.TEXT,
            description="Currency code (USD, CAD, etc.)",
            required=False,
            example="CAD",
        ),
        Field(
            name="notes",
            field_type=FieldType.TEXT,
            description="Any special notes or instructions on the order",
            required=False,
            example="Deliver to warehouse dock B",
        ),
    )

    # Build extraction prompt
    prompt_template = """
You are an expert at extracting structured data from purchase order documents.

Analyze this purchase order image and extract the following information:

**REQUIRED FIELDS:**
- order_number: PO number or reference ID
- vendor: Vendor/supplier company name
- order_date: Date of order (YYYY-MM-DD format)
- line_items: Array of items with SKU, description, quantity, unit_price, total
- subtotal: Subtotal amount (numbers only, no currency symbol)
- total: Total amount (numbers only, no currency symbol)

**OPTIONAL FIELDS (extract if visible):**
- vendor_contact: Contact person name
- expected_delivery: Expected delivery date (YYYY-MM-DD)
- tax: Tax amount (numbers only)
- shipping: Shipping cost (numbers only)
- payment_terms: Payment terms
- currency: Currency code (USD, CAD, etc.)
- notes: Special notes or instructions

**LINE ITEMS FORMAT:**
Extract all line items as an array of objects. Each line item should have:
- sku: Product SKU or item code
- description: Product description
- quantity: Quantity ordered
- unit_price: Price per unit (numbers only)
- total: Line total (numbers only)

**IMPORTANT INSTRUCTIONS:**
1. Extract EXACTLY what you see - don't calculate or infer
2. For dates: use YYYY-MM-DD format (e.g., "2025-10-20")
3. For prices: numbers only, no currency symbols (e.g., "1250.00" not "$1,250.00")
4. For line items: preserve exact SKUs and descriptions from document
5. If subtotal/tax/total math doesn't add up, report what's shown (don't calculate)
6. If a field is not visible, omit it from the response

**OUTPUT FORMAT:**
Return a JSON object with the extracted fields:

```json
{
  "order_number": "PO-2025-001234",
  "vendor": "One Wholesale Distribution",
  "vendor_contact": "John Smith",
  "order_date": "2025-10-20",
  "expected_delivery": "2025-10-25",
  "line_items": [
    {
      "sku": "RAW-KSS-32",
      "description": "RAW Classic King Size Slim Rolling Papers",
      "quantity": "50",
      "unit_price": "1.50",
      "total": "75.00"
    },
    {
      "sku": "ZIG-ZAG-125",
      "description": "Zig-Zag 1¼ Rolling Papers",
      "quantity": "100",
      "unit_price": "0.85",
      "total": "85.00"
    }
  ],
  "subtotal": "1250.00",
  "tax": "162.50",
  "shipping": "25.00",
  "total": "1437.50",
  "payment_terms": "Net 30",
  "currency": "CAD",
  "notes": "Deliver to warehouse dock B"
}
```

Only include fields that are clearly visible in the document.
""".strip()

    # Define JSON output schema
    output_schema = """{
  "type": "object",
  "properties": {
    "order_number": {"type": "string"},
    "vendor": {"type": "string"},
    "vendor_contact": {"type": "string"},
    "order_date": {"type": "string", "pattern": "^\\\\d{4}-\\\\d{2}-\\\\d{2}$"},
    "expected_delivery": {"type": "string", "pattern": "^\\\\d{4}-\\\\d{2}-\\\\d{2}$"},
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sku": {"type": "string"},
          "description": {"type": "string"},
          "quantity": {"type": "string"},
          "unit_price": {"type": "string"},
          "total": {"type": "string"}
        },
        "required": ["sku", "description", "quantity", "unit_price", "total"]
      }
    },
    "subtotal": {"type": "string", "pattern": "^\\\\d+(\\\\.\\\\d{2})?$"},
    "tax": {"type": "string", "pattern": "^\\\\d+(\\\\.\\\\d{2})?$"},
    "shipping": {"type": "string", "pattern": "^\\\\d+(\\\\.\\\\d{2})?$"},
    "total": {"type": "string", "pattern": "^\\\\d+(\\\\.\\\\d{2})?$"},
    "payment_terms": {"type": "string"},
    "currency": {"type": "string"},
    "notes": {"type": "string"}
  },
  "required": ["order_number", "vendor", "order_date", "line_items", "subtotal", "total"]
}"""

    # Create template
    template = Template(
        name="order_extraction",
        template_type=TemplateType.ORDER,
        description="Extract purchase order details from documents",
        fields=fields,
        prompt_template=prompt_template,
        output_schema=output_schema,
    )

    return template


# Convenience: Pre-built instance
ORDER_TEMPLATE = create_order_template()
