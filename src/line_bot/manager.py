import logging
import random
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
from src.config.settings import config
from src.map.client import nearby_search
from src.line_bot.session import get_session_manager, UserLocation
from src.line_bot.commands import get_command_parser, CommandType

# Configure logging
logger = logging.getLogger(__name__)


class LineBotManager:
    """Manages LINE Bot API and message handlers with session support"""
    
    def __init__(self):
        self.line_bot_api = None
        self.handler = None
        self.session_manager = get_session_manager()
        self.command_parser = get_command_parser()
    
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
    
    def _select_open_restaurant(self, restaurants, user_id: str, max_attempts=10):
        """
        Select a random restaurant that is currently open and not recently recommended.
        
        Args:
            restaurants: List of restaurant objects from Google Places API
            user_id: LINE user ID for tracking recommendation history
            max_attempts: Maximum number of attempts to find an open restaurant
            
        Returns:
            tuple: (selected_restaurant, attempt_count) or (None, attempt_count) if no restaurant found
        """
        if not restaurants:
            logger.warning("⚠️ No restaurants provided to select from")
            return None, 0
        
        # Helper function to get restaurant ID
        def get_restaurant_id(restaurant) -> str:
            # Use Google Place ID if available, otherwise use display name as fallback
            place_id = getattr(restaurant, 'id', None)
            if place_id:
                return place_id
            
            display_name = getattr(restaurant, 'display_name', None)
            if display_name and hasattr(display_name, 'text'):
                return display_name.text
            
            return 'unknown_restaurant'
        
        # Get user's recent recommendations to avoid duplicates
        recent_recommendations = self.session_manager.get_recent_recommendations(user_id)
        logger.info(f"🔍 User {user_id} has {len(recent_recommendations)} recent recommendations")
        
        # Filter out recently recommended restaurants
        available_restaurants = []
        excluded_count = 0
        
        for restaurant in restaurants:
            restaurant_id = get_restaurant_id(restaurant)
            if not self.session_manager.is_recently_recommended(user_id, restaurant_id):
                available_restaurants.append(restaurant)
            else:
                excluded_count += 1
                restaurant_name = getattr(restaurant, 'display_name', None)
                restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
                logger.info(f"🚫 Excluded recently recommended restaurant: {restaurant_name}")
        
        logger.info(f"📊 Available restaurants: {len(available_restaurants)}, Excluded: {excluded_count}")
        
        # If no restaurants available (all recently recommended), reset and use all
        if not available_restaurants:
            logger.info("🔄 All restaurants recently recommended, resetting to full list")
            available_restaurants = restaurants
        
        attempt_count = 0
        open_restaurants = []
        
        # First, try to find restaurants that are definitely open
        for restaurant in available_restaurants:
            if self._is_restaurant_open(restaurant):
                open_restaurants.append(restaurant)
        
        if open_restaurants:
            selected = random.choice(open_restaurants)
            restaurant_id = get_restaurant_id(selected)
            restaurant_name = getattr(selected, 'display_name', None)
            restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
            
            # Add to recommendation history
            self.session_manager.add_recommendation(user_id, restaurant_id)
            
            logger.info(f"✅ Selected open restaurant: {restaurant_name} (ID: {restaurant_id})")
            return selected, 1
        
        # If no restaurants are confirmed open, try random selection with retry mechanism
        logger.info("🔄 No confirmed open restaurants found, trying random selection with retry...")
        
        while attempt_count < max_attempts:
            attempt_count += 1
            selected_restaurant = random.choice(available_restaurants)
            restaurant_id = get_restaurant_id(selected_restaurant)
            restaurant_name = getattr(selected_restaurant, 'display_name', None)
            restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
            
            logger.info(f"🎲 Attempt {attempt_count}: Checking restaurant {restaurant_name}")
            
            if self._is_restaurant_open(selected_restaurant):
                # Add to recommendation history
                self.session_manager.add_recommendation(user_id, restaurant_id)
                
                logger.info(f"✅ Found open restaurant after {attempt_count} attempts: {restaurant_name} (ID: {restaurant_id})")
                return selected_restaurant, attempt_count
            else:
                logger.info(f"❌ Restaurant {restaurant_name} is currently closed, trying again...")
        
        # If we couldn't find an open restaurant after max attempts, return a random one
        logger.warning(f"⚠️ Could not find open restaurant after {max_attempts} attempts, returning random selection")
        final_selection = random.choice(available_restaurants)
        final_restaurant_id = get_restaurant_id(final_selection)
        
        # Still add to recommendation history to prevent immediate re-selection
        self.session_manager.add_recommendation(user_id, final_restaurant_id)
        
        return final_selection, attempt_count
    
    def _handle_text_message(self, event: TextMessage):
        """Handle text messages from users with command parsing"""
        user_id = event.source.user_id
        user_message = event.message.text
        
        logger.info(f"💬 Text message from user {user_id}: {user_message}")
        
        # Parse the command
        command = self.command_parser.parse(user_message)
        
        try:
            if command.type == CommandType.RECOMMEND:
                reply_text = self._handle_recommend_command(user_id)
            elif command.type == CommandType.HELP:
                reply_text = self.command_parser.get_help_text()
            elif command.type == CommandType.STATUS:
                reply_text = self._handle_status_command(user_id)
            elif command.type == CommandType.CLEAR:
                reply_text = self._handle_clear_command(user_id)
            else:
                reply_text = self._handle_unknown_command(user_message)
                
        except Exception as e:
            logger.error(f"❌ Error handling command: {str(e)}")
            reply_text = "抱歉，處理您的指令時發生錯誤，請稍後再試。"
        
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    
    def _handle_location_message(self, event: LocationMessage):
        """Handle location messages from users"""
        user_id = event.source.user_id
        logger.info(f"🌍 Location message received from user: {user_id}")

        try:
            location = event.message
            
            # Prepare location data for session storage
            location_data = {
                'title': location.title,
                'address': location.address,
                'latitude': location.latitude,
                'longitude': location.longitude
            }
            
            # Store location in session
            user_location = self.session_manager.set_user_location(user_id, location_data)
            
            # Provide confirmation with usage instructions
            reply_text = (
                f"✅ 已設置您的位置！\n\n"
                f"📍 **{user_location.title}**\n"
                f"📮 {user_location.address}\n\n"
                f"🕒 **位置有效期：30 分鐘**\n\n"
                f"現在您可以使用以下指令：\n"
                f"• 輸入「抽餐廳」或「推薦」開始抽獎\n"
                f"• 輸入「幫助」查看所有指令\n\n"
                f"💡 在位置有效期內，您可以重複抽取不同的餐廳！"
            )
            
            logger.info(f"✅ Location stored for user {user_id}: {user_location}")
            
        except Exception as e:
            logger.error(f"❌ Error setting location for user {user_id}: {str(e)}")
            reply_text = "抱歉，設置位置時發生錯誤，請稍後再試。"
            
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    
    def _handle_recommend_command(self, user_id: str) -> str:
        """Handle restaurant recommendation command"""
        # Check if user has a cached location
        user_location = self.session_manager.get_user_location(user_id)
        
        if not user_location:
            return (
                "📍 **請先設置您的位置！**\n\n"
                "請分享您的位置給我，然後就可以開始抽餐廳了！\n\n"
                "💡 位置設置後會保存 30 分鐘，期間可重複抽取餐廳。"
            )
        
        try:
            logger.info(f"🔍 Searching restaurants near {user_location}")
            restaurants = nearby_search(user_location.latitude, user_location.longitude)
            logger.info(f"✅ Found {len(restaurants)} restaurants")
            
            if not restaurants:
                return (
                    f"😔 **很抱歉，在您的位置附近沒有找到餐廳**\n\n"
                    f"📍 搜尋位置：{user_location}\n\n"
                    f"💡 建議：\n"
                    f"• 嘗試重新設置位置\n"
                    f"• 或移動到餐廳較多的區域"
                )
            
            # Select a restaurant (with duplicate prevention)
            selected_restaurant, attempt_count = self._select_open_restaurant(restaurants, user_id)
            
            if selected_restaurant is None:
                return (
                    f"😔 **附近餐廳都已休息**\n\n"
                    f"📍 搜尋位置：{user_location}\n"
                    f"🔍 找到 {len(restaurants)} 家餐廳，但都已休息\n\n"
                    f"💡 建議稍後再試，或重新設置其他位置。"
                )
            
            # Format restaurant information
            return self._format_restaurant_recommendation(selected_restaurant, user_location, attempt_count, user_id)
            
        except Exception as e:
            logger.error(f"❌ Error getting restaurant recommendation: {str(e)}")
            return "抱歉，搜尋餐廳時發生錯誤，請稍後再試。"
    
    def _handle_status_command(self, user_id: str) -> str:
        """Handle status command to show user's current location"""
        user_location = self.session_manager.get_user_location(user_id)
        
        if not user_location:
            return (
                "📍 **目前沒有設置位置**\n\n"
                "請分享您的位置給我開始使用餐廳推薦功能！"
            )
        
        stats = self.session_manager.get_cache_stats()
        
        return (
            f"📍 **您的當前位置**\n\n"
            f"🏷️ {user_location.title}\n"
            f"📮 {user_location.address}\n"
            f"🌐 {user_location.latitude:.4f}, {user_location.longitude:.4f}\n\n"
            f"⏰ **位置有效期**：30 分鐘\n"
            f"💡 您可以輸入「抽餐廳」開始推薦！\n\n"
            f"📊 系統狀態：{stats['current_users']} 位用戶在線"
        )
    
    def _handle_clear_command(self, user_id: str) -> str:
        """Handle clear command to remove user's location"""
        was_removed = self.session_manager.remove_user_location(user_id)
        
        if was_removed:
            return (
                "🗑️ **已清除您的位置記錄**\n\n"
                "要重新開始使用，請分享您的位置給我！"
            )
        else:
            return (
                "📍 **目前沒有位置記錄需要清除**\n\n"
                "請分享您的位置給我開始使用餐廳推薦功能！"
            )
    
    def _handle_unknown_command(self, user_message: str) -> str:
        """Handle unknown or unrecognized commands"""
        return (
            f"❓ **不太理解您的指令**\n\n"
            f"您說的是：「{user_message}」\n\n"
            f"💡 **常用指令：**\n"
            f"• 抽餐廳 / 推薦 - 推薦餐廳\n"
            f"• 狀態 - 查看目前位置\n"
            f"• 幫助 - 顯示完整指令說明\n\n"
            f"或者直接分享您的位置開始使用！"
        )
    
    def _format_restaurant_recommendation(self, restaurant, user_location: UserLocation, attempt_count: int, user_id: str) -> str:
        """Format restaurant recommendation into user-friendly message"""
        restaurant_name = getattr(restaurant, 'display_name', None)
        restaurant_name = restaurant_name.text if restaurant_name else 'Unknown'
        
        restaurant_rating = getattr(restaurant, 'rating', 'N/A')
        restaurant_address = getattr(restaurant, 'formatted_address', 'Address not available')
        restaurant_types = getattr(restaurant, 'types', [])
        restaurant_price_level = getattr(restaurant, 'price_level', 'N/A')
        restaurant_google_maps_uri = getattr(restaurant, 'google_maps_uri', 'N/A')
        
        opening_hours_info = self._format_opening_hours(restaurant)
        
        # Get user session for recommendation stats (after recommendation was added)
        user_session = self.session_manager.get_user_session(user_id)
        recent_count = user_session.get_recent_count() if user_session else 0
        total_count = user_session.recommendation_count if user_session else 0
        
        selection_info = f"🎯 第 {attempt_count} 次嘗試找到營業中餐廳" if attempt_count > 1 else "🎲 智能推薦餐廳"
        
        # Show appropriate duplicate prevention status
        if total_count == 1:
            duplicate_prevention = "🆕 首次推薦"
        elif recent_count <= 5:
            duplicate_prevention = f"🔄 防重複推薦 ({recent_count}/5 記錄中)"
        else:
            duplicate_prevention = "🔄 防重複推薦 (已滿 5 次記錄)"
        
        return (
            f"🍽️ **為您推薦餐廳！**\n\n"
            f"📍 **您的位置**：{user_location.title}\n"
            f"📊 **推薦統計**：第 {total_count} 次推薦\n"
            f"🛡️ **防重複**：{duplicate_prevention}\n\n"
            f"{selection_info}\n\n"
            f"🍴 **{restaurant_name}**\n"
            f"⭐ 評分：{restaurant_rating}\n"
            f"📍 地址：{restaurant_address}\n"
            f"🏷️ 類型：{', '.join(restaurant_types) if restaurant_types else '未分類'}\n"
            f"💰 價位：{restaurant_price_level}\n\n"
            f"{opening_hours_info}\n\n"
            f"🔗 [Google Maps 導航]({restaurant_google_maps_uri})\n\n"
            f"💡 想要換一家？再輸入「抽餐廳」即可！\n"
            f"🎯 已記錄此推薦，近 5 次內不會重複推薦此餐廳"
        )
    
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