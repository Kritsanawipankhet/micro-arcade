import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"pygame", "M5", "machine", "esp32", "esp", "network", "socket",
             "dataclasses", "abc", "typing", "asyncio"}
DISALLOWED = {
    "contracts": {"core", "games", "scenes", "adapters", "simulator", "main"},
    "core": {"games", "scenes", "adapters", "simulator", "main"},
    "games": {"core", "scenes", "adapters", "simulator", "main"},
    "scenes": {"games", "adapters", "simulator", "main"},
}


def test_shared_import_boundaries():
    for layer, disallowed in DISALLOWED.items():
        for path in (ROOT / layer).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                for module in modules:
                    assert module.split(".")[0] not in FORBIDDEN | disallowed, (
                        path, module
                    )
