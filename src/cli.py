from __future__ import annotations

import argparse
import json

from src.config import list_configs
from src.pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the Harborline RAG assistant")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--config", default="v1", help="Config name: v1, v2, or v3")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON")
    parser.add_argument("--list-configs", action="store_true")
    args = parser.parse_args()

    if args.list_configs:
        for cfg in list_configs():
            print(f"{cfg.name:4}  k={cfg.retriever.k:<3} critic={cfg.critic.enabled} ({cfg.critic.mode})  {cfg.description}")
        return

    if not args.question:
        parser.error("question is required unless --list-configs is set")

    result = run(args.question, config_name=args.config)
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"[{result['config']['name']}] k={result['config']['k']}  critic={result['config']['critic_enabled']}")
    t = result["totals"]
    print(
        f"tokens {t['input_tokens']} in / {t['output_tokens']} out  "
        f"latency {t['latency_ms']} ms  est. ${t['cost_usd']:.6f}"
    )
    print()
    print(result["answer"])
    print()
    print("Sources:")
    for doc in result["retrieved"]:
        print(f"  {doc['rank']}. {doc['title']} ({doc['id']})")
    print()
    print("Steps:")
    for s in result["steps"]:
        extra = ""
        if s.get("input_tokens") or s.get("output_tokens"):
            extra = (
                f"  {s['input_tokens']} in / {s['output_tokens']} out  "
                f"${s.get('cost_usd', 0):.6f}"
            )
        print(f"  {s['name']:10}  {s['latency_ms']} ms{extra}")


if __name__ == "__main__":
    main()
