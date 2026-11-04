import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from goliath.core.load_balancer import VRAMLoadBalancer


class GoliathTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.logger = type(
            "Logger",
            (),
            {
                "warning": lambda *_args: None,
                "info": lambda *_args: None,
            },
        )()
        self.balancer = VRAMLoadBalancer(self.logger)

    @patch.object(VRAMLoadBalancer, "get_vram_usage", return_value=None)
    def test_missing_gpu_telemetry_is_unknown_not_simulated(self, _usage):
        metrics = self.balancer.get_metrics()
        self.assertIsNone(metrics["vram_usage_gb"])
        self.assertFalse(metrics["telemetry_available"])
        self.assertEqual(metrics["status"], "unknown")
        self.assertFalse(self.balancer.check_capacity(0.5))


if __name__ == "__main__":
    unittest.main()
