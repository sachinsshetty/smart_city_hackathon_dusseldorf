import google.generativeai as genai
import json
from datetime import datetime
import pytz
import cv2
import os
import tempfile
import base64
import numpy as np
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
import math
import dotenv
import PIL.Image

# Import configuration
try:
    from config import Config
except ImportError:
    # Fallback if config.py doesn't exist
    class Config:
        @staticmethod
        def get_tool_server_url():
            return os.getenv("API_SERVER", "https://generativelanguage.googleapis.com/v1beta")
        
        @staticmethod
        def get_vision_server_url():
            return os.getenv("API_SERVER_VLM", "https://generativelanguage.googleapis.com/v1beta")

# Global variables
send_image = False
selected_object = None
navigation_mode = False
current_frame = None
object_positions = {}

dotenv.load_dotenv()

class BlindNavigationAssistant:
    def __init__(self):
        # Initialize Google Gemini API
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("❌ GOOGLE_API_KEY is not set! Please set it in your .env file.")
            raise RuntimeError("GOOGLE_API_KEY is required for Google Gemini API.")
        
        print("=== Blind Navigation Assistant Initialization ===")
        print(f"Using Google Gemini API")
        
        try:
            # Configure Google Gemini API
            genai.configure(api_key=self.api_key)
            
            # Initialize models
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
            self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
            
            print("✅ Google Gemini API clients initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Google Gemini API clients: {e}")
            raise
        
        # Camera parameters (assuming standard webcam)
        self.camera_fov = 60  # degrees
        self.camera_height = 1.6  # meters (average human height)
        self.frame_width = 640
        self.frame_height = 480
        
        # Navigation state
        self.user_position = (0, 0, 0)  # (x, y, z) in meters
        self.user_orientation = 0  # degrees (0 = forward)
        
    def mouse_callback(self, event: int, x: int, y: int, flags: int, param: Any) -> None:
        global send_image, selected_object, navigation_mode
        if event == cv2.EVENT_LBUTTONDOWN:
            if navigation_mode and object_positions:
                # Find closest object to click
                min_distance = float('inf')
                closest_object = None
                for obj_name, (obj_x, obj_y, obj_z) in object_positions.items():
                    distance = math.sqrt((x - obj_x)**2 + (y - obj_y)**2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_object = obj_name
                
                if closest_object and min_distance < 50:  # Within 50 pixels
                    selected_object = closest_object
                    send_image = True
            else:
                send_image = True

    def capture_webcam_image(self) -> Dict[str, str]:
        """Capture and process webcam image for analysis"""
        global send_image, current_frame, navigation_mode
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return {"error": "Failed to open webcam"}

            ret, frame = cap.read()
            if not ret:
                cap.release()
                return {"error": "Failed to capture image from webcam"}

            current_frame = frame.copy()
            
            # Display the captured frame
            cv2.namedWindow("Blind Navigation Assistant")
            cv2.setMouseCallback("Blind Navigation Assistant", self.mouse_callback)
            send_image = False

            # Show instructions
            instructions = "Click to analyze scene" if not navigation_mode else "Click on object to navigate to"
            cv2.putText(frame, instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit, 'n' for navigation mode", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            while True:
                cv2.imshow("Blind Navigation Assistant", frame)
                key = cv2.waitKey(1) & 0xFF
                if send_image or key == ord('q'):
                    break
                elif key == ord('n'):
                    navigation_mode = not navigation_mode
                    instructions = "Click to analyze scene" if not navigation_mode else "Click on object to navigate to"
                    cv2.putText(frame, instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.destroyAllWindows()
            cap.release()

            if not send_image:
                return {"error": "Image not sent (user closed window without clicking)"}

            # Save and process the frame
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = temp_file.name
                cv2.imwrite(temp_path, frame)

            with open(temp_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_path}: {str(e)}")

            return {"image_path": temp_path, "base64_image": base64_image}

        except Exception as e:
            return {"error": f"Error capturing webcam image: {str(e)}"}

    def analyze_scene(self, base64_image: str) -> Dict[str, Any]:
        """Analyze scene and detect objects with positions"""
        try:
            # Enhanced prompt for detailed scene analysis
            prompt = """
            You are a specialized AI assistant for blind navigation. Analyze this image and provide detailed information about ALL visible objects.

            IMPORTANT: You must detect and list ALL objects you can see, no matter how small or seemingly unimportant. Even basic objects like walls, floors, chairs, tables, doors, windows, etc. are important for navigation.

            Provide your response in this EXACT JSON format:
            {
                "scene_description": "A clear description of what you see in the scene",
                "objects": [
                    {
                        "name": "object_name",
                        "position": "front-left/front-right/center-left/center-right/back-left/back-right/center",
                        "distance": "close/medium/far",
                        "height": "floor/knee/waist/chest/head/above-head",
                        "accessibility": "easy/medium/hard"
                    }
                ],
                "hazards": ["list any potential hazards"],
                "recommendations": ["navigation tips"]
            }

            Guidelines:
            - List EVERY object you can see (furniture, walls, doors, windows, items on surfaces, etc.)
            - Use "close" for objects within 2 meters, "medium" for 2-5 meters, "far" for 5+ meters
            - Use "easy" for easily reachable objects, "medium" for somewhat reachable, "hard" for difficult to reach
            - Be specific about object names (e.g., "wooden chair" not just "chair")
            - Include structural elements like walls, floors, ceilings if visible
            """
            
            # Convert base64 to image for Google Gemini
            image_data = base64.b64decode(base64_image)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Load image for Google Gemini using PIL
                image = PIL.Image.open(temp_path)
                
                # Generate content with image
                response = self.vision_model.generate_content([prompt, image])
                description = response.text
                
            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            # Try to parse JSON response
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
                        scene_data = json.loads(json_str)
                        return scene_data
                    else:
                        # If no JSON found, try to parse the entire response
                        scene_data = json.loads(cleaned_description)
                        return scene_data
                else:
                    return {
                        "scene_description": "No description available",
                        "objects": [],
                        "hazards": [],
                        "recommendations": []
                    }
            except json.JSONDecodeError as e:
                # Fallback: create a basic response from the text
                print(f"⚠️  JSON parsing failed: {e}")
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
                    "scene_description": description or "No description available",
                    "objects": objects,
                    "hazards": [],
                    "recommendations": ["Try adjusting camera position or lighting for better detection"]
                }
                
        except Exception as e:
            return {"error": f"Failed to analyze scene: {str(e)}"}

    def estimate_object_positions(self, objects: List[Dict[str, Any]]) -> Dict[str, Tuple[int, int, float]]:
        """Estimate pixel positions for objects based on their descriptions"""
        global object_positions
        object_positions = {}
        
        # Simple heuristic positioning based on object descriptions
        for i, obj in enumerate(objects):
            name = obj.get("name", f"object_{i}")
            position = obj.get("position", "center")
            distance = obj.get("distance", "medium")
            
            # Convert relative positions to approximate pixel coordinates
            x, y = self.position_to_pixels(position)
            
            # Adjust based on distance
            if distance == "close":
                z = 1.0  # 1 meter
            elif distance == "far":
                z = 5.0  # 5 meters
            else:
                z = 2.5  # 2.5 meters
            
            object_positions[name] = (x, y, z)
        
        return object_positions

    def position_to_pixels(self, position: str) -> Tuple[int, int]:
        """Convert relative position description to pixel coordinates"""
        if "front" in position and "left" in position:
            return (self.frame_width // 4, self.frame_height // 2)
        elif "front" in position and "right" in position:
            return (3 * self.frame_width // 4, self.frame_height // 2)
        elif "center" in position:
            return (self.frame_width // 2, self.frame_height // 2)
        elif "left" in position:
            return (self.frame_width // 4, self.frame_height // 2)
        elif "right" in position:
            return (3 * self.frame_width // 4, self.frame_height // 2)
        else:
            return (self.frame_width // 2, self.frame_height // 2)

    def generate_navigation_instructions(self, target_object: str, object_data: Dict[str, Any]) -> str:
        """Generate step-by-step navigation instructions"""
        try:
            position = object_data.get("position", "center")
            distance = object_data.get("distance", "medium")
            height = object_data.get("height", "waist")
            accessibility = object_data.get("accessibility", "medium")
            
            # Generate natural language instructions
            instructions = []
            
            # Distance-based instructions with more detail
            if distance == "close":
                instructions.append("The object is very close to you (within 2 meters).")
                steps = "Take 1-2 small steps forward"
                reach_distance = "within arm's reach"
            elif distance == "far":
                instructions.append("The object is quite far away (5+ meters).")
                steps = "Take 5-7 steps forward"
                reach_distance = "several steps away"
            else:
                instructions.append("The object is at a moderate distance (2-5 meters).")
                steps = "Take 3-4 steps forward"
                reach_distance = "a few steps away"
            
            # Direction-based instructions with more precision
            if "left" in position:
                instructions.append(f"Turn 30 degrees to your left. {steps}.")
            elif "right" in position:
                instructions.append(f"Turn 30 degrees to your right. {steps}.")
            elif "center" in position:
                instructions.append(f"{steps} straight ahead.")
            else:
                instructions.append(f"{steps}.")
            
            # Height and accessibility information
            instructions.append(f"The {target_object} is at {height} height and is {reach_distance}.")
            
            # Accessibility warnings
            if accessibility == "hard":
                instructions.append("⚠️ This object may be difficult to reach safely.")
            elif accessibility == "easy":
                instructions.append("This object should be easy to reach.")
            
            # Add safety warnings for hazardous objects
            if any(word in target_object.lower() for word in ["sharp", "hot", "fragile", "dangerous", "hazard"]):
                instructions.append("⚠️ WARNING: This object may be dangerous. Proceed with extreme caution.")
            
            return " ".join(instructions)
            
        except Exception as e:
            return f"Error generating navigation instructions: {str(e)}"

    def handle_edge_cases(self, scene_data: Dict[str, Any]) -> str:
        """Handle edge cases like no objects detected, multiple similar objects, etc."""
        objects = scene_data.get("objects", [])
        
        if not objects:
            return "No clear objects detected. Try adjusting your camera position, improving lighting, or moving closer to objects."
        
        # Check for multiple similar objects
        object_names = [obj.get("name", "") for obj in objects]
        duplicates = [name for name in set(object_names) if object_names.count(name) > 1]
        
        if duplicates:
            return f"Multiple {duplicates[0]}s detected. Please be more specific about which one you want to navigate to."
        
        # Check for unclear directions
        unclear_objects = []
        for obj in objects:
            if obj.get("accessibility") == "hard" or "behind" in obj.get("position", ""):
                unclear_objects.append(obj.get("name"))
        
        if unclear_objects:
            return f"Some objects ({', '.join(unclear_objects)}) may be difficult to reach or behind obstacles. Consider choosing a different object."
        
        return "Scene analysis complete! You can now select an object to navigate to."

    def run_navigation_assistant(self) -> None:
        """Main function to run the blind navigation assistant"""
        global send_image, selected_object, navigation_mode
        
        print("=" * 60)
        print("🎯 BLIND NAVIGATION ASSISTANT")
        print("=" * 60)
        print("📋 Instructions:")
        print("   • Click anywhere on the camera window to analyze the scene")
        print("   • Press 'n' to toggle navigation mode")
        print("   • In navigation mode, click on objects to get directions")
        print("   • Press 'q' to quit")
        print("=" * 60)
        print()
        
        while True:
            try:
                # Capture image
                image_data = self.capture_webcam_image()
                if "error" in image_data:
                    print(f"❌ Error: {image_data['error']}")
                    continue
                
                # Analyze scene
                print("🔍 Analyzing scene...")
                scene_data = self.analyze_scene(image_data["base64_image"])
                
                if "error" in scene_data:
                    print(f"❌ Analysis error: {scene_data['error']}")
                    continue
                
                # Handle edge cases
                edge_case_message = self.handle_edge_cases(scene_data)
                print(f"ℹ️  {edge_case_message}")
                
                # Display scene description
                scene_desc = scene_data.get('scene_description', 'No description available')
                print(f"\n📸 SCENE DESCRIPTION:")
                print(f"   {scene_desc}")
                
                # List available objects with better formatting
                objects = scene_data.get("objects", [])
                if objects:
                    print(f"\n🎯 DETECTED OBJECTS ({len(objects)} found):")
                    print("-" * 40)
                    
                    for i, obj in enumerate(objects, 1):
                        name = obj.get("name", f"Object {i}")
                        position = obj.get("position", "unknown position")
                        distance = obj.get("distance", "unknown distance")
                        height = obj.get("height", "unknown height")
                        accessibility = obj.get("accessibility", "unknown")
                        
                        # Create accessibility icon
                        access_icon = "🟢" if accessibility == "easy" else "🟡" if accessibility == "medium" else "🔴"
                        
                        print(f"   {i:2d}. {name}")
                        print(f"       📍 Position: {position}")
                        print(f"       📏 Distance: {distance}")
                        print(f"       📐 Height: {height}")
                        print(f"       {access_icon} Accessibility: {accessibility}")
                        print()
                else:
                    print("\n❌ No objects detected in the scene.")
                
                # Estimate object positions for navigation
                if navigation_mode:
                    self.estimate_object_positions(objects)
                    print("🎯 NAVIGATION MODE ACTIVE")
                    print("   Click on an object in the camera window to get directions!")
                
                # If object was selected, generate navigation instructions
                if selected_object and navigation_mode:
                    print(f"\n🗺️ GENERATING NAVIGATION INSTRUCTIONS")
                    print(f"   Target: {selected_object}")
                    print("-" * 50)
                    
                    # Find the selected object data
                    target_object_data = None
                    for obj in objects:
                        if obj.get("name") == selected_object:
                            target_object_data = obj
                            break
                    
                    if target_object_data:
                        instructions = self.generate_navigation_instructions(selected_object, target_object_data)
                        print("📋 STEP-BY-STEP INSTRUCTIONS:")
                        print("   " + instructions.replace(". ", ".\n   "))
                        
                        # Add additional safety tips
                        print("\n⚠️  SAFETY REMINDERS:")
                        print("   • Always verify the object's position before moving")
                        print("   • Use your cane or guide dog as additional assistance")
                        print("   • Move slowly and carefully")
                        print("   • If unsure, ask for help")
                    else:
                        print(f"❌ Could not find data for {selected_object}")
                    
                    selected_object = None
                
                print("\n" + "=" * 60)
                print("Ready for next analysis...")
                print("=" * 60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Thank you for using the Blind Navigation Assistant!")
                print("   Stay safe and have a great day!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                print("   Please try again...")
                continue

def main():
    assistant = BlindNavigationAssistant()
    assistant.run_navigation_assistant()

if __name__ == "__main__":
    main()
