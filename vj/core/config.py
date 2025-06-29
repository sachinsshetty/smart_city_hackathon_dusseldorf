"""
Configuration module for Dwani AI
Manages all settings, constants, and environment variables
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DwaniConfig:
    """Configuration class for Dwani AI"""
    
    # API Configuration
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENROUTE_SERVICE_API_KEY = os.getenv("OPENROUTE_SERVICE_API_KEY", "5b3ce3597851110001cf624837f79cdfc84c43c6a3d86c7dec071d74")
    
    # Model Configuration (can be changed to avoid quota issues)
    GEMINI_TEXT_MODEL = 'gemini-1.5-flash'  # or 'gemini-1.5-pro', 'gemini-pro'
    GEMINI_VISION_MODEL = 'gemini-1.5-flash'  # or 'gemini-1.5-pro'
    
    # Speech Recognition Configuration
    SPEECH_RECOGNITION_LANGUAGE = 'en-US'
    SPEECH_RECOGNITION_TIMEOUT = 5
    SPEECH_RECOGNITION_PHRASE_TIME_LIMIT = 10
    
    # Text-to-Speech Configuration
    TTS_VOICE_RATE = 150
    TTS_VOICE_VOLUME = 0.9
    
    # Camera Configuration
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    
    # Disaster Detection Configuration
    DISASTER_KEYWORDS = [
        'fire', 'smoke', 'flood', 'earthquake', 'debris', 'rubble',
        'collapsed', 'dangerous', 'hazard', 'emergency', 'evacuation',
        'explosion', 'gas leak', 'chemical spill', 'structural damage'
    ]
    
    # Safe Locations
    SAFE_LOCATIONS = {
        'hospital': 'Nearest hospital',
        'shelter': 'Emergency shelter',
        'police': 'Police station',
        'fire_station': 'Fire station',
        'safe_zone': 'Designated safe zone'
    }
    
    # Navigation Configuration
    NAVIGATION_COMMANDS = {
        'turn_left': 'Turn left',
        'turn_right': 'Turn right',
        'go_forward': 'Go forward',
        'go_backward': 'Go backward',
        'stop': 'Stop',
        'evacuate': 'Evacuate immediately'
    }
    
    # Risk Levels
    RISK_LEVELS = {
        'low': 'Low risk - proceed with caution',
        'medium': 'Medium risk - consider alternative route',
        'high': 'High risk - evacuate immediately',
        'critical': 'Critical risk - emergency evacuation required'
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        if not cls.GEMINI_API_KEY:
            print("❌ GOOGLE_API_KEY is not set!")
            return False
        return True
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'api_keys_configured': bool(cls.GEMINI_API_KEY),
            'speech_language': cls.SPEECH_RECOGNITION_LANGUAGE,
            'camera_resolution': f"{cls.CAMERA_WIDTH}x{cls.CAMERA_HEIGHT}",
            'disaster_keywords_count': len(cls.DISASTER_KEYWORDS),
            'safe_locations_count': len(cls.SAFE_LOCATIONS)
        } 