"""
Configuration file for Blind Navigation Assistant
Set your API server URLs here or use environment variables
"""

import os
from typing import Optional
import dotenv
dotenv.load_dotenv()

class Config:
    # Default API server URLs - Google Gemini API
    DEFAULT_TOOL_SERVER = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_VISION_SERVER = "https://generativelanguage.googleapis.com/v1beta"
    
    @staticmethod
    def get_tool_server_url() -> str:
        """Get the tool server URL from environment or use default"""
        return os.getenv("API_SERVER", Config.DEFAULT_TOOL_SERVER)
    
    @staticmethod
    def get_vision_server_url() -> str:
        """Get the vision server URL from environment or use default"""
        return os.getenv("API_SERVER_VLM", Config.DEFAULT_VISION_SERVER)
    
    @staticmethod
    def get_google_api_key() -> Optional[str]:
        return os.getenv("GOOGLE_API_KEY")
    
    @staticmethod
    def setup_environment():
        """Setup environment variables if not already set"""
        if not os.getenv("API_SERVER"):
            print(f"Setting API_SERVER to default: {Config.DEFAULT_TOOL_SERVER}")
            os.environ["API_SERVER"] = Config.DEFAULT_TOOL_SERVER
        
        if not os.getenv("API_SERVER_VLM"):
            print(f"Setting API_SERVER_VLM to default: {Config.DEFAULT_VISION_SERVER}")
            os.environ["API_SERVER_VLM"] = Config.DEFAULT_VISION_SERVER
        
        if not os.getenv("GOOGLE_API_KEY"):
            print("Warning: GOOGLE_API_KEY is not set. Please set it in your .env file.")
    
    @staticmethod
    def print_config():
        """Print current configuration"""
        print("=== Blind Navigation Assistant Configuration ===")
        print(f"Tool Server: {Config.get_tool_server_url()}")
        print(f"Vision Server: {Config.get_vision_server_url()}")
        print(f"Google API Key: {'SET' if Config.get_google_api_key() else 'NOT SET'}")
        print("=" * 50)

# Common API server configurations
API_CONFIGS = {
    "google": {
        "tool_server": "https://generativelanguage.googleapis.com/v1beta",
        "vision_server": "https://generativelanguage.googleapis.com/v1beta"
    },
    "local": {
        "tool_server": "http://localhost:9100/v1",
        "vision_server": "http://localhost:9000/v1"
    },
    "custom": {
        "tool_server": "http://your-tool-server:port/v1",
        "vision_server": "http://your-vision-server:port/v1"
    }
}

def set_api_config(config_name: str = "google"):
    """Set API configuration by name"""
    if config_name in API_CONFIGS:
        config = API_CONFIGS[config_name]
        os.environ["API_SERVER"] = config["tool_server"]
        os.environ["API_SERVER_VLM"] = config["vision_server"]
        print(f"✅ Set API configuration to: {config_name}")
        Config.print_config()
    else:
        print(f"❌ Unknown configuration: {config_name}")
        print(f"Available configurations: {list(API_CONFIGS.keys())}")

if __name__ == "__main__":
    # Setup default environment
    Config.setup_environment()
    Config.print_config() 