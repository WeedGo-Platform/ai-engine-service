"""
OCR Extraction System - Usage Examples

This file demonstrates how to use the OCR extraction system
for various use cases.

Prerequisites:
    1. Install at least one of:
       - Ollama with vision model: `ollama pull minicpm-v`
       - Hugging Face model in ocr/models/ directory
       - Set GEMINI_API_KEY environment variable

    2. Install Python dependencies:
       pip install pillow google-generativeai transformers torch httpx

Run Examples:
    python USAGE_EXAMPLE.py
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Simple Accessory Extraction (Recommended Approach)
# ============================================================================

async def example_1_simple_accessory_extraction():
    """
    Simplest way to extract accessory details from a photo.

    Use this approach for most use cases.
    """
    from services.ocr_extraction import ocr_service, accessory_extractor

    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Simple Accessory Extraction")
    logger.info("=" * 60)

    # Initialize OCR service (auto-discovers models)
    await ocr_service.initialize()

    # Extract from accessory photo
    # Replace with actual image path
    image_path = "/path/to/accessory_photo.jpg"

    # Check if file exists (for demo)
    if not Path(image_path).exists():
        logger.warning(f"Image not found: {image_path}")
        logger.info("Please update image_path with actual file")
        return

    # Extract!
    result = await accessory_extractor.extract_from_file(image_path)

    # Access extracted data
    print("\n✅ Extraction Complete!")
    print(f"Product: {result.extracted_data.get('product_name')}")
    print(f"Brand: {result.extracted_data.get('brand')}")
    print(f"SKU: {result.extracted_data.get('sku')}")
    print(f"Barcode: {result.extracted_data.get('barcode')}")
    print(f"Price: ${result.extracted_data.get('price')}")
    print(f"Category: {result.extracted_data.get('category')}")
    print(f"\nConfidence: {result.get_overall_confidence():.2%}")
    print(f"Validation: {'✅ Passed' if result.validation_passed else '❌ Failed'}")
    print(f"Manual Review: {'⚠️ Required' if result.requires_manual_review else '✅ Not Needed'}")


# ============================================================================
# EXAMPLE 2: Order Extraction with Line Items
# ============================================================================

async def example_2_order_extraction():
    """
    Extract purchase order details including line items.
    """
    from services.ocr_extraction import ocr_service, order_extractor

    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Order Extraction")
    logger.info("=" * 60)

    # Initialize OCR service
    await ocr_service.initialize()

    # Extract from order document
    order_path = "/path/to/purchase_order.pdf"  # or .jpg, .png

    if not Path(order_path).exists():
        logger.warning(f"Order document not found: {order_path}")
        logger.info("Please update order_path with actual file")
        return

    # Extract!
    result = await order_extractor.extract_from_file(order_path)

    # Access extracted data
    print("\n✅ Extraction Complete!")
    print(f"Order Number: {result.extracted_data.get('order_number')}")
    print(f"Vendor: {result.extracted_data.get('vendor')}")
    print(f"Date: {result.extracted_data.get('order_date')}")
    print(f"Payment Terms: {result.extracted_data.get('payment_terms')}")

    # Line items
    line_items = order_extractor.get_line_items(result)
    print(f"\nLine Items ({len(line_items)}):")
    for idx, item in enumerate(line_items, 1):
        print(f"  {idx}. {item.get('description')}")
        print(f"     SKU: {item.get('sku')}, Qty: {item.get('quantity')}, "
              f"Price: ${item.get('unit_price')}, Total: ${item.get('total')}")

    # Totals
    print(f"\nSubtotal: ${result.extracted_data.get('subtotal')}")
    print(f"Tax: ${result.extracted_data.get('tax')}")
    print(f"Shipping: ${result.extracted_data.get('shipping')}")
    print(f"Total: ${result.extracted_data.get('total')}")

    # Verify totals
    verification = order_extractor.verify_totals(result)
    if verification.get('is_correct'):
        print("\n✅ Totals verified correctly")
    else:
        print(f"\n⚠️ Total mismatch: {verification}")


# ============================================================================
# EXAMPLE 3: Custom Extraction with Options
# ============================================================================

async def example_3_custom_extraction_options():
    """
    Advanced extraction with custom options.

    Demonstrates:
    - Specific strategy selection
    - Custom timeout and retries
    - Manual provider selection
    """
    from services.ocr_extraction import (
        ocr_service,
        Document,
        ExtractionOptions,
        ACCESSORY_TEMPLATE
    )

    logger.info("=" * 60)
    logger.info("EXAMPLE 3: Custom Extraction Options")
    logger.info("=" * 60)

    # Initialize
    await ocr_service.initialize()

    # Create document
    image_path = "/path/to/image.jpg"
    if not Path(image_path).exists():
        logger.warning("Image not found, skipping example")
        return

    document = Document(file_path=image_path)

    # Custom extraction options
    options = ExtractionOptions(
        strategy='hybrid',  # Force hybrid strategy
        max_retries=3,
        timeout_seconds=60,
        preferred_provider='ollama_minicpm-v',  # Try specific provider
    )

    # Extract with custom options
    result = await ocr_service.extract(document, ACCESSORY_TEMPLATE, options)

    print(f"\n✅ Extracted with strategy: {result.provider_used}")
    print(f"Confidence: {result.get_overall_confidence():.2%}")


# ============================================================================
# EXAMPLE 4: Barcode-Only Extraction
# ============================================================================

async def example_4_barcode_only():
    """
    Extract only barcode from image (fastest).
    """
    from services.ocr_extraction import ocr_service, accessory_extractor

    logger.info("=" * 60)
    logger.info("EXAMPLE 4: Barcode-Only Extraction")
    logger.info("=" * 60)

    await ocr_service.initialize()

    image_path = "/path/to/product_with_barcode.jpg"
    if not Path(image_path).exists():
        logger.warning("Image not found, skipping example")
        return

    # Extract only barcode (convenience method)
    barcode = await accessory_extractor.extract_barcode_only(image_path)

    if barcode:
        print(f"\n✅ Barcode found: {barcode}")
    else:
        print("\n❌ No barcode found in image")


# ============================================================================
# EXAMPLE 5: Check Available Models and Providers
# ============================================================================

async def example_5_check_available_providers():
    """
    Check what models and providers are available.
    """
    from services.ocr_extraction import ocr_service

    logger.info("=" * 60)
    logger.info("EXAMPLE 5: Available Providers")
    logger.info("=" * 60)

    # Initialize
    await ocr_service.initialize()

    # Get stats
    stats = ocr_service.get_stats()

    print("\n📊 OCR Service Statistics:")
    print(f"Initialized: {stats['initialized']}")

    # Discovery info
    discovery = stats.get('discovery', {})
    if discovery:
        print(f"\nModels Found: {len(discovery.get('models_found', []))}")
        for model in discovery.get('models_found', []):
            print(f"  - {model['name']} ({model['provider_type']}, {model['size_mb']}MB)")

        print(f"\nOllama Available: {discovery.get('ollama_available')}")
        print(f"Gemini API Key: {'✅ Set' if discovery.get('gemini_api_key') else '❌ Not Set'}")

    # Provider stats
    providers = stats.get('providers', {})
    if providers:
        print(f"\nTotal Providers: {providers.get('total_providers', 0)}")
        print("Available Providers:")
        for name in providers.get('provider_names', []):
            print(f"  - {name}")

    # Strategies
    strategies = stats.get('strategies', [])
    print(f"\nAvailable Strategies: {', '.join(strategies)}")


# ============================================================================
# EXAMPLE 6: Batch Processing Multiple Images
# ============================================================================

async def example_6_batch_processing():
    """
    Process multiple images in parallel.
    """
    from services.ocr_extraction import ocr_service, accessory_extractor
    import asyncio

    logger.info("=" * 60)
    logger.info("EXAMPLE 6: Batch Processing")
    logger.info("=" * 60)

    await ocr_service.initialize()

    # List of images to process
    image_paths = [
        "/path/to/image1.jpg",
        "/path/to/image2.jpg",
        "/path/to/image3.jpg",
    ]

    # Filter existing files
    existing_paths = [p for p in image_paths if Path(p).exists()]

    if not existing_paths:
        logger.warning("No images found, skipping example")
        return

    print(f"\nProcessing {len(existing_paths)} images...")

    # Process in parallel
    tasks = [
        accessory_extractor.extract_from_file(path)
        for path in existing_paths
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Show results
    print("\n✅ Batch Processing Complete!")
    for idx, (path, result) in enumerate(zip(existing_paths, results), 1):
        if isinstance(result, Exception):
            print(f"{idx}. {Path(path).name}: ❌ FAILED - {result}")
        else:
            product = result.extracted_data.get('product_name', 'Unknown')
            confidence = result.get_overall_confidence()
            print(f"{idx}. {Path(path).name}: ✅ {product} ({confidence:.2%})")


# ============================================================================
# EXAMPLE 7: Error Handling
# ============================================================================

async def example_7_error_handling():
    """
    Proper error handling for extraction.
    """
    from services.ocr_extraction import (
        ocr_service,
        accessory_extractor,
        ExtractionError,
        AllProvidersExhaustedError,
        RateLimitError
    )

    logger.info("=" * 60)
    logger.info("EXAMPLE 7: Error Handling")
    logger.info("=" * 60)

    try:
        await ocr_service.initialize()

        image_path = "/path/to/image.jpg"
        result = await accessory_extractor.extract_from_file(image_path)

        print(f"✅ Success: {result.extracted_data.get('product_name')}")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")

    except AllProvidersExhaustedError as e:
        print(f"❌ All providers failed: {e}")
        print("Solution: Install Ollama or set GEMINI_API_KEY")

    except RateLimitError as e:
        print(f"❌ Rate limit exceeded: {e}")
        print(f"Retry after: {e.retry_after} seconds")

    except ExtractionError as e:
        print(f"❌ Extraction failed: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ============================================================================
# Main - Run All Examples
# ============================================================================

async def main():
    """Run all examples"""
    print("🚀 OCR Extraction System - Usage Examples\n")

    examples = [
        ("Simple Accessory Extraction", example_1_simple_accessory_extraction),
        ("Order Extraction", example_2_order_extraction),
        ("Custom Options", example_3_custom_extraction_options),
        ("Barcode Only", example_4_barcode_only),
        ("Check Providers", example_5_check_available_providers),
        ("Batch Processing", example_6_batch_processing),
        ("Error Handling", example_7_error_handling),
    ]

    # Run example 5 (check providers) to see what's available
    await example_5_check_available_providers()

    # Uncomment to run other examples:
    # await example_1_simple_accessory_extraction()
    # await example_2_order_extraction()
    # await example_3_custom_extraction_options()
    # await example_4_barcode_only()
    # await example_6_batch_processing()
    # await example_7_error_handling()


if __name__ == "__main__":
    asyncio.run(main())
