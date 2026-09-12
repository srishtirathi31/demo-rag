# Harborline RAG Constitution

This file is the project constitution. Feature specs, plans, and code changes
must stay consistent with it.

## I. Specs are executable

Product behavior lives in `specs/`. Python interprets those files; it does not
own prompts, sample questions, citation rules, or retrieval penalties.

When behavior changes, edit the spec and its contracts first. Then change code
only as needed to honor the new spec.

## II. Grounded answers only

Answers must come from `corpus/` documents retrieved for that question. If the
documents do not contain the answer, the assistant says it does not know.

Do not invent policies, prices, warranties, or product facts.

## III. Profiles, not forks

`configs/v1.yaml`, `v2.yaml`, and `v3.yaml` are profiles of the same spec.
They may change retrieval depth and whether the reviewer runs. They must not
fork prompts or invent a second product.

## IV. Traces are first-class

Every answer records retrieved doc ids, per-step tokens, latency, and cost.
That payload is the integration surface for an external agent-change checker.

## V. Small and testable

Keep the pipeline retrieve → reason → optional critic. Prefer unit tests that
assert the implementation still matches the contracts, without calling the
gateway unless a test is explicitly live.
