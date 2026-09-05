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
from backend.routes.api_keys import router as api_keys_router

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
    # Phase 12: CORS origins are explicit in production via FRONTEND_ORIGINS
    # (or FRONTEND_URL). Unconfigured deployments keep the legacy wildcard
    # for dev parity; production validation flags that state.
    try:
        from backend.core.ops.config import effective_cors_origins
    except ImportError:
        from core.ops.config import effective_cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=effective_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Phase 12: request IDs (observability metadata only) + security headers.
    # Pure-ASGI middleware; never touches canonical calculation outputs.
    @app.middleware("http")
    async def _ops_middleware(request, call_next):
        try:
            from backend.core.ops.request_id import new_request_id
            from backend.core.ops.headers import SECURITY_HEADERS
        except ImportError:
            from core.ops.request_id import new_request_id
            from core.ops.headers import SECURITY_HEADERS
        request.state.request_id = new_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response

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
    app.include_router(api_keys_router)
    
    from backend.routes.family import router as family_router
    app.include_router(family_router)
    try:
        from backend.routes.dynamic import router as dynamic_router
        app.include_router(dynamic_router)
    except Exception as e:
        print(f"[Dynamic] router import failed: {e}")
    try:
        # Phase 11: read-only Research Lab API (no calculation changes)
        from backend.routes.research import router as research_router
        app.include_router(research_router)
    except Exception as e:
        print(f"[Research] router import failed: {e}")
    try:
        # Phase 12: operations routes (/ready). Additive only.
        from backend.routes.ops import router as ops_router
        app.include_router(ops_router)
    except Exception as e:
        print(f"[Ops] router import failed: {e}")

    # ---------------------------
    # EVENTS
    # ---------------------------
    @app.on_event("startup")
    def create_tables():
        Base.metadata.create_all(bind=engine)
        
    return app

# Explicitly expose app for Uvicorn/Render
app = create_app()
