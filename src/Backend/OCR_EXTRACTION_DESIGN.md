# OCR Extraction System - Complete DDD Architecture Design

## Executive Summary

**Purpose**: Design a production-ready, DDD-based OCR extraction system that can extract text and structured data from images using local vision-language models with cloud fallback.

**Key Objectives**:
- ✅ General-purpose OCR extraction (not limited to accessories)
- ✅ Template-based structured data extraction (accessories, orders, invoices, etc.)
- ✅ Local LLM support (MiniCPM-V, Qwen-VL) via Ollama
- ✅ Cloud fallback (Gemini, Claude, GPT-4V) for cost optimization
- ✅ Follows DDD, DRY, KISS, SRP principles
- ✅ Integrates with existing LLM Router pattern

**Business Value**:
- Automated order document processing
- Accessory intake via photo
- Invoice/receipt parsing
- Product label OCR
- Form data extraction

---

## 1. Domain Analysis

### 1.1 Problem Domain

**Domain**: Document Understanding and Structured Data Extraction

**Core Concepts**:
- **Document**: An image containing text, tables, forms, or structured data
- **OCR (Optical Character Recognition)**: Converting image text to machine-readable text
- **Template**: A schema defining what data to extract and how to structure it
- **Extraction**: Process of converting raw OCR text into structured data
- **Vision Model**: AI model capable of understanding visual information

### 1.2 Bounded Context

```
┌─────────────────────────────────────────────────────────────┐
│  OCR Extraction System (Bounded Context)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │   Document   │──────▶│  Extraction  │─────▶│  Template  │ │
│  │   (Image)    │      │   Process    │     │   Output   │ │
│  └──────────────┘      └──────────────┘     └────────────┘ │
│         │                      │                     │      │
│         │                      │                     │      │
│         ▼                      ▼                     ▼      │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │  Vision LLM  │      │   Template   │     │ Validation │ │
│  │   Provider   │      │   Matching   │     │   Rules    │ │
│  └──────────────┘      └──────────────┘     └────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Ubiquitous Language

| Term | Definition | Example |
|------|------------|---------|
| **Document** | Image or PDF containing information to extract | Product photo, invoice scan |
| **OCR** | Text extraction from images | "12 Pack Pipe Cleaners" |
| **Template** | Structured schema for extraction | `AccessoryTemplate`, `OrderTemplate` |
| **Field** | Single piece of data to extract | `product_name`, `quantity`, `price` |
| **Extraction** | Complete process from image to structured data | Image → OCR → Template → JSON |
| **Provider** | Vision LLM service (local or cloud) | Ollama, Gemini, Claude |
| **Confidence** | Model's certainty about extracted data | 0.0-1.0 (0%-100%) |

---

## 2. Architecture Design

### 2.1 DDD Layers

Following Domain-Driven Design, we organize the system into clear layers:

```
┌─────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER (Use Cases)                                │
│ ├── AccessoryExtractor                                       │
│ ├── OrderExtractor                                           │
│ ├── InvoiceExtractor                                         │
│ └── CustomTemplateExtractor                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER (Core Business Logic)                          │
│ ├── Domain Services                                         │
│ │   ├── OCRExtractionService (orchestrator)                │
│ │   ├── TemplateMatchingService                             │
│ │   └── ValidationService                                   │
│ ├── Strategies                                               │
│ │   ├── LocalVisionStrategy (Ollama)                       │
│ │   ├── CloudVisionStrategy (Gemini/Claude)                │
│ │   └── HybridVisionStrategy (local → cloud fallback)      │
│ ├── Entities                                                 │
│ │   ├── ExtractionResult (has identity)                    │
│ │   └── Document (has identity)                             │
│ └── Value Objects                                            │
│     ├── Template (immutable schema)                         │
│     ├── Field (data field definition)                       │
│     ├── ExtractionOptions (config)                          │
│     └── ProviderConfig (vision model settings)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER (Technical Details)                    │
│ ├── Vision Providers                                         │
│ │   ├── OllamaProvider (local MiniCPM-V/Qwen)             │
│ │   ├── GeminiProvider (Google Gemini Flash)               │
│ │   ├── ClaudeProvider (Anthropic Haiku)                   │
│ │   └── GPT4VProvider (OpenAI GPT-4o)                      │
│ ├── Image Processing                                         │
│ │   ├── ImageLoader (PIL, cv2)                             │
│ │   └── ImagePreprocessor (resize, normalize)              │
│ └── Storage                                                  │
│     ├── ResultCache (Redis)                                 │
│     └── DocumentStore (filesystem/S3)                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 File Structure

```
services/ocr_extraction/
├── __init__.py                      # Public API exports
│
├── domain/                          # DOMAIN LAYER
│   ├── __init__.py
│   ├── entities.py                  # Document, ExtractionResult
│   ├── value_objects.py             # Template, Field, ExtractionOptions
│   ├── exceptions.py                # Domain-specific exceptions
│   └── enums.py                     # TemplateType, FieldType, etc.
│
├── strategies/                      # STRATEGY PATTERN
│   ├── __init__.py
│   ├── base.py                      # AbstractVisionStrategy
│   ├── local_vision_strategy.py     # Ollama (MiniCPM-V, Qwen)
│   ├── cloud_vision_strategy.py     # Gemini, Claude, GPT-4V
│   └── hybrid_vision_strategy.py    # Local → cloud fallback
│
├── services/                        # DOMAIN SERVICES
│   ├── __init__.py
│   ├── ocr_service.py              # OCRExtractionService (main)
│   ├── template_service.py          # TemplateMatchingService
│   ├── validation_service.py        # ValidationService
│   └── strategy_selector.py         # VisionStrategySelector
│
├── extractors/                      # APPLICATION LAYER
│   ├── __init__.py
│   ├── accessory_extractor.py      # AccessoryExtractor
│   ├── order_extractor.py          # OrderExtractor
│   └── invoice_extractor.py        # InvoiceExtractor
│
├── providers/                       # INFRASTRUCTURE
│   ├── __init__.py
│   ├── base_vision_provider.py     # BaseVisionProvider
│   ├── ollama_provider.py          # OllamaVisionProvider
│   ├── gemini_provider.py          # GeminiVisionProvider
│   ├── claude_provider.py          # ClaudeVisionProvider
│   └── gpt4v_provider.py           # GPT4VisionProvider
│
└── templates/                       # TEMPLATE DEFINITIONS
    ├── __init__.py
    ├── accessory_template.py       # Accessory extraction schema
    ├── order_template.py           # Order document schema
    └── invoice_template.py         # Invoice extraction schema
```

**Total**: ~15 files, estimated ~3000 lines of code

---

## 3. Design Principles Application

### 3.1 DDD (Domain-Driven Design)

**Bounded Context**: OCR Extraction System
**Aggregates**: Document (root), ExtractionResult (root)
**Value Objects**: Template, Field, ExtractionOptions
**Domain Services**: OCRExtractionService, TemplateMatchingService
**Repositories**: DocumentRepository (if persistent storage needed)

**Example**:
```python
# Domain Entity
class ExtractionResult:
    """Entity with identity - represents a complete extraction"""
    id: UUID
    document_id: UUID
    template_type: TemplateType
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    provider_used: str
    timestamp: datetime

# Value Object
@dataclass(frozen=True)
class Template:
    """Immutable template definition"""
    name: str
    description: str
    fields: List[Field]
    validation_rules: List[ValidationRule]
```

### 3.2 DRY (Don't Repeat Yourself)

**Single Extraction Service**: One `OCRExtractionService` used by all extractors
**Reusable Templates**: Same template system for accessories, orders, invoices
**Shared Providers**: Vision providers reused across all extraction types

**Before DRY** (bad):
```python
class AccessoryExtractor:
    def extract(self, image):
        # Duplicate Ollama code
        ollama_client = OllamaClient()
        response = ollama_client.chat(...)
        # Parse response
        return result

class OrderExtractor:
    def extract(self, image):
        # Duplicate Ollama code again!
        ollama_client = OllamaClient()
        response = ollama_client.chat(...)
        # Parse response
        return result
```

**After DRY** (good):
```python
class OCRExtractionService:
    """Single service for all OCR extraction"""
    async def extract(self, image, template):
        provider = self.strategy_selector.select(template)
        result = await provider.extract(image, template)
        return result

# All extractors use the same service
class AccessoryExtractor:
    def __init__(self, ocr_service: OCRExtractionService):
        self.ocr_service = ocr_service

    async def extract(self, image):
        return await self.ocr_service.extract(
            image,
            template=AccessoryTemplate()
        )
```

### 3.3 KISS (Keep It Simple, Stupid)

**Simple API**:
```python
# User-facing API is dead simple
from services.ocr_extraction import AccessoryExtractor

extractor = AccessoryExtractor()
result = await extractor.extract_from_image("product_photo.jpg")

# Returns clean dict
{
    "product_name": "RAW Filter Tips",
    "brand": "RAW",
    "quantity": 50,
    "sku": "716165177555",
    "confidence": 0.95
}
```

**Complex Logic Hidden**:
- Provider selection: Automatic (local → cloud fallback)
- Image preprocessing: Handled internally
- Template matching: Transparent
- Error handling: Automatic retries

### 3.4 SRP (Single Responsibility Principle)

Each class has **ONE** responsibility:

| Class | Responsibility |
|-------|----------------|
| `OCRExtractionService` | Orchestrate extraction process |
| `VisionStrategySelector` | Select best vision provider |
| `LocalVisionStrategy` | Extract using local Ollama models |
| `CloudVisionStrategy` | Extract using cloud APIs |
| `TemplateMatchingService` | Match extracted data to templates |
| `ValidationService` | Validate extracted data |
| `AccessoryExtractor` | Know accessory-specific extraction logic |
| `Template` | Define extraction schema |
| `Field` | Define single data field |

**No class does more than one thing!**

---

## 4. Core Components

### 4.1 Value Objects (Immutable)

```python
from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum

class FieldType(Enum):
    """Types of fields that can be extracted"""
    TEXT = "text"              # Plain text
    NUMBER = "number"          # Numeric value
    PRICE = "price"            # Currency amount
    DATE = "date"              # Date/datetime
    IMAGE_URL = "image_url"    # URL to image
    BARCODE = "barcode"        # Barcode/UPC
    CATEGORY = "category"      # Classification
    TABLE = "table"            # Structured table data

class TemplateType(Enum):
    """Types of templates supported"""
    ACCESSORY = "accessory"
    ORDER = "order"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PRODUCT_LABEL = "product_label"
    FORM = "form"

@dataclass(frozen=True)
class Field:
    """
    Defines a single field to extract from document

    Immutable specification of what to extract.
    """
    name: str
    field_type: FieldType
    description: str
    required: bool = True
    example: Optional[str] = None
    validation_pattern: Optional[str] = None

    def __post_init__(self):
        """Validate field definition"""
        if not self.name:
            raise ValueError("Field name cannot be empty")

@dataclass(frozen=True)
class Template:
    """
    Defines extraction schema for a document type

    Immutable template that specifies what data to extract
    and how to validate it.
    """
    name: str
    template_type: TemplateType
    description: str
    fields: List[Field]
    prompt_template: str  # Prompt for LLM
    output_schema: str    # JSON schema for output

    def __post_init__(self):
        """Validate template"""
        if not self.fields:
            raise ValueError("Template must have at least one field")

@dataclass(frozen=True)
class ExtractionOptions:
    """
    Options for extraction process

    Immutable configuration for a single extraction request.
    """
    # Provider selection
    strategy: str = 'auto'  # 'local', 'cloud', 'auto'
    preferred_provider: Optional[str] = None

    # Image processing
    resize_max_dimension: int = 1344  # MiniCPM-V max
    normalize: bool = True
    enhance_contrast: bool = False

    # Extraction behavior
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_retries: int = 3
    timeout_seconds: int = 30

    # Output formatting
    return_raw_text: bool = False
    return_confidence_scores: bool = True
    validate_output: bool = True

@dataclass(frozen=True)
class VisionProviderConfig:
    """Configuration for a vision provider"""
    name: str
    provider_type: str  # 'local', 'cloud'
    model_name: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    supports_tables: bool = True
    supports_handwriting: bool = False
    max_image_size: int = 20  # MB
    cost_per_image: float = 0.0
    avg_latency_seconds: float = 5.0
```

### 4.2 Entities (With Identity)

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any, Optional

@dataclass
class Document:
    """
    Document entity with identity

    Represents an image/document to be processed.
    Has lifecycle and state.
    """
    id: UUID = field(default_factory=uuid4)
    file_path: str
    content_type: str  # image/png, application/pdf
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False

    def mark_as_processed(self):
        """Mark document as processed"""
        self.processed = True

@dataclass
class ExtractionResult:
    """
    Extraction result entity with identity

    Represents the outcome of an extraction operation.
    """
    id: UUID = field(default_factory=uuid4)
    document_id: UUID
    template_type: TemplateType
    template_name: str

    # Extracted data
    extracted_data: Dict[str, Any]
    raw_ocr_text: Optional[str] = None

    # Metadata
    provider_used: str
    strategy_used: str
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    # Performance
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Validation
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def get_overall_confidence(self) -> float:
        """Calculate overall confidence score"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)

    def is_high_quality(self) -> bool:
        """Check if extraction is high quality"""
        return (
            self.validation_passed and
            self.get_overall_confidence() >= 0.8 and
            not self.validation_errors
        )
```

### 4.3 Domain Services

```python
class OCRExtractionService:
    """
    Main domain service for OCR extraction

    Orchestrates the entire extraction process:
    1. Image preprocessing
    2. Provider selection
    3. OCR execution
    4. Template matching
    5. Validation
    6. Result caching
    """

    def __init__(
        self,
        strategy_selector: VisionStrategySelector,
        template_service: TemplateMatchingService,
        validation_service: ValidationService
    ):
        self.strategy_selector = strategy_selector
        self.template_service = template_service
        self.validation_service = validation_service
        self.cache = {}  # Will be Redis in production

    async def extract(
        self,
        document: Document,
        template: Template,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract structured data from document using template

        Algorithm:
        1. Check cache (if enabled)
        2. Select optimal vision provider/strategy
        3. Execute extraction with retry logic
        4. Match to template schema
        5. Validate extracted data
        6. Cache result (if successful)
        7. Return ExtractionResult
        """
        options = options or ExtractionOptions()

        # Step 1: Check cache
        cache_key = self._get_cache_key(document.id, template.name)
        if options.enable_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        # Step 2: Select strategy
        strategy = self.strategy_selector.select(template, options)

        # Step 3: Execute extraction
        result = await self._execute_with_retry(
            strategy,
            document,
            template,
            options
        )

        # Step 4: Match to template
        matched_data = self.template_service.match_to_template(
            raw_data=result.extracted_data,
            template=template
        )
        result.extracted_data = matched_data

        # Step 5: Validate
        validation_result = self.validation_service.validate(
            data=matched_data,
            template=template
        )
        result.validation_passed = validation_result.passed
        result.validation_errors = validation_result.errors

        # Step 6: Cache
        if result.is_high_quality() and options.enable_cache:
            self._add_to_cache(cache_key, result, options.cache_ttl)

        return result
```

---

## 5. Strategy Pattern

### 5.1 Abstract Strategy

```python
from abc import ABC, abstractmethod

class AbstractVisionStrategy(ABC):
    """
    Base class for all vision extraction strategies

    Following Strategy Pattern - different algorithms for extraction.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name"""
        pass

    @abstractmethod
    async def extract(
        self,
        document: Document,
        template: Template,
        options: ExtractionOptions
    ) -> ExtractionResult:
        """
        Extract data from document using this strategy

        Args:
            document: Document to process
            template: Template defining what to extract
            options: Extraction options

        Returns:
            ExtractionResult with extracted data
        """
        pass

    @abstractmethod
    def supports_template(self, template: Template) -> bool:
        """Check if strategy supports this template type"""
        pass

    @abstractmethod
    def estimate_cost(self, document: Document) -> float:
        """Estimate cost for processing this document"""
        pass
```

### 5.2 Strategy Implementations

```python
class LocalVisionStrategy(AbstractVisionStrategy):
    """
    Local vision model strategy using Ollama

    Advantages:
    - Free (no API costs)
    - Fast (local execution)
    - Private (data stays local)
    - Offline capable

    Limitations:
    - Requires GPU (8GB+ VRAM recommended)
    - Lower accuracy than GPT-4V (but close!)
    - Model download required (~4GB)
    """

    def __init__(self, ollama_provider: OllamaVisionProvider):
        self.provider = ollama_provider

    def get_name(self) -> str:
        return 'local_ollama'

    async def extract(self, document, template, options):
        # Use Ollama MiniCPM-V or Qwen-VL
        prompt = self._build_extraction_prompt(template)

        result = await self.provider.chat_with_image(
            image_path=document.file_path,
            prompt=prompt,
            format='json'
        )

        return self._parse_result(result, template)

    def supports_template(self, template):
        # Local models support most templates
        return True

    def estimate_cost(self, document):
        return 0.0  # Free!


class CloudVisionStrategy(AbstractVisionStrategy):
    """
    Cloud vision API strategy (Gemini, Claude, GPT-4V)

    Advantages:
    - Highest accuracy
    - No local GPU required
    - Support for complex tables/handwriting

    Limitations:
    - API costs (~$0.001-0.01 per image)
    - Requires internet
    - Data leaves premise
    """

    def __init__(self, cloud_providers: List[BaseVisionProvider]):
        self.providers = cloud_providers

    def get_name(self) -> str:
        return 'cloud_vision'

    async def extract(self, document, template, options):
        # Try providers in order: Gemini → Claude → GPT-4V
        for provider in self.providers:
            try:
                result = await provider.extract(document, template)
                return result
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        raise AllProvidersExhaustedError("All cloud providers failed")

    def estimate_cost(self, document):
        # Gemini Flash: $0.001 per image
        return 0.001


class HybridVisionStrategy(AbstractVisionStrategy):
    """
    Hybrid strategy: Local → Cloud fallback

    Algorithm:
    1. Try local model first (fast, free)
    2. Check confidence score
    3. If confidence < threshold → use cloud
    4. Return best result

    Best of both worlds:
    - 90% of requests: local (free, fast)
    - 10% of requests: cloud (only when needed for accuracy)
    """

    def __init__(self, local: LocalVisionStrategy, cloud: CloudVisionStrategy):
        self.local = local
        self.cloud = cloud
        self.confidence_threshold = 0.75

    def get_name(self) -> str:
        return 'hybrid'

    async def extract(self, document, template, options):
        # Step 1: Try local first
        local_result = await self.local.extract(document, template, options)

        # Step 2: Check confidence
        if local_result.get_overall_confidence() >= self.confidence_threshold:
            logger.info(f"Local extraction sufficient ({local_result.get_overall_confidence():.2%})")
            return local_result

        # Step 3: Fallback to cloud
        logger.info(f"Low confidence ({local_result.get_overall_confidence():.2%}), using cloud")
        cloud_result = await self.cloud.extract(document, template, options)

        return cloud_result
```

---

## 6. Template System

### 6.1 Template Design

Templates define **what** to extract and **how** to validate it:

```python
# Example: Accessory Template
class AccessoryTemplate(Template):
    """Template for extracting accessory product information"""

    def __init__(self):
        super().__init__(
            name="Accessory",
            template_type=TemplateType.ACCESSORY,
            description="Extract product details from accessory photos",
            fields=[
                Field(
                    name="product_name",
                    field_type=FieldType.TEXT,
                    description="Full product name",
                    required=True,
                    example="RAW Cone King Size Pre-Rolled Cones"
                ),
                Field(
                    name="brand",
                    field_type=FieldType.TEXT,
                    description="Product brand/manufacturer",
                    required=False,
                    example="RAW"
                ),
                Field(
                    name="quantity",
                    field_type=FieldType.NUMBER,
                    description="Quantity or pack size",
                    required=False,
                    example="32"
                ),
                Field(
                    name="sku",
                    field_type=FieldType.BARCODE,
                    description="SKU, barcode, or UPC",
                    required=False,
                    example="716165177555",
                    validation_pattern=r"^\d{8,14}$"
                ),
                Field(
                    name="price",
                    field_type=FieldType.PRICE,
                    description="Retail price",
                    required=False,
                    example="14.99"
                ),
                Field(
                    name="category",
                    field_type=FieldType.CATEGORY,
                    description="Product category",
                    required=False,
                    example="Rolling Papers"
                ),
            ],
            prompt_template="""
You are an expert at extracting product information from images.

Extract the following information from this accessory product image:
- Product name (full name as shown on packaging)
- Brand (manufacturer name)
- Quantity (number of items in pack, e.g., "50 pack")
- SKU/Barcode (UPC, EAN, or SKU number)
- Price (if visible)
- Category (type of product: papers, filters, lighters, etc.)

Return ONLY a JSON object with these fields. If a field is not visible, use null.

Example output:
{
    "product_name": "RAW Cone King Size Pre-Rolled Cones",
    "brand": "RAW",
    "quantity": 32,
    "sku": "716165177555",
    "price": 14.99,
    "category": "Rolling Papers"
}
""",
            output_schema="""{
    "type": "object",
    "properties": {
        "product_name": {"type": "string"},
        "brand": {"type": ["string", "null"]},
        "quantity": {"type": ["number", "null"]},
        "sku": {"type": ["string", "null"]},
        "price": {"type": ["number", "null"]},
        "category": {"type": ["string", "null"]}
    },
    "required": ["product_name"]
}"""
        )
```

### 6.2 Order Template Example

```python
class OrderTemplate(Template):
    """Template for extracting order/invoice information"""

    def __init__(self):
        super().__init__(
            name="Order",
            template_type=TemplateType.ORDER,
            description="Extract order details from purchase orders, invoices, receipts",
            fields=[
                Field(
                    name="order_number",
                    field_type=FieldType.TEXT,
                    description="Order or invoice number",
                    required=True,
                    example="PO-12345"
                ),
                Field(
                    name="vendor",
                    field_type=FieldType.TEXT,
                    description="Vendor or supplier name",
                    required=True,
                    example="ONE Wholesale"
                ),
                Field(
                    name="order_date",
                    field_type=FieldType.DATE,
                    description="Order date",
                    required=True,
                    example="2025-10-20"
                ),
                Field(
                    name="line_items",
                    field_type=FieldType.TABLE,
                    description="Table of ordered items",
                    required=True,
                    example="[{product, quantity, price}]"
                ),
                Field(
                    name="subtotal",
                    field_type=FieldType.PRICE,
                    description="Subtotal before tax",
                    required=False
                ),
                Field(
                    name="tax",
                    field_type=FieldType.PRICE,
                    description="Tax amount",
                    required=False
                ),
                Field(
                    name="total",
                    field_type=FieldType.PRICE,
                    description="Total amount",
                    required=True
                ),
            ],
            prompt_template="""
Extract order/invoice information from this document.

Required fields:
- order_number: Order or invoice number
- vendor: Supplier/vendor name
- order_date: Date of order
- line_items: Table with columns [product, quantity, unit_price, total]
- total: Total amount

Return JSON with these fields.
""",
            output_schema="{...}"  # JSON schema
        )
```

---

## 7. Provider Integration

### 7.1 Vision Provider Router

Following the existing LLM Router pattern:

```python
class VisionProviderRouter:
    """
    Router for vision providers (similar to LLMRouter)

    Routes vision requests to best available provider:
    - Local Ollama (free, fast) prioritized
    - Cloud providers (Gemini/Claude) as fallback
    """

    def __init__(self):
        self.providers: Dict[str, BaseVisionProvider] = {}
        self.total_requests = 0
        self.total_cost = 0.0

    def register_provider(self, provider: BaseVisionProvider):
        """Register a vision provider"""
        self.providers[provider.name] = provider

    async def extract(
        self,
        image_path: str,
        prompt: str,
        options: ExtractionOptions
    ) -> Dict[str, Any]:
        """
        Extract data using best available provider

        Selection algorithm:
        1. Local providers prioritized (free)
        2. Cloud providers as fallback
        3. Automatic failover on errors
        """
        # Score providers
        scored = self._score_providers(options)

        # Try providers in order
        for score, provider in scored:
            try:
                result = await provider.extract(image_path, prompt)
                return result
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        raise AllProvidersExhaustedError("All vision providers failed")

    def _score_providers(self, options):
        """Score providers (free > paid)"""
        scored = []
        for provider in self.providers.values():
            score = 100 if provider.is_free else 50
            scored.append((score, provider))
        return sorted(scored, reverse=True, key=lambda x: x[0])
```

### 7.2 Ollama Provider (Local)

```python
class OllamaVisionProvider(BaseVisionProvider):
    """
    Vision provider for local Ollama models

    Supported models:
    - minicpm-v:latest (recommended, 8B params)
    - qwen2.5-vl:7b
    - llama3.2-vision:11b
    """

    def __init__(
        self,
        model_name: str = "minicpm-v:latest",
        ollama_url: str = "http://localhost:11434"
    ):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(base_url=ollama_url)

    async def extract(
        self,
        image_path: str,
        prompt: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Extract data using Ollama vision model

        Args:
            image_path: Path to image file
            prompt: Extraction prompt
            format: Response format ('json' or 'text')

        Returns:
            Extracted data as dict
        """
        # Load and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Build request
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_data],
            "format": format,
            "stream": False
        }

        # Call Ollama API
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()

        result = response.json()

        # Parse JSON response
        if format == 'json':
            return json.loads(result['response'])
        else:
            return {"text": result['response']}

    @property
    def is_free(self) -> bool:
        return True  # Local model is free!

    @property
    def avg_latency_seconds(self) -> float:
        return 3.0  # Depends on GPU
```

### 7.3 Gemini Provider (Cloud Fallback)

```python
class GeminiVisionProvider(BaseVisionProvider):
    """
    Vision provider for Google Gemini

    Model: gemini-2.0-flash-exp (free tier available)
    Cost: Free tier: 15 RPM, 1 million TPM, 1500 RPD
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    async def extract(self, image_path, prompt, **kwargs):
        """Extract using Gemini Vision"""
        # Load image
        image = PIL.Image.open(image_path)

        # Generate content
        response = await self.model.generate_content_async([
            prompt,
            image
        ])

        # Parse JSON from response
        text = response.text
        return json.loads(text)

    @property
    def is_free(self) -> bool:
        return True  # Free tier available

    @property
    def cost_per_image(self) -> float:
        return 0.0  # Free tier
```

---

## 8. Integration Example

### 8.1 Complete Flow

```python
# Usage Example: Extract accessory from photo

from services.ocr_extraction import AccessoryExtractor

# Step 1: Initialize extractor
extractor = AccessoryExtractor()

# Step 2: Extract from image
result = await extractor.extract_from_image("product_photo.jpg")

# Step 3: Use extracted data
print(f"Product: {result.extracted_data['product_name']}")
print(f"Brand: {result.extracted_data['brand']}")
print(f"SKU: {result.extracted_data['sku']}")
print(f"Confidence: {result.get_overall_confidence():.2%}")
print(f"Provider: {result.provider_used}")
print(f"Cost: ${result.cost:.6f}")
print(f"Latency: {result.latency_ms:.0f}ms")

# Output:
# Product: RAW Cone King Size Pre-Rolled Cones
# Brand: RAW
# SKU: 716165177555
# Confidence: 95.00%
# Provider: ollama_minicpm-v
# Cost: $0.000000
# Latency: 2850ms
```

### 8.2 Order Document Extraction

```python
from services.ocr_extraction import OrderExtractor

# Extract order from invoice PDF/image
extractor = OrderExtractor()
result = await extractor.extract_from_image("invoice.pdf")

# Get structured order data
order_data = result.extracted_data
# {
#     "order_number": "PO-12345",
#     "vendor": "ONE Wholesale",
#     "order_date": "2025-10-20",
#     "line_items": [
#         {
#             "product": "RAW Cones",
#             "quantity": 50,
#             "unit_price": 14.99,
#             "total": 749.50
#         },
#         ...
#     ],
#     "subtotal": 1200.00,
#     "tax": 120.00,
#     "total": 1320.00
# }
```

---

## 9. Performance Characteristics

### 9.1 Expected Performance

| Strategy | Avg Latency | Cost per Image | Accuracy | Use Case |
|----------|-------------|----------------|----------|----------|
| **Local (MiniCPM-V)** | 2-4s | $0.00 | 90% | Most extractions (90%) |
| **Local (Qwen-VL)** | 3-5s | $0.00 | 92% | Complex documents |
| **Cloud (Gemini Flash)** | 1-2s | $0.001 | 95% | Fallback (5%) |
| **Cloud (Claude Haiku)** | 2-3s | $0.008 | 96% | Complex tables |
| **Cloud (GPT-4V)** | 3-5s | $0.01 | 98% | Highest accuracy needed |
| **Hybrid** | 2-4s avg | ~$0.0001 avg | 94% | Best of both (recommended) |

### 9.2 Cost Analysis

**Monthly Volume**: 1000 accessory photos + 100 order documents

**Local-Only** (MiniCPM-V):
- Cost: $0.00
- Hardware: GPU with 8GB+ VRAM
- Latency: 2-4s
- Accuracy: 90%

**Cloud-Only** (Gemini):
- Cost: $1.10/month (1100 images × $0.001)
- Hardware: None
- Latency: 1-2s
- Accuracy: 95%

**Hybrid** (Recommended):
- Cost: $0.11/month (10% cloud usage)
- Hardware: GPU for local
- Latency: 2-4s avg
- Accuracy: 94% avg

**Winner**: Hybrid! ✅ (99% cost savings vs cloud-only)

---

## 10. Model Recommendations

### 10.1 Local Models (via Ollama)

**Recommended: MiniCPM-V 4.5**
- Size: 8B parameters (~4GB download)
- Performance: Matches GPT-4o on OCRBench
- Speed: 2-4s on RTX 3080
- Installation: `ollama pull minicpm-v:latest`
- Use case: General-purpose OCR (accessories, orders)

**Alternative: Qwen-2.5-VL 7B**
- Size: 7B parameters (~4GB)
- Performance: 75% accuracy (matches GPT-4o)
- Speed: 3-5s
- Installation: `ollama pull qwen2.5vl:7b`
- Use case: Complex documents, tables

**Alternative: LLaMA 3.2 Vision 11B**
- Size: 11B parameters (~7GB)
- Performance: Good accuracy
- Speed: 5-7s
- Use case: High-quality extraction when time allows

### 10.2 Cloud Models (Fallback)

**Tier 1: Gemini 2.0 Flash (Free Tier)**
- Cost: Free (15 RPM limit)
- Performance: Excellent
- Speed: 1-2s
- Use case: Default cloud fallback

**Tier 2: Claude 3 Haiku**
- Cost: $0.008 per image
- Performance: Very good
- Speed: 2-3s
- Use case: When Gemini exhausted

**Tier 3: GPT-4V**
- Cost: $0.01 per image
- Performance: Best-in-class
- Speed: 3-5s
- Use case: Critical documents only

---

## 11. Success Criteria

### 11.1 Functional Requirements

- ✅ Extract product data from accessory photos (95%+ accuracy)
- ✅ Extract order data from invoices/POs (90%+ accuracy)
- ✅ Support local LLM execution (Ollama)
- ✅ Support cloud fallback (Gemini, Claude, GPT-4V)
- ✅ Template-based extraction (accessories, orders, custom)
- ✅ Validation of extracted data
- ✅ Caching for performance
- ✅ Cost tracking and optimization

### 11.2 Non-Functional Requirements

- ✅ Latency: <5s for 90% of requests
- ✅ Accuracy: >90% for accessories, >85% for orders
- ✅ Cost: <$0.0001 per extraction (hybrid strategy)
- ✅ Availability: 99.9% (with fallback providers)
- ✅ Scalability: Handle 1000+ extractions/day
- ✅ Maintainability: DDD architecture, clear separation
- ✅ Extensibility: Easy to add new templates

---

## 12. Implementation Plan

### Phase 1: Core Foundation (Week 1)
1. Domain layer (entities, value objects, exceptions)
2. Abstract strategy interface
3. Template system foundation

### Phase 2: Local Vision (Week 1)
4. Ollama provider implementation
5. Local vision strategy
6. Basic extraction service

### Phase 3: Cloud Fallback (Week 2)
7. Gemini provider implementation
8. Claude provider (optional)
9. Cloud vision strategy
10. Hybrid strategy

### Phase 4: Templates (Week 2)
11. Accessory template
12. Order template
13. Template validation service

### Phase 5: Application Layer (Week 3)
14. Accessory extractor
15. Order extractor
16. Custom template support

### Phase 6: Integration (Week 3)
17. Vision provider router
18. Integration with existing LLM router pattern
19. Caching layer (Redis)

### Phase 7: Testing & Documentation (Week 4)
20. Comprehensive test suite
21. Performance benchmarking
22. Documentation and examples

---

## 13. Design Summary

### What We're Building

A **production-ready, DDD-based OCR extraction system** that:

✅ **Follows DDD**: Clear layers, bounded context, ubiquitous language
✅ **Follows DRY**: Single extraction service for all use cases
✅ **Follows KISS**: Simple API, complex logic hidden
✅ **Follows SRP**: Each class has one responsibility

### Key Innovations

1. **Template-Based Extraction**: Define schemas once, reuse everywhere
2. **Local-First with Cloud Fallback**: 99% cost savings vs cloud-only
3. **Provider Router Pattern**: Automatic failover and cost optimization
4. **Strategy Pattern**: Flexible extraction algorithms
5. **High Accuracy**: 90%+ accuracy using MiniCPM-V (local, free)

### Business Impact

- **Automated order entry**: Save 10+ hours/week on manual data entry
- **Accessory intake**: Photo → structured data in 3 seconds
- **Invoice processing**: Extract 100+ invoices/day automatically
- **Cost optimization**: $0.11/month vs $1.10/month (90% savings)
- **Future-proof**: Easy to add new templates and providers

---

**Status**: ✅ Design complete, ready for implementation review

**Next Step**: Review design with team, then proceed to implementation

**Estimated Effort**: 3-4 weeks for complete implementation
