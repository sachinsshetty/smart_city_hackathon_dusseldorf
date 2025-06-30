@echo off
echo ========================================
echo    Blind Navigation Assistant
echo    Streamlit Web App Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements_app.txt
pip install streamlit pillow

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please create a .env file with your GOOGLE_API_KEY
    echo Copy env_template.txt to .env and add your API key
    echo.
    pause
)

REM Start Streamlit app
echo.
echo Starting Streamlit app...
echo Open your browser and go to: http://localhost:8501
echo Press Ctrl+C to stop the server
echo.
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

pause 