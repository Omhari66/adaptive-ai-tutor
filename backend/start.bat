@echo off
echo ========================================
echo   RAG Study Assistant - Backend Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing PyTorch CPU...
pip install torch --index-url https://download.pytorch.org/whl/cpu
echo Installing remaining dependencies...
pip install -r requirements.txt
echo.

REM Create uploads directory
if not exist "uploads" (
    echo Creating uploads directory...
    mkdir uploads
)

REM Run database migrations (if alembic is configured)
REM echo Running database migrations...
REM alembic upgrade head

REM Start the server
echo.
echo Starting FastAPI server on http://localhost:8000
echo API docs available at http://localhost:8000/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
