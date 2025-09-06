#!/usr/bin/env python3
# ai/scripts/policy/commit_msg_check.py

import sys, re, os, subprocess

MAX_SUBJECT = int(os.environ.get("MAX_SUBJECT", "72"))
MAX_BODY_LINES = int(os.environ.get("MAX_BODY_LINES", "30"))

HELP = f"""Commit message policy failed.
- Subject (line 1) must be <= {MAX_SUBJECT} chars.
- Body must be <= {MAX_BODY_LINES} non-comment lines.
Tip: Use multiple -m flags or an editor (git commit) instead of one huge CLI string.
"""

def check_text(msg: str) -> int:
    lines = msg.splitlines()
    subject = lines[0] if lines else ""
    body = lines[1:]

    subj_len = len(subject)
    if subj_len > MAX_SUBJECT:
        sys.stderr.write(f"✖ Subject too long: {subj_len} > {MAX_SUBJECT}\n")
        sys.stderr.write(f"  {subject[:120]}\n")
        sys.stderr.write(HELP)
        return 1

    non_comment = [ln for ln in body if not re.match(r'^[#;]', ln)]
    if len(non_comment) > MAX_BODY_LINES:
        sys.stderr.write(f"✖ Body has {len(non_comment)} lines > {MAX_BODY_LINES}\n")
        sys.stderr.write(HELP)
        return 1

    return 0

def main(argv):
    if len(argv) == 2 and argv[1].startswith("--range="):
        rng = argv[1].split("=", 1)[1]
        revs = subprocess.check_output(["git", "rev-list", rng], text=True).split()
        for c in revs:
            msg = subprocess.check_output(["git", "log", "--format=%B", "-n", "1", c], text=True)
            rc = check_text(msg)
            if rc != 0:
                sys.stderr.write(f"Commit failed policy: {c}\n")
                return rc
        return 0

    if len(argv) != 2:
        sys.stderr.write("Usage: commit_msg_check.py <msg_file> | --range=<A..B>\n")
        return 2
    with open(argv[1], "r", encoding="utf-8", errors="replace") as f:
        msg = f.read().replace("\r", "")
    return check_text(msg)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
