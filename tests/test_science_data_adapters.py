import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from science_data.adapters import (
    ScienceDataError,
    list_sources,
    query_exoplanets,
    search_inspire,
)


class JsonResponse:
    def __init__(self, value):
        self.payload = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return self.payload[:size]


class ScienceDataAdapterTests(unittest.TestCase):
    def test_source_catalog_marks_unimplemented_archives(self):
        result = list_sources("astronomy")
        sources = {item["id"]: item for item in result["domains"]["astronomy"]}
        self.assertTrue(sources["nasa-exoplanet-archive"]["implemented"])
        self.assertFalse(sources["mast"]["implemented"])

    def test_exoplanet_query_uses_allowlisted_columns_and_bounded_limit(self):
        requested = {}

        def opener(request, timeout):
            requested["url"] = request.full_url
            requested["timeout"] = timeout
            return JsonResponse([{"pl_name": "Example b"}])

        result = query_exoplanets(["pl_name"], 4, opener=opener)
        self.assertEqual(result["record_count"], 1)
        self.assertIn("select+top+4+pl_name", requested["url"])
        self.assertEqual(requested["timeout"], 20)
        self.assertEqual(len(result["sha256"]), 64)

    def test_exoplanet_query_rejects_untrusted_query_fragments(self):
        with self.assertRaises(ScienceDataError):
            query_exoplanets(["pl_name; drop table users"], opener=lambda *_a, **_k: None)
        with self.assertRaises(ScienceDataError):
            query_exoplanets(limit=101, opener=lambda *_a, **_k: None)

    def test_inspire_query_is_encoded_and_limited(self):
        requested = {}

        def opener(request, timeout):
            requested["url"] = request.full_url
            return JsonResponse({"hits": {"hits": [{"id": "record"}]}})

        result = search_inspire("dark matter", 2, opener=opener)
        self.assertIn("q=dark+matter", requested["url"])
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["source"], "inspire-hep")

    def test_inspire_rejects_empty_or_unbounded_queries(self):
        with self.assertRaises(ScienceDataError):
            search_inspire(" ")
        with self.assertRaises(ScienceDataError):
            search_inspire("physics", 21)


if __name__ == "__main__":
    unittest.main()
