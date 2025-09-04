# Integration with ai-guardrails
- Merge `.ai/guardrails.demos-on-rails.example.yaml` into your main guardrails config.
- Add `docs/copilot_demo_rails.md` to guardrails context so Copilot follows the scenario pattern.
- In CI, run:
    ai-guardrails validate --config .ai/guardrails.yaml   # if your kit exposes this
    python scripts/check_demo_on_rails.py
    python tools/demo_harness.py run demo_scenarios/example.yaml || true
