"""
Session management for LINE Bot user interactions.

This module provides session-based caching for user locations and interaction state,
allowing users to set their location once and then perform multiple restaurant queries
without re-sending their location each time.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Deque
from collections import deque
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

@dataclass
class UserLocation:
    """
    Represents a user's location data with associated metadata.
    
    Attributes:
        title: Human-readable location name
        address: Full address string
        latitude: Geographic latitude
        longitude: Geographic longitude
        timestamp: When this location was set (handled by cache TTL)
    """
    title: str
    address: str
    latitude: float
    longitude: float
    
    def __str__(self) -> str:
        return f"{self.title} ({self.address})"


@dataclass
class UserSession:
    """
    Represents a complete user session with location and recommendation history.
    
    Attributes:
        location: User's current location
        recent_recommendations: Deque of recently recommended restaurant IDs
        recommendation_count: Total number of recommendations made
    """
    location: UserLocation
    recent_recommendations: Deque[str] = field(default_factory=lambda: deque(maxlen=5))
    recommendation_count: int = 0
    
    def add_recommendation(self, restaurant_id: str) -> None:
        """Add a restaurant ID to the recent recommendations history."""
        self.recent_recommendations.append(restaurant_id)
        self.recommendation_count += 1
    
    def has_recent_recommendation(self, restaurant_id: str) -> bool:
        """Check if a restaurant was recently recommended."""
        return restaurant_id in self.recent_recommendations
    
    def get_recent_count(self) -> int:
        """Get the number of recent recommendations."""
        return len(self.recent_recommendations)
    
    def clear_recommendations(self) -> None:
        """Clear the recommendation history."""
        self.recent_recommendations.clear()
        self.recommendation_count = 0


class SessionManager:
    """
    Manages user sessions with TTL-based location caching.
    
    Features:
    - Thread-safe user location storage
    - Automatic expiration after configurable TTL
    - Support for multiple concurrent users
    - Memory-efficient with size limits
    """
    
    def __init__(self, max_users: int = 1000, location_ttl: int = 1800):
        """
        Initialize the session manager.
        
        Args:
            max_users: Maximum number of user sessions to cache
            location_ttl: Time-to-live for session data in seconds (default: 30 minutes)
        """
        self.max_users = max_users
        self.location_ttl = location_ttl
        
        # Thread-safe TTL cache for user sessions (includes location + history)
        self._session_cache: TTLCache[str, UserSession] = TTLCache(
            maxsize=max_users, 
            ttl=location_ttl
        )
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logger.info(f"🎯 SessionManager initialized: max_users={max_users}, ttl={location_ttl}s")
    
    def set_user_location(self, user_id: str, location_data: Dict[str, Any]) -> UserLocation:
        """
        Set location for a user from LINE location message data.
        
        Args:
            user_id: LINE user ID
            location_data: Location message data from LINE Bot SDK
            
        Returns:
            UserLocation object that was stored
            
        Raises:
            ValueError: If location data is missing required fields
        """
        try:
            # Extract location information with validation
            title = location_data.get('title') or "Unknown Location"
            address = location_data.get('address') or "No address provided"
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')
            
            if latitude is None or longitude is None:
                raise ValueError("Missing required coordinates (latitude/longitude)")
            
            user_location = UserLocation(
                title=title,
                address=address,
                latitude=float(latitude),
                longitude=float(longitude)
            )
            
            with self._lock:
                # Check if user already has a session
                existing_session = self._session_cache.get(user_id)
                if existing_session:
                    # Update location but keep recommendation history
                    existing_session.location = user_location
                    logger.info(f"📍 Updated location for user {user_id}: {user_location}")
                else:
                    # Create new session
                    user_session = UserSession(location=user_location)
                    self._session_cache[user_id] = user_session
                    logger.info(f"📍 New session created for user {user_id}: {user_location}")
                
            return user_location
            
        except Exception as e:
            logger.error(f"❌ Error setting location for user {user_id}: {str(e)}")
            raise ValueError(f"Invalid location data: {str(e)}")
    
    def get_user_location(self, user_id: str) -> Optional[UserLocation]:
        """
        Get cached location for a user.
        
        Args:
            user_id: LINE user ID
            
        Returns:
            UserLocation if found and not expired, None otherwise
        """
        with self._lock:
            session = self._session_cache.get(user_id)
            
        if session:
            logger.info(f"📍 Retrieved location for user {user_id}: {session.location}")
            return session.location
        else:
            logger.info(f"❌ No cached session found for user {user_id}")
            return None
    
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """
        Get complete user session including location and recommendation history.
        
        Args:
            user_id: LINE user ID
            
        Returns:
            UserSession if found and not expired, None otherwise
        """
        with self._lock:
            session = self._session_cache.get(user_id)
            
        if session:
            logger.info(f"📊 Retrieved session for user {user_id}: {session.recommendation_count} recommendations")
        else:
            logger.info(f"❌ No cached session found for user {user_id}")
            
        return session
    
    def has_user_location(self, user_id: str) -> bool:
        """
        Check if user has a valid cached location.
        
        Args:
            user_id: LINE user ID
            
        Returns:
            True if user has cached location, False otherwise
        """
        with self._lock:
            return user_id in self._session_cache
    
    def remove_user_location(self, user_id: str) -> bool:
        """
        Remove user's cached session (location + history).
        
        Args:
            user_id: LINE user ID
            
        Returns:
            True if session was removed, False if not found
        """
        with self._lock:
            if user_id in self._session_cache:
                del self._session_cache[user_id]
                logger.info(f"🗑️ Removed session for user {user_id}")
                return True
            else:
                logger.info(f"❌ No session to remove for user {user_id}")
                return False
    
    def add_recommendation(self, user_id: str, restaurant_id: str) -> bool:
        """
        Add a restaurant recommendation to user's history.
        
        Args:
            user_id: LINE user ID
            restaurant_id: Unique identifier for the restaurant
            
        Returns:
            True if recommendation was added, False if user session not found
        """
        with self._lock:
            session = self._session_cache.get(user_id)
            if session:
                session.add_recommendation(restaurant_id)
                logger.info(f"📝 Added recommendation {restaurant_id} for user {user_id} (total: {session.recommendation_count})")
                return True
            else:
                logger.warning(f"❌ Cannot add recommendation: no session for user {user_id}")
                return False
    
    def is_recently_recommended(self, user_id: str, restaurant_id: str) -> bool:
        """
        Check if a restaurant was recently recommended to the user.
        
        Args:
            user_id: LINE user ID
            restaurant_id: Unique identifier for the restaurant
            
        Returns:
            True if restaurant was recently recommended, False otherwise
        """
        with self._lock:
            session = self._session_cache.get(user_id)
            if session:
                is_recent = session.has_recent_recommendation(restaurant_id)
                logger.info(f"🔍 Restaurant {restaurant_id} recent check for user {user_id}: {is_recent}")
                return is_recent
            else:
                return False
    
    def get_recent_recommendations(self, user_id: str) -> List[str]:
        """
        Get list of recently recommended restaurant IDs for a user.
        
        Args:
            user_id: LINE user ID
            
        Returns:
            List of restaurant IDs recently recommended
        """
        with self._lock:
            session = self._session_cache.get(user_id)
            if session:
                recent_list = list(session.recent_recommendations)
                logger.info(f"📋 Recent recommendations for user {user_id}: {len(recent_list)} restaurants")
                return recent_list
            else:
                return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_recommendations = sum(session.recommendation_count for session in self._session_cache.values())
            return {
                "current_users": len(self._session_cache),
                "max_users": self.max_users,
                "ttl_seconds": self.location_ttl,
                "total_recommendations": total_recommendations,
                "cache_info": {
                    "hits": getattr(self._session_cache, 'hits', 0),
                    "misses": getattr(self._session_cache, 'misses', 0),
                }
            }
    
    def cleanup_expired(self) -> int:
        """
        Manually trigger cleanup of expired entries.
        
        Returns:
            Number of entries that were cleaned up
        """
        with self._lock:
            before_count = len(self._session_cache)
            self._session_cache.expire()
            after_count = len(self._session_cache)
            
        cleaned_count = before_count - after_count
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} expired session entries")
            
        return cleaned_count


# Global session manager instance
# Using 30 minutes TTL by default for user convenience
session_manager = SessionManager(max_users=1000, location_ttl=1800)


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        Global SessionManager instance
    """
    return session_manager