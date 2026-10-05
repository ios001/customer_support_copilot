"""Chat with the agent in your terminal:  python app/cli.py"""
import asyncio
import json

from agent import run_agent


def main():
    history = []
    print("Support Copilot. Type a question (Ctrl+C to quit).")
    while True:
        try:
            q = input("\nyou> ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not q:
            continue
        out = asyncio.run(run_agent(q, history))
        for call in out["tool_calls"]:
            print(f"  [tool] {call['tool']} {json.dumps(call['input'])}")
        print(f"\ncopilot> {out['answer']}")
        print(f"  (turns={out['turns']}, cost=${out['cost_usd'] or 0:.4f})")
        history += [{"role": "user", "content": q}, {"role": "assistant", "content": out["answer"]}]


if __name__ == "__main__":
    main()
