import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.probe_v2 import (
    build_tool_coverage,
    gate_exit_code,
    is_error_result,
    validate_tool_catalog,
)


class ProbeResultTests(unittest.TestCase):
    def test_detects_mcp_error_flag(self):
        self.assertTrue(is_error_result(True, ""))

    def test_detects_error_shaped_json_payload(self):
        self.assertTrue(is_error_result(False, '{"status": "error", "error": "timeout"}'))
        self.assertTrue(is_error_result(False, '{"error": "upstream_failed"}'))

    def test_accepts_success_json_and_plain_text(self):
        self.assertFalse(is_error_result(False, '{"status": "success", "results": []}'))
        self.assertFalse(is_error_result(False, "No suggestions available"))

    def test_validates_tool_schemas_and_expected_goliath_surface(self):
        tool = SimpleNamespace(
            name="goliath_get_swarm_state",
            inputSchema={"type": "object", "properties": {}},
        )
        self.assertTrue(validate_tool_catalog([tool], {"goliath_get_swarm_state"})["valid"])

    def test_rejects_bad_schema_or_unexpected_tools(self):
        tools = [
            SimpleNamespace(name="expected", inputSchema={"type": "object", "properties": {}}),
            SimpleNamespace(name="unexpected", inputSchema={"type": "string"}),
        ]
        result = validate_tool_catalog(tools, {"expected"})
        self.assertFalse(result["valid"])
        self.assertEqual(result["invalid_schemas"], ["unexpected"])
        self.assertEqual(result["unexpected_names"], ["unexpected"])

    def test_tool_coverage_distinguishes_smoked_and_unverified_tools(self):
        coverage = build_tool_coverage(
            ["goliath_get_swarm_state", "legacy_route"],
            {"goliath_get_swarm_state": True},
        )
        self.assertEqual(
            coverage,
            [
                {"tool": "goliath_get_swarm_state", "status": "positive_smoke_passed"},
                {"tool": "legacy_route", "status": "not_individually_exercised"},
            ],
        )

    def test_gate_exit_code_fails_unless_every_server_is_ok(self):
        self.assertEqual(gate_exit_code([{"status": "OK"}, {"status": "OK"}]), 0)
        self.assertEqual(gate_exit_code([{"status": "OK"}, {"status": "FAIL"}]), 1)
        self.assertEqual(gate_exit_code([{"status": "ADDITIONAL_CALL_FAILED"}]), 1)
        self.assertEqual(gate_exit_code([{}]), 1)
        self.assertEqual(gate_exit_code([]), 1)


if __name__ == "__main__":
    unittest.main()
