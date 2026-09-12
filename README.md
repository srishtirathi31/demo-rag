# Harborline RAG demo

A small retrieve-then-answer app over a fictional consumer-electronics knowledge base. Built as a stand-alone repo so an agent-change checker can be pointed at it later.

It does **not** include that checker. It only answers questions from local markdown.

The app is **spec-driven**: product behavior lives in `specs/001-harborline-rag/`, and the code executes that spec. A config file then chooses retrieval depth and whether a reviewer step runs.

## Spec-driven loop

1. Edit the constitution only when project rules change: `.specify/memory/constitution.md`
2. Edit product behavior in `specs/001-harborline-rag/spec.md` and `contracts/pipeline.yaml` (prompts, copy, samples, unsure markers, outdated-doc penalty)
3. Edit a profile in `configs/*.yaml` only to change `k` or critic policy
4. Change Python or HTML only so it still loads those files
5. Run `pytest` — contract tests fail if the runtime drifts from the spec

Active feature pointer: `.specify/feature.json`.

## What you can change later

| Config | Retrieval | Reviewer |
|---|---|---|
| `v1` | top 5 docs | off |
| `v2` | top 20 docs | always on |
| `v3` | top 7 docs | only if the draft looks unsure |

Configs live in `configs/*.yaml`. The pipeline is retrieve → reason → optional critic. Prompts for those steps come from `specs/001-harborline-rag/contracts/pipeline.yaml`.

## Setup

Python 3.11+ recommended.

```bash
cd demo/RAG
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

```
AI_GATEWAY_BASE_URL=...
AI_GATEWAY_TOKEN=...
ANTHROPIC_MODEL=claude-haiku-4
```

If the gateway rejects `claude-haiku-4`, set `ANTHROPIC_MODEL` to the exact id in your catalog (the sibling hackathon repo uses names like `claude-sonnet-5`).

## Tests

```bash
source .venv/bin/activate
pytest
```

These tests do not call the model gateway. They check that the loaded spec, profiles, API, and UI stay aligned.

## Run the UI

```bash
source .venv/bin/activate
uvicorn app:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The page title, lede, and sample questions come from the pipeline spec. Pick a config, click a sample question, or type your own.

## Run from the terminal

```bash
python -m src.cli "What is the return window for electronics?" --config v1
python -m src.cli --list-configs
python -m src.cli "What is the warranty on refurbished Pulse Headphones?" --config v2 --json
```

`--json` prints the answer plus retrieved docs, spec identity, and per-step token counts. That payload is what a later package can wrap.

## Layout

```
.specify/         constitution + active feature pointer
specs/            feature spec, plan, tasks, executable contracts
configs/          v1 / v2 / v3 YAML profiles
corpus/           ~30 Harborline markdown docs
src/spec.py       loads contracts/pipeline.yaml
src/retrieve.py   BM25 over the corpus
src/pipeline.py   retrieve → Claude → optional critic
src/cli.py        terminal entrypoint
app.py            FastAPI + the page in static/
tests/            contract tests (no gateway)
```

Answers are grounded in `corpus/` only. Some files are marked outdated or internal on purpose, so retrieving 20 docs pulls in noise.
