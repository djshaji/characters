# Characters

Chat with Shakespearean dramatic characters without anachronistic knowledge — a research
project in Computational Literary Studies (CLS) modeling epistemic state, verse/prose
register, and Early Modern pronoun norms (*thou/thee* vs *you/ye*).

Full design and rationale: [docs/Plan.md](docs/Plan.md).
Module layout: [docs/skel.md](docs/skel.md).
Agent/contributor conventions: [AGENTS.md](AGENTS.md).

## Status

Partially implemented. Corpus ingestion, SQLite storage, stage-presence tracking, verse scansion,
the prompt engine, and a Streamlit chat UI are available for local experimentation. The standalone
RAG module and comprehensive evaluation suite are still incomplete.

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

Launch the Streamlit chat UI after building the corpus and stage-presence table:

```bash
streamlit run src/ui/app.py
```

The prompt engine defaults to a local Ollama backend. This requires a running Ollama server, the
configured model, and the Python `ollama` client, which is not included in `requirements.txt`
(`pip install ollama`). Gemini is also supported when `GOOGLE_GENAI_API_KEY` is set.

Run the small inference-based anachronism and scansion benchmark with:

```bash
python -m src.eval.run_benchmark
```

It calls the configured LLM backend; it is not a unit test suite or a comprehensive evaluation.

## Layout

```
data/raw_tei/shakespeare/tei/  # 37 TEI-XML plays from DraCor
data/processed/shakespeare.db  # Generated SQLite corpus
data/chroma_index/              # Reserved for planned vector index
src/data/build_corpus.py       # TEI-XML parsing and SQLite ingestion
src/kg/stage_tracker.py        # Stage presence and witnessed-turn tracking
src/engine/prompt_engine.py    # Chronologically bounded persona prompts
src/engine/shakespeare_rag.py  # Planned standalone RAG module
src/engine/scansion.py         # Verse-scansion estimates
src/ui/app.py                 # Streamlit chat UI
src/eval/run_benchmark.py      # Small LLM-backed benchmark
src/eval/                      # Evaluation metric modules (incomplete)
app.py                         # Root entry point stub
```

## Current limitations

- The root `app.py` and standalone RAG module are stubs; the Streamlit UI lives at `src/ui/app.py`.
- The evaluation metric modules are incomplete. `src/eval/run_benchmark.py` provides a small,
	inference-based benchmark only.
- The first scansion import may download the NLTK CMU pronunciation dictionary if it is not already
	available locally.
- There is no automated test suite, formatter, linter, or type-check configuration yet.
- Chronological bounds are a correctness requirement: character context must never include facts or
	dialogue from beyond the selected act and scene.

See [docs/Plan.md](docs/Plan.md) for the research design and [AGENTS.md](AGENTS.md) for development
conventions and known implementation boundaries.
