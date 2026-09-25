from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interview_app.config import get_settings
from interview_app.db import create_tables
from interview_app.routers import interviews, recommend


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Interview Practice", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(interviews.router)
    app.include_router(recommend.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def run() -> None:
    """Entry point for `uv run interview-app`."""
    uvicorn.run("interview_app.main:app", host="127.0.0.1", port=8000, reload=True)
