"""Core graph model: parse Markdown notes into entities and relations."""

from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]\n]+)\]\]")
# [[A]] -> [[B]] : label   (label optional, defaults to "related")
RELATION_RE = re.compile(
    r"\[\[([^\]\n]+)\]\]\s*->\s*\[\[([^\]\n]+)\]\]\s*(?::\s*(.+?)\s*)?$"
)

DEFAULT_LABEL = "related"


class Graph:
    """Deterministic entity/relation graph built from a folder of Markdown notes."""

    def __init__(self) -> None:
        # name -> {"mentions": int, "files": set[str]}
        self.nodes: dict[str, dict] = {}
        # {"source": str, "target": str, "label": str, "file": str}
        self.edges: list[dict] = []

    def add_mention(self, name: str, filename: str) -> None:
        name = name.strip()
        if not name:
            return
        node = self.nodes.setdefault(name, {"mentions": 0, "files": set()})
        node["mentions"] += 1
        node["files"].add(filename)

    def add_edge(self, source: str, target: str, label: str, filename: str) -> None:
        source, target = source.strip(), target.strip()
        label = label.strip() if label else DEFAULT_LABEL
        if not source or not target:
            return
        self.edges.append(
            {"source": source, "target": target, "label": label, "file": filename}
        )

    # -- derived views -------------------------------------------------

    def entity_count(self) -> int:
        return len(self.nodes)

    def relation_count(self) -> int:
        return len(self.edges)

    def neighbours(self, name: str) -> list[tuple[str, str, str]]:
        """(neighbour, label, direction) sorted by neighbour, then label.

        Direction is "outgoing" when ``name -> neighbour`` and "incoming"
        when ``neighbour -> name``.
        """
        out: list[tuple[str, str, str]] = []
        for edge in self.edges:
            if edge["source"] == name:
                out.append((edge["target"], edge["label"], "outgoing"))
            elif edge["target"] == name:
                out.append((edge["source"], edge["label"], "incoming"))
        out.sort()
        return out

    def shortest_path(self, start: str, goal: str) -> list[tuple[str, str]] | None:
        """BFS over directed edges. Returns [(node, label)] steps from start.

        The returned list holds one (node, label) pair per hop, where label is
        the relation used to reach that node; the start node itself is not in
        the list. Returns None when no path exists.
        """
        if start not in self.nodes or goal not in self.nodes:
            return None
        if start == goal:
            return []
        adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for edge in self.edges:
            adjacency[edge["source"]].append((edge["target"], edge["label"]))
        for targets in adjacency.values():
            targets.sort()
        queue: deque[str] = deque([start])
        came_from: dict[str, tuple[str, str] | None] = {start: None}
        while queue:
            current = queue.popleft()
            for neighbour, label in adjacency.get(current, []):
                if neighbour in came_from:
                    continue
                came_from[neighbour] = (current, label)
                if neighbour == goal:
                    steps: list[tuple[str, str]] = []
                    node = goal
                    while came_from[node] is not None:
                        prev, step_label = came_from[node]
                        steps.append((node, step_label))
                        node = prev
                    steps.reverse()
                    return steps
                queue.append(neighbour)
        return None

    def most_connected(self) -> tuple[str, int] | None:
        """(entity, incident-edge count); ties broken alphabetically."""
        if not self.nodes:
            return None
        degree: dict[str, int] = {name: 0 for name in self.nodes}
        for edge in self.edges:
            degree[edge["source"]] += 1
            degree[edge["target"]] += 1
        best = max(sorted(degree), key=lambda name: degree[name])
        return best, degree[best]

    def isolated(self) -> list[str]:
        """Entities mentioned but in no relation, sorted alphabetically."""
        involved = set()
        for edge in self.edges:
            involved.add(edge["source"])
            involved.add(edge["target"])
        return sorted(name for name in self.nodes if name not in involved)

    # -- serialisation ---------------------------------------------------

    def to_dict(self) -> dict:
        nodes = [
            {
                "name": name,
                "mentions": data["mentions"],
                "files": sorted(data["files"]),
            }
            for name, data in sorted(self.nodes.items())
        ]
        edges = sorted(
            self.edges,
            key=lambda e: (e["source"], e["target"], e["label"], e["file"]),
        )
        return {"nodes": nodes, "edges": edges}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False) + "\n"


def parse_text(text: str, filename: str, graph: Graph) -> None:
    """Parse one note's text into the graph."""
    for line in text.splitlines():
        stripped = line.strip()
        relation = RELATION_RE.search(stripped)
        if relation:
            source, target, label = relation.groups()
            graph.add_mention(source, filename)
            graph.add_mention(target, filename)
            graph.add_edge(source, target, label or DEFAULT_LABEL, filename)
            continue
        for match in LINK_RE.finditer(line):
            graph.add_mention(match.group(1), filename)


def build_graph(notes_dir: str | Path) -> Graph:
    """Scan all ``*.md`` files under ``notes_dir`` (sorted) into a Graph."""
    notes_path = Path(notes_dir)
    graph = Graph()
    for md_file in sorted(notes_path.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        parse_text(text, md_file.name, graph)
    return graph


def load_graph(notes_dir: str | Path) -> Graph:
    """Alias for build_graph: every command rebuilds from the notes folder."""
    return build_graph(notes_dir)
