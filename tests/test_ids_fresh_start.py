import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MCP_ROOT = Path(__file__).resolve().parents[1]

# Blocking numpy simulates a minimal install, which is all requirements.txt guarantees.
LAUNCHER = (
    "import os, runpy, sys; sys.modules['numpy'] = None; "
    "sys.path.insert(0, os.path.dirname(sys.argv[1])); "
    "runpy.run_path(sys.argv[1], run_name='__main__')"
)


class IdsFreshStartTests(unittest.TestCase):
    def test_server_starts_with_empty_cache_and_without_optional_ai_libraries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fleet = Path(temp_dir) / ".mcp"
            ignore = shutil.ignore_patterns("__pycache__", ".cache", "*.pkl")
            shutil.copytree(MCP_ROOT / "shared", fleet / "shared", ignore=ignore)
            shutil.copytree(MCP_ROOT / "ids", fleet / "ids", ignore=ignore)

            result = subprocess.run(
                [sys.executable, "-c", LAUNCHER, str(fleet / "ids" / "server_ai_enhanced.py")],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                env={**os.environ, "PYTHONUTF8": "1", "MCP_WORKSPACE_ROOT": temp_dir},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            cache = fleet / "ids" / ".cache"
            self.assertTrue((cache / "knowledge_graph.json").exists())
            self.assertEqual(list(cache.glob("*.pkl")), [])


if __name__ == "__main__":
    unittest.main()
