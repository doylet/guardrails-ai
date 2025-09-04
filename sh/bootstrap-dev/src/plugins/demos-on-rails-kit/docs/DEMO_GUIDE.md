# Demos on Rails — ai-deck-gen Integration

Keep demos on the real product rails: scenarios + harness calling the production CLI.

## Overview

This plugin provides seamless integration between demo scenarios and the ai-deck-gen project, ensuring that demos exercise the actual production code paths rather than mock implementations.

## Architecture

```
Demo Scenario (YAML) → Demo Harness → CLI Bridge → ai-deck-gen CLI → LMStudioProvider
```

**Components:**
- **Demo Scenarios**: YAML files defining test cases
- **Demo Harness**: Orchestrator that runs scenarios and validates results
- **CLI Bridge**: Translator between demo format and ai-deck-gen CLI
- **ai-deck-gen CLI**: The actual production interface

## Quick Start

### 1. Setup ai-deck-gen Integration

```bash
# Set environment variables (or copy .env.example to .env)
export AI_DECK_GEN_ROOT=/path/to/ai_deck_gen
export LM_STUDIO_URL=http://localhost:1234
export LM_STUDIO_MODEL=llama-3.2-3b-instruct
```

### 2. Run Integration Test

```bash
python test_integration.py
```

### 3. Run Demo Scenarios

```bash
# Run a single scenario
python ai/tools/demo_harness.py run ai/demo_scenarios/example.yaml

# Run with custom settings
DECKGEN_CLI="python ai/tools/deckgen_bridge.py" python ai/tools/demo_harness.py run ai/demo_scenarios/example.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_DECK_GEN_ROOT` | Path to ai-deck-gen project | `/Users/thomasdoyle/Daintree/projects/python/ai_deck_gen` |
| `AI_DECK_GEN_CLI` | CLI command for ai-deck-gen | `python -m app.cli.v1` |
| `LM_STUDIO_URL` | LMStudio server URL | `http://localhost:1234` |
| `LM_STUDIO_MODEL` | Model name in LMStudio | `llama-3.2-3b-instruct` |
| `DECKGEN_CLI` | Demo harness CLI command | `python ai/tools/deckgen_bridge.py` |

### Demo Scenario Format

```yaml
# Example scenario
topic: Quarterly GTM Review
audience: Exec
slide_types:
  - Narrative
  - Comparison
  - Process
  - Data
feature_flags:
  exemplar_retrieval: true
  hybrid_solver: true
  critic_ranker: true
provider_profile:
  model: openai/gpt-4o-mini
  temperature: 0.2
seed: 17
output_dir: out/demos/q3-gtm-review
expectations:
  min_layout_satisfaction: 0.7
  min_elements_per_slide: 5
  no_placeholders: true
```

## Integration Details

### CLI Bridge (`deckgen_bridge.py`)

The bridge translates demo scenario parameters into ai-deck-gen CLI arguments:

- **Topic/Audience/Slides**: Direct mapping to CLI args
- **Feature Flags**: Converted to `--flag` arguments
- **Provider Profile**: Maps to `--model` and `--temperature`
- **Output**: Converts to JSON format for quality parsing

### Quality Metrics

The harness extracts and validates these metrics:

- **Layout Satisfaction**: Overall layout quality score (0-1)
- **Elements Per Slide**: Average number of content elements
- **Placeholders Found**: Count of unresolved placeholder content

### Error Handling

- **Missing ai-deck-gen**: Falls back to error reporting
- **LMStudio Unavailable**: Reports connection issues
- **Invalid Scenarios**: Validates YAML structure and required fields
