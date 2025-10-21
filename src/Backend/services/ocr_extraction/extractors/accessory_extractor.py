"""
Accessory Extractor

Domain-specific extractor for accessory products.
Following SRP: Only handles accessory extraction.
Following DDD: Application layer adapter for domain use case.
"""

import logging
from typing import Optional
from pathlib import Path

from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import ExtractionOptions
from ..templates import ACCESSORY_TEMPLATE
from ..services import ocr_service

logger = logging.getLogger(__name__)


class AccessoryExtractor:
    """
    Extractor for accessory product information

    Provides convenient interface for extracting product details
    from accessory packaging photos.

    Use Case:
    - Barcode lookup failed or low confidence
    - Need product details from photo
    - Quick accessory intake

    Usage:
        extractor = AccessoryExtractor()

        # From file path
        result = await extractor.extract_from_file('/path/to/photo.jpg')

        # From Document object
        result = await extractor.extract_from_document(document)

        # Access extracted data
        product_name = result.extracted_data.get('product_name')
        brand = result.extracted_data.get('brand')
        barcode = result.extracted_data.get('barcode')
    """

    def __init__(self):
        """Initialize accessory extractor"""
        self.template = ACCESSORY_TEMPLATE
        logger.info("Accessory extractor initialized")

    async def extract_from_file(
        self,
        file_path: str,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract accessory details from image file

        Args:
            file_path: Path to accessory photo
            options: Extraction options (optional)

        Returns:
            ExtractionResult with product details

        Raises:
            FileNotFoundError: If file doesn't exist
            ExtractionError: If extraction fails
        """
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        logger.info(f"📸 Extracting accessory details from: {file_path}")

        # Create document
        document = Document(file_path=str(path.absolute()))

        # Extract using main service
        result = await self.extract_from_document(document, options)

        return result

    async def extract_from_bytes(
        self,
        image_bytes: bytes,
        extraction_options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract accessory details from image bytes (base64 decoded)

        Args:
            image_bytes: Raw image bytes
            extraction_options: Extraction options (optional)

        Returns:
            ExtractionResult with product details

        Raises:
            ExtractionError: If extraction fails
        """
        logger.info(f"📸 Extracting accessory details from image bytes ({len(image_bytes)} bytes)")

        # Create document from bytes
        document = Document(image_bytes=image_bytes)

        # Extract using main service
        result = await self.extract_from_document(document, extraction_options)

        return result

    async def extract_from_document(
        self,
        document: Document,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract accessory details from document

        Args:
            document: Document object
            options: Extraction options (optional)

        Returns:
            ExtractionResult with product details
        """
        # Use OCR service with accessory template
        result = await ocr_service.extract(
            document=document,
            template=self.template,
            options=options
        )

        # Log extracted data
        self._log_extraction(result)

        return result

    def _log_extraction(self, result: ExtractionResult):
        """Log extracted data for debugging"""
        data = result.extracted_data

        logger.info("Extracted accessory details:")
        logger.info(f"  Product: {data.get('product_name', 'N/A')}")
        logger.info(f"  Brand: {data.get('brand', 'N/A')}")
        logger.info(f"  SKU: {data.get('sku', 'N/A')}")
        logger.info(f"  Barcode: {data.get('barcode', 'N/A')}")
        logger.info(f"  Price: ${data.get('price', 'N/A')}")
        logger.info(f"  Confidence: {result.get_overall_confidence():.2f}")
        logger.info(f"  Validation: {'✅ Passed' if result.validation_passed else '❌ Failed'}")

    async def extract_barcode_only(
        self,
        file_path: str,
        options: Optional[ExtractionOptions] = None
    ) -> Optional[str]:
        """
        Extract only barcode from image

        Convenience method for barcode-focused extraction.

        Args:
            file_path: Path to product photo
            options: Extraction options (optional)

        Returns:
            Barcode string if found, None otherwise
        """
        result = await self.extract_from_file(file_path, options)

        barcode = result.extracted_data.get('barcode')

        if barcode:
            logger.info(f"✅ Extracted barcode: {barcode}")
        else:
            logger.warning("⚠️ No barcode found in image")

        return barcode

    async def extract_product_name(
        self,
        file_path: str,
        options: Optional[ExtractionOptions] = None
    ) -> Optional[str]:
        """
        Extract only product name from image

        Convenience method for product name extraction.

        Args:
            file_path: Path to product photo
            options: Extraction options (optional)

        Returns:
            Product name if found, None otherwise
        """
        result = await self.extract_from_file(file_path, options)

        product_name = result.extracted_data.get('product_name')

        if product_name:
            logger.info(f"✅ Extracted product name: {product_name}")
        else:
            logger.warning("⚠️ No product name found in image")

        return product_name


# Convenience: Global instance
accessory_extractor = AccessoryExtractor()
