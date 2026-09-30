# Characters — Agent Instructions

Research project in Computational Literary Studies (CLS): an epistemic/stylometric dialogue
system that lets users chat with Shakespearean characters without anachronistic plot knowledge,
while respecting verse/prose register and Early Modern pronoun norms (*thou/thee* vs *you/ye*).
Full design and rationale: [docs/Plan.md](docs/Plan.md). Planned module layout: [docs/skel.md](docs/skel.md).

## Current state

The repository is partially implemented. Corpus ingestion, stage tracking, verse scansion, a
Streamlit UI, and a prompt engine exist; the full research evaluation suite is not complete. The
working path is:

`data/raw_tei/shakespeare/tei/` -> `src/data/build_corpus.py` -> SQLite ->
`src/kg/stage_tracker.py` -> chronologically bounded context in
`src/engine/prompt_engine.py`.

Implemented enough to exercise locally:

- `src/data/build_corpus.py`: parses the TEI corpus into `data/processed/shakespeare.db`.
- `src/kg/stage_tracker.py`: tracks stage presence and populates witness rows.
- `src/engine/scansion.py`: estimates line-level stress and verse regularity.
- `src/engine/prompt_engine.py`: builds character prompts and calls Ollama or Gemini.
- `src/ui/app.py`: Streamlit chat UI backed by the prompt engine.
- `src/eval/run_benchmark.py`: small, inference-based anachronism and scansion benchmark; this is
  not a comprehensive evaluation suite.

Stubs or incomplete surfaces include the root `app.py`, `src/data/parse_shakespeare.py`,
`src/kg/stage_presence.py`, `src/kg/epistemic_graph.py`, `src/engine/shakespeare_rag.py`, and the
individual metric modules under `src/eval/`. Do not describe these as complete or silently duplicate
their intended responsibilities; update the owning module or document a deliberate change in
[docs/Plan.md](docs/Plan.md).

## Environment

- Python venv already created at `.venv/`. Activate with `source .venv/bin/activate` before
  installing packages or running scripts.
- Install deps with `pip install -r requirements.txt`.
- Build the corpus with `python -m src.data.build_corpus`.
- Build/update stage-presence witnesses with `python -m src.kg.stage_tracker`.
- Launch the UI with `streamlit run src/ui/app.py` after building the corpus and witness table.
- Exercise the prompt engine with `python -m src.engine.prompt_engine`; the default Ollama path
  requires a local Ollama server, its configured model, and the Python `ollama` client (not listed
  in `requirements.txt`). Gemini requires `GOOGLE_GENAI_API_KEY`.
- Run the small inference benchmark with `python -m src.eval.run_benchmark`; it calls the selected
  LLM backend and is not a substitute for a unit test suite.
- There is currently no test suite, formatter, linter, or type-check configuration. If adding one,
  document its command here and keep it focused on the changed behavior.

## Architecture (see docs/Plan.md §3 for the full pipeline diagram)

Data flow in the current implementation: DraCor TEI-XML -> `build_corpus.py` -> SQLite ->
`stage_tracker.py` -> prompt context -> Ollama or Gemini -> scansion. The Streamlit UI uses this
prompt engine; broader stylometry, sociolect, and anachronism evaluation remains planned or partial.

**A character must never access facts or dialogue from beyond the current dramatic timeline.**
Every retrieval or knowledge-graph query must carry an explicit chronological bound (`act`, `scene`,
or `global_line_index`) and apply it before prompt construction. This is a correctness requirement,
not an optimization.

## Conventions

- Speaker identity: normalize to canonical speaker IDs across all 37 plays (don't key on raw
  `<speaker>` text, which varies by play/edition).
- Dialogue rows distinguish `meter_type` (`verse`/`prose`/`mixed`) and `speech_type`
  (`dialogue`/`soliloquy`/`aside`) — asides and soliloquies are excluded from other characters'
  witnessed knowledge.
- Stage tracking currently owns the implemented witness logic; inspect it before changing the
  planned graph modules.
- Scansion/prosody code must handle Shakespearean elisions (*e'en*, *ne'er*, *'tis*, *o'er*) —
  standard CMUdict lookups will fail on these without preprocessing.
- Treat evaluation metrics as correctness checks for leakage, meter, stylometry, and pronoun use.
  The current benchmark is small and inference-based; do not present it as validating the full
  research claims.
