# 🏙️ Dwani AI - Disaster-Aware Navigation Assistant

Voice-guided AI navigation and disaster awareness assistant for Smart Cities

## 🎯 What It Does

- **🧠 Real-time Disaster Detection**: Identifies fires, floods, structural damage, and other hazards using Gemini Vision
- **🎙️ Voice Commands**: Understands natural language using Speech-to-Text (e.g., "Is there fire?")
- **🗣️ Voice Responses**: Speaks back answers using Text-to-Speech (e.g., "Yes, smoke detected ahead")
- **🧭 Smart Navigation**: Guides evacuation with commands like "go left 20 meters" or "turn around"
- **📍 Safe Routing**: Routes users to safe locations (hospitals/shelters) via navigation services
- **🚨 Emergency Alerts**: Provides immediate safety guidance and emergency response

## 🏗️ Architecture

```
[User] ⇆ [Microphone/Camera]
      ⇅                ⇅
[Speech Handler]  [Vision Handler]
      ⇅                ⇅
[AI Processor] ← [Disaster Detection]
      ⇅
[Dwani AI Bot]
      ⇅
[Streamlit UI] → User Interface
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **AI Processing** | Google Gemini 1.5 Flash |
| **Speech Recognition** | Google Speech Recognition API |
| **Text-to-Speech** | pyttsx3 |
| **Computer Vision** | OpenCV + Gemini Vision |
| **UI Framework** | Streamlit |
| **Language** | Python 3.8+ |

## 📁 Project Structure

```
vj/
├── core/                    # Core bot functionality
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── speech_handler.py   # Speech recognition & TTS
│   ├── vision_handler.py   # Camera & image analysis
│   ├── ai_processor.py     # Gemini AI processing
│   └── dwani_bot.py        # Main bot orchestrator
├── ui/                     # User interface
│   ├── __init__.py
│   └── streamlit_ui.py     # Streamlit web interface
├── main.py                 # Application entry point
├── test_dwani_bot.py       # Test suite
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Microphone and camera access
- Internet connection

### 2. Installation

```bash
# Clone the repository
cd vj

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
```

### 3. Run the Application

#### Option A: Streamlit UI (Recommended)
```bash
python main.py
```
Then open your browser to `http://localhost:8501`

#### Option B: Direct Bot Mode
```bash
python main.py --bot
```

#### Option C: Run Tests
```bash
python main.py --test
```

## 🎮 Usage Examples

### Voice Commands
- "Is there fire nearby?"
- "Guide me to safety"
- "What's the emergency situation?"
- "How do I navigate to the hospital?"
- "Help me find the nearest shelter"

### Chat Interface
- Ask questions about safety and navigation
- Get real-time disaster analysis
- Receive step-by-step navigation guidance
- Emergency response instructions

### Disaster Detection
- Automatic hazard identification
- Risk level assessment
- Safety recommendations
- Emergency contact information

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
OPENROUTE_SERVICE_API_KEY=your_openroute_api_key_here  # Optional
```

### Customization

Edit `core/config.py` to customize:
- Speech recognition settings
- Camera configuration
- Disaster keywords
- Safe locations
- Risk levels

## 🧪 Testing

Run the comprehensive test suite:

```bash
python main.py --test
```

Tests include:
- ✅ Voice command processing
- ✅ Disaster detection
- ✅ Navigation guidance
- ✅ Emergency response

## 📊 Features

### 🎤 Voice Mode
- Real-time speech recognition
- Natural language processing
- Voice response generation
- Emergency alert system

### 💬 Chat Mode
- Text-based interaction
- Conversation history
- Context-aware responses
- Multi-turn dialogue

### 🚨 Disaster Detection Mode
- Continuous environment monitoring
- Real-time hazard identification
- Risk level assessment
- Automatic emergency alerts

### 🔧 System Status
- Component health monitoring
- Configuration validation
- Performance metrics
- Error reporting

## 🏗️ Software Architecture

### Separation of Concerns
- **Core Module**: Business logic and AI processing
- **UI Module**: User interface and interaction
- **Configuration**: Centralized settings management
- **Testing**: Comprehensive test coverage

### Design Patterns
- **Factory Pattern**: Component initialization
- **Observer Pattern**: Event handling
- **Strategy Pattern**: Different processing modes
- **Singleton Pattern**: Configuration management

### Error Handling
- Graceful degradation
- Comprehensive logging
- User-friendly error messages
- Fallback mechanisms

## 🔒 Security & Privacy

- No data storage (conversations are not saved)
- Local speech processing
- Secure API key management
- Privacy-focused design

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Run the test suite for troubleshooting

## 🎯 Roadmap

- [ ] Integration with OpenRouteService for navigation
- [ ] Multi-language support
- [ ] Mobile app development
- [ ] IoT sensor integration
- [ ] Machine learning model training
- [ ] Cloud deployment options

---

**🏙️ Dwani AI** - Making Smart Cities safer, one voice command at a time!