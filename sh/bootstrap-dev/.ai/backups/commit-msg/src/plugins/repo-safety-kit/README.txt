Repo Safety Kit

Purpose: Protect work if .git or the folder is deleted.
- scripts/make-local-mirror.sh : make/update a local bare mirror at ~/GitMirrors/<repo>.git and push all branches/tags there
- scripts/backup-bundle.sh    : rotating git bundles at ~/GitBundles/<repo>/ (keep 7)
- .githooks/post-commit       : auto-bundle and push to mirror after each commit (best-effort)
- scripts/install-repo-safety.sh: install hooks & perms

Install:
  unzip repo-safety-kit.zip -d .
  bash scripts/install-repo-safety.sh
  scripts/make-local-mirror.sh
  scripts/backup-bundle.sh
