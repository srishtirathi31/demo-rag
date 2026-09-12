# Tasks: Harborline Care RAG (spec-driven retrofit)

**Input**: Design documents from `/specs/001-harborline-rag/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

## Phase 1: Spec artifacts

- [x] T001 Write constitution in `.specify/memory/constitution.md`
- [x] T002 [P] Write feature spec, plan, data-model, and quickstart
- [x] T003 [P] Write executable contracts (`pipeline.yaml`, `openapi.yaml`, `agent-config.schema.yaml`)

## Phase 2: Runtime loads the spec

- [x] T004 Implement `src/spec.py` to load and validate `contracts/pipeline.yaml`
- [x] T005 Drive reasoner/critic prompts and unsure markers from the spec in `src/pipeline.py`
- [x] T006 Drive outdated-document penalty from the spec in `src/retrieve.py`
- [x] T007 Expose `/api/spec` and attach spec identity to ask results in `app.py`
- [x] T008 [US5] Render branding and sample questions from `/api/spec` in `static/index.html`

## Phase 3: Tests and guidance

- [x] T009 [P] Contract tests that fail if prompts, copy, or profiles drift
- [x] T010 [P] Cursor rule so later changes edit the spec first
- [x] T011 Update README to describe the spec-driven loop
