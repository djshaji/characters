# Characters

Chat with Shakespearean dramatic characters without anachronistic knowledge — a research
project in Computational Literary Studies (CLS) modeling epistemic state, verse/prose
register, and Early Modern pronoun norms (*thou/thee* vs *you/ye*).

Full design and rationale: [docs/Plan.md](docs/Plan.md).
Module layout: [docs/skel.md](docs/skel.md).
Agent/contributor conventions: [AGENTS.md](AGENTS.md).
Copilot guidance: [.github/copilot-instructions.md](.github/copilot-instructions.md).

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

Build or rebuild the SQLite corpus from the bundled DraCor TEI files:

```bash
python -m src.data.build_corpus
```

Populate or rebuild the stage-presence witness table (requires the corpus database):

```bash
python -m src.kg.stage_tracker
```

Launch the Streamlit chat UI after building the corpus and witness table:

```bash
streamlit run src/ui/app.py
```

The prompt engine defaults to a local Ollama backend. It requires a running Ollama server, the
configured model, and the `ollama` Python client, which is not in `requirements.txt`:

```bash
pip install ollama
python -m src.engine.prompt_engine
```

Gemini is also supported. Install dependencies from `requirements.txt`, set
`GOOGLE_GENAI_API_KEY`, and choose the Gemini backend in the UI.

Run the small inference-based anachronism and scansion benchmark:

```bash
python -m src.eval.run_benchmark
```

The benchmark calls the configured LLM backend and is not a unit-test suite or comprehensive
evaluation. For the paper build, run this from the repository root:

```bash
make -C paper
```

The paper build uses `pdflatex` and `bibtex`. There is currently no automated test suite, so there
is no single-test command; no linter, formatter, or type checker is configured either.

## Implemented data flow

The active path is:

`data/raw_tei/shakespeare/tei/` → `src/data/build_corpus.py` → SQLite at
`data/processed/shakespeare.db` → `src/kg/stage_tracker.py` (the `turn_witnesses` table) →
`src/engine/prompt_engine.py` → Ollama or Gemini.

The Streamlit UI in `src/ui/app.py` uses the prompt engine. `src/engine/scansion.py` estimates
syllable stress and verse regularity. The corpus builder stores dialogue meter as `verse`, `prose`,
or `mixed`; speech-type classification (`dialogue`, `soliloquy`, `aside`) is not currently persisted
in that schema.

## Current limitations

- The root `app.py`, `src/data/parse_shakespeare.py`, `src/kg/stage_presence.py`,
	`src/kg/epistemic_graph.py`, and `src/engine/shakespeare_rag.py` are stubs or incomplete.
- Evaluation metric modules under `src/eval/` are incomplete. `src/eval/run_benchmark.py` is a
	small, inference-based benchmark only and does not validate the full research claims.
- The first scansion import may download the NLTK CMU pronunciation dictionary if it is not already
	available locally.
- Chronological bounds are a correctness requirement: every context or knowledge retrieval must be
	limited to the selected act/scene or line position before prompt construction. Characters must
	never receive later plot information or dialogue.
- Speaker IDs should be canonical across plays; raw TEI speaker labels can vary by play or edition.
- Stage-presence witness logic currently belongs to `src/kg/stage_tracker.py`. Asides and
	soliloquies should not become witnessed knowledge for other characters.
- Scansion must account for Early Modern elisions such as *e'en*, *ne'er*, *'tis*, and *o'er*,
	which standard CMUdict lookups may not recognize.

See [docs/Plan.md](docs/Plan.md) for the research design and [AGENTS.md](AGENTS.md) for development
conventions and known implementation boundaries.
