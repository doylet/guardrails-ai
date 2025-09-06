"""System constants and defaults for the AI Guardrails Bootstrap System.

This module defines all default values, paths, and configuration constants
used throughout the system. These values can be overridden through configuration
but provide sensible defaults for most use cases.
"""



# Core directory structure
GUARDRAILS_DIR = ".ai"
RECEIPT_DIR = "guardrails/installed"
MANIFEST_FILENAME = "installation-manifest.yaml"
PLUGIN_MANIFEST_FILENAME = "plugin-manifest.yaml"

# File and directory permissions (octal)
DEFAULT_FILE_MODE = 0o644
DEFAULT_DIR_MODE = 0o755
EXECUTABLE_MODE = 0o755

# Default profile and component settings
DEFAULT_PROFILE = "standard"
BUILTIN_PLUGIN_ID = "__builtin__"

# Template and configuration paths
TEMPLATES_DIR = "ai-guardrails-templates"
PLUGINS_DIR = "plugins"
SCRIPTS_DIR = "scripts"

# Standard hook and workflow names
HOOKS = {
    "pre-commit": ".pre-commit-config.yaml",
    "commit-msg": ".githooks/commit-msg",
    "pre-push": ".githooks/pre-push",
}

WORKFLOWS = {
    "guardrails": ".github/workflows/ai_guardrails_on_commit.yaml",
    "pr-template": ".github/pull_request_template.md",
}

# Schema and validation files
SCHEMA_FILES = {
    "envelope": "ai/schemas/copilot_envelope.schema.json",
    "target": "target-structure.schema.yaml",
    "manifest": "schemas/installation-manifest.schema.json",
    "plugin": "schemas/plugin-manifest.schema.json",
}

# Script names for policy enforcement
POLICY_SCRIPTS = {
    "check_envelope": "ai/scripts/check_envelope.py",
    "check_envelope_local": "ai/scripts/check_envelope_local.py",
    "lang_lint": "ai/scripts/lang_lint.sh",
    "lang_test": "ai/scripts/lang_test.sh",
    "validate_docs": "scripts/validate_docs.py",
}

# Configuration file patterns
CONFIG_FILES = {
    "guardrails": "ai/guardrails.yaml",
    "envelope": "ai/envelope.json",
    "capabilities": "ai/capabilities.md",
    "pre_commit": ".pre-commit-config.yaml",
}

# Backup and staging directory patterns
STAGING_PREFIX = ".staging"
BACKUP_PREFIX = ".backup"
SENTINEL_SUFFIX = ".bootstrap-sentinel"

# Hash and receipt metadata
HASH_ALGORITHM = "sha256"
RECEIPT_VERSION = "1.0"

# Supported file extensions for different operations
YAML_EXTENSIONS = {".yaml", ".yml"}
JSON_EXTENSIONS = {".json"}
TEMPLATE_EXTENSIONS = {".template", ".j2", ".jinja"}
MERGEABLE_EXTENSIONS = YAML_EXTENSIONS | JSON_EXTENSIONS

# Component priorities (lower numbers = higher priority)
COMPONENT_PRIORITIES = {
    "core": 0,
    "hooks": 10,
    "workflows": 20,
    "scripts": 30,
    "policies": 40,
    "docs": 50,
    "examples": 60,
}

# Dependency resolution limits
MAX_DEPENDENCY_DEPTH = 10
MAX_COMPONENTS_PER_PROFILE = 50

# Performance and safety limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_MANIFEST_SIZE = 1024 * 1024   # 1MB
STAGING_TIMEOUT = 300  # 5 minutes
CLEANUP_GRACE_PERIOD = 3600  # 1 hour

# CLI output formatting
CLI_WIDTH = 80
PROGRESS_BAR_WIDTH = 40
