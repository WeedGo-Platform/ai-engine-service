# OCR Extraction System - Implementation Roadmap

## Overview

This document provides a step-by-step implementation plan for the OCR Extraction System following DDD, DRY, KISS, and SRP principles.

**Timeline**: 4 weeks
**Effort**: ~80-100 hours
**Team Size**: 1-2 developers

---

## Phase 1: Foundation & Research (Week 1)

### 1.1 Environment Setup

**Tasks**:
- [ ] Install Ollama on development machine
- [ ] Pull MiniCPM-V model (`ollama pull minicpm-v:latest`)
- [ ] Test Ollama API with sample image
- [ ] Verify GPU acceleration working
- [ ] Set up Gemini API account (free tier)

**Deliverables**:
- Working Ollama installation
- Sample extraction working
- Performance baseline established

**Time Estimate**: 4 hours

**Acceptance Criteria**:
```bash
# Should complete in <5 seconds
ollama run minicpm-v:latest "Extract text from this image" < test.jpg
```

---

### 1.2 Domain Layer Implementation

**Tasks**:
- [ ] Create `services/ocr_extraction/` directory structure
- [ ] Implement value objects (`Template`, `Field`, `ExtractionOptions`)
- [ ] Implement entities (`Document`, `ExtractionResult`)
- [ ] Define domain exceptions
- [ ] Create enums (`TemplateType`, `FieldType`)

**Files to Create**:
```
services/ocr_extraction/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── value_objects.py    # ← Template, Field, ExtractionOptions
│   ├── entities.py          # ← Document, ExtractionResult
│   ├── exceptions.py        # ← Domain exceptions
│   └── enums.py            # ← TemplateType, FieldType
```

**Deliverables**:
- All domain objects implemented
- Unit tests for value object validation
- Immutability verified

**Time Estimate**: 8 hours

**Acceptance Criteria**:
```python
# Value objects are immutable
template = Template(name="Test", ...)
template.name = "Changed"  # Should raise error

# Validation works
field = Field(name="", ...)  # Should raise ValueError
```

---

### 1.3 Strategy Interface

**Tasks**:
- [ ] Create abstract strategy base class
- [ ] Define strategy interface (`extract()`, `supports_template()`)
- [ ] Create strategy selector skeleton

**Files to Create**:
```
services/ocr_extraction/
└── strategies/
    ├── __init__.py
    └── base.py              # ← AbstractVisionStrategy
```

**Deliverables**:
- Abstract base class complete
- Documentation for strategy contract

**Time Estimate**: 3 hours

**Acceptance Criteria**:
```python
# Cannot instantiate abstract class
strategy = AbstractVisionStrategy()  # Should raise TypeError

# Subclasses must implement all methods
class MyStrategy(AbstractVisionStrategy):
    pass
# Should raise error about missing methods
```

---

## Phase 2: Local Vision Provider (Week 1-2)

### 2.1 Ollama Provider

**Tasks**:
- [ ] Implement `OllamaVisionProvider`
- [ ] Handle image encoding (base64)
- [ ] Implement retry logic
- [ ] Add error handling
- [ ] Create provider configuration

**Files to Create**:
```
services/ocr_extraction/
└── providers/
    ├── __init__.py
    ├── base_vision_provider.py   # ← BaseVisionProvider
    └── ollama_provider.py        # ← OllamaVisionProvider
```

**Deliverables**:
- Working Ollama integration
- Error handling for network issues, timeouts
- Configuration for model selection

**Time Estimate**: 10 hours

**Acceptance Criteria**:
```python
provider = OllamaVisionProvider(model='minicpm-v')
result = await provider.extract(
    image_path='test.jpg',
    prompt='Extract product name'
)
assert result['product_name'] is not None
```

---

### 2.2 Local Vision Strategy

**Tasks**:
- [ ] Implement `LocalVisionStrategy`
- [ ] Integrate with Ollama provider
- [ ] Build extraction prompts
- [ ] Parse JSON responses
- [ ] Handle extraction errors

**Files to Create**:
```
services/ocr_extraction/
└── strategies/
    └── local_vision_strategy.py  # ← LocalVisionStrategy
```

**Deliverables**:
- Strategy implementation complete
- Prompt engineering for extraction
- JSON parsing with fallbacks

**Time Estimate**: 8 hours

**Acceptance Criteria**:
```python
strategy = LocalVisionStrategy(ollama_provider)
result = await strategy.extract(document, template, options)
assert result.found == True
assert result.latency_ms < 5000  # <5s
```

---

### 2.3 Testing with Real Images

**Tasks**:
- [ ] Collect 20 test images (10 accessories, 10 orders)
- [ ] Run extraction on all images
- [ ] Measure accuracy
- [ ] Benchmark performance
- [ ] Document edge cases

**Deliverables**:
- Test dataset (20 images)
- Accuracy report
- Performance benchmarks
- Known limitations documented

**Time Estimate**: 6 hours

**Acceptance Criteria**:
- Accessory extraction: >85% accuracy
- Order extraction: >75% accuracy
- Average latency: <5s

---

## Phase 3: Cloud Fallback (Week 2)

### 3.1 Gemini Provider

**Tasks**:
- [ ] Install Google GenerativeAI SDK
- [ ] Implement `GeminiVisionProvider`
- [ ] Handle authentication
- [ ] Rate limit handling (15 RPM)
- [ ] Error handling and retries

**Files to Create**:
```
services/ocr_extraction/
└── providers/
    └── gemini_provider.py        # ← GeminiVisionProvider
```

**Deliverables**:
- Gemini integration complete
- Free tier limits enforced
- Graceful degradation on quota exhaustion

**Time Estimate**: 6 hours

**Acceptance Criteria**:
```python
provider = GeminiVisionProvider(api_key=key)
result = await provider.extract(image_path, prompt)
assert result is not None
# Should respect rate limits
```

---

### 3.2 Cloud Vision Strategy

**Tasks**:
- [ ] Implement `CloudVisionStrategy`
- [ ] Multi-provider support (Gemini → Claude → GPT-4V)
- [ ] Automatic failover
- [ ] Cost tracking

**Files to Create**:
```
services/ocr_extraction/
└── strategies/
    └── cloud_vision_strategy.py  # ← CloudVisionStrategy
```

**Deliverables**:
- Cloud strategy with failover
- Cost tracking per provider
- Performance comparison

**Time Estimate**: 8 hours

**Acceptance Criteria**:
```python
strategy = CloudVisionStrategy([gemini, claude])
result = await strategy.extract(document, template, options)
# Should try Gemini first, Claude on failure
assert result.cost < 0.01  # Cheap provider used
```

---

### 3.3 Hybrid Strategy

**Tasks**:
- [ ] Implement `HybridVisionStrategy`
- [ ] Confidence threshold logic
- [ ] Local → cloud fallback
- [ ] Performance optimization

**Files to Create**:
```
services/ocr_extraction/
└── strategies/
    └── hybrid_vision_strategy.py # ← HybridVisionStrategy
```

**Deliverables**:
- Hybrid strategy complete
- Configurable confidence threshold
- Fallback logic tested

**Time Estimate**: 6 hours

**Acceptance Criteria**:
```python
strategy = HybridVisionStrategy(local, cloud, threshold=0.75)
result = await strategy.extract(document, template, options)
# Should use local first, cloud only if confidence < 75%
assert result.provider_used in ['local', 'cloud']
```

---

## Phase 4: Template System (Week 2-3)

### 4.1 Template Definitions

**Tasks**:
- [ ] Create `AccessoryTemplate`
- [ ] Create `OrderTemplate`
- [ ] Create `InvoiceTemplate` (optional)
- [ ] Define validation rules
- [ ] Write prompt templates

**Files to Create**:
```
services/ocr_extraction/
└── templates/
    ├── __init__.py
    ├── accessory_template.py     # ← AccessoryTemplate
    ├── order_template.py         # ← OrderTemplate
    └── invoice_template.py       # ← InvoiceTemplate
```

**Deliverables**:
- 3 production-ready templates
- Validation rules defined
- LLM prompts optimized

**Time Estimate**: 10 hours

**Acceptance Criteria**:
```python
template = AccessoryTemplate()
assert len(template.fields) >= 5
assert template.prompt_template is not None
# Validation rules work
assert template.validate({'product_name': 'RAW Cones'}) == True
```

---

### 4.2 Template Matching Service

**Tasks**:
- [ ] Implement `TemplateMatchingService`
- [ ] Field mapping logic
- [ ] Type conversion (text → number, price)
- [ ] Missing field handling

**Files to Create**:
```
services/ocr_extraction/
└── services/
    ├── __init__.py
    └── template_service.py       # ← TemplateMatchingService
```

**Deliverables**:
- Template matching complete
- Type conversions working
- Error handling for malformed data

**Time Estimate**: 8 hours

**Acceptance Criteria**:
```python
service = TemplateMatchingService()
matched = service.match_to_template(
    raw_data={'name': 'Product', 'qty': '50'},
    template=AccessoryTemplate()
)
assert matched['quantity'] == 50  # String → int conversion
```

---

### 4.3 Validation Service

**Tasks**:
- [ ] Implement `ValidationService`
- [ ] Required field validation
- [ ] Pattern validation (regex)
- [ ] Range validation (min/max)
- [ ] Custom validation rules

**Files to Create**:
```
services/ocr_extraction/
└── services/
    └── validation_service.py     # ← ValidationService
```

**Deliverables**:
- Validation service complete
- All validation types supported
- Clear error messages

**Time Estimate**: 6 hours

**Acceptance Criteria**:
```python
service = ValidationService()
result = service.validate(
    data={'sku': 'abc'},  # Invalid (should be numeric)
    template=AccessoryTemplate()
)
assert result.passed == False
assert 'sku' in result.errors
```

---

## Phase 5: Main Service & Integration (Week 3)

### 5.1 OCR Extraction Service

**Tasks**:
- [ ] Implement `OCRExtractionService`
- [ ] Orchestration logic
- [ ] Retry mechanism
- [ ] Caching layer
- [ ] Performance tracking

**Files to Create**:
```
services/ocr_extraction/
└── services/
    ├── ocr_service.py            # ← OCRExtractionService (main)
    └── strategy_selector.py      # ← VisionStrategySelector
```

**Deliverables**:
- Main service implementation
- Complete extraction pipeline
- Caching working

**Time Estimate**: 12 hours

**Acceptance Criteria**:
```python
service = OCRExtractionService(...)
result = await service.extract(document, template, options)
assert result.extracted_data is not None
assert result.latency_ms > 0
assert result.validation_passed == True
```

---

### 5.2 Vision Provider Router

**Tasks**:
- [ ] Implement `VisionProviderRouter`
- [ ] Provider scoring algorithm
- [ ] Health checking
- [ ] Statistics tracking
- [ ] Integration with existing LLM router pattern

**Files to Create**:
```
services/ocr_extraction/
└── router.py                    # ← VisionProviderRouter
```

**Deliverables**:
- Router implementation
- Provider selection working
- Stats dashboard data

**Time Estimate**: 8 hours

**Acceptance Criteria**:
```python
router = VisionProviderRouter()
router.register_provider(ollama_provider)
router.register_provider(gemini_provider)

result = await router.extract(image, prompt, options)
stats = router.get_stats()
assert stats['total_requests'] > 0
```

---

### 5.3 Application Layer (Extractors)

**Tasks**:
- [ ] Implement `AccessoryExtractor`
- [ ] Implement `OrderExtractor`
- [ ] Simple API wrappers
- [ ] Documentation

**Files to Create**:
```
services/ocr_extraction/
└── extractors/
    ├── __init__.py
    ├── accessory_extractor.py    # ← AccessoryExtractor
    └── order_extractor.py        # ← OrderExtractor
```

**Deliverables**:
- 2 production-ready extractors
- Simple, clean API
- Usage examples

**Time Estimate**: 6 hours

**Acceptance Criteria**:
```python
# Dead simple API
extractor = AccessoryExtractor()
result = await extractor.extract_from_image('photo.jpg')
assert 'product_name' in result.extracted_data
```

---

## Phase 6: Testing & Documentation (Week 4)

### 6.1 Comprehensive Testing

**Tasks**:
- [ ] Unit tests for all domain objects
- [ ] Integration tests for strategies
- [ ] End-to-end extraction tests
- [ ] Performance benchmarks
- [ ] Accuracy measurements

**Files to Create**:
```
tests/
└── ocr_extraction/
    ├── test_domain.py
    ├── test_strategies.py
    ├── test_providers.py
    ├── test_templates.py
    ├── test_ocr_service.py
    └── benchmark_performance.py
```

**Deliverables**:
- 90%+ test coverage
- Performance benchmarks
- Accuracy report

**Time Estimate**: 12 hours

**Acceptance Criteria**:
- All tests passing
- Accessory extraction: >90% accuracy
- Order extraction: >85% accuracy
- Average cost: <$0.0001/image

---

### 6.2 Documentation

**Tasks**:
- [ ] API documentation
- [ ] Installation guide
- [ ] Usage examples
- [ ] Template creation guide
- [ ] Troubleshooting guide

**Files to Create**:
```
docs/
└── ocr_extraction/
    ├── README.md
    ├── INSTALLATION.md
    ├── API_REFERENCE.md
    ├── TEMPLATE_GUIDE.md
    └── TROUBLESHOOTING.md
```

**Deliverables**:
- Complete documentation set
- Code examples
- Architecture diagrams

**Time Estimate**: 8 hours

**Acceptance Criteria**:
- New developer can set up and use in <30 minutes
- All API methods documented
- Common issues addressed

---

### 6.3 Integration with Existing Systems

**Tasks**:
- [ ] Integrate with barcode lookup service
- [ ] Add OCR fallback for barcode failures
- [ ] Integrate with order intake workflow
- [ ] Add to admin dashboard

**Integration Points**:
```python
# In barcode_lookup_service.py
from services.ocr_extraction import AccessoryExtractor

async def lookup_barcode(self, barcode: str):
    # Try standard barcode lookup first
    result = await self._try_all_sources(barcode)

    if not result['found']:
        # Fallback: If user has uploaded product photo
        if product_photo_path:
            extractor = AccessoryExtractor()
            ocr_result = await extractor.extract_from_image(product_photo_path)
            return ocr_result
```

**Deliverables**:
- OCR extraction available in barcode lookup
- Order document upload working
- Admin UI updated

**Time Estimate**: 10 hours

**Acceptance Criteria**:
- Can upload product photo → get structured data
- Can upload order PDF → import line items
- Admin dashboard shows OCR stats

---

## Phase 7: Deployment & Monitoring (Week 4)

### 7.1 Production Deployment

**Tasks**:
- [ ] Deploy Ollama on production server
- [ ] Configure GPU acceleration
- [ ] Set up API keys (Gemini, Claude)
- [ ] Configure Redis caching
- [ ] Set up monitoring

**Infrastructure**:
```yaml
# Docker Compose for Ollama
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Deliverables**:
- Production deployment complete
- Monitoring dashboard
- Alert configuration

**Time Estimate**: 8 hours

**Acceptance Criteria**:
- Ollama responding on production
- GPU utilization monitored
- Alerts configured for failures

---

### 7.2 Performance Tuning

**Tasks**:
- [ ] Optimize image preprocessing
- [ ] Tune confidence thresholds
- [ ] Configure caching TTLs
- [ ] Optimize prompt templates
- [ ] Batch processing setup

**Deliverables**:
- Performance improved 20%+
- Cost reduced via caching
- Latency targets met

**Time Estimate**: 6 hours

**Acceptance Criteria**:
- 90% cache hit rate for duplicates
- Average latency <3s
- Cloud usage <10%

---

## Summary

### Total Time Estimate

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1: Foundation | 3 | 15 |
| Phase 2: Local Vision | 3 | 24 |
| Phase 3: Cloud Fallback | 3 | 20 |
| Phase 4: Templates | 3 | 24 |
| Phase 5: Integration | 3 | 26 |
| Phase 6: Testing & Docs | 3 | 30 |
| Phase 7: Deployment | 2 | 14 |
| **Total** | **20** | **153** |

### Milestones

- **Week 1 End**: Local vision extraction working
- **Week 2 End**: Cloud fallback and hybrid strategy complete
- **Week 3 End**: Templates and main service ready
- **Week 4 End**: Production deployment and documentation

### Success Criteria

✅ **Functional**:
- Accessory extraction: 90%+ accuracy
- Order extraction: 85%+ accuracy
- <3s average latency
- Hybrid strategy working

✅ **Technical**:
- DDD architecture implemented
- 90%+ test coverage
- Complete documentation
- Production deployment

✅ **Business**:
- <$0.0001 average cost per image
- 10+ hours/week saved on manual entry
- Photo upload working in UI
- Order import from PDF working

---

## Risk Mitigation

### Risk 1: GPU Unavailable in Production

**Mitigation**: Cloud-first strategy, local as optimization
**Fallback**: Use Gemini free tier (sufficient for initial load)

### Risk 2: Local Model Accuracy Too Low

**Mitigation**: Hybrid strategy with low confidence threshold (70%)
**Fallback**: Use cloud providers more frequently

### Risk 3: Implementation Takes Longer

**Mitigation**: Prioritize core features (Phase 1-3)
**Fallback**: Deploy with cloud-only, add local later

### Risk 4: Ollama Integration Issues

**Mitigation**: Direct Hugging Face integration as backup
**Fallback**: Use transformers library instead

---

## Next Steps

1. **Review this roadmap** with team
2. **Approve design documents**:
   - OCR_EXTRACTION_DESIGN.md
   - OCR_RESEARCH_SUMMARY.md
3. **Set up development environment**:
   - Install Ollama
   - Pull MiniCPM-V
   - Test with sample images
4. **Begin Phase 1**: Foundation & Research

---

**Status**: ✅ Roadmap complete, awaiting approval to start implementation
**Estimated Start Date**: Upon approval
**Estimated Completion**: 4 weeks from start
