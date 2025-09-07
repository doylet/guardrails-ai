#!/usr/bin/env bash
# commit-msg: enforce concise, readable commit messages
# - Subject (line 1) <= 72 chars
# - Body <= 30 non-comment lines
# - Soft-wrap body to 72 columns
# Exits non-zero on violations.

set -euo pipefail

msg_file="$1"
max_subject=72
max_body_lines=30
wrap_cols=72

# Normalize line endings to LF and strip trailing spaces (portable, no in-place sed assumptions)
tmpfile="$(mktemp)"
# 1) remove CR
tr -d '\r' < "$msg_file" > "$tmpfile"
# 2) strip trailing spaces on each line
awk '{ sub(/[ \t]+$/, "", $0); print }' "$tmpfile" > "$msg_file"
rm -f "$tmpfile"

# Read subject and body
subject="$(sed -n '1p' "$msg_file")"
body="$(sed -n '2,$p' "$msg_file")"

# Helper to print an excerpt safely
excerpt() {
  printf '%s\n' "$1" | head -n 1 | awk '{print substr($0,1,120)}'
}

# Check subject length (count characters, not bytes where possible)
subject_len=$(printf '%s' "$subject" | wc -m | tr -d ' ')
if [ "$subject_len" -gt "$max_subject" ]; then
  echo "✖ Commit subject is ${subject_len} chars (limit ${max_subject}):"
  echo "  \"$(excerpt "$subject")\""
  echo "→ Please shorten the first line (imperative mood, <= ${max_subject} chars)."
  exit 1
fi

# Count body lines ignoring comments and empty lines markers from templates (# or ; at start)
body_lines=$(printf '%s\n' "$body" | grep -vE '^[#;]' | wc -l | tr -d ' ')
if [ "$body_lines" -gt "$max_body_lines" ]; then
  echo "✖ Commit body has ${body_lines} lines (limit ${max_body_lines})."
  echo "→ Summarize or move detail to the PR description."
  exit 1
fi

# Soft-wrap body to wrap_cols (preserve blank lines)
wrapped="$(mktemp)"
{
  printf '%s\n' "$subject"
  # keep a blank line between subject and body if body exists
  if [ -n "$body" ]; then
    echo
    # fold only non-empty lines; keep blank lines
    # Use POSIX fold; -s soft-wrap on spaces
    printf '%s\n' "$body" | awk -v w="$wrap_cols" '
      NF==0 { print ""; next }
      { cmd = "fold -s -w " w; print | cmd; close(cmd) }
    '
  fi
} > "$wrapped"
mv "$wrapped" "$msg_file"

exit 0
