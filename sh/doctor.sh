#!/bin/bash
# doctor.sh: Enforces naming policy for repos, packages, and files.
# See doctor.md for full policy details.

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions for output
print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  BMAD Naming Policy Doctor v1.0${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Start the doctor check
print_header

# Detect submodule roots
print_info "Scanning repository structure..."
SUBMODULES=""
if [ -f .gitmodules ]; then
  SUBMODULES=$(git config --file .gitmodules --get-regexp path | awk '{print $2}')
  print_info "Found .gitmodules with configured submodules"
fi
# Also detect submodules without .gitmodules (corrupted state)
SUBMODULES_FROM_STAGE=$(git ls-files --stage | grep "^160000" | awk '{print $4}')
if [ -n "$SUBMODULES_FROM_STAGE" ]; then
  SUBMODULES="$SUBMODULES $SUBMODULES_FROM_STAGE"
  if [ ! -f .gitmodules ]; then
    print_warning "Found submodules without .gitmodules file (corrupted state)"
  fi
fi

if [ -n "$SUBMODULES" ]; then
  print_info "Detected submodules: $(echo $SUBMODULES | tr ' ' ', ')"
fi




# Parse arguments

print_info "Parsing command line options..."
DRY_RUN=0
EXTRA_IGNORE_PATTERNS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=1
      print_info "Dry-run mode enabled - no changes will be made"
      shift
      ;;
    --extra-ignore)
      if [ -n "$2" ]; then
        EXTRA_IGNORE_PATTERNS+=("$2")
        print_info "Added extra ignore pattern: $2"
        shift 2
      else
        print_fail "--extra-ignore requires a pattern or file argument"
        exit 2
      fi
      ;;
    *)
      shift
      ;;
  esac
done

echo ""
print_info "Building ignore patterns from .gitignore and git configuration..."

# Build list of ignored files/dirs (and treat as prefixes)
IGNORED=$(git ls-files --others --ignored --exclude-standard)
IGNORED_PREFIXES=""
for ignore in $IGNORED; do
  # If it's a directory, add trailing slash for prefix match
  if [ -d "$ignore" ]; then
    IGNORED_PREFIXES+="$ignore/\n"
  else
    IGNORED_PREFIXES+="$ignore\n"
  fi
done

# Add extra ignore patterns if provided (files or direct patterns)
EXTRA_IGNORED=""
for pattern in "${EXTRA_IGNORE_PATTERNS[@]}"; do
  if [ -f "$pattern" ]; then
    print_info "Loading ignore patterns from file: $pattern"
    while IFS= read -r filepattern; do
      [ -z "$filepattern" ] && continue
      EXTRA_IGNORED+="$(find . -path ./.git -prune -o -path "$filepattern" -print)\n"
    done < "$pattern"
  else
    EXTRA_IGNORED+="$(find . -path ./.git -prune -o -path "$pattern" -print)\n"
  fi
done

echo ""
print_info "Phase 1: Checking all paths for lowercase and underscore/dash compliance..."

# Fail if any path (except .git and .gitignored) contains uppercase or spaces

# Fail if any path (except .git and .gitignored) contains uppercase or spaces

violations=""
violation_count=0
total_paths=0

find . -type f -o -type d > .doctor_find_tmp
total_paths=$(wc -l < .doctor_find_tmp)
print_info "Examining $total_paths paths..."

while IFS= read -r path; do
  skip=0
  
  # Skip submodules first to avoid git check-ignore fatal errors
  for sub in $SUBMODULES; do
    if [[ "$path" == "./$sub"* ]]; then
      skip=1
      break
    fi
  done
  if [ $skip -eq 1 ]; then
    continue
  fi
  
  # Skip .git directories
  if [[ "$path" == ./.git* ]]; then
    skip=1
  fi
  if [ $skip -eq 1 ]; then
    continue
  fi
  
  # Use git check-ignore for .gitignore and .git/info/exclude
  if git check-ignore -q "$path" 2>/dev/null; then
    skip=1
  fi
  if [ $skip -eq 1 ]; then
    continue
  fi
  
  # Extra ignore patterns (manual, not git-aware)
  for ignore in $EXTRA_IGNORED; do
    if [[ "$path" == "$ignore"* ]]; then
      skip=1
      break
    fi
  done
  if [ $skip -eq 1 ]; then
    continue
  fi
  
  if [[ "$path" =~ [A-Z] ]] || [[ "$path" =~ [[:space:]] ]]; then
    violations+="$path\n"
    ((violation_count++))
  fi
done < .doctor_find_tmp
rm -f .doctor_find_tmp

if [ -n "$violations" ]; then
  print_fail "Found $violation_count path naming violations:"
  echo ""
  echo -e "${RED}Violations (must be lowercase with dashes/underscores only):${NC}"
  echo -e "$violations" | head -20
  if [ $violation_count -gt 20 ]; then
    print_warning "Showing first 20 of $violation_count violations. Fix these and run again."
  fi
  echo ""
  print_info "Fix these paths by renaming to lowercase and using dashes or underscores"
  if [ $DRY_RUN -eq 0 ]; then
    exit 1
  fi
else
  print_pass "All paths are lowercase and use only dashes/underscores"
fi

echo ""
print_info "Phase 2: Checking top-level entries for kebab-case compliance..."

# Check for kebab-case at repo root (top-level folders/files)
fail=0
entries_checked=0
# Check for kebab-case at repo root (top-level folders/files)
fail=0
entries_checked=0
for entry in $(ls -1 | grep -vE '^(\.|\.git)$'); do
  ((entries_checked++))
  if [[ "$entry" =~ [A-Z_] ]] || [[ "$entry" =~ [[:space:]] ]]; then
    print_fail "Top-level entry '$entry' is not kebab-case"
    fail=1
  fi
  if [[ "$entry" =~ _ ]]; then
    print_fail "Top-level entry '$entry' uses underscores; use dashes (kebab-case)"
    fail=1
  fi
  if [[ "$entry" =~ [A-Z] ]]; then
    print_fail "Top-level entry '$entry' uses uppercase; use lowercase only"
    fail=1
  fi
  if [[ "$entry" =~ [[:space:]] ]]; then
    print_fail "Top-level entry '$entry' contains spaces; use dashes"
    fail=1
  fi
done

print_info "Checked $entries_checked top-level entries"

if [ $fail -eq 1 ]; then
  echo ""
  print_info "Top-level entries must use kebab-case (lowercase with dashes only)"
  if [ $DRY_RUN -eq 0 ]; then
    exit 1
  fi
else
  print_pass "All top-level entries are kebab-case"
fi

echo ""
if [ $DRY_RUN -eq 1 ]; then
  print_info "Dry-run completed - no changes were made"
else
  print_pass "All naming policy checks passed!"
fi
print_info "For detailed policy information, see doctor.md"

# Optionally: add more checks for language-specific conventions here
# (e.g., Python package dirs, Node package.json name, etc.)

exit 0
