# Characters — Agent Instructions

Research project in Computational Literary Studies (CLS): an epistemic/stylometric dialogue
system that lets users chat with Shakespearean characters without anachronistic plot knowledge,
while respecting verse/prose register and Early Modern pronoun norms (*thou/thee* vs *you/ye*).
Full design and rationale: [docs/Plan.md](docs/Plan.md). Planned module layout: [docs/skel.md](docs/skel.md).

## Status

This repo is pre-implementation: only `docs/` and `requirements.txt` exist so far. `src/`, `data/`,
and `app.py` in [docs/skel.md](docs/skel.md) are the target layout, not yet created — when adding
code, follow that layout rather than improvising a new structure.

## Environment

- Python venv already created at `.venv/`. Activate with `source .venv/bin/activate` before
  installing packages or running scripts.
- Install deps with `pip install -r requirements.txt`.
- No test suite or lint config exists yet; if you add one, wire it up here.

## Architecture (see docs/Plan.md §3 for the full pipeline diagram)

Data flow: DraCor TEI-XML → `parse_shakespeare.py` → SQLite (`data/shakespeare.db`) +
stage-presence bipartite graph → chronologically-bounded retrieval (facts/turns filtered to
`line_index <= current`) → prompt engine (verse/prose + T-V pronoun selection) → LLM (Gemini via
`google-genai`) → evaluation suite (scansion, stylometry, sociolect, anachronism leakage).

Key invariant: **a character must never access facts or dialogue from scenes beyond the current
timeline position.** Any retrieval or knowledge-graph query needs an explicit chronological bound
(`act`, `scene`, or `global_line_index`) — this is the core research mechanism, not an optimization.

## Conventions

- Speaker identity: normalize to canonical speaker IDs across all 37 plays (don't key on raw
  `<speaker>` text, which varies by play/edition).
- Dialogue rows distinguish `meter_type` (`verse`/`prose`/`mixed`) and `speech_type`
  (`dialogue`/`soliloquy`/`aside`) — asides and soliloquies are excluded from other characters'
  witnessed knowledge.
- Scansion/prosody code must handle Shakespearean elisions (*e'en*, *ne'er*, *'tis*, *o'er*) —
  standard CMUdict lookups will fail on these without preprocessing.
- Evaluation scripts under `src/eval/` are the acceptance criteria for the research paper's claims
  (leakage rate, meter regularity, Burrows' Delta, pronoun precision) — treat their metrics as
  correctness checks, not just reporting.
