@echo off
echo Setting up LifePath Backend...

cd backend

echo.
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Backend setup complete!
echo.
echo To start the backend server, run:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn main:app --reload
echo.
pause

