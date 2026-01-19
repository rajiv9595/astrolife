# Database Setup Guide

## Prerequisites

1. **Install PostgreSQL**
   - Download and install PostgreSQL from https://www.postgresql.org/download/
   - Make sure PostgreSQL service is running

2. **Create Database**
   ```sql
   CREATE DATABASE lifepath_db;
   ```

## Installation Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database Connection:**
   - Edit `backend/database.py`
   - Update `DATABASE_URL` with your PostgreSQL credentials:
     ```python
     DATABASE_URL = "postgresql://username:password@localhost:5432/lifepath_db"
     ```
   - Or set it as an environment variable:
     ```bash
     export DATABASE_URL="postgresql://username:password@localhost:5432/lifepath_db"
     ```

3. **Initialize Database:**
   ```bash
   python init_db.py
   ```
   
   Or tables will be created automatically when the FastAPI app starts (due to `@app.on_event("startup")`).

4. **Start the Backend:**
   ```bash
   uvicorn main:app --reload --port 8001
   ```

## API Endpoints

### Authentication
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Login with email and password
- `GET /auth/me` - Get current user info (requires auth token)
- `GET /auth/chart-data` - Get user's birth data for chart (requires auth token)

### Chart Computation
- `POST /compute` - Compute astrological chart

## Frontend Integration

The frontend will:
1. Store JWT token in `localStorage` after login/signup
2. Automatically fetch and display user's chart on login
3. Send auth token in `Authorization` header for protected routes

## Environment Variables

For production, set these environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key (change in `auth.py`)


