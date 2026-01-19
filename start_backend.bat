@echo off
cd backend
call .venv\Scripts\activate.bat
echo Starting backend server on http://localhost:8001
uvicorn main:app --reload --port 8001

