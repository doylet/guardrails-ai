# scripts/validate_demo_scenarios.py
import sys
import yaml
import glob

required = [
    "topic", "audience", "slide_types",
    "expectations.min_layout_satisfaction",
    "expectations.min_elements_per_slide",
    "expectations.no_placeholders"
]


def has_keys(doc, dotted):
    cur = doc
    for part in dotted.split("."):
        if part not in cur:
            return False
        cur = cur[part]
    return True


bad = []
for path in glob.glob("demo_scenarios/*.yaml"):
    y = yaml.safe_load(open(path))
    miss = [k for k in required if not has_keys(y, k)]
    if miss:
        bad.append((path, miss))

if bad:
    for p, m in bad:
        print(f"[guardrails] {p} missing keys: {m}")
    sys.exit(1)
print("Demo scenarios OK")
