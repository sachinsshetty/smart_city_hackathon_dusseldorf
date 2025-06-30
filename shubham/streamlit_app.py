import streamlit as st
import os
import sys
import base64
import tempfile
import json
from PIL import Image
import io

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="Blind Navigation Assistant",
    page_icon="👁️‍🗨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .object-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 2px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .object-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }
    .object-card h4 {
        color: #2c3e50;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .object-card p {
        color: #34495e;
        margin: 0.5rem 0;
        font-size: 1rem;
    }
    .object-card strong {
        color: #2c3e50;
        font-weight: 600;
    }
    .easy-access { 
        border-left: 5px solid #28a745;
        background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
    }
    .easy-access:hover {
        border-color: #28a745;
        background: linear-gradient(135deg, #f8fff9 0%, #e8f5e8 100%);
    }
    .medium-access { 
        border-left: 5px solid #ffc107;
        background: linear-gradient(135deg, #ffffff 0%, #fffef8 100%);
    }
    .medium-access:hover {
        border-color: #ffc107;
        background: linear-gradient(135deg, #fffef8 0%, #fff8e8 100%);
    }
    .hard-access { 
        border-left: 5px solid #dc3545;
        background: linear-gradient(135deg, #ffffff 0%, #fff8f8 100%);
    }
    .hard-access:hover {
        border-color: #dc3545;
        background: linear-gradient(135deg, #fff8f8 0%, #ffe8e8 100%);
    }
    .navigation-instructions {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 2px solid #2196f3;
        color: #0d47a1;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(33, 150, 243, 0.1);
    }
    .objects-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #dee2e6;
        margin: 1rem 0;
    }
    .objects-header {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assistant' not in st.session_state:
    st.session_state.assistant = None
if 'navigation_mode' not in st.session_state:
    st.session_state.navigation_mode = False
if 'detected_objects' not in st.session_state:
    st.session_state.detected_objects = []
if 'scene_data' not in st.session_state:
    st.session_state.scene_data = {}

def initialize_assistant():
    """Initialize the navigation assistant"""
    try:
        from blind_navigation_assistant import BlindNavigationAssistant
        assistant = BlindNavigationAssistant()
        return assistant
    except Exception as e:
        st.error(f"Failed to initialize assistant: {e}")
        return None

def analyze_image(image):
    """Analyze uploaded image using the assistant"""
    try:
        # Convert PIL image to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Analyze with assistant
        scene_data = st.session_state.assistant.analyze_scene(img_str)
        return scene_data
    except Exception as e:
        st.error(f"Error analyzing image: {e}")
        return None

def generate_navigation_instructions(target_object, object_data):
    """Generate navigation instructions using the assistant"""
    try:
        instructions = st.session_state.assistant.generate_navigation_instructions(target_object, object_data)
        return instructions
    except Exception as e:
        st.error(f"Error generating navigation instructions: {e}")
        return None

def handle_edge_cases(scene_data):
    """Handle edge cases using the assistant's method"""
    try:
        return st.session_state.assistant.handle_edge_cases(scene_data)
    except Exception as e:
        return f"Error handling edge cases: {e}"

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👁️‍🗨️ Blind Navigation Assistant</h1>
        <p>AI-powered navigation assistance for visually impaired individuals</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Settings")
        
        # Initialize assistant
        if st.button("🔄 Initialize Assistant", type="primary"):
            with st.spinner("Initializing assistant..."):
                st.session_state.assistant = initialize_assistant()
                if st.session_state.assistant:
                    st.success("✅ Assistant initialized successfully!")
                else:
                    st.error("❌ Failed to initialize assistant")
        
        # Navigation mode toggle
        st.session_state.navigation_mode = st.checkbox(
            "🗺️ Navigation Mode", 
            value=st.session_state.navigation_mode,
            help="Enable to get navigation instructions for objects"
        )
        
        # Status display
        st.header("📊 Status")
        if st.session_state.assistant:
            st.markdown('<div class="status-box success-box">✅ Assistant Ready</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box error-box">❌ Assistant Not Ready</div>', unsafe_allow_html=True)
        
        # Instructions
        st.header("📋 Instructions")
        st.markdown("""
        1. **Initialize** the assistant first
        2. **Upload** an image or use camera
        3. **Analyze** the scene
        4. **Enable** navigation mode for directions
        5. **Click** on objects for navigation help
        """)
        
        # API Key info
        st.header("🔑 API Configuration")
        if os.getenv("GOOGLE_API_KEY"):
            st.success("✅ Google API Key configured")
        else:
            st.error("❌ Google API Key not found")
            st.info("Set GOOGLE_API_KEY in your environment variables")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📷 Image Input")
        
        # Image upload
        uploaded_file = st.file_uploader(
            "Choose an image file", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload an image to analyze"
        )
        
        # Camera input (if available)
        camera_photo = st.camera_input(
            "Or take a photo with camera",
            help="Take a photo with your camera"
        )
        
        # Display uploaded image
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
        elif camera_photo is not None:
            image = Image.open(camera_photo)
            st.image(image, caption="Camera Photo", use_container_width=True)
        else:
            st.info("👆 Please upload an image or take a photo to get started")
            return
        
        # Analyze button
        if st.button("🔍 Analyze Scene", type="primary"):
            if not st.session_state.assistant:
                st.error("❌ Please initialize the assistant first!")
                return
            
            with st.spinner("Analyzing scene..."):
                scene_data = analyze_image(image)
                
                if scene_data and 'error' not in scene_data:
                    st.session_state.detected_objects = scene_data.get('objects', [])
                    st.session_state.scene_data = scene_data
                    st.success("✅ Analysis complete!")
                    
                    # Handle edge cases
                    edge_case_message = handle_edge_cases(scene_data)
                    if edge_case_message:
                        st.info(f"ℹ️ {edge_case_message}")
                else:
                    st.error(f"❌ Analysis failed: {scene_data.get('error', 'Unknown error') if scene_data else 'No response'}")
    
    with col2:
        st.header("📊 Analysis Results")
        
        if not st.session_state.detected_objects:
            st.info("📸 No analysis results yet. Upload an image and click 'Analyze Scene'")
            return
        
        # Scene description
        if 'scene_description' in st.session_state.scene_data:
            st.subheader("🎯 Scene Description")
            st.write(st.session_state.scene_data['scene_description'])
        
        # Detected objects
        st.markdown(f"""
        <div class="objects-section">
            <div class="objects-header">
                🎯 Detected Objects ({len(st.session_state.detected_objects)})
            </div>
        """, unsafe_allow_html=True)
        
        for i, obj in enumerate(st.session_state.detected_objects):
            # Determine accessibility class
            accessibility = obj.get('accessibility', 'medium')
            if accessibility == 'easy':
                access_class = 'easy-access'
                access_icon = '🟢'
            elif accessibility == 'hard':
                access_class = 'hard-access'
                access_icon = '🔴'
            else:
                access_class = 'medium-access'
                access_icon = '🟡'
            
            # Create object card
            with st.container():
                st.markdown(f"""
                <div class="object-card {access_class}">
                    <h4>📦 {obj.get('name', f'Object {i+1}')}</h4>
                    <p><strong>📍 Position:</strong> {obj.get('position', 'Unknown')}</p>
                    <p><strong>📏 Distance:</strong> {obj.get('distance', 'Unknown')}</p>
                    <p><strong>📐 Height:</strong> {obj.get('height', 'Unknown')}</p>
                    <p><strong>♿ Accessibility:</strong> {access_icon} {accessibility.title()}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Navigation button
                if st.session_state.navigation_mode:
                    if st.button(f"🗺️ Get Directions", key=f"nav_{i}"):
                        instructions = generate_navigation_instructions(
                            obj.get('name', f'Object {i+1}'), 
                            obj
                        )
                        if instructions:
                            st.session_state.navigation_instructions = instructions
                            st.session_state.selected_object = obj.get('name', f'Object {i+1}')
                            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Navigation instructions
        if hasattr(st.session_state, 'navigation_instructions'):
            st.subheader(f"🗺️ Navigation to: {st.session_state.selected_object}")
            st.markdown(f"""
            <div class="navigation-instructions">
                <h4>📋 Step-by-Step Instructions:</h4>
                <p>{st.session_state.navigation_instructions}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Safety tips
            st.markdown("""
            <div class="status-box warning-box">
                <h4>⚠️ Safety Reminders:</h4>
                <ul>
                    <li>Always verify the object's position before moving</li>
                    <li>Use your cane or guide dog as additional assistance</li>
                    <li>Move slowly and carefully</li>
                    <li>If unsure, ask for help</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Clear button
            if st.button("Clear Instructions"):
                del st.session_state.navigation_instructions
                del st.session_state.selected_object
                st.rerun()
        
        # Hazards and recommendations
        if 'hazards' in st.session_state.scene_data and st.session_state.scene_data['hazards']:
            st.subheader("⚠️ Hazards Detected")
            for hazard in st.session_state.scene_data['hazards']:
                st.warning(hazard)
        
        if 'recommendations' in st.session_state.scene_data and st.session_state.scene_data['recommendations']:
            st.subheader("💡 Recommendations")
            for rec in st.session_state.scene_data['recommendations']:
                st.info(rec)

if __name__ == "__main__":
    main()
