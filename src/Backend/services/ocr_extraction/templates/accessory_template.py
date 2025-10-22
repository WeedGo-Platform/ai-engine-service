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
You are a precise OCR system. Your ONLY job is to read visible text from this image.

⚠️ CRITICAL RULES - VIOLATION WILL CAUSE SYSTEM FAILURE:

1. **ONLY EXTRACT TEXT YOU CAN LITERALLY SEE AND READ**
2. **DO NOT INVENT, GUESS, OR HALLUCINATE ANY INFORMATION**
3. **IF YOU CANNOT CLEARLY READ SOMETHING → LEAVE IT BLANK/EMPTY**
4. **MAKING UP DATA IS STRICTLY FORBIDDEN**

---

**EXTRACTION INSTRUCTIONS:**

**product_name** (REQUIRED):
- Read the main product name printed on the package
- Must be exact text as shown - no modifications
- Example: "RAW Original Tips" (not "RAW King Size Tips" if King Size isn't visible)

**brand** (REQUIRED):
- The brand name ONLY - typically the logo or main brand text
- Examples: "RAW", "Zig Zag", "OCB"
- ⚠️ DO NOT extract: warning labels, legal disclaimers, manufacturer addresses
- ⚠️ If brand logo/text is not clearly visible → leave empty

**barcode**:
- Look for vertical black/white bars (barcode pattern)
- Read the 12-13 digit number printed UNDER those bars
- ⚠️ If barcode bars are NOT visible → leave empty
- ⚠️ If numbers under bars are blurry/unreadable → leave empty
- ⚠️ DO NOT guess or make up barcode numbers
- ⚠️ DO NOT use random product codes as barcodes

**size_variant**:
- Read ANY size-related text visible on package
- Examples of what to extract:
  * "50 tips per pack" ✓
  * "King Size" ✓
  * "1¼ size" ✓
  * "100 leaves" ✓
  * "25 packs per box" ✓
- ⚠️ ONLY extract size text that is ACTUALLY PRINTED on the package
- ⚠️ If you don't see any size text → leave empty
- ⚠️ DO NOT assume or infer size from product type

**description**:
- Any visible product features, materials, descriptions
- Examples: "unbleached", "natural gum", "made in Spain"
- Only include text you can actually read on the package

**sku**, **price**, **quantity**, **category**:
- Extract if clearly visible
- Leave empty if not visible

---

**VALIDATION CHECKLIST BEFORE RESPONDING:**

For EACH field you're about to fill in, ask yourself:
- ✓ Can I see this exact text in the image?
- ✓ Can I read it clearly enough to be certain?
- ✓ Am I copying it exactly as shown?

If any answer is NO → DO NOT fill that field!

---

**EXAMPLES OF CORRECT BEHAVIOR:**

Image shows: "RAW Original Tips - 50 tips per pack"
✓ CORRECT: {"product_name": "RAW Original Tips", "brand": "RAW", "size_variant": "50 tips per pack"}
✗ WRONG: {"product_name": "RAW Original Tips", "brand": "RAW", "size_variant": "King Size"} ← HALLUCINATION!

Image shows barcode bars with clear numbers underneath: 716165250333
✓ CORRECT: {"barcode": "716165250333"}

Image shows barcode bars but numbers are blurry
✓ CORRECT: {"barcode": ""} ← Leave empty, don't guess!

Image shows "Not labeled for sport or sale in the US"
✓ CORRECT: Do NOT extract this as brand - it's a warning label
✗ WRONG: {"brand": "Not labeled for sport or sale in the US"}

---

**OUTPUT FORMAT - JSON ONLY:**
```json
{
  "product_name": "",
  "brand": "",
  "barcode": "",
  "size_variant": "",
  "description": "",
  "sku": "",
  "price": "",
  "quantity": "",
  "category": ""
}
```

**FINAL REMINDER: Empty fields are REQUIRED when data is not clearly visible. Accuracy > Completeness.**
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
