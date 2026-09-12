from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

from src.config import list_configs, load_config
from src.pipeline import _is_unsure, run
from src.retrieve import Retriever
from src.spec import CONFIG_SCHEMA_PATH, PIPELINE_SPEC_PATH, load_pipeline_spec

ROOT = Path(__file__).resolve().parent.parent


def test_pipeline_spec_loads_and_has_required_placeholders():
    spec = load_pipeline_spec()
    assert spec.id == "harborline-rag"
    assert spec.version
    assert spec.samples
    assert "{context}" in spec.reasoner.template
    assert "{question}" in spec.reasoner.template
    assert "{draft}" in spec.critic.template
    assert spec.retriever.outdated_score_penalty == 0.25
    assert "don't know" in spec.unsure_markers


def test_profiles_match_spec_and_schema():
    schema = yaml.safe_load(CONFIG_SCHEMA_PATH.read_text())
    allowed_modes = schema["properties"]["critic"]["properties"]["mode"]["enum"]
    expected = {
        "v1": {"k": 5, "enabled": False, "mode": "always"},
        "v2": {"k": 20, "enabled": True, "mode": "always"},
        "v3": {"k": 7, "enabled": True, "mode": "if_unsure"},
    }
    names = {cfg.name for cfg in list_configs()}
    assert names == set(expected)
    for name, want in expected.items():
        cfg = load_config(name)
        assert cfg.retriever.k == want["k"]
        assert cfg.critic.enabled is want["enabled"]
        assert cfg.critic.mode == want["mode"]
        assert cfg.critic.mode in allowed_modes


def test_unsure_markers_come_from_spec():
    spec = load_pipeline_spec()

    class Doc:
        title = "Returns policy"
        id = "POL-returns"

    class Hit:
        doc = Doc()

    hits = [Hit()]
    assert _is_unsure("I don't know the window.", hits, spec.unsure_markers)
    assert not _is_unsure("Electronics may be returned in 14 days [Returns policy].", hits, spec.unsure_markers)
    assert _is_unsure("Fourteen days, no citation.", hits, spec.unsure_markers)


def test_outdated_penalty_comes_from_spec():
    spec = load_pipeline_spec()
    retriever = Retriever.from_corpus()
    outdated = next(d for d in retriever.docs if d.status != "current")
    query = outdated.title
    mild = {h.doc.id: h.score for h in retriever.search(query, k=len(retriever.docs), outdated_score_penalty=1.0)}
    penalized = {
        h.doc.id: h.score
        for h in retriever.search(
            query, k=len(retriever.docs), outdated_score_penalty=spec.retriever.outdated_score_penalty
        )
    }
    assert penalized[outdated.id] == mild[outdated.id] * spec.retriever.outdated_score_penalty


def test_run_executes_spec_templates_and_profiles():
    spec = load_pipeline_spec()
    prompts: list[str] = []

    def fake_complete(prompt, max_tokens=700):
        prompts.append(prompt)
        return {
            "text": "Electronics may be returned in 14 days [Returns policy].",
            "model": "test",
            "input_tokens": 1,
            "output_tokens": 1,
        }

    with patch("src.pipeline.complete", side_effect=fake_complete):
        v1 = run("What is the return window for electronics?", "v1")
        v2 = run("What is the return window for electronics?", "v2")

    assert spec.reasoner.template.split("{context}")[0].strip() in prompts[0]
    assert v1["spec"]["id"] == spec.id
    assert v1["spec"]["version"] == spec.version
    assert v1["config"]["critic_ran"] is False
    assert v1["config"]["k"] == 5
    assert v2["config"]["critic_ran"] is True
    assert v2["config"]["k"] == 20
    assert spec.critic.template.split("{context}")[0].strip() in prompts[2]


def test_runtime_does_not_hardcode_product_copy():
    pipeline = (ROOT / "src" / "pipeline.py").read_text()
    html = (ROOT / "static" / "index.html").read_text()
    spec_text = PIPELINE_SPEC_PATH.read_text()
    assert "You are Harborline's support assistant" in spec_text
    assert "You are Harborline's support assistant" not in pipeline
    assert "What is the return window for electronics?" in spec_text
    assert "What is the return window for electronics?" not in html
