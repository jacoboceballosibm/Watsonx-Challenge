import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routers import profile, seats, agents, auth, owner, cvs
from app.services.application_service import seed_applications
from app.services.auth_service import seed_users
from app.services.cv_service import seed_cvs_from_profiles
from app.services.database import init_database
from app.services.profile_service import seed_profiles
from app.services.seat_service import seed_seats

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IBM Professional Marketplace API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(cvs.router, prefix="/api/cvs", tags=["CV Repository"])
app.include_router(seats.router, prefix="/api/seats", tags=["Seats"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(owner.router, prefix="/api/owner", tags=["Owner Portal"])


@app.on_event("startup")
def startup() -> None:
    init_database()
    seed_profiles()
    seed_cvs_from_profiles()
    seed_users()
    seed_seats()
    seed_applications()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "prom-api"}
