import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Initialize database pools, etc.
    # e.g., await init_db()
    yield
    # Shutdown logic: Close connections
    # e.g., await close_db()

def create_app() -> FastAPI:
    # 1. Initialize structured logging first
    setup_logging()
    
    # 2. Initialize FastAPI app with lifespan management
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        lifespan=lifespan
    )

    # 3. Configure CORS
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 4. Mount the central router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application

app = create_app()

if __name__ == "__main__":
    # This entrypoint is for local development only.
    # In production (Cloud Run), uvicorn or gunicorn should be called directly.
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True if settings.ENVIRONMENT == "development" else False
    )
