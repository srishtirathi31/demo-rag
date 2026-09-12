# Feature Specification: Harborline Care RAG

**Feature Branch**: `001-harborline-rag`

**Created**: 2026-09-12

**Status**: Active

**Input**: Make the existing Harborline retrieve-then-answer assistant spec-driven so product behavior is defined in specs and executed by the app.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a grounded support question (Priority: P1)

A shopper or support agent opens Harborline Care, types a policy or product question, and receives a short answer that cites Harborline documents. If the knowledge base does not contain the answer, the assistant says it does not know.

**Why this priority**: This is the product. Everything else exists to change or inspect how that answer is produced.

**Independent Test**: Submit a known question (return window for electronics) and confirm the answer is drawn from retrieved corpus documents, with square-bracket citations.

**Acceptance Scenarios**:

1. **Given** the corpus is loaded and a valid config is selected, **When** the user asks a question answered by current policy docs, **Then** the assistant returns 4–6 sentences that cite document titles in square brackets.
2. **Given** the corpus is loaded, **When** the user asks something not covered by any document, **Then** the assistant says it does not know and names related docs it checked.
3. **Given** an empty question, **When** the user submits, **Then** the request is rejected and no model call is made.

---

### User Story 2 - Switch retrieval / reviewer profile (Priority: P1)

The same question can be run under `v1` (top 5, no reviewer), `v2` (top 20, always review), or `v3` (top 7, review only if the draft looks unsure). Profiles change depth and reviewer policy, not the product voice.

**Why this priority**: Profiles are how later tooling compares cost, latency, and quality of an agent change.

**Independent Test**: List configs and confirm each exposes name, description, `k`, critic enabled flag, and critic mode.

**Acceptance Scenarios**:

1. **Given** configs exist on disk, **When** the user lists configs, **Then** they see `v1`, `v2`, and `v3` with the retrieval and critic settings from those YAML files.
2. **Given** a question, **When** the user runs it with `v1`, **Then** at most 5 documents are retrieved and the critic step does not run.
3. **Given** a question, **When** the user runs it with `v2`, **Then** up to 20 documents are retrieved and the critic always runs.
4. **Given** a confident draft under `v3`, **When** the reasoner answer does not look unsure, **Then** the critic is skipped.

---

### User Story 3 - Inspect sources and pipeline (Priority: P2)

After an answer, the user can see which documents were retrieved, their rank and status, and the retrieve → reason → optional critic steps with token and latency counts.

**Why this priority**: Trust and later CI comparison both depend on a visible trace, not only the final sentence.

**Independent Test**: Ask a question and confirm the response includes `retrieved` and `steps` arrays plus totals for tokens, latency, and estimated cost.

**Acceptance Scenarios**:

1. **Given** a successful ask, **When** the result is shown, **Then** each retrieved document has id, title, rank, score, snippet, and status.
2. **Given** a successful ask, **When** the result is shown, **Then** each pipeline step has a name, type, latency, and (for LLM steps) model and token counts.

---

### User Story 4 - Ask from the terminal (Priority: P2)

A developer can ask the same question from the CLI, optionally as JSON, so an adapter or script can wrap the assistant without the browser.

**Why this priority**: The parent impact-analyzer contract is a command that returns a trace.

**Independent Test**: `python -m src.cli --list-configs` prints profiles; `python -m src.cli "…" --config v1 --json` prints the same result shape as `POST /api/ask`.

**Acceptance Scenarios**:

1. **Given** a question and `--json`, **When** the CLI runs, **Then** stdout is the full result object (answer, config, retrieved, steps, totals).
2. **Given** `--list-configs`, **When** the CLI runs, **Then** no model call is made.

---

### User Story 5 - Change behavior by editing the spec (Priority: P1)

Prompts, unsure-draft markers, outdated-doc scoring, UI sample questions, and product copy are defined in the executable pipeline contract. Changing that file changes the running app without editing Python.

**Why this priority**: This is what “spec-driven” means for this repo: the spec is not a write-up of the code; the code runs the spec.

**Independent Test**: Load the pipeline contract and assert the reasoner prompt, critic prompt, sample questions, and outdated penalty used at runtime match that file.

**Acceptance Scenarios**:

1. **Given** `contracts/pipeline.yaml`, **When** the app starts, **Then** the UI kicker, title, lede, and sample questions come from that file.
2. **Given** the same contract, **When** a question is answered, **Then** the reasoner and critic prompts are the templates from that file.
3. **Given** a corpus file marked not `current`, **When** documents are ranked, **Then** its score is multiplied by the contract’s outdated penalty.

## Edge Cases

- Unknown config name returns a not-found error listing available profiles.
- Missing gateway URL or token fails with a clear runtime error, not a stack dump in the UI.
- Outdated or internal corpus files may still be retrieved, but they are down-ranked.
- An empty corpus directory is a hard error at retrieve time.
- Critic output that is empty falls back to the reasoner draft.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST answer using only retrieved Harborline markdown documents.
- **FR-002**: System MUST cite document titles in square brackets when claims are made.
- **FR-003**: System MUST expose three named profiles (`v1`, `v2`, `v3`) whose retrieval `k` and critic policy come from `configs/*.yaml`.
- **FR-004**: System MUST run retrieve → reasoner, then a critic only when the selected profile requires it.
- **FR-005**: System MUST treat a draft as unsure when it matches configured markers or cites no retrieved document.
- **FR-006**: Users MUST be able to ask from the web UI and from the CLI.
- **FR-007**: System MUST return a per-step trace (tokens, latency, cost, retrieved ids) with every answer.
- **FR-008**: System MUST load prompts, product copy, sample questions, and retrieval penalties from `specs/001-harborline-rag/contracts/pipeline.yaml`.
- **FR-009**: System MUST reject empty questions.
- **FR-010**: System MUST down-rank documents whose status is not `current` using the contract penalty.
- **FR-011**: Web UI MUST render branding and sample questions from the loaded spec, not from hardcoded page copy.

### Key Entities

- **Document**: A corpus markdown file with id, title, tags, body, path, and status.
- **Hit**: A ranked retrieval result (document, score, rank, snippet).
- **Agent profile**: Named YAML config with retriever `k` and critic `{enabled, mode}`.
- **Pipeline spec**: Executable contract for prompts, markers, copy, samples, and penalties.
- **Trace step**: Named pipeline stage with timing and optional token/cost fields.
- **Ask result**: Question, answer, profile, spec identity, totals, retrieved hits, steps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from landing page to a cited answer in one submit, with sources visible on the same screen.
- **SC-002**: Switching profile changes only `k` and critic behavior; the product voice stays the same spec.
- **SC-003**: Contract tests pass without a live model call and fail if prompts or copy drift from `pipeline.yaml`.
- **SC-004**: CLI `--json` output is sufficient for an external adapter to wrap the assistant later.

## Assumptions

- Answers are grounded in the local `corpus/` only; there is no live web search.
- Some corpus files are intentionally outdated or internal so a large `k` can pull in noise.
- Model access is through the AI Gateway (`AI_GATEWAY_BASE_URL`, `AI_GATEWAY_TOKEN`).
- Estimated cost is from a static price table, not a gateway invoice.
- This repo does not include the agent-change checker; it only produces a wrap-able trace.
