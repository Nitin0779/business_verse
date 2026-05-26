"""
BusinessVerse - FastAPI Server Main Entry Point
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import auth, data, ml, database, reports

app = FastAPI(
    title="BusinessVerse Analytics Engine API",
    description="High-performance data analytics, SQL execution, and ML predictions API backend.",
    version="1.0.0"
)

# Configure CORS Middleware
# Allows seamless connectivity from Flutter Web (which runs on random localhost ports) and Mobile Emulators
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(ml.router)
app.include_router(database.router)
app.include_router(reports.router)


@app.get("/")
def read_root():
    """Welcome/Health Check endpoint."""
    return {
        "status": "healthy",
        "service": "BusinessVerse Analytics Engine API",
        "documentation_docs": "/docs",
        "documentation_redoc": "/redoc"
    }


if __name__ == "__main__":
    # Start the server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
