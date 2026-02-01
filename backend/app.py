from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import swisseph as swe
import os

# Config
from backend.config import EPHE_PATH

# Database
from backend.database import engine
from backend.models import Base

# Routes
from backend.auth_routes import router as auth_router
from backend.geocode import router as geocode_router
from backend.routes.astro import router as astro_router
from backend.routes.ai_routes import router as ai_router
from backend.routes.learning import router as learning_router

def create_app() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application.
    """
    
    # ---------------------------
    # GLOBAL SETUP
    # ---------------------------
    swe.set_ephe_path(EPHE_PATH)
    
    # Force Lahiri sidereal mode globally
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    except Exception:
        pass

    # ---------------------------
    # APP INITIALIZATION
    # ---------------------------
    app = FastAPI(title="Astro Engine (Swiss Ephemeris - Lahiri)")

    # ---------------------------
    # MIDDLEWARE
    # ---------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:4173",
            "https://astrolife-nine.vercel.app",
            "https://astrolife.vercel.app",
            "https://yourlifepath.vercel.app"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------
    # ROUTES
    # ---------------------------
    @app.get("/health")
    def health_check():
        return {"status": "active", "message": "Server is running"}

    app.include_router(auth_router)
    app.include_router(geocode_router)
    app.include_router(astro_router)
    app.include_router(ai_router)
    app.include_router(learning_router)
    
    from backend.routes.family import router as family_router
    app.include_router(family_router)

    # ---------------------------
    # EVENTS
    # ---------------------------
    @app.on_event("startup")
    def create_tables():
        Base.metadata.create_all(bind=engine)
        
    return app

# Explicitly expose app for Uvicorn/Render
app = create_app()
