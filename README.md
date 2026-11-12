# note-ontology

Turn a folder of Markdown notes into a tiny, deterministic entity/relation graph — no server, no dependencies, no network.

## The problem

Your notes already contain a knowledge graph (`[[WikiLinks]]` and `A -> B` relations), but it is invisible until you can query it. This CLI makes it visible: build the graph, ask who connects to whom, and find the shortest path between two ideas.

## Input format

Notes are `.md` files in one folder:

- **Entities** are `[[WikiLinks]]`. A bare `[[A]]` mention registers `A` as a node.
- **Relations** are lines of the form `[[A]] -> [[B]] : relation-label`. The label is optional and defaults to `related`.

Example (`examples/notes/python.md`):

```markdown
[[Python]] -> [[Agents]] : powers
[[Python]] -> [[Graphs]] : uses
```

## Quick start

Requires Python 3.9+ and nothing else (standard library only).

```bash
python3 -m note_ontology build examples/notes
python3 -m note_ontology query examples/notes --entity Agents
python3 -m note_ontology path examples/notes --from Python --to Ontology
python3 -m note_ontology stats examples/notes
```

### Commands

| Command | What it does |
| --- | --- |
| `build <notes-dir> [--out FILE]` | Scan all `.md` files, print `entities: N, relations: M`, write `graph.json` (nodes with mention counts + source files, edges with label + source file). Default output is `<notes-dir>/graph.json`. |
| `query <notes-dir> --entity X` | Print X's neighbours with relation labels, one per line, sorted alphabetically. |
| `path <notes-dir> --from A --to B` | BFS shortest path, printed as an `A -> rel -> B` chain, or `no path`. |
| `stats <notes-dir>` | Entity count, relation count, most-connected entity, isolated entities (mentioned but in no relation). |

Exit codes: `0` success, `1` no path / nothing found, `2` usage error. All lists are sorted alphabetically, so output is deterministic.

## Example output

Real output from the bundled example notes (`examples/notes/`, 5 files: `python.md`, `agents.md`, `graphs.md`, `ontology.md`, `misc.md`):

```console
$ python3 -m note_ontology build examples/notes
entities: 5, relations: 6
wrote examples/notes/graph.json

$ python3 -m note_ontology query examples/notes --entity Agents
Graphs : build (outgoing)
Ontology : describes (incoming)
Python : powers (incoming)
Python : run-on (outgoing)

$ python3 -m note_ontology path examples/notes --from Python --to Ontology
Python -> uses -> Graphs -> enable -> Ontology

$ python3 -m note_ontology path examples/notes --from Zettelkasten --to Python
no path

$ python3 -m note_ontology stats examples/notes
entities: 5
relations: 6
most-connected: Agents (4 connections)
isolated: Zettelkasten
```

`build` also writes `examples/notes/graph.json`, e.g.:

```json
{
  "nodes": [
    {"name": "Agents", "mentions": 5, "files": ["agents.md", "ontology.md", "python.md"]},
    {"name": "Graphs", "mentions": 5, "files": ["agents.md", "graphs.md", "ontology.md", "python.md"]},
    {"name": "Ontology", "mentions": 2, "files": ["graphs.md", "ontology.md"]},
    {"name": "Python", "mentions": 6, "files": ["agents.md", "graphs.md", "python.md"]},
    {"name": "Zettelkasten", "mentions": 1, "files": ["misc.md"]}
  ],
  "edges": [
    {"source": "Agents", "target": "Graphs", "label": "build", "file": "agents.md"},
    {"source": "Agents", "target": "Python", "label": "run-on", "file": "agents.md"},
    {"source": "Graphs", "target": "Ontology", "label": "enable", "file": "graphs.md"},
    {"source": "Ontology", "target": "Agents", "label": "describes", "file": "ontology.md"},
    {"source": "Python", "target": "Agents", "label": "powers", "file": "python.md"},
    {"source": "Python", "target": "Graphs", "label": "uses", "file": "python.md"}
  ]
}
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

24 tests, covering link/relation parsing, build counts, neighbour queries, BFS path found and not-found, stats (most-connected and isolated entities), and deterministic ordering.

## License

MIT — see [LICENSE](LICENSE).
