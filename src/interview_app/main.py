from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from interview_app import db as db_module
from interview_app.config import get_settings
from interview_app.db import create_tables
from interview_app.routers import cv, extract, interviews, recommend, speech
from interview_app.services.judge import fail_interrupted_judges


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    with Session(db_module.engine) as db:
        fail_interrupted_judges(db)
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
    app.include_router(cv.router)
    app.include_router(extract.router)
    app.include_router(speech.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def run() -> None:
    """Entry point for `uv run interview-app`."""
    uvicorn.run("interview_app.main:app", host="127.0.0.1", port=8000, reload=True)
