# main.py - Entry point
import uvicorn
from backend.app import create_app

# Create the application instance
# This 'app' variable is what uvicorn looks for when running "main:app"
app = create_app()

if __name__ == "__main__":
    # Run server with uvicorn
    # Host 0.0.0.0 allows access from other machines for testing (safe for local dev)
    # Reload=True checks for code changes (dev mode)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
