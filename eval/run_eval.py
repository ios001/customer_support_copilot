"""Evaluate the agent on eval_set.jsonl.

Metrics per question:
  citation_hit  - the expected source file is cited in the answer
  tool_recall   - fraction of expected tools the agent actually called
  correct       - Claude-as-judge verdict vs. the reference answer

Usage:  python eval/run_eval.py            (writes eval/results.md)
"""
import asyncio
import json
import os
import pathlib
import sys

import anthropic

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "app"))
from agent import run_agent  # noqa: E402

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-haiku-4-5")
judge = anthropic.Anthropic()

JUDGE_PROMPT = """You grade a customer-support answer against a reference answer.
Question: {question}
Reference answer: {reference}
Agent answer: {answer}

Is the agent answer factually consistent with the reference and does it cover its key points?
Extra correct detail is fine; contradictions or invented facts are not.
Reply with JSON only: {{"correct": true|false, "reason": "<one sentence>"}}"""


def grade(question, reference, answer) -> dict:
    msg = judge.messages.create(
        model=JUDGE_MODEL, max_tokens=200,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(question=question, reference=reference, answer=answer)}],
    )
    text = msg.content[0].text.strip().strip("`").removeprefix("json").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"correct": False, "reason": f"unparseable judge output: {text[:100]}"}


async def main():
    cases = [json.loads(l) for l in (ROOT / "eval_set.jsonl").read_text().splitlines() if l.strip()]
    rows = []
    for c in cases:
        out = await run_agent(c["question"])
        called = {t["tool"] for t in out["tool_calls"]}
        expected = set(c["expected_tools"])
        citation_hit = (c["expected_source"] in out["answer"]) if c["expected_source"] else True
        verdict = grade(c["question"], c["reference"], out["answer"])
        rows.append({
            "id": c["id"], "citation_hit": citation_hit,
            "tool_recall": len(called & expected) / len(expected) if expected else 1.0,
            "correct": bool(verdict.get("correct")), "reason": verdict.get("reason", ""),
            "cost": out["cost_usd"] or 0.0,
        })
        r = rows[-1]
        print(f"{c['id']}  correct={r['correct']!s:5}  cite={r['citation_hit']!s:5}  tools={r['tool_recall']:.2f}  {r['reason']}")

    n = len(rows)
    summary = {
        "answer_correctness": sum(r["correct"] for r in rows) / n,
        "citation_hit_rate": sum(r["citation_hit"] for r in rows) / n,
        "tool_recall": sum(r["tool_recall"] for r in rows) / n,
        "avg_cost_usd": sum(r["cost"] for r in rows) / n,
    }
    print("\n" + json.dumps(summary, indent=2))

    lines = ["# Eval results", "", "| Metric | Value |", "|---|---|"]
    lines += [f"| {k} | {v:.2%} |" if k != "avg_cost_usd" else f"| {k} | ${v:.4f} |" for k, v in summary.items()]
    lines += ["", "| id | correct | citation | tool recall | judge reason |", "|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['correct']} | {r['citation_hit']} | {r['tool_recall']:.2f} | {r['reason']} |" for r in rows]
    (ROOT / "results.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {ROOT / 'results.md'}")


if __name__ == "__main__":
    asyncio.run(main())
