#!/bin/bash

echo "========================================"
echo "   Blind Navigation Assistant"
echo "   Streamlit Web App Launcher"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements_app.txt
pip install streamlit pillow

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo
    echo "WARNING: .env file not found!"
    echo "Please create a .env file with your GOOGLE_API_KEY"
    echo "Copy env_template.txt to .env and add your API key"
    echo
    read -p "Press Enter to continue..."
fi

# Start Streamlit app
echo
echo "Starting Streamlit app..."
echo "Open your browser and go to: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 