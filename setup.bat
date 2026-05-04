@echo off
echo ================================
echo  Resume Analyzer - Setup Script
echo ================================

echo.
echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo.
echo [2/4] Installing Python dependencies (including python-dotenv)...
pip install -r requirements.txt

echo.
echo [3/4] Downloading spaCy English model...
python -m spacy download en_core_web_sm

echo.
echo [4/4] Setting up environment variables...
if not exist .env (
    echo ANTHROPIC_API_KEY=your_api_key_here > .env
    echo Created .env file - ADD YOUR API KEY INSIDE IT
) else (
    echo .env already exists, skipping...
)

echo.
echo ================================
echo  Setup Complete!
echo ================================
echo.
echo NEXT STEPS:
echo  1. Open .env and replace 'your_api_key_here' with your real Anthropic API key
echo     Get one free at: https://console.anthropic.com
echo  2. Run the server:  python app.py
echo  3. Open browser:    http://localhost:5000
echo.
pause