import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from goliath.server import GoliathOrchestrationBridge


class GoliathContractTests(unittest.TestCase):
    def setUp(self):
        self.memory = SimpleNamespace(
            get_state=lambda: {"finding_count": 0},
            register_finding=lambda *_args: self.fail("read-only status mutated swarm memory"),
            update_context=lambda *_args: self.fail("read-only status mutated swarm context"),
        )
        self.balancer = SimpleNamespace(get_metrics=lambda: {"status": "available"})
        self.bridge = GoliathOrchestrationBridge(
            Path("."),
            logger=SimpleNamespace(),
            guardian=None,
            memory=self.memory,
            balancer=self.balancer,
        )

    def test_only_read_only_status_tool_is_advertised(self):
        self.assertEqual(
            [tool.name for tool in self.bridge.get_tools()],
            ["goliath_get_swarm_state"],
        )

    def test_status_returns_memory_and_hardware_without_mutation(self):
        result = asyncio.run(
            self.bridge.execute_tool("goliath_get_swarm_state", {})
        )
        self.assertEqual(
            result,
            {
                "memory": {"finding_count": 0},
                "hardware": {"status": "available"},
            },
        )

    def test_unimplemented_or_mutating_routes_are_rejected(self):
        for name in ("goliath_synergize_memory", "eds_scrape_mit_ocw"):
            with self.subTest(name=name):
                result = asyncio.run(self.bridge.execute_tool(name, {}))
                self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
