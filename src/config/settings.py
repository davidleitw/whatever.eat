import os
from dotenv import load_dotenv

def load_env():
    """
    Load environment variables from .env file
    Returns True if .env file exists and is loaded, False otherwise
    """
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
        return True
    else:
        print("⚠️  .env file not found, using system environment variables")
        return False

class Config:
    """
    Configuration class for LINE Bot
    """
    def __init__(self):
        # Load environment variables
        load_env()

        # LINE Bot credentials
        self.LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        self.LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
        self.GOOGLE_MAP_API_KEY = os.getenv('GOOGLE_MAP_API_TOKEN')
        
        # Server configuration
        self.PORT = int(os.getenv('PORT', 5000))
        self.DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
        self.HOST = os.getenv('HOST', '0.0.0.0')
    
    def validate(self, require_google_maps: bool = False):
        """
        Validate that required environment variables are set
        
        Args:
            require_google_maps: Whether to require Google Maps API key (default: False)
        """
        missing_vars = []
        
        if not self.LINE_CHANNEL_ACCESS_TOKEN:
            missing_vars.append('LINE_CHANNEL_ACCESS_TOKEN')
        
        if not self.LINE_CHANNEL_SECRET:
            missing_vars.append('LINE_CHANNEL_SECRET')
        
        if require_google_maps and not self.GOOGLE_MAP_API_KEY:
            missing_vars.append('GOOGLE_MAP_API_TOKEN')
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    def has_google_maps_api(self) -> bool:
        """Check if Google Maps API key is configured"""
        return bool(self.GOOGLE_MAP_API_KEY)
    
    def display_config(self):
        """
        Display current configuration (without sensitive data)
        """
        print("🔧 Current Configuration:")
        print(f"   PORT: {self.PORT}")
        print(f"   HOST: {self.HOST}")
        print(f"   DEBUG: {self.DEBUG}")
        print(f"   ACCESS_TOKEN: {'✅ Set' if self.LINE_CHANNEL_ACCESS_TOKEN else '❌ Missing'}")
        print(f"   CHANNEL_SECRET: {'✅ Set' if self.LINE_CHANNEL_SECRET else '❌ Missing'}")
        print(f"   GOOGLE_MAP_API_KEY: {'✅ Set' if self.GOOGLE_MAP_API_KEY else '❌ Missing'}")

# Create global config instance
config = Config() 