#!/usr/bin/env bash
set -euo pipefail
read_cfg() { awk "/^$1:/{f=1} f&&/$2:/{print substr(\$0,index(\$0,\":\")+2); exit}" .ai/guardrails.yaml 2>/dev/null || true; }
if [[ -f pyproject.toml || -f requirements.txt || -n "$(echo **/*.py 2>/dev/null)" ]]; then
  cmd=$(read_cfg python test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; elif command -v pytest >/dev/null; then pytest -q; fi
fi
if [[ -f package.json ]]; then
  cmd=$(read_cfg node test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else npm test --silent || pnpm -s test || yarn -s test || true; fi
fi
if [[ -f go.mod ]]; then
  cmd=$(read_cfg go test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else go test ./...; fi
fi
if [[ -f Cargo.toml ]]; then
  cmd=$(read_cfg rust test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else cargo test --quiet; fi
fi
if [[ -f pom.xml || -f build.gradle || -f build.gradle.kts ]]; then
  cmd=$(read_cfg java test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else mvn -q -DskipTests=false test || ./gradlew test; fi
fi
if compgen -G "**/*.sln" > /dev/null || compgen -G "**/*.csproj" > /dev/null; then
  cmd=$(read_cfg dotnet test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else dotnet test --no-build --nologo --verbosity quiet; fi
fi
