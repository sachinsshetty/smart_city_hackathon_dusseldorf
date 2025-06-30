# Blind Navigation Assistant - Streamlit Web App

A modern web interface for the Blind Navigation Assistant using Streamlit, providing AI-powered scene analysis and navigation assistance for visually impaired individuals.

## 🚀 Features

- **Modern Web Interface**: Clean, accessible UI built with Streamlit
- **Image Upload**: Upload images from your device for analysis
- **Camera Integration**: Take photos directly with your camera
- **AI Scene Analysis**: Powered by Google Gemini Vision API
- **Navigation Instructions**: Step-by-step guidance to objects
- **Safety Features**: Hazard detection and safety reminders
- **Accessibility Focused**: Designed with visually impaired users in mind

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **Google Gemini API Key** - Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Webcam** (optional, for camera input)

## 🛠️ Installation

### 1. Clone or Download the Project
```bash
# If you have the project files, navigate to the project directory
cd smart_city_hackathon_dusseldorf
```

### 2. Install Dependencies
```bash
# Install Streamlit-specific requirements
pip install -r requirements_streamlit.txt

# Or install manually
pip install streamlit google-generativeai opencv-python pillow python-dotenv numpy pytz
```

### 3. Configure API Key
Create a `.env` file in the project directory:
```bash
# .env file
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

**Important**: Replace `your_google_gemini_api_key_here` with your actual Google Gemini API key.

## 🎯 Usage

### Quick Start
1. **Run the Streamlit App**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open in Browser**: The app will automatically open at `http://localhost:8501`

3. **Initialize Assistant**: Click "🔄 Initialize Assistant" in the sidebar

4. **Upload Image or Use Camera**: Choose an image file or take a photo

5. **Analyze Scene**: Click "🔍 Analyze Scene" to get AI analysis

6. **Get Navigation Help**: Enable "🗺️ Navigation Mode" and click on objects for directions

### Detailed Workflow

#### Step 1: Initialize the Assistant
- Click the "🔄 Initialize Assistant" button in the sidebar
- Wait for the success message confirming the assistant is ready
- Check that your API key is properly configured

#### Step 2: Input an Image
- **Option A**: Upload an image file (PNG, JPG, JPEG)
- **Option B**: Use your camera to take a photo
- The image will be displayed in the left panel

#### Step 3: Analyze the Scene
- Click "🔍 Analyze Scene" to process the image
- The AI will detect objects, their positions, and accessibility
- Results appear in the right panel

#### Step 4: Navigation Mode (Optional)
- Enable "🗺️ Navigation Mode" in the sidebar
- Click "🗺️ Get Directions" on any detected object
- Receive step-by-step navigation instructions
- View safety reminders and tips

## 🎨 Interface Overview

### Sidebar
- **Settings**: Initialize assistant and toggle navigation mode
- **Status**: Shows if the assistant is ready
- **Instructions**: Step-by-step usage guide
- **API Configuration**: Shows API key status

### Main Area
- **Left Panel**: Image input and upload controls
- **Right Panel**: Analysis results and navigation instructions

### Object Cards
Each detected object shows:
- 📍 **Position**: front-left, center, back-right, etc.
- 📏 **Distance**: close, medium, far
- 📐 **Height**: floor, knee, waist, chest, head, above-head
- 🟢🟡🔴 **Accessibility**: easy, medium, hard (color-coded)

## 🔧 Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional (for advanced configuration)
API_SERVER=https://generativelanguage.googleapis.com/v1beta
API_SERVER_VLM=https://generativelanguage.googleapis.com/v1beta
```

### Customization
You can modify the app by editing `streamlit_app.py`:
- Change the page title and icon
- Modify the CSS styling
- Add new features or modify existing ones

## 🚨 Troubleshooting

### Common Issues

**1. "Assistant Not Ready" Error**
- Check that your Google API key is set in the `.env` file
- Verify the API key is valid and has proper permissions
- Try reinitializing the assistant

**2. "Analysis Failed" Error**
- Check your internet connection
- Verify the image is clear and well-lit
- Try a different image or camera angle

**3. Camera Not Working**
- Ensure your browser has camera permissions
- Try refreshing the page
- Check if another application is using the camera

**4. Import Errors**
- Make sure all dependencies are installed: `pip install -r requirements_streamlit.txt`
- Check that you're in the correct directory
- Verify Python version is 3.8 or higher

### Getting Help
- Check the console output for detailed error messages
- Ensure all files are in the same directory
- Verify the Google Gemini API is working with the test script

## 🔒 Privacy & Security

- Images are processed locally and sent to Google Gemini API for analysis
- No images are stored permanently on the server
- API keys should be kept secure and not shared
- The app runs locally on your machine

## 🎯 Use Cases

### For Visually Impaired Users
- **Indoor Navigation**: Find furniture, doors, and objects
- **Hazard Detection**: Identify potential obstacles and dangers
- **Object Location**: Get precise directions to specific items
- **Accessibility Assessment**: Understand how easy objects are to reach

### For Caregivers and Support Workers
- **Training Tool**: Help users learn navigation techniques
- **Assessment Tool**: Evaluate navigation capabilities
- **Support Tool**: Provide real-time assistance

## 🔄 Integration with Other Apps

This Streamlit app integrates with the existing `blind_navigation_assistant.py` file and can be used alongside:
- **CLI Version**: `python blind_navigation_assistant.py`
- **GUI Version**: `python app.py`
- **Web Version**: `python web_app.py`
- **Launcher**: `python launcher.py`

## 📱 Mobile Compatibility

The Streamlit app is mobile-responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Android Chrome)
- Tablet browsers

## 🎉 Success!

Your Blind Navigation Assistant Streamlit app is now running! 

**Access it at**: http://localhost:8501

The app provides a modern, accessible interface for AI-powered navigation assistance, making it easier for visually impaired individuals to navigate their environment safely and independently. 