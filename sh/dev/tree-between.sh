# Save as: ~/bin/tree-between (and chmod +x ~/bin/tree-between)
#!/usr/bin/env bash
set -euo pipefail

usage(){ echo "usage: tree-between [-L depth] <dirA> <dirB>"; exit 1; }
[[ $# -ge 2 ]] || usage
DEPTH=2
if [[ "${1:-}" == "-L" ]]; then DEPTH="${2:-2}"; shift 2; fi
A="${1:?}"; B="${2:?}"

abs() { (cd "$1" 2>/dev/null && pwd -P) || { echo "not a directory: $1" >&2; exit 1; }; }
A="$(abs "$A")"; B="$(abs "$B")"

# Find lowest common ancestor (LCA)
IFS=/ read -r -a aa <<<"${A#/}"
IFS=/ read -r -a bb <<<"${B#/}"
common=()
for ((i=0; i<${#aa[@]} && i<${#bb[@]}; i++)); do
[[ "${aa[i]}" == "${bb[i]}" ]] || break
common+=("${aa[i]}")
done
LCA="/${common[*]}"
LCA="${LCA// /\/}"
[[ -z "${common[*]:-}" ]] && LCA="/"

# Relative paths from LCA
relA="${A#$LCA/}"; relB="${B#$LCA/}"
# Distances (levels)
distA=$(awk -F/ '{print NF}' <<<"$relA")
distB=$(awk -F/ '{print NF}' <<<"$relB")

echo "Common ancestor: $LCA"
echo "A: $A"
echo "B: $B"
echo "Rel paths:"
echo " A: $relA (levels: $distA)"
echo " B: $relB (levels: $distB)"
echo

# 1) Show just the branches down to the two targets (names only)
# NOTE: if both dirs share very common names (like 'src'), this may include extra branches.
echo "# Branches from ancestor to targets"
tree -d --prune -P "$(basename "$A")|$(basename "$B")" "$LCA" || true
echo

# 2) Show each subtree (folders only) to a limited depth
echo "# Subtree of A (depth $DEPTH)"
tree -d -L "$DEPTH" "$A" || true
echo
echo "# Subtree of B (depth $DEPTH)"
tree -d -L "$DEPTH" "$B" || true
