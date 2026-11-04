import json
import os
import pickle
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ids.graph_bridge import GraphBridge


class PickleTripwire:
    """Unpickling this object creates a directory, which proves code executed."""

    def __init__(self, marker):
        self.marker = marker

    def __reduce__(self):
        return (os.mkdir, (self.marker,))


class GraphBridgeTests(unittest.TestCase):
    def test_trace_lineage_returns_empty_for_unknown_entity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bridge = GraphBridge(root, graph_cache_path=root / "cache.json")

            self.assertEqual(bridge.trace_lineage("missing.py"), [])

    def test_trace_lineage_returns_defining_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bridge = GraphBridge(root, graph_cache_path=root / "cache.json")
            bridge.graph.add_node("module.py", type="file")
            bridge.graph.add_node("module.py:Thing", type="class")
            bridge.graph.add_edge("module.py", "module.py:Thing", relation="defines")

            self.assertEqual(
                bridge.trace_lineage("module.py:Thing"),
                ["module.py", "module.py:Thing"],
            )

    def test_graph_cache_round_trips_as_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / "cache.json"
            bridge = GraphBridge(root, graph_cache_path=cache)
            bridge.graph.add_node("module.py", type="file", size=42)
            bridge.graph.add_node("module.py:Thing", type="class", docstring=None)
            bridge.graph.add_edge("module.py", "module.py:Thing", relation="defines")
            bridge.save_graph()

            self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["version"], 1)
            self.assertFalse((root / "cache.json.tmp").exists())

            reloaded = GraphBridge(root, graph_cache_path=cache)
            self.assertEqual(
                dict(reloaded.graph.nodes(data=True)),
                dict(bridge.graph.nodes(data=True)),
            )
            self.assertEqual(
                list(reloaded.graph.edges(data=True)),
                list(bridge.graph.edges(data=True)),
            )

    def test_pickle_cache_is_never_deserialized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            marker = root / "executed.marker"
            cache = root / "cache.json"
            cache.write_bytes(pickle.dumps(PickleTripwire(str(marker))))

            bridge = GraphBridge(root, graph_cache_path=cache)

            self.assertFalse(marker.exists())
            self.assertEqual(len(bridge.graph), 0)

    def test_unknown_cache_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / "cache.json"
            cache.write_text(
                json.dumps({"version": 99, "nodes": [], "edges": []}), encoding="utf-8"
            )

            bridge = GraphBridge(root, graph_cache_path=cache)

            self.assertEqual(len(bridge.graph), 0)
            self.assertFalse(bridge.load_graph())


if __name__ == "__main__":
    unittest.main()
