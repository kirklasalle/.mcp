import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

SERVER_PATH = Path(__file__).resolve().parents[1] / "loc" / "server.py"
SPEC = importlib.util.spec_from_file_location("project_loc_server", SERVER_PATH)
loc_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loc_server)


class LibraryOfCongressErrorTests(unittest.TestCase):
    @patch.object(loc_server.requests, "get", side_effect=requests.Timeout("read timed out"))
    def test_upstream_failure_raises_instead_of_returning_success_payload(self, _get):
        with self.assertRaisesRegex(RuntimeError, "loc_search_catalog_upstream_failure"):
            loc_server.loc_search_catalog("astronomy", limit=1)

    def test_metadata_rejects_non_loc_host(self):
        with self.assertRaisesRegex(ValueError, "approved loc.gov host"):
            loc_server.loc_get_item_metadata("https://example.org/item/1")


if __name__ == "__main__":
    unittest.main()
