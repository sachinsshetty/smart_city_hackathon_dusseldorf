#!/usr/bin/env python3
"""
Dwani AI - Main Application Entry Point
Disaster-aware navigation assistant for Smart Cities

Usage:
    python main.py                    # Run Streamlit UI
    python main.py --bot              # Run bot directly
    python main.py --test             # Run tests
"""

import sys
import os
import argparse
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_streamlit_ui():
    """Run the Streamlit UI"""
    try:
        import subprocess
        import streamlit
        
        # Get the path to the Streamlit UI file
        ui_path = Path(__file__).parent / "ui" / "streamlit_ui.py"
        
        if not ui_path.exists():
            print("❌ Streamlit UI file not found!")
            return False
        
        print("🚀 Starting Dwani AI Streamlit UI...")
        print("📱 Open your browser to the URL shown below")
        print("=" * 50)
        
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(ui_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
        return True
        
    except ImportError:
        print("❌ Streamlit not installed. Please install it with: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Error running Streamlit UI: {e}")
        return False

def run_bot_directly():
    """Run the bot directly without UI"""
    try:
        from core.dwani_bot import DwaniAIBot
        
        print("🤖 Starting Dwani AI Bot (Direct Mode)...")
        print("=" * 50)
        # Initialize and run bot
        bot = DwaniAIBot()
        bot.speech_mode_loop()
        
        return True
        
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        return False

def run_tests():
    """Run the test suite"""
    try:
        print("🧪 Running Dwani AI Tests...")
        print("=" * 50)
        
        # Run basic system tests
        from core.dwani_bot import DwaniAIBot
        bot = DwaniAIBot()
        status = bot.get_system_status()
        print(f"System status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_speech_mode():
    """Run the robust speech mode loop"""
    try:
        from core.dwani_bot import DwaniAIBot
        print("🤖 Starting Dwani AI Speech Mode (Voice Loop)...")
        print("Speak for 5 seconds per turn. Press Ctrl+C to stop.")
        bot = DwaniAIBot()
        bot.speech_mode_loop()
        return True
    except Exception as e:
        print(f"❌ Error running speech mode: {e}")
        return False

def show_help():
    """Show help information"""
    print("🏙️ Dwani AI - Disaster-Aware Navigation Assistant")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python main.py                    # Run Streamlit UI (default)")
    print("  python main.py --bot              # Run bot directly")
    print("  python main.py --test             # Run tests")
    print("  python main.py --help             # Show this help")
    print()
    print("Features:")
    print("  🎤 Voice Commands: 'Is there fire?', 'Guide me to safety'")
    print("  🚨 Disaster Detection: Real-time hazard identification")
    print("  🧭 Navigation: Safe path recommendations")
    print("  🆘 Emergency Response: Immediate safety guidance")
    print()
    print("Requirements:")
    print("  - GOOGLE_API_KEY in .env file")
    print("  - Microphone and camera access")
    print("  - Internet connection for AI processing")
    print()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Dwani AI - Disaster-Aware Navigation Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run Streamlit UI
  python main.py --bot              # Run bot directly
  python main.py --test             # Run tests
        """
    )
    
    parser.add_argument(
        "--bot", 
        action="store_true", 
        help="Run bot directly without UI"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run test suite"
    )
    parser.add_argument(
        "--speech-mode",
        action="store_true",
        help="Run robust speech mode (continuous voice chat)"
    )
    
    args = parser.parse_args()
    
    # Run appropriate mode
    if args.speech_mode:
        success = run_speech_mode()
    elif args.test:
        success = run_tests()
    elif args.bot:
        success = run_bot_directly()
    else:
        success = run_streamlit_ui()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 