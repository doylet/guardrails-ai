---
applyTo: "*"
role: agent
---

# POLICY

## Golden Rules (Non-Negotiable)

1. **Single LLM pathway:**
   All LLM calls go through ai_deck_gen/adapters/LMStudioProvider. No alternatives. No stubs.
2. **Fail fast over guessing:** If anything is unclear (API, schema, invariants), STOP and ask. Do not invent.
3. **Prefer maintainability:** Small changes, clear structure. Follow SOLID/DRY, naming and folder conventions.
4. **Always reuse first:** Before proposing code, discover and cite existing modules, tests, schemas, and CLIs you will call.
5. **Working code with tests:** Every new behavior is covered by tests. All tests must pass.
6. **Clean repo + clean history:** Respect project structure; practice proper branching and commit hygiene; never develop on main.

## Hard DO NOTs

- Do not introduce new adapters/engines/clients if one exists.
- Do not add stubs, mocks, “fake” providers, or speculative scaffolding.
- Do not ship features without a design note (even brief) and tests.
- Do not use emojis.
- Do not bypass planning: no broad refactors hidden in a “fix”.
- Do not push to main. Keep main releasable at all times.

## Strict DRY/Reuse Mode

### Discovery-before-design

- Run a focused search and list the exact functions/classes (by module path) you intend to call, and why.

### ACK handshake

- If reuse is found, begin reply with ACK REUSE and include a call graph (who calls what).
- If an import fails, STOP. Do not scaffold an alternative.

### No duplicate capability

- If a capability exists (e.g., PPTX rendering), you may extend or fix itbut not clone it.
