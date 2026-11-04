import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.mutation_gate import APPROVED_PROPERTY, mutation_denial


class MutationGateTests(unittest.TestCase):
    def test_denied_without_operator_flag_even_when_call_is_approved(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCP_ALLOW_MUTATIONS", None)
            denial = mutation_denial("probe_tool", {"approved": True})
        self.assertEqual(denial["error"], "explicit_approval_required")
        self.assertEqual(denial["tool"], "probe_tool")

    def test_denied_when_flag_is_not_exactly_one(self):
        for value in ("0", "true", "yes", ""):
            with self.subTest(value=value), patch.dict(
                os.environ, {"MCP_ALLOW_MUTATIONS": value}
            ):
                self.assertIsNotNone(mutation_denial("probe_tool", {"approved": True}))

    def test_denied_when_call_is_not_approved(self):
        with patch.dict(os.environ, {"MCP_ALLOW_MUTATIONS": "1"}):
            for arguments in (None, {}, {"approved": False}, {"approved": "true"}, {"approved": 1}):
                with self.subTest(arguments=arguments):
                    self.assertIsNotNone(mutation_denial("probe_tool", arguments))

    def test_allowed_only_with_flag_and_literal_true_approval(self):
        with patch.dict(os.environ, {"MCP_ALLOW_MUTATIONS": "1"}):
            self.assertIsNone(mutation_denial("probe_tool", {"approved": True}))

    def test_approval_property_is_a_boolean_schema(self):
        self.assertEqual(APPROVED_PROPERTY["type"], "boolean")


if __name__ == "__main__":
    unittest.main()
