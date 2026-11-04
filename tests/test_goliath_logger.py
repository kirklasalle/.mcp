import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

FLEET_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLEET_ROOT))

from goliath.core.unified_logger import GoliathLogger


class GoliathLoggerLocationTests(unittest.TestCase):
    def test_default_log_dir_follows_cache_dir(self):
        with tempfile.TemporaryDirectory() as cache:
            with patch.dict(os.environ, {"MCP_CACHE_DIR": cache}):
                self.assertEqual(GoliathLogger._default_log_dir(), Path(cache) / "goliath_logs")

    def test_default_log_dir_falls_back_to_fleet_cache(self):
        with patch.dict(os.environ):
            os.environ.pop("MCP_CACHE_DIR", None)
            self.assertEqual(
                GoliathLogger._default_log_dir(), FLEET_ROOT / ".cache" / "goliath_logs"
            )

    def test_logger_does_not_write_into_working_directory(self):
        cwd_dir = tempfile.TemporaryDirectory()
        cache_dir = tempfile.TemporaryDirectory()
        # Cleanups run last-in first-out: release log handles, restore cwd, then delete.
        self.addCleanup(cache_dir.cleanup)
        self.addCleanup(cwd_dir.cleanup)
        previous_cwd = os.getcwd()
        self.addCleanup(os.chdir, previous_cwd)
        self.addCleanup(self._close_goliath_handlers)

        os.chdir(cwd_dir.name)
        with patch.dict(os.environ, {"MCP_CACHE_DIR": cache_dir.name}):
            GoliathLogger(mcp_mode=True)

        self.assertFalse((Path(cwd_dir.name) / ".goliath_logs").exists())
        self.assertTrue((Path(cache_dir.name) / "goliath_logs" / "goliath.log").exists())

    @staticmethod
    def _close_goliath_handlers():
        logger = logging.getLogger("goliath")
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
