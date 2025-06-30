#!/usr/bin/env python3
"""
Test script to verify Streamlit app integration with Blind Navigation Assistant
"""

import os
import sys
import base64
import tempfile
from PIL import Image
import io

def test_imports():
    """Test if all required modules can be imported"""
    print("=== Testing Imports ===")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        from blind_navigation_assistant import BlindNavigationAssistant
        print("✅ BlindNavigationAssistant imported successfully")
    except ImportError as e:
        print(f"❌ BlindNavigationAssistant import failed: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ Google GenerativeAI imported successfully")
    except ImportError as e:
        print(f"❌ Google GenerativeAI import failed: {e}")
        return False
    
    return True

def test_assistant_initialization():
    """Test if the assistant can be initialized"""
    print("\n=== Testing Assistant Initialization ===")
    
    try:
        from blind_navigation_assistant import BlindNavigationAssistant
        
        # Check if API key is available
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            print("   Please set your API key in the .env file")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        
        # Try to initialize assistant
        assistant = BlindNavigationAssistant()
        print("✅ Assistant initialized successfully")
        
        return assistant
        
    except Exception as e:
        print(f"❌ Assistant initialization failed: {e}")
        return None

def test_image_analysis(assistant):
    """Test image analysis functionality"""
    print("\n=== Testing Image Analysis ===")
    
    try:
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='white')
        
        # Convert to base64
        buffer = io.BytesIO()
        test_image.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        print("✅ Test image created and converted to base64")
        
        # Test analysis
        scene_data = assistant.analyze_scene(img_str)
        
        if scene_data and 'error' not in scene_data:
            print("✅ Scene analysis successful")
            print(f"   Objects detected: {len(scene_data.get('objects', []))}")
            return True
        else:
            print(f"❌ Scene analysis failed: {scene_data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Image analysis test failed: {e}")
        return False

def test_navigation_instructions(assistant):
    """Test navigation instruction generation"""
    print("\n=== Testing Navigation Instructions ===")
    
    try:
        # Create a test object
        test_object = {
            "name": "test chair",
            "position": "center",
            "distance": "medium",
            "height": "waist",
            "accessibility": "easy"
        }
        
        # Generate instructions
        instructions = assistant.generate_navigation_instructions("test chair", test_object)
        
        if instructions:
            print("✅ Navigation instructions generated successfully")
            print(f"   Instructions: {instructions[:100]}...")
            return True
        else:
            print("❌ Navigation instructions generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Navigation instructions test failed: {e}")
        return False

def test_streamlit_app_import():
    """Test if the Streamlit app can be imported"""
    print("\n=== Testing Streamlit App Import ===")
    
    try:
        import streamlit_app
        print("✅ Streamlit app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Streamlit app import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Streamlit Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed. Please install missing dependencies.")
        return False
    
    # Test 2: Streamlit app import
    if not test_streamlit_app_import():
        print("\n❌ Streamlit app import failed.")
        return False
    
    # Test 3: Assistant initialization
    assistant = test_assistant_initialization()
    if not assistant:
        print("\n❌ Assistant initialization failed.")
        return False
    
    # Test 4: Image analysis
    if not test_image_analysis(assistant):
        print("\n❌ Image analysis test failed.")
        return False
    
    # Test 5: Navigation instructions
    if not test_navigation_instructions(assistant):
        print("\n❌ Navigation instructions test failed.")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n✅ Your Streamlit app is ready to use!")
    print("   Run: streamlit run streamlit_app.py")
    print("   Access: http://localhost:8501")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 