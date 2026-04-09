"""FastAPI application factory — spec S9."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import endpoints

DEFAULT_DATA_DIR = Path("data/processed")


def create_app(
    data_dir: Path = DEFAULT_DATA_DIR,
    enable_prewarm: bool = True,
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        endpoints.set_data_dir(data_dir)
        if enable_prewarm:
            from src.api.prewarm import prewarm_scenarios
            prewarm_scenarios(data_dir)
        yield

    app = FastAPI(
        title="Visaudio Optique Analytics",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(endpoints.router)
    return app
