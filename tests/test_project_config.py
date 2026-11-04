import json
import unittest
from pathlib import Path

SUBMODULE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SUBMODULE_ROOT.parent
CONFIG_PATH = PROJECT_ROOT / ".vscode" / "mcp.json"


class ProjectMcpConfigurationTests(unittest.TestCase):
    def test_profile_launches_every_local_server_and_goliath(self):
        if not CONFIG_PATH.is_file():
            self.skipTest("No parent workspace MCP profile in standalone submodule checkout")
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        servers = config["servers"]
        expected = {
            "project-ids",
            "project-eds",
            "project-ipa",
            "project-vrgc",
            "project-dpa",
            "project-web-search",
            "project-loc",
            "science-data",
            "project-goliath",
        }
        self.assertEqual(set(servers), expected)

        for name, server in servers.items():
            with self.subTest(server=name):
                self.assertEqual(server["command"], "python")
                self.assertEqual(server["cwd"], "${workspaceFolder}")
                self.assertEqual(len(server["args"]), 1)
                script = server["args"][0]
                self.assertTrue(script.startswith("${workspaceFolder}/.mcp/"))
                self.assertNotIn("\\", script)
                entrypoint = PROJECT_ROOT / script.removeprefix("${workspaceFolder}/")
                self.assertTrue(entrypoint.is_file())
                self.assertIn("MCP_WORKSPACE_ROOT", server["env"])
                self.assertEqual(server["env"]["MCP_WORKSPACE_ROOT"], "${workspaceFolder}")
                self.assertIn("MCP_CACHE_DIR", server["env"])
                self.assertEqual(server["env"]["MCP_CACHE_DIR"], "${workspaceFolder}/.mcp/.cache")

    def test_servers_with_guarded_tools_disable_mutations(self):
        if not CONFIG_PATH.is_file():
            self.skipTest("No parent workspace MCP profile in standalone submodule checkout")
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for name in ("project-goliath", "project-vrgc", "project-dpa"):
            with self.subTest(server=name):
                self.assertEqual(
                    config["servers"][name]["env"]["MCP_ALLOW_MUTATIONS"],
                    "0",
                )


if __name__ == "__main__":
    unittest.main()
