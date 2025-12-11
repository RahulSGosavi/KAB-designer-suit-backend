# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from app.routers import auth, projects, catalog, gemini, ai_designer
from app.middleware.error_handler import setup_error_handlers

load_dotenv()

app = FastAPI(
    title="KABS Design Tool API",
    description="Backend API for KABS 2D Design Tool",
    version="1.0.0"
)

# CORS configuration
cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
# Support multiple origins if comma-separated
cors_origins = [origin.strip() for origin in cors_origin.split(",")] if cors_origin else ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
if os.getenv("NODE_ENV") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

# Setup error handlers
setup_error_handlers(app)

# Root route
@app.get("/")
async def root():
    return {
        "service": "KABS 2D Design Tool API",
        "status": "ok",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(gemini.router, prefix="/api/gemini", tags=["gemini"])
app.include_router(ai_designer.router, prefix="/api/ai-designer", tags=["ai-designer"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))  # Default to 3001 to match frontend
    is_production = os.getenv("NODE_ENV") == "production"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production  # Disable reload in production
    )

