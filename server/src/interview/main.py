from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import dspy
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from interview.api import router
from interview.cli.programs import get_default_path, load_optimized
from interview.config import settings
from interview.engine.dspy_modules import create_interview_step, create_text_extractor
from interview.engine.orchestrator import InterviewOrchestrator
from interview.session.store import InMemorySessionStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.validate_api_key()
    logger.info("Using LLM model: %s (provider: %s)", settings.llm_model, settings.llm_provider)
    lm = dspy.LM(settings.llm_model)
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())

    interview_step = create_interview_step()
    text_extractor = create_text_extractor()

    interview_step_path = get_default_path("interview_step")
    if interview_step_path.exists():
        interview_step = load_optimized(interview_step, interview_step_path)
        logger.info("Loaded optimized InterviewStep from %s", interview_step_path)

    text_extractor_path = get_default_path("text_extractor")
    if text_extractor_path.exists():
        text_extractor = load_optimized(text_extractor, text_extractor_path)
        logger.info("Loaded optimized TextDataExtractor from %s", text_extractor_path)

    store = InMemorySessionStore()
    app.state.orchestrator = InterviewOrchestrator(
        store=store,
        interview_step=interview_step,
        text_extractor=text_extractor,
    )
    app.state.store = store

    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Conversational Interview", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {type(exc).__name__}"},
        )

    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "interview.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
