#!/usr/bin/env python3
"""Demo harness that executes demos through the production interface."""
import argparse
import subprocess
import sys
import json
import os
import time
import yaml

DEFAULT_CLI = os.environ.get("DECKGEN_CLI", "deckgen")

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def cli_cmd(sc):
    args = [
        sc.get("topic",""),
        "--audience", sc.get("audience","General"),
        "--slides", ",".join(sc.get("slide_types", [])) or "Narrative",
        "--seed", str(sc.get("seed", 0)),
    ]
    for k, v in (sc.get("feature_flags") or {}).items():
        if v: args += ["--flag", k]
    prof = sc.get("provider_profile") or {}
    if prof.get("model"): args += ["--model", prof["model"]]
    if prof.get("temperature") is not None: args += ["--temperature", str(prof["temperature"])]
    return [DEFAULT_CLI, "build"] + args

def run_cli(cmd):
    print(">> Running:", " ".join(cmd))
    start = time.time()
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    elapsed = time.time() - start
    print(p.stdout)
    return p.returncode, elapsed, p.stdout

def parse_quality(stdout):
    rep = {"layout_satisfaction": None, "placeholders_found": 0, "elements_per_slide": None}
    for line in stdout.splitlines():
        s = line.strip()
        if s.startswith("{") and '"satisfaction"' in s:
            try:
                b = json.loads(s)
                rep["layout_satisfaction"] = b.get("satisfaction_overall")
                rep["elements_per_slide"] = b.get("mean_elements_per_slide")
            except Exception:
                pass
    markers = ["Slide Title:", "Headline:", "• Main content point", "{ }", "{}", "<placeholder>"]
    rep["placeholders_found"] = sum(m in stdout for m in markers)
    return rep

def check_expectations(exp, q):
    fail = []
    if exp.get("no_placeholders") and q["placeholders_found"] > 0: fail.append("placeholders_present")
    if exp.get("min_layout_satisfaction") is not None and q["layout_satisfaction"] is not None:
        if q["layout_satisfaction"] < exp["min_layout_satisfaction"]: fail.append("layout_satisfaction_below_threshold")
    if exp.get("min_elements_per_slide") is not None and q["elements_per_slide"] is not None:
        if q["elements_per_slide"] < exp["min_elements_per_slide"]: fail.append("elements_per_slide_below_threshold")
    return fail

def write_report(out_dir, data):
    ensure_dir(out_dir)
    with open(os.path.join(out_dir, "demo_report.json"), "w") as f:
        json.dump(data, f, indent=2)

def cmd_run(args):
    sc = load_yaml(args.scenario)
    out_dir = sc.get("output_dir") or "out/demos/default"
    ensure_dir(out_dir)
    cmd = cli_cmd(sc)
    code, elapsed, stdout = run_cli(cmd)
    q = parse_quality(stdout)
    failures = check_expectations(sc.get("expectations") or {}, q)
    report = {
        "scenario": os.path.basename(args.scenario),
        "cli": cmd,
        "elapsed_sec": elapsed,
        "quality": q,
        "expectation_failures": failures,
        "return_code": code,
    }
    write_report(out_dir, report)
    print("== DEMO REPORT ==")
    print(json.dumps(report, indent=2))
    if failures: sys.exit(2 if code == 0 else code)
    sys.exit(code)

def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="sub")
    r = sp.add_parser("run")
    r.add_argument("scenario", help="Path to demo scenario YAML")
    r.set_defaults(func=cmd_run)
    a = p.parse_args()
    if not a.sub:
        p.print_help(); sys.exit(1)
    a.func(a)

if __name__ == "__main__":
    main()
