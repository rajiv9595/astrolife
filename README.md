# LifePath - Vedic Astrology Chart Generator

A comprehensive Vedic Astrology application with accurate D1 (Rasi) chart generation using Swiss Ephemeris.

## Features

### Backend
- **Accurate Astrological Calculations** using Swiss Ephemeris
- **Lahiri Ayanamsa** for sidereal calculations
- **Planet Positions**: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu
- **Houses System**: Whole sign houses based on ascendant
- **D1 Chart**: South Indian style Rasi chart
- **Navamsa (D9)**: Navamsa chart calculations
- **Nakshatra & Pada**: Moon's nakshatra and pada calculation
- **Vimshottari Dasha**: Mahadasha timeline
- **REST API**: FastAPI-based backend

### Frontend
- **Beautiful Modern UI** with gradient design
- **Strength Chart**: Bar chart showing planetary strengths
- **D1 Chart Visualization**: South Indian style chart with zodiac symbols
- **Interactive Forms**: Easy birth details input
- **Responsive Design**: Works on desktop and mobile
- **Real-time Computations**: Fast API integration

## Project Structure

```
lifepath/
├── backend/
│   ├── main.py              # FastAPI backend
│   ├── requirements.txt     # Python dependencies
│   └── ephe/               # Swiss Ephemeris files
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── D1Chart.jsx      # D1 chart visualization
│   │   │   ├── D1Chart.css
│   │   │   ├── StrengthChart.jsx # Strength bar chart
│   │   │   └── StrengthChart.css
│   │   ├── App.jsx         # Main app component
│   │   ├── App.css
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Node dependencies
│   ├── vite.config.js      # Vite configuration
│   └── index.html
└── README.md
```

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Ensure Swiss Ephemeris files are in `backend/ephe/` directory

5. Start the backend server:
```bash
uvicorn main:app --reload
```

The backend will run on http://localhost:8001

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Enter birth details:
   - Date, time, and timezone
   - Latitude and longitude
3. Click "Compute Chart"
4. View the generated:
   - **Strength Chart**: Planetary strength values
   - **D1 Chart**: South Indian style Rasi chart with zodiac symbols

## API Endpoints

### POST /compute

Calculate astrological chart data.

**Request Body:**
```json
{
  "year": 2005,
  "month": 8,
  "day": 17,
  "hour": 0,
  "minute": 0,
  "second": 0,
  "tz": "Asia/Kolkata",
  "lat": 12.9716,
  "lon": 77.5946
}
```

**Response:**
- Planetary positions (tropical and sidereal)
- Ascendant information
- Whole sign houses
- D9 Navamsa data
- Nakshatra and pada
- Vimshottari dasha timeline

## Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **Swiss Ephemeris**: High-precision astronomical calculations
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI library
- **Vite**: Build tool and dev server
- **Chart.js**: Chart visualization
- **Axios**: HTTP client
- **CSS3**: Styling

## Features

### D1 Chart Display
- South Indian style layout
- 12 houses arranged in traditional grid
- Zodiac sign symbols with colors
- Planetary positions in houses
- Center panel: "Rasi D1"
- Orange border matching traditional charts

### Strength Chart
- Color-coded bars for each planet
- Y-axis: 200-550 strength range
- Visual representation of planetary strengths

## Development

### Backend Development
```bash
cd backend
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Building for Production

**Backend:**
```bash
pip install gunicorn
gunicorn main:app
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve the dist folder
```

## License

This project uses Swiss Ephemeris which has its own licensing terms. Please review the Swiss Ephemeris license at: https://www.astro.com/swisseph/swephinfo_e.htm

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Swiss Ephemeris by Astrodienst for astronomical calculations
- Lahiri Ayanamsa for sidereal calculations
- FastAPI team for the excellent framework
- React and Vite teams for the modern frontend ecosystem

## Notes

- The backend uses Lahiri Ayanamsa for all sidereal calculations
- Whole sign houses are used for the D1 chart
- Swiss Ephemeris data files are required in the `ephe` directory
- The frontend assumes the backend is running on localhost:8001

"# astrolife" 
