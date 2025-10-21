# OCR Extraction System

Complete OCR extraction system with runtime provider discovery, multiple extraction strategies, and template-based data extraction.

## ✨ Features

- **🔍 Auto-Discovery**: Automatically detects available models (Ollama, Hugging Face, cloud APIs)
- **🎯 Template-Based**: Pre-built templates for common use cases (accessories, orders)
- **🔄 Multiple Strategies**: Local-only, cloud-only, or intelligent hybrid
- **💰 Free Providers Only**: All providers are completely free (no paid API calls!)
- **✅ Built-in Validation**: Automatic validation with detailed error messages
- **🏗️ Clean Architecture**: DDD, DRY, KISS, SRP principles throughout

## 🚀 Quick Start

### Installation

```bash
# Install one or more providers:

# Option 1: Ollama (recommended)
ollama pull minicpm-v

# Option 2: Hugging Face model
cd services/ocr_extraction/models
git clone https://huggingface.co/PaddlePaddle/PaddleOCR-VL

# Option 3: Cloud fallback (free tier)
export GEMINI_API_KEY="your-api-key"

# Install Python dependencies
pip install pillow google-generativeai transformers torch httpx
```

### Basic Usage

```python
from services.ocr_extraction import ocr_service, accessory_extractor

# Initialize (auto-discovers available models)
await ocr_service.initialize()

# Extract accessory details from photo
result = await accessory_extractor.extract_from_file('/path/to/photo.jpg')

# Access extracted data
print(f"Product: {result.extracted_data['product_name']}")
print(f"Brand: {result.extracted_data['brand']}")
print(f"Barcode: {result.extracted_data['barcode']}")
print(f"Confidence: {result.get_overall_confidence():.2%}")
```

## 📚 Documentation

### Pre-Built Templates

#### Accessory Template
Extracts product details from accessory packaging photos:
- Product name, brand, SKU
- Barcode (UPC/EAN)
- Price, quantity
- Description, category

```python
from services.ocr_extraction import accessory_extractor

result = await accessory_extractor.extract_from_file('/path/to/product.jpg')
```

#### Order Template
Extracts purchase order details from documents:
- Order number, vendor, date
- Line items (SKU, description, quantity, price)
- Subtotal, tax, shipping, total

```python
from services.ocr_extraction import order_extractor

result = await order_extractor.extract_from_file('/path/to/po.pdf')
line_items = order_extractor.get_line_items(result)
```

### Extraction Strategies

#### Local Strategy (Default)
- Uses Ollama + Hugging Face models only
- Fast, free, unlimited
- Works offline
- Privacy-friendly

```python
from services.ocr_extraction import ExtractionOptions

options = ExtractionOptions(strategy='local')
result = await ocr_service.extract(document, template, options)
```

#### Cloud Strategy
- Uses Google Gemini free tier only
- Fast (1-2s), highly accurate (95%+)
- 1,500 requests/day limit
- Requires internet

```python
options = ExtractionOptions(strategy='cloud')
result = await ocr_service.extract(document, template, options)
```

#### Hybrid Strategy (Recommended)
- Tries local first (fast, free)
- Falls back to cloud if confidence <75%
- Best of both worlds: 90% local, 10% cloud

```python
options = ExtractionOptions(strategy='hybrid')  # Default
result = await ocr_service.extract(document, template, options)
```

## 🏗️ Architecture

### Layered Design (DDD)

```
services/ocr_extraction/
├── domain/                  # Domain Layer (business logic)
│   ├── enums.py            # Ubiquitous language
│   ├── exceptions.py       # Domain exceptions
│   ├── value_objects.py    # Immutable configs
│   └── entities.py         # Domain entities
│
├── providers/              # Infrastructure Layer
│   ├── ollama_provider.py
│   ├── huggingface_provider.py
│   └── gemini_provider.py
│
├── strategies/             # Strategy Pattern
│   ├── local_vision_strategy.py
│   ├── cloud_vision_strategy.py
│   └── hybrid_vision_strategy.py
│
├── services/               # Application Services
│   ├── model_discovery.py  # Auto-discovery
│   ├── validation_service.py
│   └── ocr_extraction_service.py  # Main orchestrator
│
├── templates/              # Pre-built templates
│   ├── accessory_template.py
│   └── order_template.py
│
└── extractors/             # Application Layer
    ├── accessory_extractor.py
    └── order_extractor.py
```

### Key Design Principles

**DDD (Domain-Driven Design)**:
- Clear bounded context (OCR extraction)
- Ubiquitous language (enums used everywhere)
- Layered architecture (domain → services → application)

**DRY (Don't Repeat Yourself)**:
- Shared provider base class
- Centralized validation service
- Reusable template system

**KISS (Keep It Simple, Stupid)**:
- Auto-discovery (just install model, it works!)
- Pre-built templates (no configuration needed)
- Clean API (2 lines to extract data)

**SRP (Single Responsibility Principle)**:
- Each class has one job
- ModelDiscoveryService: only discovers models
- ValidationService: only validates data
- Providers: only talk to their API

## 🔧 Advanced Usage

### Custom Templates

```python
from services.ocr_extraction import Template, Field, FieldType, TemplateType

# Define custom template
custom_template = Template(
    name="invoice_extraction",
    template_type=TemplateType.INVOICE,
    description="Extract invoice details",
    fields=(
        Field(
            name="invoice_number",
            field_type=FieldType.TEXT,
            description="Invoice number",
            required=True
        ),
        Field(
            name="total_amount",
            field_type=FieldType.PRICE,
            description="Total amount",
            required=True,
            validation_pattern=r"^\d+(\.\d{2})?$"
        ),
    ),
    prompt_template="Extract invoice details from this image...",
    output_schema='{"type": "object", ...}'
)

# Use custom template
result = await ocr_service.extract(document, custom_template)
```

### Batch Processing

```python
import asyncio

# Process multiple images in parallel
tasks = [
    accessory_extractor.extract_from_file(path)
    for path in image_paths
]

results = await asyncio.gather(*tasks)
```

### Error Handling

```python
from services.ocr_extraction import (
    ExtractionError,
    AllProvidersExhaustedError,
    RateLimitError
)

try:
    result = await accessory_extractor.extract_from_file('/path/to/image.jpg')
except AllProvidersExhaustedError:
    print("No providers available - install Ollama or set GEMINI_API_KEY")
except RateLimitError as e:
    print(f"Rate limited - retry after {e.retry_after}s")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
```

## 📊 Provider Comparison

| Provider | Cost | Latency | Accuracy | Offline | Limit |
|----------|------|---------|----------|---------|-------|
| Ollama (MiniCPM-V) | Free | 2-3s | 90% | ✅ Yes | Unlimited |
| HuggingFace (PaddleOCR) | Free | 4-6s | 85% | ✅ Yes | Unlimited |
| Gemini Free Tier | Free | 1-2s | 95%+ | ❌ No | 1500/day |

## 🎯 Use Cases

### 1. Accessory Intake
When barcode lookup fails or returns low confidence:
```python
result = await accessory_extractor.extract_from_file(photo_path)
product_name = result.extracted_data['product_name']
barcode = result.extracted_data['barcode']
```

### 2. Purchase Order Processing
Automate order entry from vendor documents:
```python
result = await order_extractor.extract_from_file(po_path)
line_items = order_extractor.get_line_items(result)
for item in line_items:
    add_to_inventory(item['sku'], item['quantity'])
```

### 3. Invoice Processing
Extract structured data from invoices:
```python
result = await ocr_service.extract(document, INVOICE_TEMPLATE)
total = result.extracted_data['total']
```

## 🔍 Troubleshooting

### No Models Found

**Problem**: `AllProvidersExhaustedError: No models found`

**Solution**:
1. Install Ollama: `ollama pull minicpm-v`
2. Or download HF model to `ocr/models/`
3. Or set `GEMINI_API_KEY` environment variable

### Low Confidence Results

**Problem**: Results have low confidence (<0.70)

**Solutions**:
1. Use higher quality images (well-lit, clear, high resolution)
2. Switch to cloud strategy: `ExtractionOptions(strategy='cloud')`
3. Try hybrid strategy for best results

### Rate Limit Errors

**Problem**: `RateLimitError` when using Gemini

**Solutions**:
1. Use local strategy: `ExtractionOptions(strategy='local')`
2. Install Ollama for unlimited requests
3. Wait for rate limit to reset (check `retry_after`)

## 📝 Examples

See `USAGE_EXAMPLE.py` for comprehensive examples:
- Simple extraction
- Order processing
- Custom options
- Barcode-only extraction
- Batch processing
- Error handling

## 🧪 Testing

Run the example to verify setup:
```bash
python USAGE_EXAMPLE.py
```

## 📄 License

Internal use only - part of WeedGo AI Engine Service.

## 🙋 Support

For issues or questions, check:
1. `OCR_IMPLEMENTATION_PROGRESS.md` - Implementation status
2. `OCR_EXTRACTION_DESIGN.md` - Architecture details
3. `OCR_RESEARCH_SUMMARY.md` - Model research
4. `USAGE_EXAMPLE.py` - Code examples
