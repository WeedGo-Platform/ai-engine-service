"""
Order Extractor

Domain-specific extractor for purchase orders.
Following SRP: Only handles order extraction.
Following DDD: Application layer adapter for domain use case.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from decimal import Decimal

from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import ExtractionOptions
from ..templates import ORDER_TEMPLATE
from ..services import ocr_service

logger = logging.getLogger(__name__)


class OrderExtractor:
    """
    Extractor for purchase order information

    Provides convenient interface for extracting order details
    from purchase order documents.

    Use Case:
    - Automate order entry from vendor POs
    - Extract line items for inventory
    - Process invoices and receipts

    Usage:
        extractor = OrderExtractor()

        # From file path
        result = await extractor.extract_from_file('/path/to/po.pdf')

        # Access extracted data
        order_number = result.extracted_data.get('order_number')
        vendor = result.extracted_data.get('vendor')
        line_items = result.extracted_data.get('line_items', [])
        total = result.extracted_data.get('total')
    """

    def __init__(self):
        """Initialize order extractor"""
        self.template = ORDER_TEMPLATE
        logger.info("Order extractor initialized")

    async def extract_from_file(
        self,
        file_path: str,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract order details from document file

        Args:
            file_path: Path to order document (image or PDF)
            options: Extraction options (optional)

        Returns:
            ExtractionResult with order details

        Raises:
            FileNotFoundError: If file doesn't exist
            ExtractionError: If extraction fails
        """
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Order document not found: {file_path}")

        logger.info(f"📄 Extracting order details from: {file_path}")

        # Create document
        document = Document(file_path=str(path.absolute()))

        # Extract using main service
        result = await self.extract_from_document(document, options)

        return result

    async def extract_from_document(
        self,
        document: Document,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract order details from document

        Args:
            document: Document object
            options: Extraction options (optional)

        Returns:
            ExtractionResult with order details
        """
        # Use OCR service with order template
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

        logger.info("Extracted order details:")
        logger.info(f"  Order #: {data.get('order_number', 'N/A')}")
        logger.info(f"  Vendor: {data.get('vendor', 'N/A')}")
        logger.info(f"  Date: {data.get('order_date', 'N/A')}")
        logger.info(f"  Line Items: {len(data.get('line_items', []))}")
        logger.info(f"  Subtotal: ${data.get('subtotal', 'N/A')}")
        logger.info(f"  Tax: ${data.get('tax', 'N/A')}")
        logger.info(f"  Total: ${data.get('total', 'N/A')}")
        logger.info(f"  Confidence: {result.get_overall_confidence():.2f}")
        logger.info(f"  Validation: {'✅ Passed' if result.validation_passed else '❌ Failed'}")

    def get_line_items(self, result: ExtractionResult) -> List[Dict[str, Any]]:
        """
        Get line items from extraction result

        Convenience method to access line items.

        Args:
            result: Extraction result

        Returns:
            List of line item dictionaries
        """
        line_items = result.extracted_data.get('line_items', [])

        if not isinstance(line_items, list):
            logger.warning(f"Line items not a list: {type(line_items)}")
            return []

        logger.info(f"Retrieved {len(line_items)} line items")
        return line_items

    def get_total_items_count(self, result: ExtractionResult) -> int:
        """
        Get total count of items ordered

        Sums quantities from all line items.

        Args:
            result: Extraction result

        Returns:
            Total item count
        """
        line_items = self.get_line_items(result)

        total_count = 0
        for item in line_items:
            qty_str = item.get('quantity', '0')
            try:
                qty = int(qty_str)
                total_count += qty
            except ValueError:
                logger.warning(f"Invalid quantity for item: {qty_str}")
                continue

        logger.info(f"Total items ordered: {total_count}")
        return total_count

    def verify_totals(self, result: ExtractionResult) -> Dict[str, Any]:
        """
        Verify order total calculation

        Checks if subtotal + tax + shipping = total.

        Args:
            result: Extraction result

        Returns:
            Dictionary with verification results
        """
        data = result.extracted_data

        try:
            subtotal = Decimal(data.get('subtotal', '0'))
            tax = Decimal(data.get('tax', '0'))
            shipping = Decimal(data.get('shipping', '0'))
            total = Decimal(data.get('total', '0'))

            calculated_total = subtotal + tax + shipping
            difference = abs(calculated_total - total)

            is_correct = difference < Decimal('0.01')  # Allow 1 cent rounding

            verification = {
                'is_correct': is_correct,
                'expected_total': str(calculated_total),
                'actual_total': str(total),
                'difference': str(difference),
                'subtotal': str(subtotal),
                'tax': str(tax),
                'shipping': str(shipping),
            }

            if is_correct:
                logger.info("✅ Order totals verified correctly")
            else:
                logger.warning(
                    f"⚠️ Order total mismatch: "
                    f"expected ${calculated_total}, got ${total} "
                    f"(difference: ${difference})"
                )

            return verification

        except Exception as e:
            logger.error(f"Failed to verify totals: {e}")
            return {
                'is_correct': False,
                'error': str(e)
            }

    async def extract_line_items_only(
        self,
        file_path: str,
        options: Optional[ExtractionOptions] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract only line items from order

        Convenience method for line item focused extraction.

        Args:
            file_path: Path to order document
            options: Extraction options (optional)

        Returns:
            List of line item dictionaries
        """
        result = await self.extract_from_file(file_path, options)
        return self.get_line_items(result)


# Convenience: Global instance
order_extractor = OrderExtractor()
