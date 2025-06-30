"""
AI Processor Module for Dwani AI
Handles Gemini text processing and natural language understanding with intelligent conversation context
"""

import google.generativeai as genai
import json
from typing import Dict, Any, List, Optional, Tuple
from .config import DwaniConfig

class AIProcessor:
    """Handles AI text processing and natural language understanding with conversation memory"""
    
    def __init__(self):
        """Initialize AI processor with Gemini text model and conversation context"""
        if not DwaniConfig.GEMINI_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is required for AI processing")
        
        # Configure Gemini API (following working pattern from assistant_v5.py)
        genai.configure(api_key=DwaniConfig.GEMINI_API_KEY)  # type: ignore
        self.text_model = genai.GenerativeModel(DwaniConfig.GEMINI_TEXT_MODEL)  # type: ignore
        
        # Initialize conversation context
        self.conversation_history = []
        self.system_message = {
            "role": "system",
            "content": """You are Dwani AI, a voice-based urban disaster assistant for smart cities. 
            
Your core capabilities:
- Detect and analyze hazards from the environment
- Help users evacuate safely during emergencies
- Provide clear navigation guidance
- Answer questions about safety and urban navigation
- Maintain calm, authoritative communication

Always respond with:
1. A clear, calm voice message for the user
2. If needed, a JSON object with structured actions

Response format:
{
  "speak": "Your voice message to the user",
  "action": "navigate|wait|warn|analyze|none",
  "direction": "left|right|forward|backward|none",
  "distance": "estimated_distance_in_meters",
  "urgency": "low|medium|high|critical",
  "hazards_detected": ["list", "of", "hazards"],
  "safe_direction": "direction_to_safety"
}

Stay focused on safety, be concise but informative, and always prioritize user safety."""
        }
        
        # Initialize conversation with system message
        self.conversation_history.append(self.system_message)
    
    def process_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message with conversation context and environmental awareness
        
        Args:
            message: User's message
            context: Environmental context (location, hazards, etc.)
            
        Returns:
            Dict[str, Any]: Structured response with voice message and actions
        """
        try:
            # Build context-aware prompt
            context_info = ""
            if context:
                hazards = context.get('hazards', [])
                location = context.get('location', 'unknown')
                safe_places = context.get('safe_places', [])
                
                context_info = f"""
Live Situation:
- User Location: {location}
- Detected Hazards: {', '.join(hazards) if hazards else 'None detected'}
- Nearest Safe Places: {', '.join(safe_places[:3]) if safe_places else 'None identified'}

"""
            
            # Add user message to conversation
            user_message = {
                "role": "user", 
                "content": f"{context_info}User says: {message}"
            }
            
            # Build full conversation for context
            full_conversation = self.conversation_history + [user_message]
            
            # Create conversation prompt
            conversation_text = "\n".join([
                f"{msg['role'].title()}: {msg['content']}" 
                for msg in full_conversation
            ])
            
            # Generate response with conversation context
            response = self.text_model.generate_content(conversation_text)
            response_text = response.text
            
            # Parse structured response
            structured_response = self._parse_structured_response(response_text, message)
            
            # Add to conversation history
            self.conversation_history.append(user_message)
            self.conversation_history.append({
                "role": "assistant",
                "content": structured_response.get('speak', response_text)
            })
            
            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history) > 21:  # system + 10 exchanges
                self.conversation_history = [self.system_message] + self.conversation_history[-20:]
            
            return structured_response
            
        except Exception as e:
            return {
                "speak": f"I'm sorry, I encountered an error processing your message: {e}",
                "action": "none",
                "direction": "none",
                "distance": 0,
                "urgency": "low",
                "hazards_detected": [],
                "safe_direction": "none"
            }
    
    def _parse_structured_response(self, response_text: str, original_message: str) -> Dict[str, Any]:
        """Parse structured response from Gemini"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                # Clean up the JSON string
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                result = json.loads(json_str)
                
                # Ensure all required fields are present
                default_response = {
                    "speak": response_text,
                    "action": "none",
                    "direction": "none", 
                    "distance": 0,
                    "urgency": "low",
                    "hazards_detected": [],
                    "safe_direction": "none"
                }
                
                # Merge with defaults
                for key, value in default_response.items():
                    if key not in result:
                        result[key] = value
                
                return result
            else:
                # No JSON found, create structured response from text
                return {
                    "speak": response_text,
                    "action": "none",
                    "direction": "none",
                    "distance": 0,
                    "urgency": "low",
                    "hazards_detected": [],
                    "safe_direction": "none"
                }
                
        except Exception as e:
            print(f"⚠️ JSON parsing failed: {e}")
            return {
                "speak": response_text,
                "action": "none",
                "direction": "none",
                "distance": 0,
                "urgency": "low",
                "hazards_detected": [],
                "safe_direction": "none"
            }
    
    def analyze_emergency_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze message for emergency intent with context awareness
        
        Args:
            message: User's message
            context: Environmental context
            
        Returns:
            Dict[str, Any]: Emergency analysis results
        """
        try:
            context_info = ""
            if context:
                hazards = context.get('hazards', [])
                location = context.get('location', 'unknown')
                context_info = f"Context: Location={location}, Hazards={hazards}. "
            
            prompt = f"""
{context_info}Analyze this message for emergency intent and urgency:
"{message}"

Provide response in JSON format:
{{
    "is_emergency": true/false,
    "urgency_level": "low/medium/high/critical",
    "detected_hazards": ["list of hazards mentioned"],
    "required_action": "immediate action needed",
    "emergency_type": "fire/flood/medical/structural/other",
    "speak": "voice message for user"
}}
"""
            
            response = self.text_model.generate_content(prompt)
            description = response.text
            
            # Parse JSON response
            try:
                if description:
                    cleaned_description = description.strip()
                    if cleaned_description.startswith('```json'):
                        cleaned_description = cleaned_description[7:]
                    if cleaned_description.startswith('```'):
                        cleaned_description = cleaned_description[3:]
                    if cleaned_description.endswith('```'):
                        cleaned_description = cleaned_description[:-3]
                    
                    cleaned_description = cleaned_description.strip()
                    
                    import re
                    json_match = re.search(r'\{.*\}', cleaned_description, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        return result
                    else:
                        result = json.loads(cleaned_description)
                        return result
                else:
                    return {
                        "is_emergency": False,
                        "urgency_level": "low",
                        "detected_hazards": [],
                        "required_action": "none",
                        "emergency_type": "none",
                        "speak": "No analysis available"
                    }
            except (json.JSONDecodeError, SyntaxError) as e:
                print(f"⚠️ JSON parsing failed: {e}")
                return {
                    "is_emergency": False,
                    "urgency_level": "low",
                    "detected_hazards": [],
                    "required_action": "none",
                    "emergency_type": "none",
                    "speak": f"Analysis completed but parsing failed: {description[:100]}..."
                }
            
        except Exception as e:
            return {
                "is_emergency": False,
                "urgency_level": "low",
                "detected_hazards": [],
                "required_action": "none",
                "emergency_type": "none",
                "speak": f"Error analyzing emergency intent: {e}"
            }
    
    def generate_navigation_instructions(self, destination: str, obstacles: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate navigation instructions with context awareness
        
        Args:
            destination: Target destination
            obstacles: List of known obstacles
            context: Environmental context
            
        Returns:
            Dict[str, Any]: Navigation instructions with actions
        """
        try:
            context_info = ""
            if context:
                hazards = context.get('hazards', [])
                location = context.get('location', 'unknown')
                context_info = f"Current location: {location}. Hazards: {', '.join(hazards)}. "
            
            obstacles_text = ", ".join(obstacles) if obstacles else "none"
            
            prompt = f"""
{context_info}Generate navigation instructions to reach: {destination}
Known obstacles: {obstacles_text}

Provide step-by-step instructions that are:
- Clear and easy to follow
- Include distance estimates
- Mention any safety considerations
- Suitable for visually impaired individuals

Respond with:
{{
    "speak": "voice navigation instructions",
    "action": "navigate",
    "direction": "initial_direction",
    "distance": "estimated_distance",
    "steps": ["step1", "step2", "step3"],
    "safety_warnings": ["warning1", "warning2"]
}}
"""
            
            response = self.text_model.generate_content(prompt)
            description = response.text
            
            # Parse structured response
            structured_response = self._parse_structured_response(description, f"Navigate to {destination}")
            return structured_response
            
        except Exception as e:
            return {
                "speak": f"Unable to generate navigation instructions: {e}",
                "action": "none",
                "direction": "none",
                "distance": 0,
                "urgency": "low",
                "hazards_detected": [],
                "safe_direction": "none"
            }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation history"""
        return {
            "total_exchanges": len(self.conversation_history) - 1,  # Exclude system message
            "recent_messages": self.conversation_history[-6:] if len(self.conversation_history) > 1 else [],
            "has_emergency_context": any("emergency" in msg.get("content", "").lower() for msg in self.conversation_history)
        }
    
    def clear_conversation_history(self):
        """Clear conversation history but keep system message"""
        self.conversation_history = [self.system_message]
    
    def extract_location_intent(self, message: str) -> Dict[str, Any]:
        """
        Extract location and navigation intent from message
        
        Args:
            message: User's message
            
        Returns:
            Dict[str, Any]: Location analysis results
        """
        try:
            prompt = f"""
            Extract location and navigation intent from this message:
            "{message}"
            
            Provide response in JSON format:
            {{
                "intent": "navigate_to/avoid/check_safety/other",
                "location": "extracted location name",
                "location_type": "hospital/shelter/police/fire_station/other",
                "urgency": "low/medium/high",
                "distance_mentioned": "any distance mentioned"
            }}
            """
            
            response = self.text_model.generate_content(prompt)
            description = response.text
            
            # Try to parse JSON response (following working pattern)
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
                        result = eval(json_str)
                        return result
                    else:
                        # If no JSON found, try to parse the entire response
                        result = eval(cleaned_description)
                        return result
                else:
                    return {
                        "intent": "other",
                        "location": "",
                        "location_type": "other",
                        "urgency": "low",
                        "distance_mentioned": ""
                    }
            except (json.JSONDecodeError, SyntaxError) as e:
                # Fallback: create a basic response
                print(f"⚠️ JSON parsing failed: {e}")
                print(f"Raw response: {description[:200]}...")
                
                return {
                    "intent": "other",
                    "location": "",
                    "location_type": "other",
                    "urgency": "low",
                    "distance_mentioned": ""
                }
            
        except Exception as e:
            return {
                "intent": "other",
                "location": "",
                "location_type": "other",
                "urgency": "low",
                "distance_mentioned": ""
            }
    
    def generate_safety_recommendations(self, risk_level: str, hazards: List[str]) -> List[str]:
        """
        Generate safety recommendations based on risk level and hazards
        
        Args:
            risk_level: Risk level (low/medium/high/critical)
            hazards: List of detected hazards
            
        Returns:
            List[str]: Safety recommendations
        """
        try:
            hazards_text = ", ".join(hazards)
            
            prompt = f"""
            Generate safety recommendations for:
            Risk Level: {risk_level}
            Hazards: {hazards_text}
            
            Provide a list of specific, actionable safety recommendations.
            """
            
            response = self.text_model.generate_content(prompt)
            # Parse response into list (assuming it's formatted as a list)
            recommendations = [rec.strip() for rec in response.text.split('\n') if rec.strip()]
            return recommendations
            
        except Exception as e:
            return [f"Unable to generate recommendations: {e}"] 