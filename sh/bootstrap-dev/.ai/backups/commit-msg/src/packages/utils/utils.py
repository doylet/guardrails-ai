import yaml
import glob

PLUGIN_DIRS = [
    "src/plugins/*/plugin-manifest.yaml",
    "ai/plugins/*/plugin-manifest.yaml"
]


class Colors:
    """Professional ANSI color codes for CLI output"""
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @classmethod
    def ok(cls, text):
        return f"{cls.GREEN}{text}{cls.RESET}"

    @classmethod
    def error(cls, text):
        return f"{cls.RED}{text}{cls.RESET}"

    @classmethod
    def warn(cls, text):
        return f"{cls.YELLOW}{text}{cls.RESET}"

    @classmethod
    def info(cls, text):
        return f"{cls.BLUE}{text}{cls.RESET}"

    @classmethod
    def bold(cls, text):
        return f"{cls.BOLD}{text}{cls.RESET}"


def discover_plugins():
    manifests = []
    for pat in PLUGIN_DIRS:
        for path in glob.glob(pat):
            with open(path) as f:
                manifests.append((path, yaml.safe_load(f)))
    return manifests

def activate_plugins():
    for path, m in discover_plugins():
        name = m["plugin"]["name"]
        print(f"[ai-guardrails] Activating plugin: {name} ({path})")
        # Optional: enforce env requirements and dependencies here
        # e.g., m["plugin"]["environment"]["requires"] etc.

# if __name__ == "__main__":
#     activate_plugins()
