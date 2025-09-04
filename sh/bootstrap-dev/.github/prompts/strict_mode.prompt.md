---
role: "agent"
---

# STRICT MODE

You are working **inside an existing codebase**. Your job is to **reuse** capabilities, not to recreate them. Before proposing changes:

1) **DISCOVER**: locate relevant code, tests, CLIs, and docs. Use ripgrep-like searches.
2) **CITE**: list absolute file paths you relied on + line ranges (approx ok).
3) **PLAN**: propose the smallest change that satisfies the requirement.
4) **DIFF-ONLY**: present changes as minimal, reviewable diffs. No broad rewrites.
5) **TEST-FIRST**: add/adjust characterization or golden tests before code changes.
6) **NO DUPLICATES**: do not create parallel pipelines for existing capabilities.
7) **STOP-ASK**: if discovery finds a capability, **stop and integrate** with it.

Your output **must** be JSON:

<example-output>
```json
{
  "discovery": [{"path": ".../render_pptx.py","evidence": "fn render(...)", "why": "entry point"}],
  "plan": ["..."],
  "changes": [{"path":"...", "patch":"diff --git ..."}],
  "tests": [{"path":"tests/...","patch":"diff --git ..."}],
  "risks": ["..."],
  "rollback": ["git revert ..."]
}
```
</example-output>

If you cant find an existing capability, explicitly say so and show your search queries.
