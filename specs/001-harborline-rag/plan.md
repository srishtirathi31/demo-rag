# Implementation Plan: Harborline Care RAG

**Branch**: `001-harborline-rag` | **Date**: 2026-09-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-harborline-rag/spec.md`

## Summary

Keep the existing retrieve → Claude → optional critic app, but make the spec the runtime source of truth. Prompts, UI copy, sample questions, unsure markers, and the outdated-document penalty live in `contracts/pipeline.yaml`. Profiles stay in `configs/*.yaml`. Python loads and executes those files.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic v2, PyYAML, rank-bm25, Anthropic SDK, python-dotenv

**Storage**: Local markdown in `corpus/`; no database

**Testing**: pytest + FastAPI TestClient; contract tests must not call the gateway

**Target Platform**: Local macOS/Linux; browser UI at port 8000

**Project Type**: Web service + CLI over a shared pipeline

**Performance Goals**: Single-user demo; trace every step rather than optimize throughput

**Constraints**: Answers grounded in local corpus only; gateway credentials required for live asks

**Scale/Scope**: ~30 markdown docs, 3 profiles, one pipeline spec

## Constitution Check

- Specs are executable: pipeline contract is loaded at runtime. **Pass**
- Grounded answers only: reasoner/critic prompts still forbid invention. **Pass**
- Profiles, not forks: v1/v2/v3 change only `k` and critic policy. **Pass**
- Traces are first-class: existing step/totals payload retained and tagged with spec version. **Pass**
- Small and testable: contract tests cover spec loading without the gateway. **Pass**

## Project Structure

### Documentation (this feature)

```text
specs/001-harborline-rag/
├── spec.md
├── plan.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── checklists/requirements.md
└── contracts/
    ├── pipeline.yaml
    ├── openapi.yaml
    └── agent-config.schema.yaml
```

### Source Code (repository root)

```text
configs/                 # v1 / v2 / v3 profiles
corpus/                  # Harborline markdown
src/spec.py              # load and validate the pipeline contract
src/config.py            # load profiles
src/retrieve.py          # BM25 over corpus
src/pipeline.py          # execute the spec
src/llm.py               # gateway client
src/cli.py               # terminal entrypoint
app.py                   # FastAPI + static UI
static/index.html        # branding and samples from /api/spec
tests/                   # contract and unit tests
```

**Structure Decision**: Keep the existing single-project layout. Add `src/spec.py` and `tests/` rather than a new package tree.

## Complexity Tracking

No constitution violations.
