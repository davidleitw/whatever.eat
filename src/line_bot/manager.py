import logging
import random
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
from src.config.settings import config
from src.map.client import nearby_search

# Configure logging
logger = logging.getLogger(__name__)


class LineBotManager:
    """Manages LINE Bot API and message handlers"""
    
    def __init__(self):
        self.line_bot_api = None
        self.handler = None
    
    def initialize(self):
        """Initialize LINE Bot API and Webhook Handler"""
        try:
            config.validate()
            self.line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
            self.handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
            self._register_handlers()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize LINE Bot: {e}")
            return False
    
    def _register_handlers(self):
        """Register message handlers with the webhook handler"""
        if self.handler:
            # Use lambda functions to properly wrap class methods for LINE Bot SDK
            self.handler.add(MessageEvent, message=TextMessage)(
                lambda event: self._handle_text_message(event)
            )
            self.handler.add(MessageEvent, message=LocationMessage)(
                lambda event: self._handle_location_message(event)
            )
    
    def _format_opening_hours(self, restaurant) -> str:
        """
        Format restaurant opening hours information
        
        Args:
            restaurant: Restaurant object from Google Places API
            
        Returns:
            str: Formatted opening hours string
        """
        try:
            # Check if regular_opening_hours exists
            if not hasattr(restaurant, 'regular_opening_hours') or not restaurant.regular_opening_hours:
                return "營業時間資訊不可用"
            
            opening_hours = restaurant.regular_opening_hours
            
            # Get current status (open/closed)
            current_status = "目前營業中" if getattr(opening_hours, 'open_now', False) else "目前休息中"
            
            # Get weekday descriptions if available
            weekday_descriptions = getattr(opening_hours, 'weekday_descriptions', [])
            
            if weekday_descriptions:
                # Format the opening hours with current status and weekly schedule
                hours_info = f"🕒 {current_status}\n\n📅 營業時間：\n"
                for day_info in weekday_descriptions:
                    hours_info += f"   {day_info}\n"
                return hours_info.strip()
            else:
                # Fallback to just current status if detailed hours not available
                return f"🕒 {current_status}"
                
        except Exception as e:
            logger.warning(f"⚠️ Error formatting opening hours: {str(e)}")
            return "營業時間資訊處理時發生錯誤"
    
    def _is_restaurant_open(self, restaurant) -> bool:
        """
        Check if a restaurant is currently open
        
        Args:
            restaurant: Restaurant object from Google Places API
            
        Returns:
            bool: True if restaurant is currently open, False otherwise
        """
        try:
            # Check if regular_opening_hours exists
            if not hasattr(restaurant, 'regular_opening_hours') or not restaurant.regular_opening_hours:
                # If opening hours info is not available, assume it's open (to avoid filtering out too many restaurants)
                restaurant_name = getattr(restaurant, 'display_name', None)
                restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
                logger.info(f"📋 No opening hours info for {restaurant_name} - assuming open")
                return True
            
            opening_hours = restaurant.regular_opening_hours
            is_open = getattr(opening_hours, 'open_now', False)
            
            restaurant_name = getattr(restaurant, 'display_name', None)
            restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
            logger.info(f"🕒 Restaurant {restaurant_name} open status: {'Open' if is_open else 'Closed'}")
            
            return is_open
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking restaurant open status: {str(e)}")
            # If we can't determine the status, assume it's open to avoid filtering out
            return True
    
    def _select_open_restaurant(self, restaurants, max_attempts=10):
        """
        Select a random restaurant that is currently open
        
        Args:
            restaurants: List of restaurant objects from Google Places API
            max_attempts: Maximum number of attempts to find an open restaurant
            
        Returns:
            tuple: (selected_restaurant, attempt_count) or (None, attempt_count) if no open restaurant found
        """
        if not restaurants:
            logger.warning("⚠️ No restaurants provided to select from")
            return None, 0
        
        attempt_count = 0
        open_restaurants = []
        
        # First, try to find restaurants that are definitely open
        for restaurant in restaurants:
            if self._is_restaurant_open(restaurant):
                open_restaurants.append(restaurant)
        
        if open_restaurants:
            selected = random.choice(open_restaurants)
            restaurant_name = getattr(selected, 'display_name', None)
            restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
            logger.info(f"✅ Selected open restaurant: {restaurant_name}")
            return selected, 1
        
        # If no restaurants are confirmed open, try random selection with retry mechanism
        logger.info("🔄 No confirmed open restaurants found, trying random selection with retry...")
        
        while attempt_count < max_attempts:
            attempt_count += 1
            selected_restaurant = random.choice(restaurants)
            restaurant_name = getattr(selected_restaurant, 'display_name', None)
            restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
            
            logger.info(f"🎲 Attempt {attempt_count}: Checking restaurant {restaurant_name}")
            
            if self._is_restaurant_open(selected_restaurant):
                logger.info(f"✅ Found open restaurant after {attempt_count} attempts: {restaurant_name}")
                return selected_restaurant, attempt_count
            else:
                logger.info(f"❌ Restaurant {restaurant_name} is currently closed, trying again...")
        
        # If we couldn't find an open restaurant after max attempts, return a random one
        logger.warning(f"⚠️ Could not find open restaurant after {max_attempts} attempts, returning random selection")
        final_selection = random.choice(restaurants)
        return final_selection, attempt_count
    
    def _handle_text_message(self, event: TextMessage):
        """Handle text messages from users"""
        user_message = event.message.text
        reply_text = f"Hello! You said: {user_message}"
        
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    
    def _handle_location_message(self, event: LocationMessage):
        """Handle location messages from users"""
        logger.info("🌍 Starting location message handling")

        try:
            location = event.message
            logger.info(f"📍 Location message received from user: {event.source.user_id}")
            
            # Extract location information
            title = location.title or "Unknown Location"
            address = location.address or "No address provided"
            latitude = location.latitude
            longitude = location.longitude

            logger.info(f"📋 Location details extracted:")
            logger.info(f"   • Title: {title}")
            logger.info(f"   • Address: {address}")
            logger.info(f"   • Latitude: {latitude}")
            logger.info(f"   • Longitude: {longitude}")
            
            logger.info("🔍 Calling nearby_search API...")
            resp = nearby_search(latitude, longitude)
            logger.info(f"✅ Nearby search completed, found {len(resp)} restaurants")

            # Randomly select one restaurant that is currently open
            if resp:
                selected_restaurant, attempt_count = self._select_open_restaurant(resp)
                
                if selected_restaurant is None:
                    logger.warning("⚠️ No restaurants available after selection process")
                    reply_text = (
                        f"📍 Location Received!\n\n"
                        f"🏷️ Your Location: {title}\n"
                        f"📮 Address: {address}\n"
                        f"🌐 Coordinates: {latitude}, {longitude}\n\n"
                        f"😔 Sorry, no restaurants found in this area.\n"
                        f"🔗 Google Maps: https://maps.google.com/?q={latitude},{longitude}"
                    )
                else:
                    print(selected_restaurant)
                    restaurant_name = getattr(selected_restaurant, 'display_name', None)
                    restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
                    logger.info(f"🎯 Selected restaurant after {attempt_count} attempt(s): {restaurant_name}")
                    
                    # Extract restaurant details
                    restaurant_rating = getattr(selected_restaurant, 'rating', 'N/A')
                    restaurant_address = getattr(selected_restaurant, 'formatted_address', 'Address not available')
                    restaurant_types = getattr(selected_restaurant, 'types', [])
                    restaurant_price_level = getattr(selected_restaurant, 'price_level', 'N/A')
                    restaurant_google_maps_uri = getattr(selected_restaurant, 'google_maps_uri', 'N/A')
                    
                    # Get formatted opening hours using the existing method
                    opening_hours_info = self._format_opening_hours(selected_restaurant)
                    
                    logger.info(f"📊 Restaurant details:")
                    logger.info(f"   • Name: {restaurant_name}")
                    logger.info(f"   • Rating: {restaurant_rating}")
                    logger.info(f"   • Address: {restaurant_address}")
                    logger.info(f"   • Types: {restaurant_types}")
                    logger.info(f"   • Price Level: {restaurant_price_level}")
                    logger.info(f"   • Opening Hours: {opening_hours_info}")
                    
                    # Create detailed reply message for the selected restaurant
                    selection_info = f"🎯 Selected after {attempt_count} attempt(s)" if attempt_count > 1 else "🎲 Randomly Selected Restaurant"
                    
                    reply_text = (
                        f"📍 Location Received!\n\n"
                        f"🏷️ Your Location: {title}\n"
                        f"📮 Address: {address}\n"
                        f"🌐 Coordinates: {latitude}, {longitude}\n\n"
                        f"{selection_info}:\n\n"
                        f"🍴 {restaurant_name}\n"
                        f"⭐ Rating: {restaurant_rating}\n"
                        f"📍 Address: {restaurant_address}\n"
                        f"🏷️ Types: {', '.join(restaurant_types) if restaurant_types else 'Not specified'}\n"
                        f"💰 Price Level: {restaurant_price_level}\n\n"
                        f"{opening_hours_info}\n\n"
                        f"🔗 Google Maps: {restaurant_google_maps_uri}"
                    )
            else:
                logger.warning("⚠️ No restaurants found in the area")
                reply_text = (
                    f"📍 Location Received!\n\n"
                    f"🏷️ Title: {title}\n"
                    f"📮 Address: {address}\n"
                    f"🌐 Coordinates: {latitude}, {longitude}\n\n"
                    f"😔 Sorry, no restaurants found in this area.\n"
                    f"🔗 Google Maps: https://maps.google.com/?q={latitude},{longitude}"
                )
            
            logger.info("💬 Preparing reply message...")
            logger.info(f"📝 Reply message length: {len(reply_text)} characters")
            
            logger.info("📤 Sending reply message to LINE Bot API...")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            logger.info("✅ Location message handling completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in location message handling: {str(e)}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            
            # Send error message to user
            error_reply = "抱歉，處理位置資訊時發生錯誤，請稍後再試。"
            try:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=error_reply)
                )
                logger.info("📤 Error message sent to user")
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message: {str(reply_error)}")
            
            raise e
    
    def handle_webhook(self, body, signature):
        """Handle LINE webhook callback"""
        if not self.line_bot_api or not self.handler:
            raise RuntimeError("LINE Bot not initialized")
        
        try:
            self.handler.handle(body, signature)
        except InvalidSignatureError:
            raise InvalidSignatureError("Invalid signature")
    
    def is_initialized(self):
        """Check if LINE Bot is properly initialized"""
        return bool(self.line_bot_api and self.handler) 