# Temporary script to debug .gitignore handling in doctor.sh
set -e

echo "--- .gitignore contents ---"
cat .gitignore || echo ".gitignore not found"

echo "--- git ls-files --others --ignored --exclude-standard ---"
git ls-files --others --ignored --exclude-standard

echo "--- find . -type f -o -type d | head -20 ---"
find . -type f -o -type d | head -20
