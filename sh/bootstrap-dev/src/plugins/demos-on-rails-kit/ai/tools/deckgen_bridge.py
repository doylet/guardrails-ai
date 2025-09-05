#!/usr/bin/env python3
"""CLI Bridge for demos-on-rails-kit integration with ai-deck-gen.

This script provides a 'deckgen' command that translates demo scenarios
into the actual ai-deck-gen CLI interface, ensuring seamless integration.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Default paths - can be overridden by environment
DEFAULT_AI_DECK_GEN_CLI = os.environ.get("AI_DECK_GEN_CLI", "python -m app.cli.v1")
DEFAULT_AI_DECK_GEN_ROOT = os.environ.get("AI_DECK_GEN_ROOT",
    "/Users/thomasdoyle/Daintree/projects/python/ai_deck_gen")

class DeckGenBridge:
    """Bridge between demo scenarios and ai-deck-gen CLI."""

    def __init__(self, ai_deck_gen_root: str = DEFAULT_AI_DECK_GEN_ROOT):
        self.ai_deck_gen_root = Path(ai_deck_gen_root)
        self.cli_cmd = DEFAULT_AI_DECK_GEN_CLI

    def translate_args(self, topic: str, audience: str = "General",
                      slides: str = "Narrative", seed: int = 0,
                      model: Optional[str] = None,
                      temperature: Optional[float] = None,
                      flags: Optional[Dict[str, bool]] = None) -> List[str]:
        """Translate demo args to ai-deck-gen CLI format."""

        # Base command - assuming the CLI supports these args
        cmd = [
            "build",
            "--topic", topic,
            "--audience", audience,
            "--slides", slides,
            "--seed", str(seed),
        ]

        # Add provider settings
        if model:
            cmd.extend(["--model", model])
        if temperature is not None:
            cmd.extend(["--temperature", str(temperature)])

        # Add feature flags
        if flags:
            for flag, enabled in flags.items():
                if enabled:
                    cmd.extend(["--flag", flag])

        return cmd

    def setup_environment(self, model: Optional[str] = None):
        """Setup environment variables for ai-deck-gen."""
        env = os.environ.copy()

        # Set LMStudio as provider
        env["CLI_PROVIDER"] = "lmstudio"
        env["LM_STUDIO_URL"] = "http://localhost:1234"

        if model:
            env["LM_STUDIO_MODEL"] = model

        return env

    def run_build(self, args: List[str], env: Dict[str, str]) -> tuple:
        """Execute the ai-deck-gen build command."""
        full_cmd = self.cli_cmd.split() + args

        print(f">> Executing: {' '.join(full_cmd)}")
        print(f">> Working directory: {self.ai_deck_gen_root}")

        # Run from ai-deck-gen root directory
        result = subprocess.run(
            full_cmd,
            cwd=self.ai_deck_gen_root,
            env=env,
            capture_output=True,
            text=True
        )

        return result.returncode, result.stdout, result.stderr

    def parse_output(self, stdout: str, stderr: str) -> Dict:
        """Parse ai-deck-gen output and extract quality metrics."""
        # This is where we'd parse the actual output format
        # For now, provide a stub structure that matches demo_harness expectations

        quality_metrics = {
            "layout_satisfaction": None,
            "placeholders_found": 0,
            "elements_per_slide": None
        }

        # Try to extract metrics from output
        # This would need to be customized based on actual ai-deck-gen output format
        lines = (stdout + stderr).split('\n')

        for line in lines:
            line = line.strip()

            # Look for JSON output
            if line.startswith('{') and 'satisfaction' in line:
                try:
                    data = json.loads(line)
                    quality_metrics["layout_satisfaction"] = data.get("satisfaction_overall")
                    quality_metrics["elements_per_slide"] = data.get("mean_elements_per_slide")
                except json.JSONDecodeError:
                    pass

        # Count placeholder markers
        all_output = stdout + stderr
        placeholder_markers = [
            "Slide Title:", "Headline:", "• Main content point",
            "{ }", "{}", "<placeholder>"
        ]
        quality_metrics["placeholders_found"] = sum(
            marker in all_output for marker in placeholder_markers
        )

        return quality_metrics


def main():
    parser = argparse.ArgumentParser(description="AI Deck Generator CLI Bridge")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build a presentation")
    build_parser.add_argument("topic", help="Presentation topic")
    build_parser.add_argument("--audience", default="General", help="Target audience")
    build_parser.add_argument("--slides", default="Narrative", help="Slide types")
    build_parser.add_argument("--seed", type=int, default=0, help="Random seed")
    build_parser.add_argument("--model", help="LLM model to use")
    build_parser.add_argument("--temperature", type=float, help="Model temperature")
    build_parser.add_argument("--flag", action="append", help="Feature flags")
    build_parser.add_argument("--output-dir", help="Output directory")
    build_parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "build":
        bridge = DeckGenBridge()

        # Parse feature flags
        flags = {}
        if args.flag:
            for flag in args.flag:
                flags[flag] = True

        # Translate arguments
        cli_args = bridge.translate_args(
            topic=args.topic,
            audience=args.audience,
            slides=args.slides,
            seed=args.seed,
            model=args.model,
            temperature=args.temperature,
            flags=flags
        )

        # Setup environment
        env = bridge.setup_environment(model=args.model)

        # Execute build
        returncode, stdout, stderr = bridge.run_build(cli_args, env)

        if args.json:
            # Output in format expected by demo_harness
            quality = bridge.parse_output(stdout, stderr)
            result = {
                "return_code": returncode,
                "quality": quality,
                "stdout": stdout,
                "stderr": stderr
            }
            print(json.dumps(result, indent=2))
        else:
            # Normal output
            print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)

        sys.exit(returncode)


if __name__ == "__main__":
    main()
