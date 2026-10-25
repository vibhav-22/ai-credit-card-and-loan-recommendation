"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.db.session import init_db, SessionLocal
from backend.app.db.seed import seed_initial_products_if_empty
from backend.app.api.routes import profile, products, recommendations, ingestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    init_db()
    
    # Auto-seed verified official products if DB is brand new
    db = SessionLocal()
    try:
        await seed_initial_products_if_empty(db)
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down FinMatch AI application.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-Powered Personalized Credit Card and Loan Recommendation Platform for India",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(profile.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "environment": settings.APP_ENV
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.APP_NAME,
        "docs_url": "/docs",
        "health": "/api/v1/health"
    }
