# Quickstart: Harborline Care RAG

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill AI_GATEWAY_BASE_URL, AI_GATEWAY_TOKEN
pytest
uvicorn app:app --reload --port 8000
```

Open http://127.0.0.1:8000. Branding and sample questions come from
`specs/001-harborline-rag/contracts/pipeline.yaml`.

```bash
python -m src.cli --list-configs
python -m src.cli "What is the return window for electronics?" --config v1
```

To change product behavior, edit the pipeline contract or a profile YAML, then
re-run. Do not hardcode prompts or sample questions in Python or HTML.
