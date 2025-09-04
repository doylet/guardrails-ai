MODE: <Loop|Debug|Express|Main> | scope=<N> | confidence=<0–100> | rationale=<one line>

```json
{
  "discovery": [],
  "assumptions": [],
  "plan": [],
  "changes": [],
  "tests": [],
  "validation": { "commands": [], "results": [] },
  "limits": { "files_touched": 5, "workflow": "Main" },
  "risks": [],
  "rollback": [],
  "question": null,
  "status": "READY_FOR_REVIEW"
}
```

## Demo on rails:

- [ ] Demo changes follow Demos on Rails (scenario + harness)
- [ ] Tests include proper markers (unit/contract/integration/e2e/smoke)
- [ ] No direct imports of engine internals from demos/tests
