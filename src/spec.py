from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from src.config import ROOT

SPEC_DIR = ROOT / "specs" / "001-harborline-rag"
PIPELINE_SPEC_PATH = SPEC_DIR / "contracts" / "pipeline.yaml"
CONFIG_SCHEMA_PATH = SPEC_DIR / "contracts" / "agent-config.schema.yaml"


class RetrieverSpec(BaseModel):
    outdated_score_penalty: float = 0.25


class PromptSpec(BaseModel):
    max_tokens: int = 700
    template: str


class PipelineSpec(BaseModel):
    id: str
    version: str
    title: str
    kicker: str
    lede: str
    samples: list[str] = Field(default_factory=list)
    retriever: RetrieverSpec = Field(default_factory=RetrieverSpec)
    reasoner: PromptSpec
    critic: PromptSpec
    unsure_markers: list[str] = Field(default_factory=list)

    def public_info(self) -> dict:
        return {
            "id": self.id,
            "version": self.version,
            "title": self.title,
            "kicker": self.kicker,
            "lede": self.lede,
            "samples": list(self.samples),
        }


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing spec file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Spec file must be a mapping: {path}")
    return data


@lru_cache
def load_pipeline_spec() -> PipelineSpec:
    return PipelineSpec.model_validate(_load_yaml(PIPELINE_SPEC_PATH))


def load_config_schema() -> dict:
    return _load_yaml(CONFIG_SCHEMA_PATH)
