# Astrolife V2 - Phase 0: Dependency Report

This report outlines the technology stack, external libraries, and infrastructure currently powering Astrolife.

## 1. Backend Stack
- **Language**: Python 3.x
- **Framework**: FastAPI (`fastapi`, `uvicorn[standard]`)
- **Database**: PostgreSQL (driver: `psycopg2-binary`)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (`python-jose[cryptography]`), bcrypt (`passlib[bcrypt]`)
- **Astrology Engine**: Swiss Ephemeris (`pyswisseph`)
- **AI SDK**: Google Generative AI (`google-generativeai`)
- **Other Notable Dependencies**: `pytz` (timezone handling), `python-dotenv`, `google-auth-library`

## 2. Frontend Stack
- **Framework**: React 18 (`react`, `react-dom`)
- **Build Tool**: Vite (`vite`)
- **Routing**: React Router (`react-router-dom`)
- **Styling**: Tailwind CSS (`tailwindcss`, `autoprefixer`, `postcss`)
- **HTTP Client**: Axios (`axios`)
- **Authentication**: Google OAuth (`@react-oauth/google`)
- **UI Components & Animation**: Framer Motion (`framer-motion`), Lucide React (`lucide-react`)
- **Utilities**: `date-fns` (date manipulation), `classnames`

## 3. Package Management
- **Backend**: `pip` (via `requirements.txt`)
- **Frontend**: `npm` (via `package.json` and `package-lock.json`)

## 4. Environment Variables
- `DATABASE_URL`: PostgreSQL connection string.
- `JWT_SECRET`: Secret for signing JWTs.
- `GEMINI_API_KEY`: API key for Google Gemini AI.
- `GOOGLE_CLIENT_ID`: OAuth client ID for frontend auth.
- `VITE_API_URL`: Backend API endpoint for the frontend.

## 5. Deployment / Build
- **Frontend Build Process**: Standard `npm run build` (vite build) -> static assets in `dist/` directory.
- **Backend Build Process**: Standard `uvicorn app:app` or `uvicorn main:app` after installing pip requirements in virtual environment.
- **Configuration**: Vercel config file (`vercel.json`) suggests possible frontend deployment on Vercel.
