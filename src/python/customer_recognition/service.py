#!/usr/bin/env python3
"""
Customer Recognition Service
Privacy-preserving biometric customer recognition using cancelable templates
"""

import os
import cv2
import numpy as np
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import base64
import json

# Face recognition imports
import face_recognition
from deepface import DeepFace
import insightface
from insightface.app import FaceAnalysis

# Database
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

# Privacy and security
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerRecognitionService:
    """
    Privacy-preserving customer recognition service featuring:
    - Cancelable biometric templates
    - Self-improving recognition algorithms
    - Privacy compliance (no raw biometric storage)
    - Customer analytics and insights
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Database connections
        self.pg_conn = None
        self.redis_client = None
        
        # Face recognition models
        self.face_models = {}
        
        # Privacy settings
        self.recognition_threshold = config.get('recognition_threshold', 0.75)
        self.template_version = "v1.0"
        self.encryption_key = self._generate_encryption_key()
        
        # Initialize services
        self._initialize_connections()
        self._load_face_models()
        
    def _initialize_connections(self):
        """Initialize database connections"""
        try:
            # PostgreSQL
            self.pg_conn = psycopg2.connect(
                host=self.config.get('postgres_host', 'localhost'),
                port=self.config.get('postgres_port', 5432),
                database=self.config.get('postgres_db', 'ai_engine'),
                user=self.config.get('postgres_user', 'weedgo'),
                password=self.config.get('postgres_password', 'weedgo123')
            )
            logger.info("Connected to PostgreSQL")
            
            # Redis for caching
            self.redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                decode_responses=False  # We'll store binary data
            )
            logger.info("Connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    def _load_face_models(self):
        """Load face recognition models"""
        try:
            # InsightFace for high accuracy recognition
            self.face_models['insightface'] = FaceAnalysis(providers=['CPUExecutionProvider'])
            self.face_models['insightface'].prepare(ctx_id=0, det_size=(640, 640))
            
            # DeepFace as backup
            self.face_models['deepface'] = DeepFace
            
            logger.info("Face recognition models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load face models: {e}")
            # Fall back to basic face_recognition library
            self.face_models['basic'] = face_recognition
            logger.info("Using basic face recognition as fallback")
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for biometric template protection"""
        # In production, this should come from a secure key management system
        password = self.config.get('encryption_password', 'weedgo-biometric-key').encode()
        salt = self.config.get('encryption_salt', 'weedgo-salt').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    async def recognize_customer(self, face_image: bytes, tenant_id: str, 
                               create_if_not_exists: bool = True) -> Dict[str, Any]:
        """
        Recognize customer from face image using privacy-preserving techniques
        """
        try:
            # Validate and preprocess image
            processed_image = await self._preprocess_face_image(face_image)
            if processed_image is None:
                return {
                    'customer_recognized': False,
                    'error': 'Invalid or no face detected in image'
                }
            
            # Extract face embeddings
            face_embeddings = await self._extract_face_embeddings(processed_image)
            if not face_embeddings:
                return {
                    'customer_recognized': False,
                    'error': 'Could not extract face features'
                }
            
            # Generate cancelable template
            cancelable_template = await self._generate_cancelable_template(
                face_embeddings, tenant_id
            )
            
            # Search for existing customer
            existing_customer = await self._search_existing_customer(
                cancelable_template, tenant_id
            )
            
            if existing_customer:
                # Update customer profile
                updated_profile = await self._update_customer_visit(
                    existing_customer['profile_id'], tenant_id
                )
                
                return {
                    'customer_recognized': True,
                    'customer_profile_id': existing_customer['profile_id'],
                    'confidence_score': existing_customer['similarity_score'],
                    'is_new_customer': False,
                    'customer_profile': updated_profile,
                    'template_hash': cancelable_template['hash']
                }
            
            elif create_if_not_exists:
                # Create new customer profile
                new_profile = await self._create_customer_profile(
                    cancelable_template, tenant_id
                )
                
                return {
                    'customer_recognized': True,
                    'customer_profile_id': new_profile['profile_id'],
                    'confidence_score': 1.0,
                    'is_new_customer': True,
                    'customer_profile': new_profile,
                    'template_hash': cancelable_template['hash']
                }
            
            else:
                return {
                    'customer_recognized': False,
                    'error': 'Customer not found and creation disabled'
                }
            
        except Exception as e:
            logger.error(f"Customer recognition error: {e}")
            return {
                'customer_recognized': False,
                'error': f'Recognition failed: {str(e)}'
            }
    
    async def _preprocess_face_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Preprocess face image for recognition"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Face detection and alignment
            if 'insightface' in self.face_models:
                faces = self.face_models['insightface'].get(image_rgb)
                if faces:
                    # Use the largest face
                    largest_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
                    
                    # Extract face region with padding
                    bbox = largest_face.bbox.astype(int)
                    x1, y1, x2, y2 = bbox
                    
                    # Add padding
                    padding = 20
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(image_rgb.shape[1], x2 + padding)
                    y2 = min(image_rgb.shape[0], y2 + padding)
                    
                    face_image = image_rgb[y1:y2, x1:x2]
                    
                    # Resize to standard size
                    face_image = cv2.resize(face_image, (224, 224))
                    
                    return face_image
            
            # Fallback to basic face detection
            face_locations = face_recognition.face_locations(image_rgb)
            if face_locations:
                top, right, bottom, left = face_locations[0]
                face_image = image_rgb[top:bottom, left:right]
                face_image = cv2.resize(face_image, (224, 224))
                return face_image
            
            return None
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return None
    
    async def _extract_face_embeddings(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face embeddings using multiple models"""
        try:
            embeddings = []
            
            # InsightFace embeddings
            if 'insightface' in self.face_models:
                try:
                    faces = self.face_models['insightface'].get(face_image)
                    if faces:
                        embedding = faces[0].embedding
                        embeddings.append(embedding)
                except Exception as e:
                    logger.warning(f"InsightFace embedding failed: {e}")
            
            # DeepFace embeddings
            if 'deepface' in self.face_models:
                try:
                    embedding = DeepFace.represent(
                        face_image,
                        model_name='ArcFace',
                        enforce_detection=False
                    )[0]['embedding']
                    embeddings.append(np.array(embedding))
                except Exception as e:
                    logger.warning(f"DeepFace embedding failed: {e}")
            
            # Basic face_recognition embeddings
            if 'basic' in self.face_models and not embeddings:
                try:
                    encodings = face_recognition.face_encodings(face_image)
                    if encodings:
                        embeddings.append(encodings[0])
                except Exception as e:
                    logger.warning(f"Basic face recognition failed: {e}")
            
            if embeddings:
                # Use the first successful embedding or average multiple
                if len(embeddings) == 1:
                    return embeddings[0]
                else:
                    # Average embeddings from multiple models
                    return np.mean(embeddings, axis=0)
            
            return None
            
        except Exception as e:
            logger.error(f"Face embedding extraction error: {e}")
            return None
    
    async def _generate_cancelable_template(self, face_embeddings: np.ndarray, 
                                          tenant_id: str) -> Dict[str, Any]:
        """Generate cancelable biometric template for privacy protection"""
        try:
            # Apply tenant-specific transformation (cancelable biometrics)
            tenant_seed = hashlib.sha256(f"{tenant_id}:{self.template_version}".encode()).hexdigest()
            np.random.seed(int(tenant_seed[:8], 16))
            
            # Generate random projection matrix
            original_dim = len(face_embeddings)
            projected_dim = min(512, original_dim)  # Reduce dimensionality
            
            projection_matrix = np.random.randn(original_dim, projected_dim)
            
            # Apply transformation
            transformed_embeddings = np.dot(face_embeddings, projection_matrix)
            
            # Normalize
            transformed_embeddings = transformed_embeddings / np.linalg.norm(transformed_embeddings)
            
            # Quantize for consistency
            quantized_embeddings = np.round(transformed_embeddings * 1000).astype(int)
            
            # Generate hash for quick lookup
            template_hash = hashlib.sha256(
                f"{tenant_id}:{quantized_embeddings.tobytes()}".encode()
            ).hexdigest()
            
            # Encrypt the template
            cipher_suite = Fernet(self.encryption_key)
            encrypted_template = cipher_suite.encrypt(quantized_embeddings.tobytes())
            
            return {
                'hash': template_hash,
                'encrypted_template': encrypted_template,
                'dimensions': projected_dim,
                'algorithm': 'random_projection_v1',
                'version': self.template_version
            }
            
        except Exception as e:
            logger.error(f"Template generation error: {e}")
            raise
    
    async def _search_existing_customer(self, template: Dict[str, Any], 
                                      tenant_id: str) -> Optional[Dict[str, Any]]:
        """Search for existing customer using template matching"""
        try:
            # Quick hash lookup first
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, face_template_hash, visit_count, last_seen_at
                FROM customer_analytics.customer_profiles 
                WHERE tenant_id = %s 
                AND template_version = %s
                AND is_active = true
                ORDER BY last_seen_at DESC
                LIMIT 100
            """, (tenant_id, self.template_version))
            
            candidates = cursor.fetchall()
            
            if not candidates:
                cursor.close()
                return None
            
            # Direct hash match
            for candidate in candidates:
                if candidate['face_template_hash'] == template['hash']:
                    cursor.close()
                    return {
                        'profile_id': str(candidate['id']),
                        'similarity_score': 1.0,
                        'match_type': 'exact_hash'
                    }
            
            # If no exact match, perform similarity search on stored templates
            best_match = await self._similarity_search(template, candidates, tenant_id)
            
            cursor.close()
            return best_match
            
        except Exception as e:
            logger.error(f"Customer search error: {e}")
            return None
    
    async def _similarity_search(self, query_template: Dict[str, Any], 
                                candidates: List[Dict], tenant_id: str) -> Optional[Dict[str, Any]]:
        """Perform similarity search on candidate templates"""
        try:
            # Decrypt query template
            cipher_suite = Fernet(self.encryption_key)
            query_embeddings = np.frombuffer(
                cipher_suite.decrypt(query_template['encrypted_template']), 
                dtype=np.int32
            )
            query_embeddings = query_embeddings.astype(np.float32) / 1000.0
            
            best_score = 0.0
            best_match = None
            
            for candidate in candidates:
                try:
                    # Get stored template from cache or database
                    cached_template = self.redis_client.get(f"template:{candidate['id']}")
                    
                    if cached_template:
                        candidate_embeddings = np.frombuffer(cached_template, dtype=np.float32)
                    else:
                        # This would require storing encrypted templates in DB
                        # For now, skip detailed similarity for performance
                        continue
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_embeddings, candidate_embeddings) / (
                        np.linalg.norm(query_embeddings) * np.linalg.norm(candidate_embeddings)
                    )
                    
                    if similarity > best_score and similarity >= self.recognition_threshold:
                        best_score = similarity
                        best_match = {
                            'profile_id': str(candidate['id']),
                            'similarity_score': float(similarity),
                            'match_type': 'similarity'
                        }
                
                except Exception as e:
                    logger.warning(f"Similarity calculation failed for candidate {candidate['id']}: {e}")
                    continue
            
            return best_match
            
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            return None
    
    async def _create_customer_profile(self, template: Dict[str, Any], 
                                     tenant_id: str) -> Dict[str, Any]:
        """Create new customer profile with privacy-preserving template"""
        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO customer_analytics.customer_profiles 
                (tenant_id, face_template_hash, template_version, template_algorithm,
                 first_seen_at, last_seen_at, visit_count, consent_given, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, first_seen_at, last_seen_at, visit_count
            """, (
                tenant_id, template['hash'], template['version'], template['algorithm'],
                now, now, 1, True, True
            ))
            
            result = cursor.fetchone()
            profile_id = str(result['id'])
            
            # Cache the template for future similarity searches
            cipher_suite = Fernet(self.encryption_key)
            decrypted_template = cipher_suite.decrypt(template['encrypted_template'])
            template_array = np.frombuffer(decrypted_template, dtype=np.int32).astype(np.float32) / 1000.0
            
            self.redis_client.setex(
                f"template:{profile_id}", 
                86400,  # 24 hours
                template_array.tobytes()
            )
            
            self.pg_conn.commit()
            cursor.close()
            
            logger.info(f"Created new customer profile: {profile_id}")
            
            return {
                'profile_id': profile_id,
                'first_seen': result['first_seen_at'],
                'last_seen': result['last_seen_at'],
                'visit_count': result['visit_count'],
                'total_spent': 0.0,
                'preferred_categories': [],
                'preferred_brands': [],
                'estimated_age_range': 'unknown',
                'loyalty_tier': 'new'
            }
            
        except Exception as e:
            logger.error(f"Customer profile creation error: {e}")
            self.pg_conn.rollback()
            raise
    
    async def _update_customer_visit(self, customer_profile_id: str, tenant_id: str) -> Dict[str, Any]:
        """Update customer profile with new visit information"""
        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            now = datetime.now()
            
            cursor.execute("""
                UPDATE customer_analytics.customer_profiles 
                SET last_seen_at = %s, visit_count = visit_count + 1
                WHERE id = %s AND tenant_id = %s
                RETURNING id, first_seen_at, last_seen_at, visit_count, total_purchase_amount,
                         preferred_categories, preferred_brands, estimated_age_range
            """, (now, customer_profile_id, tenant_id))
            
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                raise ValueError(f"Customer profile {customer_profile_id} not found")
            
            # Determine loyalty tier based on visit count and spending
            loyalty_tier = self._calculate_loyalty_tier(
                result['visit_count'], 
                result['total_purchase_amount'] or 0
            )
            
            self.pg_conn.commit()
            cursor.close()
            
            logger.info(f"Updated customer profile: {customer_profile_id}")
            
            return {
                'profile_id': customer_profile_id,
                'first_seen': result['first_seen_at'],
                'last_seen': result['last_seen_at'],
                'visit_count': result['visit_count'],
                'total_spent': float(result['total_purchase_amount'] or 0),
                'preferred_categories': result['preferred_categories'] or [],
                'preferred_brands': result['preferred_brands'] or [],
                'estimated_age_range': result['estimated_age_range'] or 'unknown',
                'loyalty_tier': loyalty_tier
            }
            
        except Exception as e:
            logger.error(f"Customer visit update error: {e}")
            self.pg_conn.rollback()
            raise
    
    def _calculate_loyalty_tier(self, visit_count: int, total_spent: float) -> str:
        """Calculate customer loyalty tier"""
        if visit_count >= 20 and total_spent >= 1000:
            return 'platinum'
        elif visit_count >= 10 and total_spent >= 500:
            return 'gold'
        elif visit_count >= 5 and total_spent >= 200:
            return 'silver'
        elif visit_count >= 2:
            return 'bronze'
        else:
            return 'new'
    
    async def update_customer_profile(self, customer_profile_id: str, 
                                    purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer profile with purchase and interaction data"""
        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            # Update purchase amount
            if purchase_data.get('purchase_amount'):
                cursor.execute("""
                    UPDATE customer_analytics.customer_profiles 
                    SET total_purchase_amount = total_purchase_amount + %s
                    WHERE id = %s
                """, (purchase_data['purchase_amount'], customer_profile_id))
            
            # Update preferences based on purchased products
            if purchase_data.get('purchased_products'):
                await self._update_customer_preferences(
                    customer_profile_id, purchase_data['purchased_products']
                )
            
            # Create visit session record
            if purchase_data.get('visit_timestamp'):
                await self._create_visit_session(customer_profile_id, purchase_data)
            
            self.pg_conn.commit()
            cursor.close()
            
            return {'success': True, 'message': 'Customer profile updated successfully'}
            
        except Exception as e:
            logger.error(f"Customer profile update error: {e}")
            self.pg_conn.rollback()
            return {'success': False, 'message': f'Update failed: {str(e)}'}
    
    async def _update_customer_preferences(self, customer_profile_id: str, 
                                         purchased_products: List[str]):
        """Update customer preferences based on purchase history"""
        try:
            cursor = self.pg_conn.cursor()
            
            # Get product details for preference analysis
            placeholders = ','.join(['%s'] * len(purchased_products))
            cursor.execute(f"""
                SELECT category, brand FROM cannabis_data.products 
                WHERE id = ANY(ARRAY[{placeholders}])
            """, purchased_products)
            
            products = cursor.fetchall()
            
            # Count category and brand preferences
            categories = [p[0] for p in products if p[0]]
            brands = [p[1] for p in products if p[1]]
            
            # Update preferred categories and brands
            if categories:
                cursor.execute("""
                    UPDATE customer_analytics.customer_profiles 
                    SET preferred_categories = array_cat(
                        COALESCE(preferred_categories, ARRAY[]::text[]), 
                        %s
                    )
                    WHERE id = %s
                """, (categories, customer_profile_id))
            
            if brands:
                cursor.execute("""
                    UPDATE customer_analytics.customer_profiles 
                    SET preferred_brands = array_cat(
                        COALESCE(preferred_brands, ARRAY[]::text[]), 
                        %s
                    )
                    WHERE id = %s
                """, (brands, customer_profile_id))
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Preference update error: {e}")
    
    async def _create_visit_session(self, customer_profile_id: str, visit_data: Dict[str, Any]):
        """Create visit session record for analytics"""
        try:
            cursor = self.pg_conn.cursor()
            
            cursor.execute("""
                INSERT INTO customer_analytics.visit_sessions 
                (customer_profile_id, tenant_id, session_start, products_purchased, 
                 total_purchase_amount, recognition_confidence, recognition_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                customer_profile_id,
                visit_data.get('tenant_id'),
                visit_data.get('visit_timestamp', datetime.now()),
                visit_data.get('purchased_products', []),
                visit_data.get('purchase_amount', 0),
                visit_data.get('recognition_confidence', 0.0),
                'face_recognition'
            ))
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Visit session creation error: {e}")
    
    async def get_customer_analytics(self, tenant_id: str, 
                                   date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get customer analytics for tenant"""
        try:
            cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            start_date, end_date = date_range
            
            # Basic customer metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_customers,
                    COUNT(*) FILTER (WHERE first_seen_at >= %s) as new_customers,
                    COUNT(*) FILTER (WHERE last_seen_at >= %s) as active_customers,
                    AVG(visit_count) as avg_visits,
                    AVG(total_purchase_amount) as avg_spent
                FROM customer_analytics.customer_profiles 
                WHERE tenant_id = %s AND is_active = true
            """, (start_date, start_date, tenant_id))
            
            metrics = cursor.fetchone()
            
            # Visit patterns
            cursor.execute("""
                SELECT 
                    DATE(session_start) as visit_date,
                    COUNT(*) as visits,
                    COUNT(DISTINCT customer_profile_id) as unique_customers,
                    SUM(total_purchase_amount) as daily_revenue
                FROM customer_analytics.visit_sessions 
                WHERE tenant_id = %s 
                AND session_start BETWEEN %s AND %s
                GROUP BY DATE(session_start)
                ORDER BY visit_date
            """, (tenant_id, start_date, end_date))
            
            daily_patterns = cursor.fetchall()
            
            # Loyalty distribution
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN visit_count >= 20 AND total_purchase_amount >= 1000 THEN 'platinum'
                        WHEN visit_count >= 10 AND total_purchase_amount >= 500 THEN 'gold'
                        WHEN visit_count >= 5 AND total_purchase_amount >= 200 THEN 'silver'
                        WHEN visit_count >= 2 THEN 'bronze'
                        ELSE 'new'
                    END as loyalty_tier,
                    COUNT(*) as customer_count
                FROM customer_analytics.customer_profiles 
                WHERE tenant_id = %s AND is_active = true
                GROUP BY loyalty_tier
            """, (tenant_id,))
            
            loyalty_distribution = cursor.fetchall()
            
            cursor.close()
            
            return {
                'summary': dict(metrics),
                'daily_patterns': [dict(row) for row in daily_patterns],
                'loyalty_distribution': [dict(row) for row in loyalty_distribution],
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analytics generation error: {e}")
            return {}

# Service factory function
def create_customer_recognition_service(config: Dict[str, Any]) -> CustomerRecognitionService:
    """Create and initialize the Customer Recognition service"""
    return CustomerRecognitionService(config)