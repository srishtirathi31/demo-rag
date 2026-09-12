from __future__ import annotations

import time

from src.config import AgentConfig, load_config
from src.llm import complete
from src.pricing import cost_usd
from src.retrieve import Hit, get_retriever
from src.spec import PipelineSpec, load_pipeline_spec


def _format_context(hits: list[Hit]) -> str:
    blocks = []
    for hit in hits:
        blocks.append(
            f"### {hit.doc.title} (id: {hit.doc.id})\n{hit.doc.body}"
        )
    return "\n\n".join(blocks)


def _is_unsure(answer: str, hits: list[Hit], markers: list[str]) -> bool:
    lower = answer.lower()
    if any(m in lower for m in markers):
        return True
    cited = sum(1 for h in hits if h.doc.title.lower() in lower or h.doc.id.lower() in lower)
    return cited == 0


def _llm_step(name: str, step_type: str, result: dict, started: float, fingerprint: str) -> dict:
    in_tok = result["input_tokens"]
    out_tok = result["output_tokens"]
    return {
        "name": name,
        "type": step_type,
        "model": result["model"],
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": round(cost_usd(result["model"], in_tok, out_tok), 6),
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "config_fingerprint": fingerprint,
    }


def _spec_fingerprint(spec: PipelineSpec, extra: str) -> str:
    return f"spec={spec.id}@{spec.version};{extra}"


def run(question: str, config_name: str = "v1") -> dict:
    spec = load_pipeline_spec()
    cfg: AgentConfig = load_config(config_name)
    retriever = get_retriever()
    steps: list[dict] = []
    t_run = time.perf_counter()

    t0 = time.perf_counter()
    hits = retriever.search(
        question,
        k=cfg.retriever.k,
        outdated_score_penalty=spec.retriever.outdated_score_penalty,
    )
    steps.append(
        {
            "name": "retriever",
            "type": "retrieve",
            "k": cfg.retriever.k,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "doc_ids": [h.doc.id for h in hits],
            "config_fingerprint": _spec_fingerprint(spec, f"retriever.k={cfg.retriever.k}"),
        }
    )

    context = _format_context(hits)
    t0 = time.perf_counter()
    reason = complete(
        spec.reasoner.template.format(context=context, question=question),
        max_tokens=spec.reasoner.max_tokens,
    )
    draft = reason["text"]
    steps.append(
        _llm_step(
            "reasoner",
            "llm",
            reason,
            t0,
            _spec_fingerprint(spec, f"retriever.k={cfg.retriever.k}"),
        )
    )

    answer = draft
    critic_ran = False
    should_critic = cfg.critic.enabled and (
        cfg.critic.mode == "always" or _is_unsure(draft, hits, spec.unsure_markers)
    )
    if should_critic:
        t0 = time.perf_counter()
        critique = complete(
            spec.critic.template.format(context=context, question=question, draft=draft),
            max_tokens=spec.critic.max_tokens,
        )
        answer = critique["text"] or draft
        critic_ran = True
        steps.append(
            _llm_step(
                "critic",
                "critic",
                critique,
                t0,
                _spec_fingerprint(spec, f"critic.mode={cfg.critic.mode}"),
            )
        )

    totals = {
        "input_tokens": sum(s.get("input_tokens") or 0 for s in steps),
        "output_tokens": sum(s.get("output_tokens") or 0 for s in steps),
        "cost_usd": round(sum(s.get("cost_usd") or 0 for s in steps), 6),
        "latency_ms": int((time.perf_counter() - t_run) * 1000),
    }
    totals["tokens"] = totals["input_tokens"] + totals["output_tokens"]

    return {
        "question": question,
        "answer": answer,
        "config": {
            "name": cfg.name,
            "description": cfg.description,
            "k": cfg.retriever.k,
            "critic_enabled": cfg.critic.enabled,
            "critic_mode": cfg.critic.mode,
            "critic_ran": critic_ran,
            "spec_id": spec.id,
            "spec_version": spec.version,
        },
        "spec": {
            "id": spec.id,
            "version": spec.version,
            "title": spec.title,
        },
        "totals": totals,
        "retrieved": [
            {
                "id": h.doc.id,
                "title": h.doc.title,
                "rank": h.rank,
                "score": round(h.score, 3),
                "snippet": h.snippet,
                "status": h.doc.status,
            }
            for h in hits
        ],
        "steps": steps,
    }
