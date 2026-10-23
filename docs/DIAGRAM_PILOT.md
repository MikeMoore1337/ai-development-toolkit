# Diagram Design: offline architecture diagram pilot (Issue #265)

[Русская инструкция](ru/DIAGRAM_PILOT.md)

This optional experiment **does not install or vendor** [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design). It independently implements a narrow idea inspired by that project's editorial approach: a self-contained HTML+SVG architecture diagram with traceable source labels, using Python's standard library only.

Mermaid remains the default low-overhead representation in Toolkit. This pilot tests whether a simple, portable static artifact makes architecture reviews easier, without changing any application's runtime.

## Run on a synthetic example

From the Toolkit repository root, with Python 3.10+:

```bash
python scripts/diagram_pilot.py docs/examples/diagram-pilot.synthetic.json --output example-diagram.html
python -m unittest tests.test_diagram_pilot -v
```

Open `example-diagram.html` locally. No account, network, third-party package or paid API is needed. The generator refuses to overwrite an existing output file.

The input JSON has `version: 1`, a `title`, nodes with `id`, `label`, `column` (0..3), `evidence`, and edges with `from`, `to`, `label`, `evidence`. The example is synthetic, **not** a deployed YFC/Hermes/Second Brain topology.

## What this does and does not prove

- Bounded left-to-right diagrams only, at most 16 nodes and 28 edges. Back edges and cycles are rejected instead of misleadingly rendered; keep Mermaid for those use cases.
- Output has no JavaScript, remote fonts or images; HTML strings are escaped and content security policy denies external resources.
- Evidence is mandatory per node/edge, but it is **supplied, not independently verified**. For actual systems cite exact source files, Issues and revisions, and avoid exposing secrets in diagrams.
- No UI overhaul, new skill registration, MANIFEST change, automatic installation, startup hook, service or production change.
- Source comparison, manual legibility assessment, and an independent visual review are **NOT_RUN**. The generator alone does not certify diagram correctness, accessibility or quality.

## Next validation stage

For Issue #265 compare 2-3 real source-grounded diagrams against existing Mermaid, check missing/incorrect nodes and links, keyboard readability, responsive behavior and contrast. Only promote to an opt-in Toolkit capability if it adds measurable value over Mermaid without unnecessary maintenance.

Source inspiration: [Diagram Design](https://github.com/cathrynlavery/diagram-design), publicly MIT licensed. Its third-party executables, skills and playbooks are **not included**.

## Mobile follow-up

The exported HTML now puts the full-size SVG inside a keyboard-focusable horizontal-scroll region so labels stay legible at 390 px, rather than scaling the full graph down to 6 px text. Relation captions are placed by the arrows; labels over 14 characters show an abbreviated visible caption with the original in SVG title and the evidence list. The strict pilot rejects multiple relations between the same pair of nodes (to avoid caption collision).

Rendering and interactive scroll behavior still require an actual browser review; static tests do not prove contrast/UX quality. Test long node labels and diagonal edges before production adoption.
