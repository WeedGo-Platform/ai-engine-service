"""
User Preference Service
Analyzes purchase history to learn user preferences
Provides statistical insights for context-aware parameter building
"""
import logging
from typing import Dict, Any, Optional, List
from collections import Counter
import aiohttp

from services.config import USER_PURCHASES_ENDPOINT

logger = logging.getLogger(__name__)


class UserPreferenceService:
    """Analyzes user purchase history to learn preferences"""

    def __init__(self):
        """Initialize user preference service"""
        self.min_purchases_for_confidence = 3  # Minimum purchases to be confident
        self.cache = {}  # Simple in-memory cache

    async def get_user_preferences(self, user_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze user's purchase history and return preferences

        Args:
            user_id: User ID to analyze
            use_cache: Whether to use cached preferences

        Returns:
            Dictionary with:
            - favorite_subcategory: Most frequently purchased subcategory
            - favorite_strain_type: Most frequently purchased strain type
            - typical_thc_range: Average THC range user purchases
            - typical_price_range: Average price range user purchases
            - confidence: Confidence score based on purchase count
            - purchase_count: Total number of purchases analyzed
        """
        try:
            # Check cache first
            if use_cache and user_id in self.cache:
                logger.info(f"Using cached preferences for user {user_id}")
                return self.cache[user_id]

            # Fetch purchase history
            purchases = await self._fetch_purchase_history(user_id)

            if not purchases:
                logger.info(f"No purchase history found for user {user_id}")
                return self._empty_preferences()

            # Analyze purchases
            preferences = self._analyze_purchases(purchases)
            preferences["user_id"] = user_id

            # Cache results
            self.cache[user_id] = preferences

            logger.info(f"Analyzed {len(purchases)} purchases for user {user_id}, confidence={preferences['confidence']:.2f}")
            return preferences

        except Exception as e:
            logger.error(f"Failed to get user preferences: {str(e)}", exc_info=True)
            return self._empty_preferences()

    def _analyze_purchases(self, purchases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform statistical analysis on purchase history

        Args:
            purchases: List of purchase records

        Returns:
            Analyzed preferences dictionary
        """
        purchase_count = len(purchases)

        # Extract fields from purchases
        subcategories = []
        strain_types = []
        thc_values = []
        cbd_values = []
        prices = []

        for purchase in purchases:
            # Extract subcategory
            if purchase.get("subcategory"):
                subcategories.append(purchase["subcategory"])

            # Extract strain type
            if purchase.get("strain_type"):
                strain_types.append(purchase["strain_type"])

            # Extract THC
            if purchase.get("thc_percentage") is not None:
                thc_values.append(float(purchase["thc_percentage"]))

            # Extract CBD
            if purchase.get("cbd_percentage") is not None:
                cbd_values.append(float(purchase["cbd_percentage"]))

            # Extract price
            if purchase.get("price") is not None:
                prices.append(float(purchase["price"]))

        # Analyze most frequent subcategory
        favorite_subcategory = None
        subcategory_confidence = 0.0
        if subcategories:
            subcategory_counts = Counter(subcategories)
            favorite_subcategory = subcategory_counts.most_common(1)[0][0]
            subcategory_confidence = subcategory_counts[favorite_subcategory] / len(subcategories)

        # Analyze most frequent strain type
        favorite_strain_type = None
        strain_confidence = 0.0
        if strain_types:
            strain_counts = Counter(strain_types)
            favorite_strain_type = strain_counts.most_common(1)[0][0]
            strain_confidence = strain_counts[favorite_strain_type] / len(strain_types)

        # Analyze typical THC range
        typical_thc_range = None
        if thc_values:
            avg_thc = sum(thc_values) / len(thc_values)
            std_thc = self._calculate_std(thc_values, avg_thc)
            typical_thc_range = {
                "min": max(0, avg_thc - std_thc),
                "max": min(100, avg_thc + std_thc),
                "average": avg_thc
            }

        # Analyze typical CBD range
        typical_cbd_range = None
        if cbd_values:
            avg_cbd = sum(cbd_values) / len(cbd_values)
            std_cbd = self._calculate_std(cbd_values, avg_cbd)
            typical_cbd_range = {
                "min": max(0, avg_cbd - std_cbd),
                "max": min(100, avg_cbd + std_cbd),
                "average": avg_cbd
            }

        # Analyze typical price range
        typical_price_range = None
        if prices:
            avg_price = sum(prices) / len(prices)
            std_price = self._calculate_std(prices, avg_price)
            typical_price_range = {
                "min": max(0, avg_price - std_price),
                "max": avg_price + std_price,
                "average": avg_price
            }

        # Calculate overall confidence
        # Based on purchase count and consistency
        base_confidence = min(1.0, purchase_count / self.min_purchases_for_confidence)
        consistency_score = (subcategory_confidence + strain_confidence) / 2 if strain_types else subcategory_confidence
        overall_confidence = base_confidence * consistency_score

        return {
            "favorite_subcategory": favorite_subcategory,
            "favorite_strain_type": favorite_strain_type,
            "typical_thc_range": typical_thc_range,
            "typical_cbd_range": typical_cbd_range,
            "typical_price_range": typical_price_range,
            "confidence": overall_confidence,
            "purchase_count": purchase_count,
            "subcategory_confidence": subcategory_confidence,
            "strain_confidence": strain_confidence
        }

    def _calculate_std(self, values: List[float], mean: float) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0

        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    async def _fetch_purchase_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch user's purchase history from API

        Args:
            user_id: User ID

        Returns:
            List of purchase records
        """
        try:
            url = USER_PURCHASES_ENDPOINT.format(user_id=user_id)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Adjust based on actual API response format
                        if isinstance(data, dict) and 'purchases' in data:
                            return data['purchases']
                        elif isinstance(data, list):
                            return data
                        else:
                            return []
                    elif resp.status == 404:
                        # User not found or no purchases
                        return []
                    else:
                        logger.warning(f"Failed to fetch purchase history: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching purchase history: {str(e)}")
            return []

    def _empty_preferences(self) -> Dict[str, Any]:
        """Return empty preferences structure"""
        return {
            "favorite_subcategory": None,
            "favorite_strain_type": None,
            "typical_thc_range": None,
            "typical_cbd_range": None,
            "typical_price_range": None,
            "confidence": 0.0,
            "purchase_count": 0,
            "subcategory_confidence": 0.0,
            "strain_confidence": 0.0
        }

    def clear_cache(self, user_id: Optional[str] = None):
        """
        Clear preference cache

        Args:
            user_id: If provided, clear only this user's cache, otherwise clear all
        """
        if user_id:
            if user_id in self.cache:
                del self.cache[user_id]
                logger.info(f"Cleared cache for user {user_id}")
        else:
            self.cache.clear()
            logger.info("Cleared all preference cache")
