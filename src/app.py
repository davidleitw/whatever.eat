import logging
import sys
import os
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError

# Add parent directory to Python path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import config
from src.line_bot.manager import LineBotManager

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create LINE Bot manager instance
line_bot_manager = LineBotManager()


@app.route("/callback", methods=['POST'])
def callback():
    """Handle LINE webhook callback"""
    if not line_bot_manager.is_initialized():
        abort(500, "LINE Bot not initialized")

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        line_bot_manager.handle_webhook(body, signature)
    except InvalidSignatureError:
        abort(400)
    except RuntimeError:
        abort(500)
    
    return 'OK'


@app.route("/")
def health_check():
    """Health check endpoint"""
    return "LINE Bot is running! 🤖"


@app.route("/config")
def show_config():
    """Display current configuration status"""
    return {
        "status": "running",
        "port": config.PORT,
        "debug": config.DEBUG,
        "access_token_set": bool(config.LINE_CHANNEL_ACCESS_TOKEN),
        "channel_secret_set": bool(config.LINE_CHANNEL_SECRET),
        "line_bot_initialized": line_bot_manager.is_initialized()
    }


if __name__ == "__main__":
    if line_bot_manager.initialize():
        print("🚀 Starting LINE Bot server...")
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    else:
        print("❌ Cannot start server without proper LINE Bot configuration") 