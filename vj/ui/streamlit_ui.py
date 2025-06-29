"""
Streamlit UI for Dwani AI
Provides a clean, modern interface for the disaster-aware navigation assistant
"""

import streamlit as st
import sys
import os
import time
import json
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.dwani_bot import DwaniAIBot
    from core.config import DwaniConfig
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.info("Please ensure all core modules are properly installed.")

class DwaniAIUI:
    """Streamlit UI for Dwani AI"""
    
    def __init__(self):
        """Initialize the UI"""
        self.setup_page_config()
        self.setup_custom_css()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="Dwani AI - Disaster-Aware Navigation Assistant",
            page_icon="🏙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_custom_css(self):
        """Setup custom CSS styling"""
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .mode-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            border: 2px solid #e9ecef;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .emergency-alert {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            animation: pulse 2s infinite;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active { background-color: #28a745; }
        .status-inactive { background-color: #dc3545; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'dwani_bot' not in st.session_state:
            st.session_state.dwani_bot = None
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_mode' not in st.session_state:
            st.session_state.current_mode = "Chat Mode"
        if 'system_status' not in st.session_state:
            st.session_state.system_status = None
    
    def render_header(self):
        """Render the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>🏙️ Dwani AI</h1>
            <p>Voice-guided AI navigation and disaster awareness assistant for Smart Cities</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the sidebar with controls and information"""
        with st.sidebar:
            st.title("🎛️ Controls")
            
            # Bot status
            if st.session_state.dwani_bot:
                status = "Active" if st.session_state.dwani_bot.is_active else "Inactive"
                status_color = "status-active" if st.session_state.dwani_bot.is_active else "status-inactive"
                st.markdown(f'<span class="status-indicator {status_color}"></span>Bot Status: {status}', unsafe_allow_html=True)
            
            # Mode selection
            st.session_state.current_mode = st.selectbox(
                "Choose Mode",
                ["Chat Mode", "Voice Mode", "Speech Mode", "Disaster Detection Mode", "System Status"]
            )
            
            # Bot controls
            if st.session_state.dwani_bot:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Start Bot"):
                        st.session_state.dwani_bot.start()
                        st.success("Bot started!")
                        st.rerun()
                
                with col2:
                    if st.button("⏹️ Stop Bot"):
                        st.session_state.dwani_bot.stop()
                        st.success("Bot stopped!")
                        st.rerun()
            
            # System information
            st.markdown("---")
            st.markdown("### ℹ️ About Dwani AI")
            st.markdown("""
            - **Voice Commands**: "Is there fire?", "Guide me to safety"
            - **Speech Mode**: Continuous, hands-free conversation
            - **Disaster Detection**: Real-time hazard identification
            - **Navigation**: Safe path recommendations
            - **Emergency Response**: Immediate safety guidance
            """)
    
    def render_chat_mode(self):
        """Render chat mode interface"""
        st.subheader("💬 Chat Mode")
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask Dwani AI anything..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process with bot
            if st.session_state.dwani_bot:
                with st.chat_message("assistant"):
                    with st.spinner("Processing..."):
                        response = st.session_state.dwani_bot.process_text_message(prompt)
                        if isinstance(response, dict):
                            st.markdown(response.get('speak', str(response)))
                        else:
                            st.markdown(str(response))
                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": response.get('speak', str(response)) if isinstance(response, dict) else str(response)})
            else:
                st.error("Bot not initialized")
    
    def render_voice_mode(self):
        """Render voice mode interface"""
        st.subheader("🎤 Voice Mode")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Voice Commands")
            if st.button("🎤 Start Voice Input"):
                if st.session_state.dwani_bot:
                    with st.spinner("Listening..."):
                        success, response = st.session_state.dwani_bot.process_voice_command()
                        if success:
                            if isinstance(response, dict):
                                st.success(response.get('speak', str(response)))
                            else:
                                st.success(str(response))
                        else:
                            st.error(str(response))
                else:
                    st.error("Bot not initialized")
        
        with col2:
            st.markdown("### Environment Analysis")
            if st.button("📷 Analyze Environment"):
                if st.session_state.dwani_bot:
                    with st.spinner("Analyzing environment..."):
                        analysis = st.session_state.dwani_bot.analyze_environment()
                        if "error" not in analysis:
                            st.json(analysis)
                            
                            # Check for emergencies
                            risk_level = analysis.get("overall_risk", "low")
                            if risk_level in ["high", "critical"]:
                                st.markdown('<div class="emergency-alert">🚨 HIGH RISK DETECTED! Please evacuate immediately!</div>', unsafe_allow_html=True)
                                
                                # Show emergency response if handled
                                if analysis.get("emergency_handled"):
                                    st.success(f"Emergency Response: {analysis.get('emergency_response', 'Handled')}")
                        else:
                            st.error(f"Analysis error: {analysis['error']}")
                else:
                    st.error("Bot not initialized")
        
        # Emergency Testing Section
        st.markdown("### 🚨 Emergency Testing")
        col1, col2 = st.columns(2)
        
        with col1:
            emergency_type = st.selectbox(
                "Emergency Type",
                ["fire", "flood", "earthquake", "chemical", "structural", "gas_leak", "general"]
            )
        
        with col2:
            urgency_level = st.selectbox(
                "Urgency Level",
                ["low", "medium", "high", "critical"]
            )
        
        if st.button("🧪 Test Emergency Response"):
            if st.session_state.dwani_bot:
                with st.spinner("Testing emergency response..."):
                    response = st.session_state.dwani_bot.trigger_emergency_test(emergency_type, urgency_level)
                    st.success(f"Emergency Response: {response}")
            else:
                st.error("Bot not initialized")
        
        # Emergency Status
        if st.button("📊 Show Emergency Status"):
            if st.session_state.dwani_bot:
                status = st.session_state.dwani_bot.get_emergency_status()
                st.json(status)
            else:
                st.error("Bot not initialized")
    
    def render_speech_mode(self):
        st.subheader("🗣️ Speech Mode (Continuous Voice Chat)")
        st.info("Click 'Start Speech Mode' to begin. Speak for 5 seconds per turn. Click 'Stop Speech Mode' to end.")
        if 'speech_mode_active' not in st.session_state:
            st.session_state.speech_mode_active = False
        if not st.session_state.speech_mode_active:
            if st.button("▶️ Start Speech Mode"):
                st.session_state.speech_mode_active = True
                st.rerun()
        else:
            if st.button("⏹️ Stop Speech Mode"):
                st.session_state.speech_mode_active = False
                st.rerun()
            else:
                # Run one speech turn per rerun
                if st.session_state.dwani_bot:
                    with st.spinner("Listening..."):
                        success, transcribed_text = st.session_state.dwani_bot.speech_handler.listen_to_voice()
                        if success and transcribed_text and not transcribed_text.isspace():
                            st.markdown(f"**You:** {transcribed_text}")
                            response = st.session_state.dwani_bot.ai_processor.process_user_message(transcribed_text)
                            speak_text = response.get('speak', str(response)) if isinstance(response, dict) else str(response)
                            st.markdown(f"**Dwani AI:** {speak_text}")
                            st.session_state.dwani_bot.speech_handler.speak_text(speak_text)
                        else:
                            st.warning("No valid input, waiting...")
                    # Rerun to keep the loop going
                    st.rerun()
                else:
                    st.error("Bot not initialized")
    
    def render_disaster_detection_mode(self):
        """Render disaster detection mode interface"""
        st.subheader("🚨 Disaster Detection Mode")
        
        if st.button("📹 Start Continuous Monitoring"):
            st.info("🔍 Monitoring for disasters...")
            
            # Create placeholders
            status_placeholder = st.empty()
            analysis_placeholder = st.empty()
            
            # Simulate continuous monitoring
            for i in range(5):  # Demo: 5 iterations
                time.sleep(1)
                
                if st.session_state.dwani_bot:
                    analysis = st.session_state.dwani_bot.analyze_environment()
                    
                    if "error" not in analysis:
                        risk_level = analysis.get("overall_risk", "low")
                        if risk_level in ["high", "critical"]:
                            status_placeholder.error(f"🚨 ALERT: {risk_level.upper()} RISK DETECTED!")
                        else:
                            status_placeholder.success(f"✅ Status: {risk_level.upper()} risk")
                        
                        analysis_placeholder.json(analysis)
                    else:
                        status_placeholder.warning(f"⚠️ Analysis error: {analysis['error']}")
                
                # Check if user wants to stop
                if st.button("⏹️ Stop Monitoring", key=f"stop_{i}"):
                    break
    
    def render_system_status(self):
        """Render system status interface"""
        st.subheader("🔧 System Status")
        
        if st.session_state.dwani_bot:
            status = st.session_state.dwani_bot.get_system_status()
            
            # Bot Status
            st.markdown("### Bot Status")
            bot_status = status.get("bot_status", {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Active", "Yes" if bot_status.get("is_active") else "No")
            with col2:
                st.metric("Mode", bot_status.get("current_mode", "Unknown"))
            with col3:
                st.metric("Conversations", bot_status.get("conversation_count", 0))
            
            # System Components
            st.markdown("### System Components")
            
            # Speech System
            speech_status = status.get("speech_system", {})
            st.markdown("#### 🎤 Speech System")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Microphone", "✅" if speech_status.get("microphone_available") else "❌")
            with col2:
                st.metric("TTS", "✅" if speech_status.get("tts_available") else "❌")
            with col3:
                st.metric("Speech Recognition", "✅" if speech_status.get("speech_recognition") else "❌")
            
            # Camera System
            camera_status = status.get("camera_system", {})
            st.markdown("#### 📷 Camera System")
            if camera_status.get("available"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", "✅ Available")
                with col2:
                    st.metric("Resolution", camera_status.get("resolution", "Unknown"))
                with col3:
                    st.metric("FPS", f"{camera_status.get('fps', 0):.1f}")
            else:
                st.error(f"❌ Camera not available: {camera_status.get('error', 'Unknown error')}")
            
            # Configuration
            st.markdown("### Configuration")
            config = status.get("configuration", {})
            st.json(config)
            
        else:
            st.error("Bot not initialized")
    
    def initialize_bot(self):
        """Initialize the Dwani AI bot"""
        try:
            if not st.session_state.dwani_bot:
                with st.spinner("Initializing Dwani AI Bot..."):
                    st.session_state.dwani_bot = DwaniAIBot()
                    st.success("✅ Dwani AI Bot initialized successfully!")
        except Exception as e:
            st.error(f"❌ Failed to initialize bot: {e}")
            st.info("Please check your GOOGLE_API_KEY in the .env file")
    
    def run(self):
        """Run the main UI application"""
        # Initialize bot
        self.initialize_bot()
        
        # Render UI
        self.render_header()
        self.render_sidebar()
        
        # Render current mode
        if st.session_state.current_mode == "Chat Mode":
            self.render_chat_mode()
        elif st.session_state.current_mode == "Voice Mode":
            self.render_voice_mode()
        elif st.session_state.current_mode == "Speech Mode":
            self.render_speech_mode()
        elif st.session_state.current_mode == "Disaster Detection Mode":
            self.render_disaster_detection_mode()
        elif st.session_state.current_mode == "System Status":
            self.render_system_status()

def main():
    """Main function to run the Streamlit UI"""
    ui = DwaniAIUI()
    ui.run()

if __name__ == "__main__":
    main() 