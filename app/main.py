from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.api.routes import router
from app.services.map_service import map_service
from app.ml.traffic_predictor import traffic_predictor
from app.ml.route_scorer import route_scorer
from app.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered vehicle route prediction system for Bali",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/maps", StaticFiles(directory="data/processed"), name="maps")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("app/static/index.html", "r") as f:
        return f.read()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "map_loaded": map_service.is_loaded,
        "traffic_model_trained": traffic_predictor.is_trained,
        "route_model_trained": route_scorer.is_trained,
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Route Prediction API...")

    logger.info("Training traffic prediction model...")
    traffic_predictor.train()

    logger.info("Training route scorer model...")
    route_scorer.train()

    logger.info("Map graph will be loaded on first request (or use fallback routing)")

    logger.info("Startup complete!")
