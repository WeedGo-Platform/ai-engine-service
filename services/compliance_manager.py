#!/usr/bin/env python3
"""
Compliance Manager for Cannabis Sales
Implements age verification, purchase limits, and regulatory compliance
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, date, timedelta
from enum import Enum
import hashlib
import jwt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ComplianceStatus(Enum):
    """Compliance check status"""
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    EXPIRED = "expired"
    BLOCKED = "blocked"

class VerificationMethod(Enum):
    """Age verification methods"""
    GOVERNMENT_ID = "government_id"
    CREDIT_CARD = "credit_card"
    BIOMETRIC = "biometric"
    MANUAL = "manual"
    THIRD_PARTY = "third_party"

class ComplianceRules:
    """Regulatory compliance rules for Ontario, Canada"""
    
    # Legal age requirements
    MIN_AGE = 19  # Ontario legal age
    
    # Purchase limits (grams)
    MAX_DRIED_FLOWER = 30  # 30g dried flower equivalent
    MAX_EDIBLES_MG = 1000  # 1000mg THC for edibles
    MAX_EXTRACTS_MG = 2000  # 2000mg THC for extracts
    MAX_TOPICALS_MG = 1000  # 1000mg THC for topicals
    
    # Transaction limits
    MAX_DAILY_TRANSACTIONS = 5
    MAX_DAILY_SPEND = 500.00  # CAD
    
    # Product restrictions
    RESTRICTED_HOURS = {
        'start': 23,  # 11 PM
        'end': 9      # 9 AM
    }
    
    # Equivalency factors (to dried flower grams)
    EQUIVALENCY = {
        'flower': 1.0,
        'pre_rolls': 1.0,
        'edibles': 0.25,  # 1g edibles = 0.25g flower
        'extracts': 0.25,
        'topicals': 0.25,
        'seeds': 1.0,
        'accessories': 0.0  # No limit
    }

class CustomerVerification(BaseModel):
    """Customer verification record"""
    customer_id: str
    birth_date: date
    verification_method: VerificationMethod
    verified_at: datetime
    expires_at: datetime
    government_id_hash: Optional[str] = None
    status: ComplianceStatus = ComplianceStatus.PENDING
    
class PurchaseRecord(BaseModel):
    """Track customer purchases for compliance"""
    customer_id: str
    transaction_id: str
    product_id: int
    product_category: str
    quantity: float
    thc_mg: float
    cbd_mg: float
    price: float
    timestamp: datetime
    dried_flower_equivalent: float

class ComplianceManager:
    """
    Comprehensive compliance management system
    Ensures all sales meet regulatory requirements
    """
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
        self.verification_cache = {}  # In-memory cache for session
        self.purchase_history = {}  # Track daily purchases
        self.blocked_customers = set()  # Customers who failed compliance
        
    def get_verification(self, customer_id: str) -> Optional[CustomerVerification]:
        """
        Get verification from cache or database
        This ensures persistence across server restarts
        """
        # Check cache first
        if customer_id in self.verification_cache:
            return self.verification_cache[customer_id]
        
        # Not in cache, check database
        if self.db_conn:
            try:
                cur = self.db_conn.cursor()
                cur.execute("""
                    SELECT customer_id, birth_date, method, verified_at, 
                           expires_at, status, government_id_hash
                    FROM customer_verifications
                    WHERE customer_id = %s
                    AND status = 'verified'
                    AND expires_at > NOW()
                """, (customer_id,))
                
                row = cur.fetchone()
                if row:
                    # Reconstruct verification object
                    verification = CustomerVerification(
                        customer_id=row['customer_id'],
                        birth_date=row['birth_date'],
                        verification_method=VerificationMethod[row['method'].upper()],
                        verified_at=row['verified_at'],
                        expires_at=row['expires_at'],
                        status=ComplianceStatus[row['status'].upper()],
                        government_id_hash=row.get('government_id_hash')
                    )
                    
                    # Cache it for this session
                    self.verification_cache[customer_id] = verification
                    logger.info(f"Loaded verification for {customer_id} from database")
                    return verification
                    
            except Exception as e:
                logger.error(f"Failed to load verification from database: {e}")
        
        return None
        
    def verify_age(self, birth_date: date) -> Tuple[bool, str]:
        """
        Verify customer meets minimum age requirement
        Returns (is_valid, message)
        """
        today = date.today()
        age = today.year - birth_date.year
        
        # Adjust for birthday not yet occurred this year
        if today.month < birth_date.month or \
           (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        if age >= ComplianceRules.MIN_AGE:
            return True, f"Age verified: {age} years old"
        else:
            return False, f"Must be {ComplianceRules.MIN_AGE} or older. Current age: {age}"
    
    def verify_customer(self, customer_id: str, birth_date: date, 
                        method: VerificationMethod = VerificationMethod.MANUAL,
                        government_id: Optional[str] = None) -> ComplianceStatus:
        """
        Perform comprehensive customer verification
        """
        # Check if customer is blocked
        if customer_id in self.blocked_customers:
            logger.warning(f"Blocked customer attempted access: {customer_id}")
            return ComplianceStatus.BLOCKED
        
        # Check age
        is_valid, message = self.verify_age(birth_date)
        if not is_valid:
            logger.warning(f"Age verification failed for {customer_id}: {message}")
            self.blocked_customers.add(customer_id)
            return ComplianceStatus.FAILED
        
        # Create verification record
        verification = CustomerVerification(
            customer_id=customer_id,
            birth_date=birth_date,
            verification_method=method,
            verified_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),  # Valid for 1 year
            status=ComplianceStatus.VERIFIED
        )
        
        # Hash government ID if provided
        if government_id:
            verification.government_id_hash = hashlib.sha256(
                government_id.encode()
            ).hexdigest()
        
        # Cache verification
        self.verification_cache[customer_id] = verification
        
        # Store in database if available
        if self.db_conn:
            self._store_verification(verification)
        
        logger.info(f"Customer {customer_id} verified via {method.value}")
        return ComplianceStatus.VERIFIED
    
    def check_purchase_limits(self, customer_id: str, 
                             products: List[Dict]) -> Tuple[bool, str]:
        """
        Check if purchase complies with daily limits
        Returns (is_compliant, message)
        """
        # Get today's purchases
        today = date.today()
        daily_purchases = self._get_daily_purchases(customer_id, today)
        
        # Calculate current totals
        current_flower_equiv = sum(p.dried_flower_equivalent for p in daily_purchases)
        current_spend = sum(p.price for p in daily_purchases)
        current_transactions = len(set(p.transaction_id for p in daily_purchases))
        
        # Calculate new purchase totals
        new_flower_equiv = 0
        new_spend = 0
        
        for product in products:
            category = product.get('category', 'flower').lower()
            quantity = product.get('quantity', 1)
            price = product.get('price', 0)
            
            # Calculate dried flower equivalent
            equivalency = ComplianceRules.EQUIVALENCY.get(category, 1.0)
            new_flower_equiv += quantity * equivalency
            new_spend += price * quantity
        
        # Check limits
        total_flower = current_flower_equiv + new_flower_equiv
        total_spend = current_spend + new_spend
        total_transactions = current_transactions + 1
        
        # Validate against limits
        if total_flower > ComplianceRules.MAX_DRIED_FLOWER:
            return False, f"Exceeds daily limit of {ComplianceRules.MAX_DRIED_FLOWER}g dried flower equivalent"
        
        if total_spend > ComplianceRules.MAX_DAILY_SPEND:
            return False, f"Exceeds daily spending limit of ${ComplianceRules.MAX_DAILY_SPEND}"
        
        if total_transactions > ComplianceRules.MAX_DAILY_TRANSACTIONS:
            return False, f"Exceeds daily transaction limit of {ComplianceRules.MAX_DAILY_TRANSACTIONS}"
        
        return True, "Purchase within compliance limits"
    
    def check_time_restrictions(self) -> Tuple[bool, str]:
        """
        Check if current time allows cannabis sales
        """
        current_hour = datetime.now().hour
        
        if (current_hour >= ComplianceRules.RESTRICTED_HOURS['start'] or 
            current_hour < ComplianceRules.RESTRICTED_HOURS['end']):
            return False, f"Sales restricted between {ComplianceRules.RESTRICTED_HOURS['start']}:00 and {ComplianceRules.RESTRICTED_HOURS['end']}:00"
        
        return True, "Sales permitted at this time"
    
    def validate_product_compliance(self, product: Dict) -> Tuple[bool, List[str]]:
        """
        Validate product meets regulatory requirements
        Returns (is_compliant, list_of_issues)
        """
        issues = []
        
        # Check THC limits for different categories
        category = product.get('category', '').lower()
        thc_mg = product.get('thc_mg', 0)
        
        if category == 'edibles' and thc_mg > 10:  # 10mg per package limit
            issues.append(f"Edibles cannot exceed 10mg THC per package (has {thc_mg}mg)")
        
        if category == 'extracts' and thc_mg > 1000:  # 1000mg per package
            issues.append(f"Extracts cannot exceed 1000mg THC per package (has {thc_mg}mg)")
        
        # Check for required warnings
        if not product.get('health_warning'):
            issues.append("Missing required health warning")
        
        if not product.get('thc_symbol'):
            issues.append("Missing required THC symbol")
        
        # Check packaging compliance
        if product.get('child_appealing', False):
            issues.append("Packaging cannot be appealing to children")
        
        return len(issues) == 0, issues
    
    def generate_compliance_token(self, customer_id: str, 
                                 verification: CustomerVerification) -> str:
        """
        Generate JWT token for verified customer
        """
        payload = {
            'customer_id': customer_id,
            'verified_at': verification.verified_at.isoformat(),
            'expires_at': verification.expires_at.isoformat(),
            'birth_date': verification.birth_date.isoformat(),
            'status': verification.status.value
        }
        
        # In production, use proper secret from environment
        secret = "your-secret-key"  # Should come from environment
        
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token
    
    def verify_compliance_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode compliance token
        """
        try:
            secret = "your-secret-key"  # Should come from environment
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if expires_at < datetime.now():
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    def record_purchase(self, customer_id: str, transaction_id: str, 
                       products: List[Dict]) -> bool:
        """
        Record purchase for compliance tracking
        """
        records = []
        
        for product in products:
            record = PurchaseRecord(
                customer_id=customer_id,
                transaction_id=transaction_id,
                product_id=product['id'],
                product_category=product.get('category', 'flower'),
                quantity=product.get('quantity', 1),
                thc_mg=product.get('thc_mg', 0),
                cbd_mg=product.get('cbd_mg', 0),
                price=product.get('price', 0),
                timestamp=datetime.now(),
                dried_flower_equivalent=self._calculate_flower_equivalent(product)
            )
            records.append(record)
        
        # Store in memory
        if customer_id not in self.purchase_history:
            self.purchase_history[customer_id] = []
        self.purchase_history[customer_id].extend(records)
        
        # Store in database if available
        if self.db_conn:
            self._store_purchase_records(records)
        
        return True
    
    def get_compliance_report(self, customer_id: str) -> Dict:
        """
        Generate compliance report for customer
        """
        today = date.today()
        daily_purchases = self._get_daily_purchases(customer_id, today)
        
        # Calculate totals
        total_flower = sum(p.dried_flower_equivalent for p in daily_purchases)
        total_spend = sum(p.price for p in daily_purchases)
        total_transactions = len(set(p.transaction_id for p in daily_purchases))
        
        # Get verification status
        verification = self.verification_cache.get(customer_id)
        
        return {
            'customer_id': customer_id,
            'date': today.isoformat(),
            'verification_status': verification.status.value if verification else 'unverified',
            'daily_totals': {
                'dried_flower_equivalent_g': round(total_flower, 2),
                'spend_cad': round(total_spend, 2),
                'transactions': total_transactions
            },
            'limits': {
                'max_flower_g': ComplianceRules.MAX_DRIED_FLOWER,
                'max_spend_cad': ComplianceRules.MAX_DAILY_SPEND,
                'max_transactions': ComplianceRules.MAX_DAILY_TRANSACTIONS
            },
            'remaining': {
                'flower_g': round(ComplianceRules.MAX_DRIED_FLOWER - total_flower, 2),
                'spend_cad': round(ComplianceRules.MAX_DAILY_SPEND - total_spend, 2),
                'transactions': ComplianceRules.MAX_DAILY_TRANSACTIONS - total_transactions
            }
        }
    
    def _calculate_flower_equivalent(self, product: Dict) -> float:
        """Calculate dried flower equivalent for product"""
        category = product.get('category', 'flower').lower()
        quantity = product.get('quantity', 1)
        equivalency = ComplianceRules.EQUIVALENCY.get(category, 1.0)
        return quantity * equivalency
    
    def _get_daily_purchases(self, customer_id: str, date: date) -> List[PurchaseRecord]:
        """Get all purchases for customer on given date"""
        if customer_id not in self.purchase_history:
            return []
        
        daily = []
        for record in self.purchase_history[customer_id]:
            if record.timestamp.date() == date:
                daily.append(record)
        
        return daily
    
    def _store_verification(self, verification: CustomerVerification):
        """Store verification in database"""
        if not self.db_conn:
            return
        
        try:
            cur = self.db_conn.cursor()
            cur.execute("""
                INSERT INTO customer_verifications 
                (customer_id, birth_date, method, verified_at, expires_at, status, government_id_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    verified_at = EXCLUDED.verified_at,
                    expires_at = EXCLUDED.expires_at,
                    status = EXCLUDED.status
            """, (
                verification.customer_id,
                verification.birth_date,
                verification.verification_method.value,
                verification.verified_at,
                verification.expires_at,
                verification.status.value,
                verification.government_id_hash
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Failed to store verification: {e}")
    
    def _store_purchase_records(self, records: List[PurchaseRecord]):
        """Store purchase records in database"""
        if not self.db_conn:
            return
        
        try:
            cur = self.db_conn.cursor()
            for record in records:
                cur.execute("""
                    INSERT INTO purchase_records 
                    (customer_id, transaction_id, product_id, category, quantity, 
                     thc_mg, cbd_mg, price, timestamp, dried_flower_equivalent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record.customer_id,
                    record.transaction_id,
                    record.product_id,
                    record.product_category,
                    record.quantity,
                    record.thc_mg,
                    record.cbd_mg,
                    record.price,
                    record.timestamp,
                    record.dried_flower_equivalent
                ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Failed to store purchase records: {e}")

# Middleware for FastAPI
class ComplianceMiddleware:
    """
    FastAPI middleware for compliance checks
    """
    
    def __init__(self, compliance_manager: ComplianceManager):
        self.compliance_manager = compliance_manager
    
    async def __call__(self, request, call_next):
        """
        Check compliance before processing request
        """
        # Check time restrictions for purchase endpoints
        if request.url.path in ['/api/cart', '/api/checkout']:
            is_allowed, message = self.compliance_manager.check_time_restrictions()
            if not is_allowed:
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail=message)
        
        # Check customer verification for protected endpoints
        if request.url.path in ['/api/cart', '/api/checkout', '/api/chat']:
            # Get customer ID from request (would come from JWT in production)
            customer_id = request.headers.get('X-Customer-ID')
            if customer_id:
                verification = self.compliance_manager.verification_cache.get(customer_id)
                if not verification or verification.status != ComplianceStatus.VERIFIED:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=403, 
                        detail="Age verification required"
                    )
        
        response = await call_next(request)
        return response

# Example usage
def test_compliance():
    """Test compliance functionality"""
    manager = ComplianceManager()
    
    # Test age verification
    birth_date = date(2000, 1, 1)  # 24 years old
    is_valid, message = manager.verify_age(birth_date)
    print(f"Age verification: {is_valid} - {message}")
    
    # Test customer verification
    status = manager.verify_customer(
        "customer_123",
        birth_date,
        VerificationMethod.GOVERNMENT_ID,
        "DL123456789"
    )
    print(f"Customer verification: {status.value}")
    
    # Test purchase limits
    products = [
        {'id': 1, 'category': 'flower', 'quantity': 7, 'price': 50},
        {'id': 2, 'category': 'edibles', 'quantity': 2, 'price': 15}
    ]
    is_compliant, message = manager.check_purchase_limits("customer_123", products)
    print(f"Purchase limits: {is_compliant} - {message}")
    
    # Generate compliance report
    report = manager.get_compliance_report("customer_123")
    print(f"Compliance report: {report}")

if __name__ == "__main__":
    test_compliance()