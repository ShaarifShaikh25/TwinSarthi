import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.websockets.routes import ws_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.init_db import init_db

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook: initialize database schema and seed demonstration entities."""
    init_db()
    yield


app = FastAPI(
    title="POLAR‑TWIN Backend",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS – allow frontend dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific frontend origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routes under /api
app.include_router(api_router, prefix="/api")

# Include WebSocket routes (/ws/{station_id})
app.include_router(ws_router)


# Simple liveness probe (non‑versioned)
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# Global exception handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
