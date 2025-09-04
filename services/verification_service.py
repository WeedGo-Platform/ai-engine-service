"""
Verification Service - Age verification for compliance
Ontario requirement: 19+ for cannabis purchase
"""

import logging
import base64
import io
import re
from typing import Dict, Any, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

import pytesseract
from PIL import Image
import cv2
import numpy as np

from services.interfaces import IVerificationService
from utils.cache import CacheManager

logger = logging.getLogger(__name__)

class VerificationService(IVerificationService):
    """
    Age verification service for regulatory compliance
    Processes ID documents locally for privacy
    """
    
    def __init__(self, cache: Optional[CacheManager] = None):
        """Initialize verification service"""
        self.cache = cache or CacheManager()
        self.min_age = 19  # Ontario legal age
        
        # Document patterns for different ID types
        self.patterns = {
            "drivers_license": {
                "dob": [
                    r"DOB[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})",
                    r"DATE OF BIRTH[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})",
                    r"D\.O\.B[:\s]+(\d{2}[-/]\d{2}[-/]\d{4})",
                ],
                "name": [
                    r"NAME[:\s]+([A-Z\s]+)",
                    r"([A-Z]+),\s+([A-Z]+)",
                ],
                "id": [
                    r"DL[:\s]+([A-Z0-9]+)",
                    r"LICENCE NO[:\s]+([A-Z0-9-]+)",
                ]
            },
            "passport": {
                "dob": [
                    r"Date of birth[:\s]+(\d{2}\s+[A-Z]{3}\s+\d{4})",
                    r"(\d{2}[-/]\d{2}[-/]\d{4})",
                ],
                "name": [
                    r"Surname[:\s]+([A-Z\s]+)",
                    r"Given names[:\s]+([A-Z\s]+)",
                ],
                "id": [
                    r"Passport No[:\s]+([A-Z0-9]+)",
                    r"([A-Z]{2}\d{7})",
                ]
            },
            "health_card": {
                "dob": [
                    r"(\d{4}[-/]\d{2}[-/]\d{2})",
                    r"BIRTH[:\s]+(\d{2}[-/]\d{2}[-/]\d{4})",
                ],
                "name": [
                    r"([A-Z]+),\s+([A-Z]+)",
                ],
                "id": [
                    r"(\d{10}[A-Z]{2})",
                ]
            }
        }
    
    async def verify(
        self,
        document_base64: str,
        document_type: str = "drivers_license"
    ) -> Dict[str, Any]:
        """
        Verify age from document image
        
        Args:
            document_base64: Base64 encoded document image
            document_type: Type of document (drivers_license, passport, health_card)
        
        Returns:
            Verification result with age and validity
        """
        try:
            # Decode and preprocess image
            image = self._decode_image(document_base64)
            processed_image = self._preprocess_image(image)
            
            # Extract text using OCR
            text = self._extract_text(processed_image)
            
            if not text:
                return {
                    "verified": False,
                    "message": "Could not extract text from document",
                    "retry_suggestion": "Please ensure document is clear and well-lit"
                }
            
            # Parse document information
            doc_info = self._parse_document(text, document_type)
            
            if not doc_info.get("dob"):
                return {
                    "verified": False,
                    "message": "Could not find date of birth on document",
                    "retry_suggestion": "Please ensure entire document is visible"
                }
            
            # Calculate age
            age = self._calculate_age(doc_info["dob"])
            
            # Verify age meets requirement
            is_valid = age >= self.min_age
            
            result = {
                "verified": is_valid,
                "age": age,
                "meets_requirement": is_valid,
                "document_type": document_type,
                "extracted_info": {
                    "name": doc_info.get("name", "Not found"),
                    "dob": doc_info["dob"].isoformat() if doc_info.get("dob") else None,
                    "document_id": doc_info.get("id", "Not found")
                }
            }
            
            if is_valid:
                result["message"] = f"Age verified: {age} years old"
                
                # Cache verification for session
                if doc_info.get("id"):
                    cache_key = f"verification:{doc_info['id']}"
                    await self.cache.set(cache_key, result, ttl=3600)
            else:
                result["message"] = f"Under minimum age ({self.min_age})"
                result["years_until_eligible"] = self.min_age - age
            
            logger.info(
                f"Verification result: {is_valid} "
                f"(Age: {age}, Type: {document_type})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Verification error: {str(e)}", exc_info=True)
            return {
                "verified": False,
                "error": "Verification failed",
                "details": str(e),
                "retry_suggestion": "Please try with a clearer image"
            }
    
    def _decode_image(self, image_base64: str) -> np.ndarray:
        """Decode base64 image to numpy array"""
        # Remove data URL prefix if present
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_base64)
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to numpy array
        return np.array(pil_image)
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        # Denoise
        denoised = cv2.medianBlur(binary, 3)
        
        # Deskew if needed
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            
            if abs(angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(
                    denoised,
                    M,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
        
        return denoised
    
    def _extract_text(self, image: np.ndarray) -> str:
        """Extract text from image using OCR"""
        try:
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6'
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                config=custom_config
            )
            
            return text.upper()  # Uppercase for consistent matching
            
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    def _parse_document(
        self,
        text: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Parse document text to extract information"""
        
        patterns = self.patterns.get(
            document_type,
            self.patterns["drivers_license"]
        )
        
        result = {}
        
        # Extract date of birth
        for pattern in patterns["dob"]:
            match = re.search(pattern, text)
            if match:
                dob_str = match.group(1)
                dob = self._parse_date(dob_str)
                if dob:
                    result["dob"] = dob
                    break
        
        # Extract name
        for pattern in patterns["name"]:
            match = re.search(pattern, text)
            if match:
                result["name"] = " ".join(match.groups()).strip()
                break
        
        # Extract document ID
        for pattern in patterns["id"]:
            match = re.search(pattern, text)
            if match:
                result["id"] = match.group(1)
                break
        
        return result
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object"""
        
        # Try different date formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d %b %Y",
            "%d %B %Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Try to extract year, month, day
        numbers = re.findall(r"\d+", date_str)
        if len(numbers) == 3:
            # Assume YYYY-MM-DD or DD-MM-YYYY based on first number
            if len(numbers[0]) == 4:
                # YYYY-MM-DD
                try:
                    return date(
                        int(numbers[0]),
                        int(numbers[1]),
                        int(numbers[2])
                    )
                except ValueError:
                    pass
            else:
                # DD-MM-YYYY
                try:
                    return date(
                        int(numbers[2]),
                        int(numbers[1]),
                        int(numbers[0])
                    )
                except ValueError:
                    pass
        
        return None
    
    def _calculate_age(self, birth_date: date) -> int:
        """Calculate age from birth date"""
        today = date.today()
        age = relativedelta(today, birth_date).years
        return age