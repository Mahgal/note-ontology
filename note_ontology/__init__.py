"""note-ontology: build a tiny deterministic entity/relation graph from Markdown notes.

Entities are ``[[WikiLinks]]``; relations are lines of the form
``[[A]] -> [[B]] : relation-label`` (label optional, defaults to "related").
A bare ``[[A]]`` mention with no relation still registers A as a node.

Standard library only.
"""

from .graph import Graph, build_graph, load_graph

__all__ = ["Graph", "build_graph", "load_graph"]
__version__ = "0.1.0"
