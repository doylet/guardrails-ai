#!/usr/bin/env bash
# Warn locally; change to --enforce to hard block.
python ai/scripts/policy/acl_check.py --staged || true
