import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import db as db_routes
from app.api.routes import jobs as jobs_routes
from app.api.routes import match as match_routes
from app.api.routes import preferences as preferences_routes
from app.api.routes import resumes as resumes_routes
from app.api.routes import scan as scan_routes
from app.api.routes import upload as upload_routes
from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.services.scheduler_service import shutdown_scheduler, start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
        await start_scheduler()
    except Exception:
        logger.exception("Failed to initialize application on startup")
        raise
    yield
    await shutdown_scheduler()
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(db_routes.router)
app.include_router(upload_routes.router)
app.include_router(match_routes.router)
app.include_router(jobs_routes.router)
app.include_router(preferences_routes.router)
app.include_router(resumes_routes.router)
app.include_router(scan_routes.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
