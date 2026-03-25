@echo off
echo Starting Voice2Value Backend Server...
echo.

REM Set Python path to include current directory
set PYTHONPATH=%CD%

REM Check if virtual environment exists, if not create one
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Download spaCy model
echo Downloading spaCy model...
python -m spacy download en_core_web_sm

REM Start the server
echo.
echo Starting Flask server...
echo Server will be available at: http://localhost:5000
echo API docs at: http://localhost:5000/info
echo.
echo Press Ctrl+C to stop the server
echo.

python app/main.py
