"""
Session management for LINE Bot user interactions.

This module provides session-based caching for user locations and interaction state,
allowing users to set their location once and then perform multiple restaurant queries
without re-sending their location each time.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
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
            location_ttl: Time-to-live for location data in seconds (default: 30 minutes)
        """
        self.max_users = max_users
        self.location_ttl = location_ttl
        
        # Thread-safe TTL cache for user locations
        self._location_cache: TTLCache[str, UserLocation] = TTLCache(
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
                self._location_cache[user_id] = user_location
                
            logger.info(f"📍 Location set for user {user_id}: {user_location}")
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
            location = self._location_cache.get(user_id)
            
        if location:
            logger.info(f"📍 Retrieved location for user {user_id}: {location}")
        else:
            logger.info(f"❌ No cached location found for user {user_id}")
            
        return location
    
    def has_user_location(self, user_id: str) -> bool:
        """
        Check if user has a valid cached location.
        
        Args:
            user_id: LINE user ID
            
        Returns:
            True if user has cached location, False otherwise
        """
        with self._lock:
            return user_id in self._location_cache
    
    def remove_user_location(self, user_id: str) -> bool:
        """
        Remove user's cached location.
        
        Args:
            user_id: LINE user ID
            
        Returns:
            True if location was removed, False if not found
        """
        with self._lock:
            if user_id in self._location_cache:
                del self._location_cache[user_id]
                logger.info(f"🗑️ Removed location for user {user_id}")
                return True
            else:
                logger.info(f"❌ No location to remove for user {user_id}")
                return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "current_users": len(self._location_cache),
                "max_users": self.max_users,
                "ttl_seconds": self.location_ttl,
                "cache_info": {
                    "hits": getattr(self._location_cache, 'hits', 0),
                    "misses": getattr(self._location_cache, 'misses', 0),
                }
            }
    
    def cleanup_expired(self) -> int:
        """
        Manually trigger cleanup of expired entries.
        
        Returns:
            Number of entries that were cleaned up
        """
        with self._lock:
            before_count = len(self._location_cache)
            self._location_cache.expire()
            after_count = len(self._location_cache)
            
        cleaned_count = before_count - after_count
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} expired location entries")
            
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