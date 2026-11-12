"""Tests for note-ontology (stdlib unittest only)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from note_ontology import build_graph  # noqa: E402
from note_ontology.__main__ import main  # noqa: E402
from note_ontology.graph import Graph, parse_text  # noqa: E402

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "notes"


def make_graph(text: str) -> Graph:
    graph = Graph()
    parse_text(text, "note.md", graph)
    return graph


class TestParsing(unittest.TestCase):
    def test_bare_link_registers_node(self):
        graph = make_graph("Just a mention of [[Python]] here.\n")
        self.assertIn("Python", graph.nodes)
        self.assertEqual(graph.nodes["Python"]["mentions"], 1)
        self.assertEqual(graph.relation_count(), 0)

    def test_relation_with_label(self):
        graph = make_graph("[[Python]] -> [[Agents]] : powers\n")
        self.assertEqual(graph.relation_count(), 1)
        edge = graph.edges[0]
        self.assertEqual((edge["source"], edge["target"], edge["label"]),
                         ("Python", "Agents", "powers"))

    def test_relation_without_label_defaults_to_related(self):
        graph = make_graph("[[A]] -> [[B]]\n")
        self.assertEqual(graph.edges[0]["label"], "related")

    def test_relation_endpoints_also_count_as_mentions(self):
        graph = make_graph("[[A]] -> [[B]] : links\n")
        self.assertEqual(graph.nodes["A"]["mentions"], 1)
        self.assertEqual(graph.nodes["B"]["mentions"], 1)

    def test_multiple_links_one_line(self):
        graph = make_graph("[[A]] and [[B]] and [[A]] again.\n")
        self.assertEqual(graph.nodes["A"]["mentions"], 2)
        self.assertEqual(graph.nodes["B"]["mentions"], 1)

    def test_non_link_lines_ignored(self):
        graph = make_graph("# Title\n\nPlain text, no links.\n")
        self.assertEqual(graph.entity_count(), 0)


class TestBuildCounts(unittest.TestCase):
    def test_example_graph_counts(self):
        graph = build_graph(EXAMPLES)
        self.assertEqual(graph.entity_count(), 5)
        self.assertEqual(graph.relation_count(), 6)

    def test_example_graph_json_is_sorted_and_deterministic(self):
        graph = build_graph(EXAMPLES)
        first = graph.to_json()
        second = build_graph(EXAMPLES).to_json()
        self.assertEqual(first, second)
        data = json.loads(first)
        names = [node["name"] for node in data["nodes"]]
        self.assertEqual(names, sorted(names))
        self.assertEqual(names, ["Agents", "Graphs", "Ontology", "Python", "Zettelkasten"])

    def test_build_writes_graph_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp) / "notes"
            notes.mkdir()
            (notes / "a.md").write_text("[[A]] -> [[B]] : links\n", encoding="utf-8")
            out = Path(tmp) / "graph.json"
            code = main(["build", str(notes), "--out", str(out)])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data["nodes"]), 2)
            self.assertEqual(len(data["edges"]), 1)


class TestQuery(unittest.TestCase):
    def test_neighbours_include_both_directions(self):
        graph = build_graph(EXAMPLES)
        neighbours = graph.neighbours("Agents")
        names = [n for n, _, _ in neighbours]
        self.assertEqual(names, ["Graphs", "Ontology", "Python", "Python"])
        self.assertIn(("Python", "powers", "incoming"), neighbours)
        self.assertIn(("Python", "run-on", "outgoing"), neighbours)

    def test_query_unknown_entity_exits_1(self):
        code = main(["query", str(EXAMPLES), "--entity", "NoSuchThing"])
        self.assertEqual(code, 1)

    def test_query_isolated_entity_exits_1(self):
        code = main(["query", str(EXAMPLES), "--entity", "Zettelkasten"])
        self.assertEqual(code, 1)


class TestPath(unittest.TestCase):
    def test_shortest_path_found(self):
        graph = build_graph(EXAMPLES)
        steps = graph.shortest_path("Python", "Ontology")
        self.assertEqual(steps, [("Graphs", "uses"), ("Ontology", "enable")])

    def test_path_to_self_is_empty(self):
        graph = build_graph(EXAMPLES)
        self.assertEqual(graph.shortest_path("Python", "Python"), [])

    def test_no_path_returns_none(self):
        graph = build_graph(EXAMPLES)
        self.assertIsNone(graph.shortest_path("Zettelkasten", "Python"))

    def test_path_cli_no_path_exits_1(self):
        code = main(["path", str(EXAMPLES), "--from", "Zettelkasten", "--to", "Python"])
        self.assertEqual(code, 1)

    def test_path_cli_found_exits_0(self):
        code = main(["path", str(EXAMPLES), "--from", "Python", "--to", "Ontology"])
        self.assertEqual(code, 0)


class TestStats(unittest.TestCase):
    def test_most_connected_and_isolated(self):
        graph = build_graph(EXAMPLES)
        self.assertEqual(graph.most_connected(), ("Agents", 4))
        self.assertEqual(graph.isolated(), ["Zettelkasten"])

    def test_stats_empty_dir_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["stats", tmp])
            self.assertEqual(code, 1)


class TestDeterministicOrdering(unittest.TestCase):
    def test_neighbours_sorted_alphabetically(self):
        graph = make_graph(
            "[[Zed]] -> [[Alpha]] : z\n"
            "[[Zed]] -> [[Mid]] : m\n"
            "[[Zed]] -> [[Beta]] : b\n"
        )
        names = [n for n, _, _ in graph.neighbours("Zed")]
        self.assertEqual(names, ["Alpha", "Beta", "Mid"])

    def test_isolated_sorted(self):
        graph = make_graph("[[Zulu]]\n[[Alpha]]\n[[Mid]]\n")
        self.assertEqual(graph.isolated(), ["Alpha", "Mid", "Zulu"])


class TestUsageErrors(unittest.TestCase):
    def test_no_command_exits_2(self):
        self.assertEqual(main([]), 2)

    def test_unknown_command_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["explode", str(EXAMPLES)])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_notes_dir_exits_2(self):
        self.assertEqual(main(["stats", "/nonexistent/dir"]), 2)


if __name__ == "__main__":
    unittest.main()
