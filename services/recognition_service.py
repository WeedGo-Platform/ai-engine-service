"""
Recognition Service - Customer face recognition
Implements privacy-first approach with local processing
"""

import logging
import base64
import io
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

import numpy as np
from PIL import Image
import face_recognition

from services.interfaces import IRecognitionService
from repositories.customer_repository import CustomerRepository
from utils.cache import CacheManager

logger = logging.getLogger(__name__)

class RecognitionService(IRecognitionService):
    """
    Face recognition service for customer identification
    Privacy-first: All processing done locally
    """
    
    def __init__(
        self,
        customer_repo: Optional[CustomerRepository] = None,
        cache: Optional[CacheManager] = None
    ):
        """Initialize recognition service"""
        self.customer_repo = customer_repo or CustomerRepository()
        self.cache = cache or CacheManager()
        self.encoding_model = "hog"  # Faster than CNN
        self.tolerance = 0.6  # Recognition tolerance
    
    async def recognize(
        self,
        image_base64: str,
        store_id: str
    ) -> Dict[str, Any]:
        """
        Recognize customer from image
        
        Args:
            image_base64: Base64 encoded image
            store_id: Store identifier
        
        Returns:
            Recognition result with customer info if found
        """
        try:
            # Decode image
            image = self._decode_image(image_base64)
            
            # Extract face encoding
            encoding = self._extract_face_encoding(image)
            
            if encoding is None:
                return {
                    "recognized": False,
                    "message": "No face detected in image"
                }
            
            # Search for matching customer
            match = await self._find_matching_customer(encoding, store_id)
            
            if match:
                # Update visit count
                await self.customer_repo.update_visit(
                    customer_id=match["customer_id"]
                )
                
                return {
                    "recognized": True,
                    "customer": {
                        "id": match["customer_id"],
                        "name": match["name"],
                        "visits": match["visit_count"] + 1,
                        "last_visit": match["last_visit"],
                        "preferences": match.get("preferences", {}),
                        "loyalty_points": match.get("loyalty_points", 0)
                    }
                }
            
            return {
                "recognized": False,
                "message": "Customer not found in database"
            }
            
        except Exception as e:
            logger.error(f"Recognition error: {str(e)}", exc_info=True)
            return {
                "recognized": False,
                "error": "Recognition failed",
                "details": str(e)
            }
    
    async def enroll(
        self,
        customer_id: str,
        image_base64: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Enroll new customer with face encoding
        
        Args:
            customer_id: Unique customer ID
            image_base64: Base64 encoded face image
            metadata: Customer metadata (name, DOB, etc.)
        
        Returns:
            Success status
        """
        try:
            # Decode image
            image = self._decode_image(image_base64)
            
            # Extract face encoding
            encoding = self._extract_face_encoding(image)
            
            if encoding is None:
                logger.warning(f"No face detected for customer {customer_id}")
                return False
            
            # Save to database
            success = await self.customer_repo.create(
                customer_id=customer_id,
                face_encoding=encoding.tobytes(),
                metadata=metadata
            )
            
            if success:
                logger.info(f"Enrolled customer {customer_id}")
                
                # Clear cache
                await self.cache.delete(f"customers:{metadata.get('store_id', 'default')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Enrollment error: {str(e)}", exc_info=True)
            return False
    
    def _decode_image(self, image_base64: str) -> np.ndarray:
        """Decode base64 image to numpy array"""
        # Remove data URL prefix if present
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_base64)
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        # Convert to numpy array
        return np.array(pil_image)
    
    def _extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face encoding from image"""
        try:
            # Find face locations
            face_locations = face_recognition.face_locations(
                image,
                model=self.encoding_model
            )
            
            if not face_locations:
                return None
            
            # Get encoding for first face
            encodings = face_recognition.face_encodings(
                image,
                face_locations[:1]
            )
            
            return encodings[0] if encodings else None
            
        except Exception as e:
            logger.error(f"Face encoding error: {str(e)}")
            return None
    
    async def _find_matching_customer(
        self,
        encoding: np.ndarray,
        store_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find matching customer by face encoding"""
        
        # Check cache first
        cache_key = f"customers:{store_id}"
        customers = await self.cache.get(cache_key)
        
        if not customers:
            # Load from database
            customers = await self.customer_repo.get_by_store(store_id)
            
            # Cache for 5 minutes
            await self.cache.set(cache_key, customers, ttl=300)
        
        # Compare encodings
        for customer in customers:
            if customer.get("face_encoding"):
                # Convert bytes to numpy array
                stored_encoding = np.frombuffer(
                    customer["face_encoding"],
                    dtype=np.float64
                )
                
                # Compare encodings
                distance = face_recognition.face_distance(
                    [stored_encoding],
                    encoding
                )[0]
                
                if distance < self.tolerance:
                    logger.info(
                        f"Recognized customer {customer['customer_id']} "
                        f"(distance: {distance:.3f})"
                    )
                    return customer
        
        return None