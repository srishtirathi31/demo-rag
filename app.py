from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config import list_configs
from src.pipeline import run
from src.spec import load_pipeline_spec

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(
    title="Harborline RAG",
    version="0.1.0",
    description="Spec-driven retrieve-then-answer API. See specs/001-harborline-rag/.",
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    config: str = "v1"


class SpecInfo(BaseModel):
    id: str
    version: str
    title: str
    kicker: str
    lede: str
    samples: list[str]


class ConfigInfo(BaseModel):
    name: str
    description: str
    k: int
    critic_enabled: bool
    critic_mode: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/spec", response_model=SpecInfo)
def spec_info() -> SpecInfo:
    return SpecInfo.model_validate(load_pipeline_spec().public_info())


@app.get("/api/configs", response_model=list[ConfigInfo])
def configs() -> list[ConfigInfo]:
    return [
        ConfigInfo(
            name=cfg.name,
            description=cfg.description,
            k=cfg.retriever.k,
            critic_enabled=cfg.critic.enabled,
            critic_mode=cfg.critic.mode,
        )
        for cfg in list_configs()
    ]


@app.post("/api/ask")
def ask(body: AskRequest) -> dict:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty")
    try:
        return run(question, config_name=body.config)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
