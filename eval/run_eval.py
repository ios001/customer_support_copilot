"""Evaluate the agent on eval_set.jsonl.

Metrics per question:
  citation_hit  - the expected source file is cited in the answer
  tool_recall   - fraction of expected tools the agent actually called
  no_overreach  - the agent did NOT call any tool listed in forbidden_tools (e.g. needless escalation)
  correct       - Claude-as-judge verdict vs. the reference answer

Cases with ids starting "h" are reported separately as the "hard" set.

Usage:  python eval/run_eval.py              (all cases, writes eval/results.md)
        python eval/run_eval.py h            (only cases whose id starts with "h")
"""
import asyncio
import json
import os
import pathlib
import sys
import time

import anthropic

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "app"))
from agent import run_agent  # noqa: E402

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")  # same default as app/config.py

# Use a model that is neither agent candidate, so no model grades its own answers.
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-opus-5-5")
judge = anthropic.Anthropic()

JUDGE_PROMPT = """You grade a customer-support assistant's answer against a short reference answer.

<question>{question}</question>

<reference>{reference}</reference>

<agent_answer>{answer}</agent_answer>

Rules:
1. Key points come ONLY from the text inside <reference>. Copy each one nearly word for word.
   Never create a key point from the agent answer, and never add requirements the reference does
   not state (e.g. extra verification steps, follow-ups or caveats it does not mention).
2. For each key point, check whether <agent_answer> conveys it (any wording; a correct
   synonym or paraphrase counts).
3. correct = true when every reference key point is conveyed and the agent answer does not
   contradict the reference. Extra detail beyond the reference is fine and must not be penalized.
Reply with JSON only:
{{"key_points": ["<copied from reference>"], "missing": ["<key points not conveyed>"], "correct": true|false, "reason": "<one sentence>"}}"""


def grade(question, reference, answer) -> dict:
    msg = judge.messages.create(
        model=JUDGE_MODEL, max_tokens=600,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(question=question, reference=reference, answer=answer)}],
    )
    # Newer models may return a thinking block before the text block; keep only the text blocks.
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()
    start, end = text.find("{"), text.rfind("}")
    try:
        verdict = json.loads(text[start:end + 1])
        if verdict.get("missing"):
            verdict["reason"] = f"{verdict.get('reason', '')} MISSING: {'; '.join(verdict['missing'])}"
        return verdict
    except (json.JSONDecodeError, ValueError):
        return {"correct": False, "reason": f"unparseable judge output: {text[:100]}"}


async def main():
    cases = [json.loads(l) for l in (ROOT / "eval_set.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(sys.argv) > 1:
        cases = [c for c in cases if c["id"].startswith(sys.argv[1])]
    print(f"Agent model: {CLAUDE_MODEL} | judge model: {JUDGE_MODEL} | cases: {len(cases)}\n")
    if JUDGE_MODEL == CLAUDE_MODEL:
        print("WARNING: the judge is the same model as the agent (self-grading bias). "
              "Set JUDGE_MODEL to a different model.\n")
    # Warm-up call so the first case doesn't pay for a cold SQL warehouse / CLI start-up.
    await run_agent("What plans does Acme Analytics offer?")
    rows = []
    for c in cases:
        start = time.perf_counter()
        out = await run_agent(c["question"])
        latency = time.perf_counter() - start
        called = {t["tool"] for t in out["tool_calls"]}
        expected = set(c["expected_tools"])
        forbidden_called = called & set(c.get("forbidden_tools", []))
        citation_hit = (c["expected_source"] in out["answer"]) if c["expected_source"] else True
        try:
            verdict = grade(c["question"], c["reference"], out["answer"])
        except Exception as e:  # one judge failure must not lose the whole run
            verdict = {"correct": False, "reason": f"JUDGE ERROR: {e}"}
        rows.append({
            "id": c["id"], "set": "hard" if c["id"].startswith("h") else "core",
            "citation_hit": citation_hit,
            "tool_recall": len(called & expected) / len(expected) if expected else 1.0,
            "no_overreach": not forbidden_called,
            "correct": bool(verdict.get("correct")), "reason": verdict.get("reason", ""),
            "cost": out["cost_usd"] or 0.0, "latency": latency,
        })
        r = rows[-1]
        flag = f"  FORBIDDEN={sorted(forbidden_called)}" if forbidden_called else ""
        print(f"{c['id']}  correct={r['correct']!s:5}  cite={r['citation_hit']!s:5}  "
              f"tools={r['tool_recall']:.2f}  {latency:5.1f}s{flag}  {r['reason']}")

    def summarize(rs):
        n = len(rs)
        return {
            "n": n,
            "answer_correctness": sum(r["correct"] for r in rs) / n,
            "citation_hit_rate": sum(r["citation_hit"] for r in rs) / n,
            "tool_recall": sum(r["tool_recall"] for r in rs) / n,
            "no_overreach": sum(r["no_overreach"] for r in rs) / n,
            "avg_cost_usd": sum(r["cost"] for r in rs) / n,
            "avg_latency_s": sum(r["latency"] for r in rs) / n,
            "p90_latency_s": sorted(r["latency"] for r in rs)[max(0, int(0.9 * n) - 1)],
        }

    summary = {name: summarize([r for r in rows if r["set"] == name])
               for name in ("core", "hard") if any(r["set"] == name for r in rows)}
    summary["all"] = summarize(rows)
    print("\n" + json.dumps(summary, indent=2))

    metrics = ["answer_correctness", "citation_hit_rate", "tool_recall", "no_overreach",
               "avg_cost_usd", "avg_latency_s", "p90_latency_s"]

    def fmt(m, v):
        if m == "avg_cost_usd":
            return f"${v:.4f}"
        if m.endswith("latency_s"):
            return f"{v:.1f}s"
        return f"{v:.0%}"

    lines = ["# Eval results", "", f"Agent model: `{CLAUDE_MODEL}` · judge model: `{JUDGE_MODEL}`", "", "| Metric | " + " | ".join(f"{k} (n={v['n']})" for k, v in summary.items()) + " |",
             "|---|" + "---|" * len(summary)]
    for m in metrics:
        cells = [fmt(m, v[m]) for v in summary.values()]
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines += ["", "| id | correct | citation | tool recall | no overreach | judge reason |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['correct']} | {r['citation_hit']} | {r['tool_recall']:.2f} | {r['no_overreach']} | {r['reason']} |"
              for r in rows]
    report = "\n".join(lines) + "\n"
    (ROOT / "results.md").write_text(report, encoding="utf-8")
    per_model = ROOT / f"results_{CLAUDE_MODEL}.md"
    per_model.write_text(report, encoding="utf-8")
    print(f"Wrote {ROOT / 'results.md'} and {per_model}")


if __name__ == "__main__":
    asyncio.run(main())