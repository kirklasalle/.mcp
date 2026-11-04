import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BRIDGE_PATH = Path(__file__).resolve().parents[1] / "dpa" / "ids_bridge.py"


def load_bridge(path=BRIDGE_PATH, name="project_dpa_ids_bridge"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DpaIdsBridgeTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("DPA_IDS_API_PATH", None)
        self.bridge = load_bridge()

    def test_disabled_by_default_and_never_spawns_a_process(self):
        with patch.object(
            self.bridge.subprocess, "run", side_effect=AssertionError("spawned")
        ) as run:
            result = self.bridge.IDSBridge().status()
        self.assertEqual(result["error"], "ids_bridge_disabled")
        run.assert_not_called()

    def test_never_executes_a_script_found_in_the_host_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = Path(tmp)
            module_dir = host / ".mcp" / "dpa"
            module_dir.mkdir(parents=True)
            copied = module_dir / "ids_bridge.py"
            copied.write_text(BRIDGE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            marker = host / "executed.marker"
            script_dir = host / "src" / "core" / "utils"
            script_dir.mkdir(parents=True)
            (script_dir / "ids_server_api.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
                encoding="utf-8",
            )
            module = load_bridge(copied, "host_layout_ids_bridge")
            module.IDSBridge().update()
            self.assertFalse(marker.exists())

    def test_rejects_relative_missing_and_directory_script_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            for configured in ("relative/ids_api.py", str(Path(tmp) / "missing.py"), tmp):
                with self.subTest(configured=configured), patch.dict(
                    os.environ, {"DPA_IDS_API_PATH": configured}
                ), patch.object(
                    self.bridge.subprocess, "run", side_effect=AssertionError("spawned")
                ):
                    result = self.bridge.IDSBridge().status()
                    self.assertEqual(result["error"], "ids_bridge_script_invalid")

    def test_runs_only_the_configured_script_with_its_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "ids_api.py"
            script.write_text(
                "import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8"
            )
            with patch.dict(os.environ, {"DPA_IDS_API_PATH": str(script)}):
                output = self.bridge.IDSBridge().search("candidate a")
        self.assertEqual(json.loads(output), ["search", "candidate a"])

    def test_child_never_inherits_the_protocol_stdin_and_is_time_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "ids_api.py"
            script.write_text("print('ok')\n", encoding="utf-8")
            completed = type("Completed", (), {"stdout": "ok\n"})()
            with patch.dict(os.environ, {"DPA_IDS_API_PATH": str(script)}), patch.object(
                self.bridge.subprocess, "run", return_value=completed
            ) as run:
                self.bridge.IDSBridge().status()
        kwargs = run.call_args.kwargs
        self.assertIs(kwargs["stdin"], self.bridge.subprocess.DEVNULL)
        self.assertEqual(kwargs["timeout"], self.bridge.COMMAND_TIMEOUT_SECONDS)
        self.assertTrue(kwargs["capture_output"])

    def test_failing_script_is_reported_as_an_error_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "ids_api.py"
            script.write_text(
                "import sys\nsys.stderr.write('boom')\nsys.exit(2)\n", encoding="utf-8"
            )
            with patch.dict(os.environ, {"DPA_IDS_API_PATH": str(script)}):
                result = self.bridge.IDSBridge().update()
        self.assertEqual(result["error"], "ids_bridge_command_failed")
        self.assertIn("boom", result["message"])


if __name__ == "__main__":
    unittest.main()
