"""
Vision Handler Module for Dwani AI
Manages camera operations and image analysis using Gemini Vision
"""

import cv2
import base64
import json
import tempfile
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io
import google.generativeai as genai
from .config import DwaniConfig

class VisionHandler:
    """Handles camera operations and image analysis"""
    
    def __init__(self):
        """Initialize vision handler with Gemini Vision model"""
        if not DwaniConfig.GEMINI_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is required for vision operations")
        
        # Configure Gemini API (following working pattern from blind_navigation_assistant.py)
        genai.configure(api_key=DwaniConfig.GEMINI_API_KEY)  # type: ignore
        self.vision_model = genai.GenerativeModel(DwaniConfig.GEMINI_VISION_MODEL)  # type: ignore
        
        # Camera configuration
        self.camera_index = DwaniConfig.CAMERA_INDEX
        self.camera_width = DwaniConfig.CAMERA_WIDTH
        self.camera_height = DwaniConfig.CAMERA_HEIGHT
    
    def capture_image(self) -> Tuple[bool, Optional[str]]:
        """
        Capture image from camera (following working pattern from blind_navigation_assistant.py)
        
        Returns:
            Tuple[bool, Optional[str]]: (success, base64_image or error_message)
        """
        try:
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                return False, "Could not open camera"
            
            # Set camera resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Could not capture image"
            
            # Convert to base64 (following working pattern)
            _, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            return True, img_str
            
        except Exception as e:
            return False, f"Error capturing image: {e}"
    
    def analyze_image_for_disasters(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze image for disaster detection using Gemini Vision
        (Following working pattern from blind_navigation_assistant.py)
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Dict[str, Any]: Disaster analysis results
        """
        try:
            # Convert base64 to image (following working pattern)
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = """
            You are a disaster detection AI assistant. Analyze this image and identify any potential disasters, hazards, or dangerous situations.
            
            Look for:
            - Fire, smoke, or flames
            - Flooding or water damage
            - Structural damage or collapsed buildings
            - Debris, rubble, or dangerous objects
            - Chemical spills or hazardous materials
            - Gas leaks or explosions
            - Any other emergency situations
            
            Provide your response in this EXACT JSON format:
            {
                "disasters_detected": ["list of detected disasters"],
                "hazards_found": ["list of hazards"],
                "risk_level": "low/medium/high/critical",
                "recommendations": ["safety recommendations"],
                "safe_direction": "direction to move for safety",
                "emergency_contacts": ["relevant emergency services"],
                "confidence": 0.95
            }
            
            If no disasters are detected, set disasters_detected to empty array and risk_level to "low".
            """
            
            response = self.vision_model.generate_content([prompt, image])
            description = response.text
            
            # Try to parse JSON response (following working pattern from blind_navigation_assistant.py)
            try:
                if description:
                    # Clean up the response - remove markdown code blocks if present
                    cleaned_description = description.strip()
                    if cleaned_description.startswith('```json'):
                        cleaned_description = cleaned_description[7:]  # Remove ```json
                    if cleaned_description.startswith('```'):
                        cleaned_description = cleaned_description[3:]  # Remove ```
                    if cleaned_description.endswith('```'):
                        cleaned_description = cleaned_description[:-3]  # Remove ```
                    
                    cleaned_description = cleaned_description.strip()
                    
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', cleaned_description, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        return result
                    else:
                        # If no JSON found, try to parse the entire response
                        result = json.loads(cleaned_description)
                        return result
                else:
                    return {
                        "disasters_detected": [],
                        "hazards_found": [],
                        "risk_level": "low",
                        "recommendations": ["No description available"],
                        "safe_direction": "unknown",
                        "emergency_contacts": [],
                        "confidence": 0.0
                    }
            except json.JSONDecodeError as e:
                # Fallback: create a basic response from the text
                print(f"⚠️ JSON parsing failed: {e}")
                print(f"Raw response: {description[:200]}...")
                
                return {
                    "disasters_detected": [],
                    "hazards_found": [],
                    "risk_level": "low",
                    "recommendations": [f"Analysis completed but parsing failed: {description[:100]}..."],
                    "safe_direction": "unknown",
                    "emergency_contacts": [],
                    "confidence": 0.0
                }
            
        except Exception as e:
            return {
                "disasters_detected": [],
                "hazards_found": [],
                "risk_level": "unknown",
                "recommendations": [f"Unable to analyze image: {e}"],
                "safe_direction": "unknown",
                "emergency_contacts": [],
                "confidence": 0.0
            }
    
    def analyze_scene_objects(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze scene for general object detection and navigation
        (Following working pattern from blind_navigation_assistant.py)
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Dict[str, Any]: Scene analysis results
        """
        try:
            # Convert base64 to image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = """
            You are a navigation assistant for visually impaired individuals. Analyze this image and provide detailed information about the scene.
            
            IMPORTANT: You must detect and list ALL objects you can see, no matter how small or seemingly unimportant. Even basic objects like walls, floors, chairs, tables, doors, windows, etc. are important for navigation.
            
            Provide your response in this JSON format:
            {
                "scene_description": "clear description of the scene",
                "objects": [
                    {
                        "name": "object_name",
                        "position": "front-left/front-right/center-left/center-right/back-left/back-right/center",
                        "distance": "close/medium/far",
                        "height": "floor/knee/waist/chest/head/above-head",
                        "accessibility": "easy/medium/hard"
                    }
                ],
                "obstacles": ["list of obstacles"],
                "safe_paths": ["available safe paths"],
                "navigation_instructions": ["step-by-step navigation guidance"]
            }
            
            Guidelines:
            - List EVERY object you can see (furniture, walls, doors, windows, items on surfaces, etc.)
            - Use "close" for objects within 2 meters, "medium" for 2-5 meters, "far" for 5+ meters
            - Use "easy" for easily reachable objects, "medium" for somewhat reachable, "hard" for difficult to reach
            - Be specific about object names (e.g., "wooden chair" not just "chair")
            - Include structural elements like walls, floors, ceilings if visible
            """
            
            response = self.vision_model.generate_content([prompt, image])
            description = response.text
            
            # Try to parse JSON response (following working pattern from blind_navigation_assistant.py)
            try:
                if description:
                    # Clean up the response - remove markdown code blocks if present
                    cleaned_description = description.strip()
                    if cleaned_description.startswith('```json'):
                        cleaned_description = cleaned_description[7:]  # Remove ```json
                    if cleaned_description.startswith('```'):
                        cleaned_description = cleaned_description[3:]  # Remove ```
                    if cleaned_description.endswith('```'):
                        cleaned_description = cleaned_description[:-3]  # Remove ```
                    
                    cleaned_description = cleaned_description.strip()
                    
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', cleaned_description, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        return result
                    else:
                        # If no JSON found, try to parse the entire response
                        result = json.loads(cleaned_description)
                        return result
                else:
                    return {
                        "scene_description": "No description available",
                        "objects": [],
                        "obstacles": [],
                        "safe_paths": [],
                        "navigation_instructions": ["No analysis available"]
                    }
            except json.JSONDecodeError as e:
                # Fallback: create a basic response from the text
                print(f"⚠️ JSON parsing failed: {e}")
                print(f"Raw response: {description[:200]}...")
                
                # Try to extract objects from the text response
                objects = []
                if description:
                    # Look for common object patterns in the text
                    import re
                    object_patterns = [
                        r'(\w+)\s+(?:chair|table|desk|bed|sofa|couch|lamp|door|window|wall|floor|ceiling)',
                        r'(?:I can see|there is|there are)\s+(\w+)',
                        r'(\w+)\s+(?:is|are)\s+(?:visible|seen|present)'
                    ]
                    
                    for pattern in object_patterns:
                        matches = re.findall(pattern, description, re.IGNORECASE)
                        for match in matches:
                            if match.lower() not in ['the', 'a', 'an', 'this', 'that', 'these', 'those']:
                                objects.append({
                                    "name": match,
                                    "position": "center",
                                    "distance": "medium",
                                    "height": "waist",
                                    "accessibility": "medium"
                                })
                
                return {
                    "scene_description": description or "Unable to analyze scene",
                    "objects": objects,
                    "obstacles": [],
                    "safe_paths": [],
                    "navigation_instructions": ["Try adjusting camera position or lighting for better detection"]
                }
            
        except Exception as e:
            return {
                "scene_description": "Unable to analyze scene",
                "objects": [],
                "obstacles": [],
                "safe_paths": [],
                "navigation_instructions": [f"Error analyzing scene: {e}"]
            }
    
    def get_camera_status(self) -> Dict[str, Any]:
        """
        Get camera status and capabilities
        
        Returns:
            Dict[str, Any]: Camera status information
        """
        try:
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                return {
                    "available": False,
                    "error": "Camera not accessible"
                }
            
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            
            return {
                "available": True,
                "resolution": f"{width}x{height}",
                "fps": fps,
                "index": self.camera_index
            }
            
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            } 