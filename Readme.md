# Characters

Chat with Shakespearean dramatic characters without anachronistic knowledge — a research
project in Computational Literary Studies (CLS) modeling epistemic state, verse/prose
register, and Early Modern pronoun norms (*thou/thee* vs *you/ye*).

Full design and rationale: [docs/Plan.md](docs/Plan.md).
Module layout: [docs/skel.md](docs/skel.md).
Agent/contributor conventions: [AGENTS.md](AGENTS.md).

## Status

Partially implemented. The corpus ingestion, SQLite schema, stage-presence tracking, and prompt
engine are available for local experimentation. The Streamlit UI, standalone RAG/scansion modules,
and evaluation suite are still incomplete.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick start

Build or rebuild the SQLite corpus from the bundled TEI files:

```bash
python -m src.data.build_corpus
```

Populate the stage-presence witness table:

```bash
python -m src.kg.stage_tracker
```

Exercise the prompt engine:

```bash
python -m src.engine.prompt_engine
```

The prompt engine defaults to a local Ollama backend and requires a running Ollama server with its
configured model. Gemini is also supported when `GOOGLE_GENAI_API_KEY` is set.

## Layout

```
data/raw_tei/shakespeare/tei/  # 37 TEI-XML plays from DraCor
data/processed/shakespeare.db  # Generated SQLite corpus
data/chroma_index/              # Reserved for planned vector index
src/data/build_corpus.py       # TEI-XML parsing and SQLite ingestion
src/kg/stage_tracker.py        # Stage presence and witnessed-turn tracking
src/engine/prompt_engine.py    # Chronologically bounded persona prompts
src/engine/shakespeare_rag.py  # Planned standalone RAG module
src/engine/scansion.py         # Planned verse-scansion module
src/eval/                      # Planned evaluation modules
app.py                         # Planned Streamlit chat UI
```

## Current limitations

- `app.py`, the standalone RAG and scansion modules, and the evaluation modules are stubs or
	incomplete; the command-line prompt engine is the current executable surface.
- There is no automated test suite, formatter, linter, or type-check configuration yet.
- Chronological bounds are a correctness requirement: character context must never include facts or
	dialogue from beyond the selected act and scene.

See [docs/Plan.md](docs/Plan.md) for the research design and [AGENTS.md](AGENTS.md) for development
conventions and known implementation boundaries.
