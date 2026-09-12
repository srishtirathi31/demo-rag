from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configs"
CORPUS_DIR = ROOT / "corpus"


class RetrieverConfig(BaseModel):
    k: int = 5


class CriticConfig(BaseModel):
    enabled: bool = False
    mode: Literal["always", "if_unsure"] = "always"


class AgentConfig(BaseModel):
    name: str
    description: str = ""
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    critic: CriticConfig = Field(default_factory=CriticConfig)
    path: Optional[Path] = Field(default=None, exclude=True)


def load_config(name: str) -> AgentConfig:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        available = [p.stem for p in CONFIG_DIR.glob("*.yaml")]
        raise FileNotFoundError(
            f"Unknown config '{name}'. Available: {', '.join(sorted(available))}"
        )
    data = yaml.safe_load(path.read_text()) or {}
    cfg = AgentConfig.model_validate(data)
    cfg.path = path
    return cfg


def list_configs() -> list[AgentConfig]:
    configs = []
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        cfg = AgentConfig.model_validate(data)
        cfg.path = path
        configs.append(cfg)
    return configs
