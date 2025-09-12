"""
User Profiling Service
Implements progressive data collection and user profile management
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from ..interfaces import IUserProfiler
from ..models import UserProfile, CustomerProfile
from ...database_connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class UserProfiler(IUserProfiler):
    """
    User profiling service with progressive data collection
    Single Responsibility: Manage user profiles and preferences
    """
    
    def __init__(self, db_manager: Optional[DatabaseConnectionManager] = None, config_path: Optional[str] = None):
        """
        Initialize the user profiler
        
        Args:
            db_manager: Database connection manager
            config_path: Path to configuration file
        """
        self.db_manager = db_manager or DatabaseConnectionManager()
        self.profiles_cache = {}  # In-memory cache for active profiles
        self.config = self._load_config(config_path)
        self.progressive_fields = self._get_progressive_fields()
        logger.info("UserProfiler initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration for user profiling"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "config" / "user_profiling.json"
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "progressive_collection": {
                "enabled": True,
                "stages": {
                    "greeting": ["language", "timezone"],
                    "discovery": ["needs", "experience_level", "customer_type"],
                    "needs_assessment": ["preferred_effects", "medical_conditions", "price_range"],
                    "recommendation": ["preferred_categories", "preferences"],
                    "checkout": ["email", "phone", "delivery_preferences"]
                }
            },
            "profile_classification": {
                "experience_levels": ["beginner", "intermediate", "experienced", "expert"],
                "customer_types": ["medical", "recreational", "both"],
                "price_sensitivity": {
                    "budget": {"min": 0, "max": 50},
                    "moderate": {"min": 50, "max": 150},
                    "premium": {"min": 150, "max": null}
                }
            },
            "data_retention": {
                "profile_ttl_days": 365,
                "anonymize_after_days": 730
            }
        }
    
    def _get_progressive_fields(self) -> Dict[str, List[str]]:
        """Get fields to collect at each stage"""
        if self.config.get("progressive_collection", {}).get("enabled"):
            return self.config["progressive_collection"]["stages"]
        return {}
    
    def create_profile(self, session_id: str, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user profile
        
        Args:
            session_id: Session identifier
            initial_data: Initial profile data
            
        Returns:
            Profile ID
        """
        profile = UserProfile(session_id=session_id)
        
        if initial_data:
            # Set initial data
            for key, value in initial_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
        
        # Store in cache
        self.profiles_cache[session_id] = profile
        
        # Persist to database if available
        if self.db_manager:
            self._persist_profile(profile)
        
        logger.info(f"Created profile {profile.id} for session {session_id}")
        return profile.id
    
    def get_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Profile data or None
        """
        # Check cache first
        if session_id in self.profiles_cache:
            return self.profiles_cache[session_id].to_dict()
        
        # Try loading from database
        if self.db_manager:
            profile_data = self._load_profile_from_db(session_id)
            if profile_data:
                profile = self._deserialize_profile(profile_data)
                self.profiles_cache[session_id] = profile
                return profile.to_dict()
        
        return None
    
    def update_profile(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update user profile with new data
        
        Args:
            session_id: Session identifier
            data: Data to update
            
        Returns:
            Success status
        """
        # Get or create profile
        if session_id not in self.profiles_cache:
            profile_dict = self.get_profile(session_id)
            if not profile_dict:
                self.create_profile(session_id)
        
        profile = self.profiles_cache.get(session_id)
        if not profile:
            return False
        
        # Update fields
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        profile.interaction_count += 1
        
        # Auto-classify customer type if enough data
        self._auto_classify_customer(profile)
        
        # Persist changes
        if self.db_manager:
            self._persist_profile(profile)
        
        logger.debug(f"Updated profile for session {session_id}")
        return True
    
    def collect_data(self, session_id: str, data_type: str, value: Any) -> bool:
        """
        Progressively collect user data
        
        Args:
            session_id: Session identifier
            data_type: Type of data being collected
            value: Data value
            
        Returns:
            Success status
        """
        if session_id not in self.profiles_cache:
            self.create_profile(session_id)
        
        profile = self.profiles_cache[session_id]
        
        # Handle different data types
        if data_type == "needs":
            if value not in profile.needs:
                profile.needs.append(value)
        elif data_type == "preferred_effects":
            if value not in profile.preferred_effects:
                profile.preferred_effects.append(value)
        elif data_type == "medical_conditions":
            if value not in profile.medical_conditions:
                profile.medical_conditions.append(value)
        elif data_type == "preferred_categories":
            if value not in profile.preferred_categories:
                profile.preferred_categories.append(value)
        elif data_type == "preferences":
            profile.preferences.update(value if isinstance(value, dict) else {data_type: value})
        elif hasattr(profile, data_type):
            setattr(profile, data_type, value)
        else:
            # Store in preferences dict
            profile.preferences[data_type] = value
        
        profile.updated_at = datetime.now()
        
        # Persist changes
        if self.db_manager:
            self._persist_profile(profile)
        
        logger.debug(f"Collected {data_type} for session {session_id}")
        return True
    
    def get_preferences(self, session_id: str) -> Dict[str, Any]:
        """
        Get user preferences
        
        Args:
            session_id: Session identifier
            
        Returns:
            User preferences
        """
        profile = self.profiles_cache.get(session_id)
        if not profile:
            profile_dict = self.get_profile(session_id)
            if not profile_dict:
                return {}
            return profile_dict.get("preferences", {})
        
        return profile.preferences
    
    def get_purchase_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get user's purchase history
        
        Args:
            session_id: Session identifier
            
        Returns:
            Purchase history
        """
        profile = self.profiles_cache.get(session_id)
        if not profile:
            profile_dict = self.get_profile(session_id)
            if not profile_dict:
                return []
            return profile_dict.get("purchase_history", [])
        
        return profile.purchase_history
    
    def _auto_classify_customer(self, profile: UserProfile):
        """Auto-classify customer type based on collected data"""
        if profile.customer_type:
            return  # Already classified
        
        # Classify based on collected data
        if profile.medical_conditions:
            profile.customer_type = CustomerProfile.MEDICAL_PATIENT
        elif profile.experience_level == "experienced" and profile.interaction_count > 5:
            profile.customer_type = CustomerProfile.EXPERIENCED_USER
        elif profile.price_range and profile.price_range.get("max", float('inf')) < 50:
            profile.customer_type = CustomerProfile.PRICE_CONSCIOUS
        elif profile.preferred_categories and len(profile.preferred_categories) > 3:
            profile.customer_type = CustomerProfile.EXPLORER
        elif profile.interaction_count == 1:
            profile.customer_type = CustomerProfile.NEW_USER
        else:
            profile.customer_type = CustomerProfile.RECREATIONAL_USER
    
    def _persist_profile(self, profile: UserProfile):
        """Persist profile to database"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Upsert profile
            query = """
                INSERT INTO user_profiles (
                    id, session_id, email, phone, age_verified,
                    customer_type, preferences, needs, experience_level,
                    medical_conditions, preferred_categories, preferred_effects,
                    price_range, purchase_history, interaction_count,
                    language, timezone, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    age_verified = EXCLUDED.age_verified,
                    customer_type = EXCLUDED.customer_type,
                    preferences = EXCLUDED.preferences,
                    needs = EXCLUDED.needs,
                    experience_level = EXCLUDED.experience_level,
                    medical_conditions = EXCLUDED.medical_conditions,
                    preferred_categories = EXCLUDED.preferred_categories,
                    preferred_effects = EXCLUDED.preferred_effects,
                    price_range = EXCLUDED.price_range,
                    purchase_history = EXCLUDED.purchase_history,
                    interaction_count = EXCLUDED.interaction_count,
                    language = EXCLUDED.language,
                    timezone = EXCLUDED.timezone,
                    updated_at = EXCLUDED.updated_at
            """
            
            cursor.execute(query, (
                profile.id,
                profile.session_id,
                profile.email,
                profile.phone,
                profile.age_verified,
                profile.customer_type.value if profile.customer_type else None,
                json.dumps(profile.preferences),
                json.dumps(profile.needs),
                profile.experience_level,
                json.dumps(profile.medical_conditions),
                json.dumps(profile.preferred_categories),
                json.dumps(profile.preferred_effects),
                json.dumps(profile.price_range) if profile.price_range else None,
                json.dumps(profile.purchase_history),
                profile.interaction_count,
                profile.language,
                profile.timezone,
                profile.created_at,
                profile.updated_at
            ))
            
            conn.commit()
            cursor.close()
            self.db_manager.release_connection(conn)
            
        except Exception as e:
            logger.error(f"Failed to persist profile: {e}")
    
    def _load_profile_from_db(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load profile from database"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM user_profiles
                WHERE session_id = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            
            cursor.close()
            self.db_manager.release_connection(conn)
            
            if result:
                return dict(result)
            
        except Exception as e:
            logger.error(f"Failed to load profile from database: {e}")
        
        return None
    
    def _deserialize_profile(self, data: Dict[str, Any]) -> UserProfile:
        """Deserialize profile from database"""
        profile = UserProfile(
            id=data.get("id"),
            session_id=data.get("session_id"),
            email=data.get("email"),
            phone=data.get("phone"),
            age_verified=data.get("age_verified", False),
            experience_level=data.get("experience_level"),
            interaction_count=data.get("interaction_count", 0),
            language=data.get("language", "en"),
            timezone=data.get("timezone"),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now())
        )
        
        # Deserialize JSON fields
        if data.get("customer_type"):
            profile.customer_type = CustomerProfile(data["customer_type"])
        
        if data.get("preferences"):
            profile.preferences = json.loads(data["preferences"]) if isinstance(data["preferences"], str) else data["preferences"]
        
        if data.get("needs"):
            profile.needs = json.loads(data["needs"]) if isinstance(data["needs"], str) else data["needs"]
        
        if data.get("medical_conditions"):
            profile.medical_conditions = json.loads(data["medical_conditions"]) if isinstance(data["medical_conditions"], str) else data["medical_conditions"]
        
        if data.get("preferred_categories"):
            profile.preferred_categories = json.loads(data["preferred_categories"]) if isinstance(data["preferred_categories"], str) else data["preferred_categories"]
        
        if data.get("preferred_effects"):
            profile.preferred_effects = json.loads(data["preferred_effects"]) if isinstance(data["preferred_effects"], str) else data["preferred_effects"]
        
        if data.get("price_range"):
            profile.price_range = json.loads(data["price_range"]) if isinstance(data["price_range"], str) else data["price_range"]
        
        if data.get("purchase_history"):
            profile.purchase_history = json.loads(data["purchase_history"]) if isinstance(data["purchase_history"], str) else data["purchase_history"]
        
        return profile
    
    def get_collection_fields_for_stage(self, stage: str) -> List[str]:
        """
        Get fields to collect for a specific stage
        
        Args:
            stage: Sales stage name
            
        Returns:
            List of fields to collect
        """
        return self.progressive_fields.get(stage, [])