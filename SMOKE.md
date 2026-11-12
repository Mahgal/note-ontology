# SMOKE.md — note-ontology

Recorded 2026-11-12 (Asia/Shanghai). All commands run from
`~/workspace/github-factory/2026-11-12/note-ontology` with Python 3.12.3.
No push to GitHub (staged only, per task).

## Tests

```
$ python3 -m unittest discover -s tests -v
Ran 24 tests in 0.021s
OK
```

- Tests passed: **24 / 24**
- Test exit code: **0**

## Demos (examples/notes — 5 .md files)

| Command | Exit code |
| --- | --- |
| `python3 -m note_ontology build examples/notes` | 0 |
| `python3 -m note_ontology query examples/notes --entity Agents` | 0 |
| `python3 -m note_ontology path examples/notes --from Python --to Ontology` | 0 |
| `python3 -m note_ontology path examples/notes --from Zettelkasten --to Python` | 1 (expected: `no path`) |
| `python3 -m note_ontology stats examples/notes` | 0 |

## Example graph counts

- **entities: 5** (Agents, Graphs, Ontology, Python, Zettelkasten)
- **relations: 6** (powers, uses, build, run-on, enable, describes)
- most-connected: Agents (4 connections)
- isolated: Zettelkasten
- `build` wrote `examples/notes/graph.json` (verified: 5 nodes, 6 edges)

## Standard pieces

- `note_ontology/__init__.py`, `note_ontology/graph.py`, `note_ontology/__main__.py` — implementation (stdlib only)
- `tests/test_note_ontology.py` — 24 unittest tests
- `examples/notes/` — 5 example notes + generated `graph.json`
- `README.md`, `LICENSE` (MIT, 2026 Mahgal), `.gitignore`, `topics.txt` (8 topics)
