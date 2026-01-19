# Quick Start Guide

## First Time Setup

### 1. Setup Backend

Run the setup script:
```bash
setup_backend.bat
```

Or manually:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Frontend

Run the setup script:
```bash
setup_frontend.bat
```

Or manually:
```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

Run:
```bash
start_backend.bat
```

Or manually:
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8001
```

Backend will be available at: http://localhost:8001

### Start Frontend Server

Run:
```bash
start_frontend.bat
```

Or manually:
```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Using the Application

1. Open http://localhost:3000 in your browser
2. Enter birth details in the form
3. Click "Compute Chart"
4. View the Strength chart and D1 Rasi chart

## Features

✅ **Strength Chart**: Visual bar chart of planetary strengths
✅ **D1 Chart**: South Indian style Rasi chart with:
   - 12 houses in traditional layout
   - Zodiac sign symbols (♈ ♉ ♊ etc.)
   - Planetary positions
   - Center "Rasi D1" panel
   - Beautiful orange border

## Troubleshooting

**Backend won't start:**
- Ensure Python virtual environment is activated
- Check that requirements.txt dependencies are installed
- Verify Swiss Ephemeris files are in backend/ephe/

**Frontend won't start:**
- Run `npm install` in the frontend directory
- Check that backend is running on port 8001
- Clear browser cache if needed

**No data appearing:**
- Ensure backend server is running
- Check browser console for errors
- Verify birth details are entered correctly

## Next Steps

- Enter different birth details to see various charts
- Explore the API at http://localhost:8001/docs
- Check the main README.md for detailed documentation

