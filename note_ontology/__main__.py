"""Command line interface for note-ontology.

Usage:
    python3 -m note_ontology build <notes-dir> [--out graph.json]
    python3 -m note_ontology query <notes-dir> --entity X
    python3 -m note_ontology path <notes-dir> --from A --to B
    python3 -m note_ontology stats <notes-dir>

Exit codes: 0 success, 1 no path / nothing found, 2 usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .graph import build_graph

USAGE = (
    "usage: python3 -m note_ontology <build|query|path|stats> <notes-dir> [options]\n"
    "  build <notes-dir> [--out FILE]   scan notes, print counts, write graph.json\n"
    "  query <notes-dir> --entity X     print X's neighbours with relation labels\n"
    "  path <notes-dir> --from A --to B print the shortest A -> ... -> B chain\n"
    "  stats <notes-dir>                print counts, most-connected and isolated entities"
)


def _fail(message: str, code: int) -> int:
    print(message, file=sys.stderr)
    return code


def _notes_dir(path: str) -> Path | None:
    notes = Path(path)
    if not notes.is_dir():
        print(f"error: notes directory not found: {path}", file=sys.stderr)
        return None
    return notes


def cmd_build(args: argparse.Namespace) -> int:
    notes = _notes_dir(args.notes_dir)
    if notes is None:
        return 2
    graph = build_graph(notes)
    out = Path(args.out) if args.out else notes / "graph.json"
    out.write_text(graph.to_json(), encoding="utf-8")
    print(f"entities: {graph.entity_count()}, relations: {graph.relation_count()}")
    print(f"wrote {out}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    notes = _notes_dir(args.notes_dir)
    if notes is None:
        return 2
    graph = build_graph(notes)
    if args.entity not in graph.nodes:
        return _fail(f"entity not found: {args.entity}", 1)
    neighbours = graph.neighbours(args.entity)
    if not neighbours:
        return _fail(f"no neighbours for entity: {args.entity}", 1)
    for neighbour, label, direction in neighbours:
        print(f"{neighbour} : {label} ({direction})")
    return 0


def cmd_path(args: argparse.Namespace) -> int:
    notes = _notes_dir(args.notes_dir)
    if notes is None:
        return 2
    graph = build_graph(notes)
    steps = graph.shortest_path(args.from_entity, args.to_entity)
    if steps is None:
        print("no path")
        return 1
    chain = args.from_entity
    for node, label in steps:
        chain += f" -> {label} -> {node}"
    print(chain)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    notes = _notes_dir(args.notes_dir)
    if notes is None:
        return 2
    graph = build_graph(notes)
    if graph.entity_count() == 0:
        return _fail("no entities found", 1)
    most = graph.most_connected()
    isolated = graph.isolated()
    print(f"entities: {graph.entity_count()}")
    print(f"relations: {graph.relation_count()}")
    if most is not None:
        print(f"most-connected: {most[0]} ({most[1]} connections)")
    print("isolated: " + (", ".join(isolated) if isolated else "(none)"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="note_ontology",
        description="Build a tiny entity/relation graph from a folder of Markdown notes.",
    )
    sub = parser.add_subparsers(dest="command")

    p_build = sub.add_parser("build", help="scan notes and write graph.json")
    p_build.add_argument("notes_dir")
    p_build.add_argument("--out", default=None, help="output JSON file (default: <notes-dir>/graph.json)")
    p_build.set_defaults(func=cmd_build)

    p_query = sub.add_parser("query", help="list an entity's neighbours")
    p_query.add_argument("notes_dir")
    p_query.add_argument("--entity", required=True)
    p_query.set_defaults(func=cmd_query)

    p_path = sub.add_parser("path", help="shortest path between two entities")
    p_path.add_argument("notes_dir")
    p_path.add_argument("--from", dest="from_entity", required=True)
    p_path.add_argument("--to", dest="to_entity", required=True)
    p_path.set_defaults(func=cmd_path)

    p_stats = sub.add_parser("stats", help="graph summary statistics")
    p_stats.add_argument("notes_dir")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        print(USAGE, file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
