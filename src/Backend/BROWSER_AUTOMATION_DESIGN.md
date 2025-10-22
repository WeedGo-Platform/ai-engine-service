# Browser Automation System - Architecture Design

## Design Principles Applied

### DDD (Domain-Driven Design)
- **Domain**: Web scraping and browser automation
- **Bounded Context**: `browser_automation` service
- **Entities**: `BrowserSession`, `ScrapingResult`
- **Value Objects**: `BrowserConfig`, `ScrapingOptions`, `SelectorSet`
- **Domain Services**: `BrowserAutomationService`, `ScrapingStrategySelector`
- **Application Services**: Site-specific scrapers (barcode, price, product)

### DRY (Don't Repeat Yourself)
- ✅ Single `BrowserAutomationService` used by all scrapers
- ✅ Reusable scraping strategies (static vs dynamic)
- ✅ Shared browser configuration and session pooling
- ✅ Common selector patterns defined once

### KISS (Keep It Simple, Stupid)
- ✅ Simple API: `scrape(url, selectors, options)`
- ✅ Hide Playwright complexity behind clean interface
- ✅ Sensible defaults, configuration optional
- ✅ Clear error handling

### SRP (Single Responsibility Principle)
- ✅ `BrowserAutomationService`: Browser lifecycle management only
- ✅ `ScrapingStrategy`: Defines HOW to scrape (static vs dynamic)
- ✅ `StrategySelector`: Decides WHICH strategy to use
- ✅ `Scraper`: Defines WHAT to scrape (selectors, parsing)

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  (Business Logic - What to scrape and why)                   │
├─────────────────────────────────────────────────────────────┤
│  BarcodeLookupService  │  PriceComparisonService            │
│  InventoryScraperService │  ProductInfoService              │
└────────────┬────────────────────────────────────────────────┘
             │ uses
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  (Core business rules - How to scrape)                       │
├─────────────────────────────────────────────────────────────┤
│         BrowserAutomationService (Domain Service)            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  - scrape(url, config) → ScrapingResult               │  │
│  │  - scrape_with_strategy(url, strategy) → Result       │  │
│  │  - detect_strategy_needed(html) → Strategy            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ScrapingStrategySelector         Scraping Strategies       │
│  ┌────────────────────┐      ┌──────────────────────────┐  │
│  │ - select(url, html)│      │ StaticScrapingStrategy   │  │
│  │ - can_use_static() │      │ DynamicScrapingStrategy  │  │
│  │ - needs_browser()  │      │ HybridScrapingStrategy   │  │
│  └────────────────────┘      └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  (Technical implementation details)                          │
├─────────────────────────────────────────────────────────────┤
│  Playwright Driver  │  aiohttp Client  │  BeautifulSoup     │
│  Browser Pool       │  Cache Layer     │  Retry Logic       │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
services/
├── browser_automation/
│   ├── __init__.py                    # Public API exports
│   │
│   ├── domain/                        # DOMAIN LAYER
│   │   ├── __init__.py
│   │   ├── entities.py                # BrowserSession, ScrapingResult
│   │   ├── value_objects.py           # BrowserConfig, ScrapingOptions, SelectorSet
│   │   └── exceptions.py              # Domain-specific exceptions
│   │
│   ├── services/                      # DOMAIN SERVICES
│   │   ├── __init__.py
│   │   ├── browser_service.py         # BrowserAutomationService (CORE)
│   │   └── strategy_selector.py       # ScrapingStrategySelector
│   │
│   ├── strategies/                    # SCRAPING STRATEGIES
│   │   ├── __init__.py
│   │   ├── base.py                    # AbstractScrapingStrategy
│   │   ├── static_strategy.py         # StaticScrapingStrategy (aiohttp)
│   │   ├── dynamic_strategy.py        # DynamicScrapingStrategy (Playwright)
│   │   └── hybrid_strategy.py         # HybridScrapingStrategy (try static first)
│   │
│   ├── scrapers/                      # APPLICATION SERVICES
│   │   ├── __init__.py
│   │   ├── base_scraper.py            # AbstractScraper
│   │   ├── barcode_scraper.py         # BarcodeProductScraper
│   │   ├── price_scraper.py           # PriceComparisonScraper
│   │   └── inventory_scraper.py       # InventoryLevelScraper
│   │
│   └── infrastructure/                # INFRASTRUCTURE
│       ├── __init__.py
│       ├── browser_pool.py            # Browser instance pool
│       ├── cache.py                   # Result caching
│       └── retry.py                   # Retry logic with exponential backoff
│
└── barcode_lookup_service.py          # Uses browser_automation
```

---

## Core Components

### 1. Value Objects (Immutable Configuration)

```python
# domain/value_objects.py

@dataclass(frozen=True)
class BrowserConfig:
    """Browser configuration settings"""
    headless: bool = True
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None

@dataclass(frozen=True)
class SelectorSet:
    """Set of CSS selectors for scraping"""
    product_name: List[str]
    product_price: List[str]
    product_image: List[str]
    product_brand: Optional[List[str]] = None

@dataclass(frozen=True)
class ScrapingOptions:
    """Options for a scraping operation"""
    wait_for_selector: Optional[str] = None
    wait_for_timeout: int = 5000
    extract_json_ld: bool = True
    take_screenshot: bool = False
    strategy: Optional[str] = None  # 'static', 'dynamic', 'auto'
```

### 2. Entities (Have Identity)

```python
# domain/entities.py

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    url: str
    found: bool
    data: Dict[str, Any]
    strategy_used: str
    latency_ms: float
    screenshot_path: Optional[str] = None
    error: Optional[str] = None

    def is_successful(self) -> bool:
        return self.found and not self.error

    def get_confidence(self) -> float:
        if not self.found:
            return 0.0
        # Strategy affects confidence
        confidence_map = {
            'static': 0.7,
            'dynamic': 0.85,
            'cached': 1.0
        }
        return confidence_map.get(self.strategy_used, 0.5)
```

### 3. Domain Service (BrowserAutomationService)

```python
# services/browser_service.py

class BrowserAutomationService:
    """
    Domain Service: Orchestrates web scraping operations

    Responsibilities:
    - Manage browser lifecycle
    - Select appropriate scraping strategy
    - Execute scraping with retry logic
    - Return standardized results

    Does NOT:
    - Know about specific sites (that's scrapers' job)
    - Contain business logic (that's application layer)
    - Parse domain-specific data (that's scrapers' job)
    """

    def __init__(
        self,
        browser_pool: BrowserPool,
        strategy_selector: ScrapingStrategySelector,
        cache: Optional[CacheService] = None
    ):
        self.browser_pool = browser_pool
        self.strategy_selector = strategy_selector
        self.cache = cache

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: Optional[ScrapingOptions] = None
    ) -> ScrapingResult:
        """
        Scrape a URL using the optimal strategy

        Algorithm:
        1. Check cache
        2. Try static scraping first (fast)
        3. If static fails or incomplete, detect if dynamic needed
        4. If needed, use Playwright (slower but complete)
        5. Cache result
        """
        options = options or ScrapingOptions()

        # Check cache
        if self.cache:
            cached = await self.cache.get(url)
            if cached:
                return cached

        # Auto-select strategy or use specified
        if options.strategy == 'auto' or options.strategy is None:
            strategy = await self.strategy_selector.select(url, options)
        else:
            strategy = self._get_strategy(options.strategy)

        # Execute scraping
        result = await strategy.scrape(url, selectors, options)

        # Cache if successful
        if result.is_successful() and self.cache:
            await self.cache.set(url, result)

        return result
```

### 4. Strategy Selector (Intelligent Decision Making)

```python
# services/strategy_selector.py

class ScrapingStrategySelector:
    """
    Selects the optimal scraping strategy based on:
    - Site characteristics (static vs JS-heavy)
    - Previous scraping history
    - Performance requirements
    """

    # Sites known to require browser automation
    DYNAMIC_SITES = [
        'onewholesale.ca',
        'shopify.com',
        'wix.com',
        # Add more as discovered
    ]

    # Indicators that a page needs JavaScript
    JS_INDICATORS = [
        'Loading...',
        'Please wait',
        'window.__INITIAL_STATE__',
        'data-react-root',
        'ng-app',
        'v-app',
    ]

    async def select(
        self,
        url: str,
        options: ScrapingOptions
    ) -> ScrapingStrategy:
        """
        Smart strategy selection:
        1. If URL in known dynamic sites → Dynamic
        2. Otherwise → Try hybrid (static first, dynamic fallback)
        """
        domain = self._extract_domain(url)

        if self._is_known_dynamic_site(domain):
            return DynamicScrapingStrategy()

        # Use hybrid: try static, fallback to dynamic
        return HybridScrapingStrategy()

    def _is_known_dynamic_site(self, domain: str) -> bool:
        return any(d in domain for d in self.DYNAMIC_SITES)

    async def detect_needs_browser(self, html: str) -> bool:
        """
        Analyze HTML to detect if browser automation needed
        """
        return any(indicator in html for indicator in self.JS_INDICATORS)
```

### 5. Scraping Strategies (Strategy Pattern)

```python
# strategies/base.py

class AbstractScrapingStrategy(ABC):
    """Base class for all scraping strategies"""

    @abstractmethod
    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

# strategies/static_strategy.py

class StaticScrapingStrategy(AbstractScrapingStrategy):
    """Fast scraping using aiohttp + BeautifulSoup"""

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        data = self._extract_data(soup, selectors)

        return ScrapingResult(
            url=url,
            found=bool(data),
            data=data,
            strategy_used='static',
            latency_ms=(time.time() - start_time) * 1000
        )

# strategies/dynamic_strategy.py

class DynamicScrapingStrategy(AbstractScrapingStrategy):
    """Full browser automation using Playwright"""

    def __init__(self, browser_pool: BrowserPool):
        self.browser_pool = browser_pool

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        start_time = time.time()

        async with self.browser_pool.get_browser() as browser:
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until='networkidle')

                # Wait for specific selector if provided
                if options.wait_for_selector:
                    await page.wait_for_selector(
                        options.wait_for_selector,
                        timeout=options.wait_for_timeout
                    )

                # Extract data
                html = await page.content()
                data = self._extract_data(html, selectors)

                return ScrapingResult(
                    url=url,
                    found=bool(data),
                    data=data,
                    strategy_used='dynamic',
                    latency_ms=(time.time() - start_time) * 1000
                )
            finally:
                await page.close()

# strategies/hybrid_strategy.py

class HybridScrapingStrategy(AbstractScrapingStrategy):
    """
    Try static first, fallback to dynamic if:
    - No data found
    - Page indicates JS rendering needed
    - Confidence too low
    """

    async def scrape(
        self,
        url: str,
        selectors: SelectorSet,
        options: ScrapingOptions
    ) -> ScrapingResult:
        # Try static first (fast)
        static_result = await StaticScrapingStrategy().scrape(url, selectors, options)

        # Check if we need browser
        if static_result.is_successful():
            return static_result

        # Fallback to browser automation
        logger.info(f"Static scraping failed, using browser for {url}")
        return await DynamicScrapingStrategy().scrape(url, selectors, options)
```

### 6. Application-Level Scrapers

```python
# scrapers/barcode_scraper.py

class BarcodeProductScraper:
    """
    Application Service: Scrapes product data from barcode searches

    Uses BrowserAutomationService but adds barcode-specific logic
    """

    def __init__(self, browser_service: BrowserAutomationService):
        self.browser_service = browser_service

    async def scrape_one_wholesale(self, barcode: str) -> Dict[str, Any]:
        """Scrape ONE Wholesale for barcode"""
        url = f"https://www.onewholesale.ca/search?q={barcode}"

        # Define what to extract (WHAT, not HOW)
        selectors = SelectorSet(
            product_name=[
                'h2.product-title',
                'h3.product-name',
                '.product-info h2'
            ],
            product_price=[
                'span.price',
                'span.money',
                '.product-price'
            ],
            product_image=[
                '.product-image img',
                '.product-photo img'
            ],
            product_brand=[
                '.product-vendor',
                '.brand-name'
            ]
        )

        # Options for JavaScript-heavy site
        options = ScrapingOptions(
            wait_for_selector='.product-card, .search-result',
            wait_for_timeout=5000,
            extract_json_ld=True,
            strategy='auto'  # Let system decide
        )

        # BrowserAutomationService handles HOW
        result = await self.browser_service.scrape(url, selectors, options)

        return {
            'found': result.found,
            'data': result.data,
            'source': 'ONE Wholesale',
            'confidence': result.get_confidence(),
            'strategy_used': result.strategy_used,
            'latency_ms': result.latency_ms
        }
```

---

## Usage Examples

### Example 1: Barcode Lookup (Current Use Case)

```python
# In barcode_lookup_service.py

from services.browser_automation import BrowserAutomationService, BarcodeProductScraper

class BarcodeLookupService:
    def __init__(self, llm_router=None, browser_service=None):
        self.browser_service = browser_service or get_browser_service()
        self.barcode_scraper = BarcodeProductScraper(self.browser_service)

    async def _scrape_one_wholesale(self, barcode: str) -> Dict[str, Any]:
        """Simple delegation to specialized scraper"""
        return await self.barcode_scraper.scrape_one_wholesale(barcode)
```

### Example 2: Price Comparison (Future Use Case)

```python
# New service for price comparison

from services.browser_automation import BrowserAutomationService, PriceComparisonScraper

class PriceComparisonService:
    def __init__(self, browser_service: BrowserAutomationService):
        self.price_scraper = PriceComparisonScraper(browser_service)

    async def compare_prices(self, product_name: str) -> List[Dict]:
        """Compare prices across multiple sites"""
        sites = [
            'onewholesale.ca',
            'canadawholesale.ca',
            'amazon.ca'
        ]

        results = []
        for site in sites:
            price_data = await self.price_scraper.scrape_site(site, product_name)
            results.append(price_data)

        return results
```

### Example 3: Inventory Scraping (Future Use Case)

```python
# Scrape supplier inventory levels

from services.browser_automation import BrowserAutomationService, InventoryLevelScraper

class SupplierInventoryService:
    def __init__(self, browser_service: BrowserAutomationService):
        self.inventory_scraper = InventoryLevelScraper(browser_service)

    async def check_stock_levels(self, supplier_url: str, sku: str) -> Dict:
        """Check if product is in stock at supplier"""
        return await self.inventory_scraper.check_availability(supplier_url, sku)
```

---

## Performance Optimization

### 1. Browser Pool (Reuse Browser Instances)

```python
# infrastructure/browser_pool.py

class BrowserPool:
    """
    Pool of reusable browser instances
    - Reduces startup overhead (2-3s saved per request)
    - Limits concurrent browsers (memory management)
    """

    def __init__(self, max_browsers: int = 3):
        self.max_browsers = max_browsers
        self.available_browsers = asyncio.Queue(maxsize=max_browsers)
        self.active_count = 0

    async def get_browser(self):
        """Get browser from pool or create new one"""
        if not self.available_browsers.empty():
            return await self.available_browsers.get()

        if self.active_count < self.max_browsers:
            browser = await self._create_browser()
            self.active_count += 1
            return browser

        # Wait for available browser
        return await self.available_browsers.get()

    async def return_browser(self, browser):
        """Return browser to pool"""
        await self.available_browsers.put(browser)
```

### 2. Intelligent Caching

```python
# infrastructure/cache.py

class ScrapingCache:
    """
    Cache scraping results to avoid repeated requests
    - Static content: 24 hours
    - Dynamic content: 1 hour
    - Errors: 5 minutes (retry sooner)
    """

    def get_ttl(self, result: ScrapingResult) -> int:
        if result.error:
            return 300  # 5 minutes
        elif result.strategy_used == 'static':
            return 86400  # 24 hours
        else:
            return 3600  # 1 hour
```

### 3. Detection Before Browser Launch

```python
# Key optimization: Only launch browser if CONFIRMED needed

async def scrape(self, url: str, selectors: SelectorSet, options: ScrapingOptions):
    # Step 1: Fast static scraping (300ms)
    static_result = await self.static_strategy.scrape(url, selectors, options)

    # Step 2: Check if result is good enough
    if static_result.is_successful() and static_result.get_confidence() >= 0.7:
        return static_result  # Done! No browser needed

    # Step 3: Analyze HTML to confirm browser needed
    needs_browser = await self.strategy_selector.detect_needs_browser(static_result.html)

    if not needs_browser:
        return static_result  # Low confidence but static is best we can do

    # Step 4: CONFIRMED browser needed → Launch Playwright (4s)
    logger.info(f"Browser confirmed needed for {url}")
    return await self.dynamic_strategy.scrape(url, selectors, options)
```

---

## Benefits Summary

| Aspect | Before | After (DDD Design) |
|--------|--------|-------------------|
| **Reusability** | Each service implements own scraping | Single `BrowserAutomationService` used everywhere |
| **Performance** | Always use same approach | Smart strategy selection (static first, browser only if needed) |
| **Maintainability** | Scraping logic scattered | Clear separation: Service (HOW) vs Scraper (WHAT) |
| **Testability** | Hard to mock browser | Easy to inject mocks via DI |
| **Extensibility** | Add new sites = duplicate code | Add new scraper class, reuse service |
| **Error Handling** | Inconsistent | Standardized `ScrapingResult` |

---

## Implementation Checklist

### Phase 1: Core Infrastructure ✅
- [ ] Create directory structure
- [ ] Implement value objects (BrowserConfig, SelectorSet, ScrapingOptions)
- [ ] Implement entities (ScrapingResult)
- [ ] Implement exceptions

### Phase 2: Strategies ✅
- [ ] AbstractScrapingStrategy
- [ ] StaticScrapingStrategy (aiohttp + BeautifulSoup)
- [ ] DynamicScrapingStrategy (Playwright)
- [ ] HybridScrapingStrategy

### Phase 3: Domain Services ✅
- [ ] BrowserAutomationService
- [ ] ScrapingStrategySelector
- [ ] BrowserPool
- [ ] ScrapingCache

### Phase 4: Application Scrapers ✅
- [ ] BarcodeProductScraper
- [ ] Integrate with BarcodeLookupService
- [ ] Test with barcode 841562004743

### Phase 5: Future Extensions 🔮
- [ ] PriceComparisonScraper
- [ ] InventoryLevelScraper
- [ ] ProductReviewScraper

---

## Metrics & Monitoring

```python
# Track performance by strategy

class ScrapingMetrics:
    def record(self, result: ScrapingResult):
        metrics = {
            'strategy': result.strategy_used,
            'latency_ms': result.latency_ms,
            'success': result.is_successful(),
            'url_domain': extract_domain(result.url)
        }

        # Send to monitoring system
        logger.info(f"Scraping metrics: {metrics}")
```

Expected metrics:
- **Static scraping**: 95% of requests, 300ms avg
- **Dynamic scraping**: 5% of requests, 4200ms avg
- **Overall avg**: 500ms (much better than "always use browser")

---

This design gives you a **professional, enterprise-grade web scraping system** that:
- ✅ Follows DDD, DRY, KISS, SRP
- ✅ Reusable across barcode lookup, price comparison, inventory checking
- ✅ Smart performance optimization (static first, browser only when needed)
- ✅ Easy to test, maintain, and extend
