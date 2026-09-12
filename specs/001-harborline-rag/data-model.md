# Data Model: Harborline Care RAG

## Document

Loaded from `corpus/*.md` with optional YAML front matter.

| Field | Type | Notes |
|---|---|---|
| id | string | Front matter `id`, else filename stem |
| title | string | Front matter `title`, else stem |
| tags | string[] | Search boost text |
| body | string | Markdown after front matter |
| path | path | Source file |
| status | string | `current` unless marked otherwise |

## Hit

| Field | Type | Notes |
|---|---|---|
| doc | Document | Retrieved document |
| score | float | BM25 score after outdated penalty |
| rank | int | 1-based |
| snippet | string | Query-biased excerpt |

## Agent profile (`configs/*.yaml`)

Validated by `src/config.py` against `contracts/agent-config.schema.yaml`.

| Field | Type | Notes |
|---|---|---|
| name | string | `v1`, `v2`, or `v3` |
| description | string | Shown in UI/CLI |
| retriever.k | int | Top-k documents |
| critic.enabled | bool | Whether critic may run |
| critic.mode | `always` \| `if_unsure` | When it runs if enabled |

## Pipeline spec (`contracts/pipeline.yaml`)

| Field | Type | Notes |
|---|---|---|
| id | string | Stable spec id |
| version | string | Shown on traces and UI |
| title, kicker, lede | string | UI copy |
| samples | string[] | Suggested questions |
| reasoner.template | string | `{context}` `{question}` |
| critic.template | string | `{context}` `{question}` `{draft}` |
| unsure_markers | string[] | Draft phrases that trigger v3 critic |
| retriever.outdated_score_penalty | float | Multiplier when `status != current` |

## Ask result

Returned by `run()` and `POST /api/ask`.

| Field | Notes |
|---|---|
| question | Echoed input |
| answer | Final text (critic output or draft) |
| config | Profile + whether critic ran + spec identity |
| spec | `{id, version, title}` |
| totals | Tokens, cost, latency |
| retrieved | Hit summaries |
| steps | Per-stage trace |
