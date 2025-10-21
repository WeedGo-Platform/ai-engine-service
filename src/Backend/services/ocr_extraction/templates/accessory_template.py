"""
Accessory Template

Pre-built template for extracting accessory product information from photos.

Use Case:
- Barcode lookup failed or returned low confidence
- Need to extract product details from packaging photo
- Quick intake of new accessories

Fields Extracted:
- product_name: Full product name
- brand: Manufacturer/brand name
- sku: Product SKU/model number
- barcode: UPC/EAN barcode (if visible)
- price: Retail price (if visible)
- quantity: Quantity visible in image
- description: Product description/details
- category: Product category (papers, tips, lighters, etc.)
"""

from ..domain.value_objects import Template, Field
from ..domain.enums import TemplateType, FieldType


def create_accessory_template() -> Template:
    """
    Create template for accessory extraction

    Returns:
        Template configured for accessory product photos
    """

    # Define fields to extract
    fields = (
        Field(
            name="product_name",
            field_type=FieldType.TEXT,
            description="Full product name as shown on packaging",
            required=True,
            example="RAW Classic King Size Slim Rolling Papers",
        ),
        Field(
            name="brand",
            field_type=FieldType.TEXT,
            description="Brand or manufacturer name",
            required=True,
            example="RAW",
        ),
        Field(
            name="sku",
            field_type=FieldType.TEXT,
            description="Product SKU, model number, or item code",
            required=False,
            example="RAW-KSS-32",
        ),
        Field(
            name="barcode",
            field_type=FieldType.BARCODE,
            description="UPC or EAN barcode number (digits only, no spaces)",
            required=False,
            example="716165177395",
            validation_pattern=r"^\d{8,14}$",  # 8-14 digits
        ),
        Field(
            name="price",
            field_type=FieldType.PRICE,
            description="Retail price if visible (numbers only, no currency symbol)",
            required=False,
            example="2.99",
            validation_pattern=r"^\d+(\.\d{2})?$",  # Money format
        ),
        Field(
            name="quantity",
            field_type=FieldType.NUMBER,
            description="Quantity or count shown in image",
            required=False,
            example="32",
            validation_pattern=r"^\d+$",  # Positive integer
        ),
        Field(
            name="description",
            field_type=FieldType.TEXT,
            description="Product description, features, or details visible on packaging",
            required=False,
            example="Ultra thin unbleached rolling papers with natural gum",
        ),
        Field(
            name="category",
            field_type=FieldType.TEXT,
            description="Product category (papers, tips, lighters, grinders, etc.)",
            required=False,
            example="rolling_papers",
        ),
        Field(
            name="size_variant",
            field_type=FieldType.TEXT,
            description="Size variant if applicable (King Size, 1¼, etc.)",
            required=False,
            example="King Size Slim",
        ),
    )

    # Build extraction prompt
    prompt_template = """
You are an expert at extracting product information from accessory packaging photos.

Analyze this image and extract the following information:

**REQUIRED FIELDS:**
- product_name: The full product name as shown on the packaging
- brand: The brand or manufacturer name

**OPTIONAL FIELDS (extract if visible):**
- sku: Product SKU or model number
- barcode: UPC/EAN barcode (numbers only, no spaces)
- price: Retail price (numbers only, no $ symbol)
- quantity: Quantity or count shown
- description: Product description or features
- category: Product category (papers, tips, lighters, grinders, etc.)
- size_variant: Size designation (King Size, 1¼, etc.)

**IMPORTANT INSTRUCTIONS:**
1. Extract EXACTLY what you see - don't infer or guess
2. For barcode: digits only, no spaces or dashes
3. For price: numbers only (e.g., "2.99" not "$2.99")
4. For quantity: just the number (e.g., "32" not "32 papers")
5. If a field is not visible, omit it from the response
6. Be precise with product names - include full details shown

**OUTPUT FORMAT:**
Return a JSON object with the extracted fields:

```json
{
  "product_name": "...",
  "brand": "...",
  "sku": "..." (if visible),
  "barcode": "..." (if visible),
  "price": "..." (if visible),
  "quantity": "..." (if visible),
  "description": "..." (if visible),
  "category": "..." (if visible),
  "size_variant": "..." (if visible)
}
```

Only include fields that are clearly visible in the image.
""".strip()

    # Define JSON output schema
    output_schema = """{
  "type": "object",
  "properties": {
    "product_name": {"type": "string"},
    "brand": {"type": "string"},
    "sku": {"type": "string"},
    "barcode": {"type": "string", "pattern": "^\\\\d{8,14}$"},
    "price": {"type": "string", "pattern": "^\\\\d+(\\\\.\\\\d{2})?$"},
    "quantity": {"type": "string", "pattern": "^\\\\d+$"},
    "description": {"type": "string"},
    "category": {"type": "string"},
    "size_variant": {"type": "string"}
  },
  "required": ["product_name", "brand"]
}"""

    # Create template
    template = Template(
        name="accessory_extraction",
        template_type=TemplateType.ACCESSORY,
        description="Extract product details from accessory packaging photos",
        fields=fields,
        prompt_template=prompt_template,
        output_schema=output_schema,
    )

    return template


# Convenience: Pre-built instance
ACCESSORY_TEMPLATE = create_accessory_template()
