import logging
import random
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
from src.config.settings import config
from src.map_service.client import nearby_search

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
    
    def _handle_text_message(self, event):
        """Handle text messages from users"""
        user_message = event.message.text
        reply_text = f"Hello! You said: {user_message}"
        
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    
    def _handle_location_message(self, event):
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

            # Randomly select one restaurant
            if resp:
                selected_restaurant = random.choice(resp)
                logger.info(f"🎲 Randomly selected restaurant: {selected_restaurant.display_name.text}")
                
                # Extract restaurant details
                restaurant_name = selected_restaurant.display_name.text
                restaurant_rating = getattr(selected_restaurant, 'rating', 'N/A')
                restaurant_address = getattr(selected_restaurant, 'formatted_address', 'Address not available')
                restaurant_types = getattr(selected_restaurant, 'types', [])
                restaurant_price_level = getattr(selected_restaurant, 'price_level', 'N/A')
                
                # Get opening hours if available
                opening_hours = "Not available"
                if hasattr(selected_restaurant, 'opening_hours') and selected_restaurant.opening_hours:
                    if hasattr(selected_restaurant.opening_hours, 'open_now'):
                        opening_hours = "Open now" if selected_restaurant.opening_hours.open_now else "Closed now"
                
                logger.info(f"📊 Restaurant details:")
                logger.info(f"   • Name: {restaurant_name}")
                logger.info(f"   • Rating: {restaurant_rating}")
                logger.info(f"   • Address: {restaurant_address}")
                logger.info(f"   • Types: {restaurant_types}")
                logger.info(f"   • Price Level: {restaurant_price_level}")
                logger.info(f"   • Opening Hours: {opening_hours}")
                
                # Create detailed reply message for the selected restaurant
                reply_text = (
                    f"📍 Location Received!\n\n"
                    f"🏷️ Your Location: {title}\n"
                    f"📮 Address: {address}\n"
                    f"🌐 Coordinates: {latitude}, {longitude}\n\n"
                    f"🎲 Randomly Selected Restaurant:\n\n"
                    f"🍴 {restaurant_name}\n"
                    f"⭐ Rating: {restaurant_rating}\n"
                    f"📍 Address: {restaurant_address}\n"
                    f"🏷️ Types: {', '.join(restaurant_types) if restaurant_types else 'Not specified'}\n"
                    f"💰 Price Level: {restaurant_price_level}\n"
                    f"🕒 Status: {opening_hours}\n\n"
                    f"🔗 Google Maps: https://maps.google.com/?q={latitude},{longitude}"
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