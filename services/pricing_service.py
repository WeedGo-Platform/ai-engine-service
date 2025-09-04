"""
Pricing Service - Dynamic pricing optimization
Implements strategy pattern for different pricing strategies
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from services.interfaces import IPricingService
from repositories.product_repository import ProductRepository
from repositories.transaction_repository import TransactionRepository
from utils.cache import CacheManager

logger = logging.getLogger(__name__)

class PricingStrategy(Enum):
    """Available pricing strategies"""
    STANDARD = "standard"
    VOLUME_DISCOUNT = "volume_discount"
    TIME_BASED = "time_based"
    CUSTOMER_LOYALTY = "customer_loyalty"
    DYNAMIC_DEMAND = "dynamic_demand"

class PricingService(IPricingService):
    """
    Dynamic pricing optimization service
    Considers inventory, demand, time, and customer type
    """
    
    def __init__(
        self,
        product_repo: Optional[ProductRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
        cache: Optional[CacheManager] = None
    ):
        """Initialize pricing service"""
        self.product_repo = product_repo or ProductRepository()
        self.transaction_repo = transaction_repo or TransactionRepository()
        self.cache = cache or CacheManager()
        
        # Pricing configuration
        self.volume_tiers = [
            {"min": 0, "max": 3.5, "discount": 0},
            {"min": 3.5, "max": 7, "discount": 0.05},
            {"min": 7, "max": 14, "discount": 0.10},
            {"min": 14, "max": 28, "discount": 0.15},
            {"min": 28, "max": float("inf"), "discount": 0.20}
        ]
        
        self.customer_discounts = {
            "regular": 0,
            "member": 0.05,
            "vip": 0.10,
            "wholesale": 0.15
        }
        
        self.time_discounts = {
            "happy_hour": 0.10,  # 4-6 PM
            "late_night": 0.15,  # After 9 PM
            "early_bird": 0.05,  # Before 10 AM
        }
    
    async def calculate(
        self,
        product_id: str,
        quantity: float,
        customer_type: str = "regular"
    ) -> Dict[str, Any]:
        """
        Calculate dynamic pricing for product
        
        Args:
            product_id: Product identifier
            quantity: Quantity in grams
            customer_type: Type of customer (regular, member, vip, wholesale)
        
        Returns:
            Pricing details with optimized price
        """
        try:
            # Get product info
            product = await self.product_repo.get_by_id(product_id)
            
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            base_price = product.get("unit_price", 0)
            
            # Calculate various discounts
            discounts = {}
            
            # Volume discount
            volume_discount = self._calculate_volume_discount(quantity)
            if volume_discount > 0:
                discounts["volume"] = volume_discount
            
            # Customer type discount
            customer_discount = self.customer_discounts.get(customer_type, 0)
            if customer_discount > 0:
                discounts["loyalty"] = customer_discount
            
            # Time-based discount
            time_discount = self._calculate_time_discount()
            if time_discount > 0:
                discounts["time"] = time_discount
            
            # Demand-based pricing adjustment
            demand_adjustment = await self._calculate_demand_adjustment(product_id)
            if demand_adjustment != 0:
                discounts["demand"] = demand_adjustment
            
            # Calculate final price
            total_discount = sum(discounts.values())
            
            # Cap total discount at 30%
            total_discount = min(total_discount, 0.30)
            
            final_price_per_gram = base_price * (1 - total_discount)
            total_price = final_price_per_gram * quantity
            
            # Calculate savings
            original_total = base_price * quantity
            savings = original_total - total_price
            
            return {
                "product_id": product_id,
                "product_name": product["product_name"],
                "quantity_grams": quantity,
                "base_price_per_gram": base_price,
                "final_price_per_gram": round(final_price_per_gram, 2),
                "total_price": round(total_price, 2),
                "original_price": round(original_total, 2),
                "savings": round(savings, 2),
                "discount_percentage": round(total_discount * 100, 1),
                "discounts_applied": discounts,
                "price_valid_until": (
                    datetime.now() + timedelta(minutes=15)
                ).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Pricing calculation error: {str(e)}", exc_info=True)
            raise
    
    async def get_recommendations(
        self,
        customer_id: str,
        product_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get pricing recommendations for multiple products
        
        Args:
            customer_id: Customer identifier
            product_ids: List of product IDs
        
        Returns:
            List of pricing recommendations
        """
        recommendations = []
        
        # Get customer type
        customer_type = await self._get_customer_type(customer_id)
        
        for product_id in product_ids:
            try:
                # Calculate prices for different quantities
                quantity_options = [3.5, 7, 14, 28]  # Common quantities
                
                options = []
                for qty in quantity_options:
                    pricing = await self.calculate(
                        product_id=product_id,
                        quantity=qty,
                        customer_type=customer_type
                    )
                    
                    options.append({
                        "quantity": qty,
                        "total_price": pricing["total_price"],
                        "price_per_gram": pricing["final_price_per_gram"],
                        "savings": pricing["savings"]
                    })
                
                # Find best value
                best_value = min(options, key=lambda x: x["price_per_gram"])
                
                recommendations.append({
                    "product_id": product_id,
                    "customer_type": customer_type,
                    "pricing_options": options,
                    "best_value": best_value,
                    "recommendation": self._generate_recommendation(
                        options,
                        best_value
                    )
                })
                
            except Exception as e:
                logger.error(
                    f"Error calculating recommendation for {product_id}: {str(e)}"
                )
                continue
        
        return recommendations
    
    def _calculate_volume_discount(self, quantity: float) -> float:
        """Calculate volume-based discount"""
        for tier in self.volume_tiers:
            if tier["min"] <= quantity < tier["max"]:
                return tier["discount"]
        return 0
    
    def _calculate_time_discount(self) -> float:
        """Calculate time-based discount"""
        now = datetime.now()
        hour = now.hour
        
        # Happy hour: 4-6 PM
        if 16 <= hour < 18:
            return self.time_discounts["happy_hour"]
        
        # Late night: After 9 PM
        elif hour >= 21:
            return self.time_discounts["late_night"]
        
        # Early bird: Before 10 AM
        elif hour < 10:
            return self.time_discounts["early_bird"]
        
        return 0
    
    async def _calculate_demand_adjustment(self, product_id: str) -> float:
        """
        Calculate demand-based price adjustment
        High demand = slight price increase
        Low demand = discount
        """
        try:
            # Check cache first
            cache_key = f"demand:{product_id}"
            cached_adjustment = await self.cache.get(cache_key)
            
            if cached_adjustment is not None:
                return cached_adjustment
            
            # Get recent sales velocity
            velocity = await self.transaction_repo.get_sales_velocity(
                product_id=product_id,
                days=7
            )
            
            # Get inventory level
            inventory = await self.product_repo.get_inventory(product_id)
            
            adjustment = 0
            
            # High velocity + low inventory = price increase
            if velocity > 10 and inventory < 100:
                adjustment = -0.05  # 5% price increase (negative discount)
            
            # Low velocity + high inventory = discount
            elif velocity < 2 and inventory > 500:
                adjustment = 0.10  # 10% discount
            
            # Cache for 1 hour
            await self.cache.set(cache_key, adjustment, ttl=3600)
            
            return adjustment
            
        except Exception as e:
            logger.error(f"Demand calculation error: {str(e)}")
            return 0
    
    async def _get_customer_type(self, customer_id: str) -> str:
        """Get customer type for pricing"""
        # This would connect to customer service in production
        # For now, return based on simple logic
        
        if not customer_id:
            return "regular"
        
        # Check purchase history
        total_purchases = await self.transaction_repo.get_customer_total(
            customer_id
        )
        
        if total_purchases > 10000:
            return "vip"
        elif total_purchases > 5000:
            return "member"
        else:
            return "regular"
    
    def _generate_recommendation(
        self,
        options: List[Dict],
        best_value: Dict
    ) -> str:
        """Generate pricing recommendation text"""
        
        if best_value["quantity"] == 28:
            return "Best value! Buy an ounce for maximum savings"
        elif best_value["quantity"] == 14:
            return "Great deal on half ounce - save more per gram"
        elif best_value["quantity"] == 7:
            return "Popular choice - quarter ounce offers good value"
        else:
            return "Perfect for trying - eighth ounce starter size"