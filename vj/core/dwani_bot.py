"""
Dwani AI Bot - Main Bot Class
Orchestrates all components for disaster-aware navigation assistance
"""

from typing import Dict, Any, List, Optional, Tuple
from .config import DwaniConfig
from .speech_handler import SpeechHandler
from .vision_handler import VisionHandler
from .ai_processor import AIProcessor
from .navigation_handler import NavigationHandler
import time
import json

class DwaniAIBot:
    """
    Main Dwani AI Bot class that orchestrates all components
    """
    
    def __init__(self):
        """Initialize Dwani AI Bot with all components"""
        # Validate configuration
        if not DwaniConfig.validate_config():
            raise RuntimeError("Invalid configuration. Please check your API keys.")
        
        # Initialize components
        self.speech_handler = SpeechHandler()
        self.vision_handler = VisionHandler()
        self.ai_processor = AIProcessor()
        self.navigation_handler = NavigationHandler()
        
        # Bot state
        self.is_active = False
        self.current_mode = "idle"
        self.conversation_history = []
        self.last_disaster_analysis = None
        
        print("✅ Dwani AI Bot initialized successfully!")
    
    def start(self) -> bool:
        """Start the bot"""
        try:
            self.is_active = True
            self.current_mode = "active"
            print("🚀 Dwani AI Bot started")
            return True
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the bot"""
        try:
            self.is_active = False
            self.current_mode = "idle"
            print("⏹️ Dwani AI Bot stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop bot: {e}")
            return False
    
    def process_voice_command(self) -> Tuple[bool, str]:
        """
        Process voice command and generate response
        
        Returns:
            Tuple[bool, str]: (success, response)
        """
        try:
            # Listen to voice input
            success, transcribed_text = self.speech_handler.listen_to_voice()
            
            if not success:
                return False, "Failed to capture voice input"
            
            if not transcribed_text or transcribed_text.isspace():
                return False, "No speech detected"
            
            print(f"Voice input: {transcribed_text}")
            
            # First, check for emergency intent
            emergency_analysis = self.ai_processor.analyze_emergency_intent(transcribed_text)
            
            # If emergency detected, handle it immediately
            if emergency_analysis.get("is_emergency", False):
                emergency_type = emergency_analysis.get("emergency_type", "unknown")
                urgency_level = emergency_analysis.get("urgency_level", "medium")
                
                # Handle the emergency situation
                emergency_response = self.handle_emergency_situation(emergency_type, urgency_level)
                
                # Add to conversation history
                self.conversation_history.append({
                    "type": "voice_emergency",
                    "input": transcribed_text,
                    "output": emergency_response,
                    "emergency_type": emergency_type,
                    "urgency_level": urgency_level,
                    "timestamp": time.time()
                })
                
                return True, emergency_response
            
            # Process with AI normally
            response = self.ai_processor.process_user_message(transcribed_text)
            
            # Add to conversation history
            self.conversation_history.append({
                "type": "voice",
                "input": transcribed_text,
                "output": response,
                "timestamp": time.time()
            })
            
            # Speak the response
            if isinstance(response, dict):
                speak_text = response.get('speak', str(response))
            else:
                speak_text = str(response)
            
            self.speech_handler.speak_text(speak_text)
            
            return True, speak_text
            
        except Exception as e:
            error_msg = f"Error processing voice command: {e}"
            print(error_msg)
            return False, error_msg
    
    def process_text_message(self, message: str) -> str:
        """
        Process text message and generate response
        
        Args:
            message: Text message to process
            
        Returns:
            str: AI-generated response
        """
        try:
            # First, check for emergency intent
            emergency_analysis = self.ai_processor.analyze_emergency_intent(message)
            
            # If emergency detected, handle it immediately
            if emergency_analysis.get("is_emergency", False):
                emergency_type = emergency_analysis.get("emergency_type", "unknown")
                urgency_level = emergency_analysis.get("urgency_level", "medium")
                
                # Handle the emergency situation
                emergency_response = self.handle_emergency_situation(emergency_type, urgency_level)
                
                # Add to conversation history
                self.conversation_history.append({
                    "type": "emergency",
                    "input": message,
                    "output": emergency_response,
                    "emergency_type": emergency_type,
                    "urgency_level": urgency_level,
                    "timestamp": time.time()
                })
                
                return emergency_response
            
            # Process with AI normally
            response = self.ai_processor.process_user_message(message)
            
            # Add to conversation history
            self.conversation_history.append({
                "type": "text",
                "input": message,
                "output": response,
                "timestamp": time.time()
            })
            
            return response.get('speak', str(response)) if isinstance(response, dict) else str(response)
            
        except Exception as e:
            error_msg = f"Error processing text message: {e}"
            print(error_msg)
            return error_msg
    
    def analyze_environment(self) -> Dict[str, Any]:
        """
        Analyze current environment for disasters and hazards
        
        Returns:
            Dict[str, Any]: Environment analysis results
        """
        try:
            # Capture image
            success, image_data = self.vision_handler.capture_image()
            if not success or image_data is None:
                return {"error": image_data or "Failed to capture image"}
            
            # Analyze for disasters
            disaster_analysis = self.vision_handler.analyze_image_for_disasters(image_data)
            
            # Analyze scene objects
            scene_analysis = self.vision_handler.analyze_scene_objects(image_data)
            
            # Combine results
            analysis_result = {
                "timestamp": time.time(),
                "disaster_analysis": disaster_analysis,
                "scene_analysis": scene_analysis,
                "overall_risk": disaster_analysis.get("risk_level", "unknown")
            }
            
            self.last_disaster_analysis = analysis_result
            
            # Check if emergency response is needed
            risk_level = disaster_analysis.get("risk_level", "low")
            disasters_detected = disaster_analysis.get("disasters_detected", [])
            
            if risk_level in ["high", "critical"] and disasters_detected:
                # Determine emergency type from detected disasters
                emergency_type = self._determine_emergency_type(disasters_detected)
                
                # Handle emergency automatically
                emergency_response = self.handle_emergency_situation(emergency_type, risk_level)
                
                # Add emergency info to analysis result
                analysis_result["emergency_handled"] = True
                analysis_result["emergency_type"] = emergency_type
                analysis_result["emergency_response"] = emergency_response
            
            return analysis_result
            
        except Exception as e:
            return {"error": f"Error analyzing environment: {e}"}
    
    def _determine_emergency_type(self, disasters_detected: List[str]) -> str:
        """
        Determine emergency type from detected disasters
        
        Args:
            disasters_detected: List of detected disasters
            
        Returns:
            str: Emergency type
        """
        disasters_text = " ".join(disasters_detected).lower()
        
        if any(word in disasters_text for word in ["fire", "smoke", "flame"]):
            return "fire"
        elif any(word in disasters_text for word in ["flood", "water", "overflow"]):
            return "flood"
        elif any(word in disasters_text for word in ["earthquake", "tremor", "seismic"]):
            return "earthquake"
        elif any(word in disasters_text for word in ["structural", "collapse", "building"]):
            return "structural"
        elif any(word in disasters_text for word in ["chemical", "spill", "hazardous"]):
            return "chemical"
        elif any(word in disasters_text for word in ["gas", "leak", "explosion"]):
            return "gas_leak"
        else:
            return "general"
    
    def handle_emergency_situation(self, emergency_type: str, urgency_level: str) -> str:
        """
        Handle emergency situation with appropriate response
        
        Args:
            emergency_type: Type of emergency
            urgency_level: Urgency level
            
        Returns:
            str: Emergency response instructions
        """
        try:
            # Generate emergency response
            if urgency_level in ["high", "critical"]:
                response = f"🚨 EMERGENCY ALERT: {emergency_type.upper()} detected! "
                response += "Evacuate immediately and call emergency services."
                
                # Generate evacuation route
                evacuation_route = self.generate_emergency_evacuation(emergency_type)
                if evacuation_route:
                    response += f"\n\n{evacuation_route}"
                
                # Speak emergency alert
                self.speech_handler.speak_emergency_alert(response)
            else:
                response = f"⚠️ Warning: {emergency_type} detected. Please proceed with caution."
                self.speech_handler.speak_text(response)
            
            return response
            
        except Exception as e:
            return f"Error handling emergency: {e}"
    
    def generate_emergency_evacuation(self, emergency_type: str, current_location: str = "Heinrich-Heine-Allee, Düsseldorf") -> str:
        """
        Generate emergency evacuation route
        
        Args:
            emergency_type: Type of emergency
            current_location: Current location address
            
        Returns:
            str: Evacuation route instructions
        """
        try:
            print(f"🚨 Generating evacuation route for {emergency_type} emergency...")
            
            # Generate evacuation route
            route_info = self.navigation_handler.generate_evacuation_route(current_location, emergency_type)
            
            if not route_info:
                return "⚠️ Could not generate evacuation route. Please evacuate to the nearest safe location."
            
            # Format route instructions
            instructions = self.navigation_handler.format_route_instructions(route_info)
            
            # Speak route instructions
            self.speech_handler.speak_text(f"Emergency evacuation route generated. {route_info['safe_place']['name']} is {route_info['total_distance_meters']} meters away.")
            
            return instructions
            
        except Exception as e:
            print(f"Error generating evacuation route: {e}")
            return f"Error generating evacuation route: {e}"
    
    def get_safe_places(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available safe places
        
        Returns:
            Dict: Safe places information
        """
        return self.navigation_handler.get_all_safe_places()
    
    def navigate_to_safe_place(self, safe_place_key: str, current_location: str = "Heinrich-Heine-Allee, Düsseldorf") -> str:
        """
        Navigate to a specific safe place
        
        Args:
            safe_place_key: Key of the safe place to navigate to
            current_location: Current location address
            
        Returns:
            str: Navigation instructions
        """
        try:
            safe_places = self.navigation_handler.get_all_safe_places()
            
            if safe_place_key not in safe_places:
                return f"Safe place '{safe_place_key}' not found. Available places: {', '.join(safe_places.keys())}"
            
            # Generate route to specific safe place
            safe_place = safe_places[safe_place_key]
            route_info = self.navigation_handler.generate_evacuation_route(current_location, "general")
            
            if not route_info:
                return f"Could not generate route to {safe_place['name']}"
            
            instructions = self.navigation_handler.format_route_instructions(route_info)
            
            # Speak navigation start
            self.speech_handler.speak_text(f"Navigating to {safe_place['name']}. Distance: {route_info['total_distance_meters']} meters.")
            
            return instructions
            
        except Exception as e:
            return f"Error navigating to safe place: {e}"
    
    def get_navigation_guidance(self, destination: str) -> str:
        """
        Get navigation guidance to a destination
        
        Args:
            destination: Target destination
            
        Returns:
            str: Navigation instructions
        """
        try:
            # Get current environment analysis
            obstacles = []
            if self.last_disaster_analysis:
                obstacles = self.last_disaster_analysis.get("scene_analysis", {}).get("obstacles", [])
            
            # Generate navigation instructions
            instructions = self.ai_processor.generate_navigation_instructions(destination, obstacles)
            # Convert instructions dict to string
            instructions_text = instructions.get("instructions", "No instructions available")
            
            # Speak instructions
            self.speech_handler.speak_text(instructions_text)
            
            return instructions_text
            
        except Exception as e:
            return f"Error getting navigation guidance: {e}"
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Dict[str, Any]: System status information
        """
        try:
            # Test speech system
            speech_status = self.speech_handler.test_speech_system()
            
            # Get camera status
            camera_status = self.vision_handler.get_camera_status()
            
            # Get configuration summary
            config_summary = DwaniConfig.get_config_summary()
            
            return {
                "bot_status": {
                    "is_active": self.is_active,
                    "current_mode": self.current_mode,
                    "conversation_count": len(self.conversation_history)
                },
                "speech_system": speech_status,
                "camera_system": camera_status,
                "configuration": config_summary,
                "last_analysis": self.last_disaster_analysis is not None
            }
            
        except Exception as e:
            return {"error": f"Error getting system status: {e}"}
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation history
        
        Args:
            limit: Number of recent conversations to return
            
        Returns:
            List[Dict[str, Any]]: Conversation history
        """
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def clear_conversation_history(self) -> bool:
        """Clear conversation history"""
        try:
            self.conversation_history.clear()
            return True
        except Exception as e:
            print(f"Error clearing conversation history: {e}")
            return False
    
    def speech_mode_loop(self):
        import json
        from datetime import datetime
        print("Speech mode loop started!")
        STOP_WORDS = {"stop", "exit", "quit", "goodbye"}
        messages = []
        try:
            while True:
                print("Top of loop")
                try:
                    # Record and transcribe
                    success, transcribed_text = self.speech_handler.listen_to_voice()
                    print("After listen_to_voice",success,transcribed_text)
                    if not success:
                        print("No valid input, waiting...")
                        continue
                    print(f"User: {transcribed_text}")
                    if transcribed_text.strip().lower() in STOP_WORDS:
                        print("User requested to stop. Exiting speech mode.")
                        break

                    # Check for emergency intent first
                    emergency_analysis = self.ai_processor.analyze_emergency_intent(transcribed_text)
                    
                    # If emergency detected, handle it immediately
                    if emergency_analysis.get("is_emergency", False):
                        emergency_type = emergency_analysis.get("emergency_type", "unknown")
                        urgency_level = emergency_analysis.get("urgency_level", "medium")
                        
                        print(f"🚨 EMERGENCY DETECTED: {emergency_type} ({urgency_level})")
                        
                        # Handle the emergency situation
                        emergency_response = self.handle_emergency_situation(emergency_type, urgency_level)
                        
                        # Add to messages
                        user_message = {"role": "user", "content": transcribed_text}
                        messages.append(user_message)
                        messages.append({"role": "assistant", "content": emergency_response})
                        
                        # Add to conversation history
                        self.conversation_history.append({
                            "type": "speech_emergency",
                            "input": transcribed_text,
                            "output": emergency_response,
                            "emergency_type": emergency_type,
                            "urgency_level": urgency_level,
                            "timestamp": time.time()
                        })
                        
                        continue  # Continue listening for more input

                    # (Optional) Add context, e.g., image/environment
                    # For now, just use user text
                    user_message = {"role": "user", "content": transcribed_text}
                    messages.append(user_message)

                    # Process with AI (pass full message history for context)
                    response = self.ai_processor.process_user_message(transcribed_text, context=None)

                    # Tool/function call handling (pseudo, adapt as needed)
                    # If your AI returns tool calls, handle them here
                    # Example:
                    # if hasattr(response, "tool_calls") and response.tool_calls:
                    #     for tool_call in response.tool_calls:
                    #         ... handle tool call, append result to messages ...
                    #     # Re-query AI with updated messages
                    #     response = self.ai_processor.process_user_message(transcribed_text, context=None)

                    print("After process_user_message")
                    if isinstance(response, dict):
                        speak_text = response.get('speak', str(response))
                    else:
                        speak_text = str(response)
                    print(f"Assistant: {speak_text}")
                    self.speech_handler.speak_text(speak_text)
                    messages.append({"role": "assistant", "content": speak_text})
                    print("End of loop")
                except Exception as e:
                    print(f"Exception in loop: {e}")
        except KeyboardInterrupt:
            print("Speech mode loop interrupted by user.")
        except Exception as e:
            print(f"Fatal error in speech mode: {e}")
        finally:
            with open("conversation_history.json", "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            print("Speech mode loop ended and conversation saved!")
    
    def trigger_emergency_test(self, emergency_type: str = "fire", urgency_level: str = "high") -> str:
        """
        Manually trigger emergency handling for testing
        
        Args:
            emergency_type: Type of emergency to test
            urgency_level: Urgency level to test
            
        Returns:
            str: Emergency response
        """
        print(f"🧪 Testing emergency handling: {emergency_type} ({urgency_level})")
        return self.handle_emergency_situation(emergency_type, urgency_level)
    
    def get_emergency_status(self) -> Dict[str, Any]:
        """
        Get current emergency status and history
        
        Returns:
            Dict[str, Any]: Emergency status information
        """
        try:
            # Get recent emergency events from conversation history
            emergency_events = []
            for entry in self.conversation_history[-20:]:  # Last 20 entries
                if entry.get("type", "").endswith("emergency"):
                    emergency_events.append({
                        "timestamp": entry.get("timestamp"),
                        "emergency_type": entry.get("emergency_type"),
                        "urgency_level": entry.get("urgency_level"),
                        "input": entry.get("input", "")[:100] + "..." if len(entry.get("input", "")) > 100 else entry.get("input", "")
                    })
            
            return {
                "has_active_emergency": len(emergency_events) > 0,
                "recent_emergencies": emergency_events,
                "total_emergency_events": len([e for e in self.conversation_history if e.get("type", "").endswith("emergency")]),
                "last_analysis_risk": self.last_disaster_analysis.get("overall_risk", "unknown") if self.last_disaster_analysis else "unknown"
            }
            
        except Exception as e:
            return {"error": f"Error getting emergency status: {e}"} 