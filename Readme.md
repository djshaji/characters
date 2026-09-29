# Characters

Chat with Shakespearean dramatic characters without anachronistic knowledge — a research
project in Computational Literary Studies (CLS) modeling epistemic state, verse/prose
register, and Early Modern pronoun norms (*thou/thee* vs *you/ye*).

Full design and rationale: [docs/Plan.md](docs/Plan.md).
Module layout: [docs/skel.md](docs/skel.md).
Agent/contributor conventions: [AGENTS.md](AGENTS.md).

## Status

Pre-implementation. The `data/`, `src/`, and `app.py` skeleton exists but the pipeline
(TEI-XML parsing, stage-presence graph, chronological RAG, evaluation suite) is not yet built.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Layout

```
data/raw_tei/shakespeare/  # 37 TEI-XML plays from DraCor
data/shakespeare.db        # SQLite: acts, scenes, turns, meter (generated)
data/chroma_index/         # Vector embeddings of speech turns (generated)
src/data/                  # TEI-XML parsing
src/kg/                    # Stage-presence & epistemic (witness) graph
src/engine/                # Chronologically bounded RAG, verse scansion
src/eval/                  # Scansion, sociolect, anachronism-leakage evaluation
app.py                     # Streamlit chat UI
```
