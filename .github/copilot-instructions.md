# Characters repository guidance

For the full research design, module map, implementation status, and detailed conventions, see
[AGENTS.md](../AGENTS.md), [docs/Plan.md](../docs/Plan.md), and [docs/skel.md](../docs/skel.md).
The codebase is partially implemented; distinguish working modules from planned or stubbed ones.

## Build and run

From the repository root, activate the existing environment with `source .venv/bin/activate`;
install dependencies with `pip install -r requirements.txt`.

- Build or rebuild the SQLite corpus: `python -m src.data.build_corpus`
- Build stage-presence witnesses: `python -m src.kg.stage_tracker`
- Launch the chat UI after both database steps: `streamlit run src/ui/app.py`
- Run the prompt engine: `python -m src.engine.prompt_engine`. The default Ollama backend needs
  a local server, its configured model, and the separately installed `ollama` client. Gemini needs
  `GOOGLE_GENAI_API_KEY`.
- Run the inference-based benchmark: `python -m src.eval.run_benchmark`. It calls an LLM; it is
  not a unit-test suite or a comprehensive evaluation.
- Build the paper from its directory: `make -C paper` (runs `pdflatex` and `bibtex`).

There is currently no automated test suite, single-test command, linter, formatter, or type-check
configuration.

## Architecture

The implemented interaction path is:

`data/raw_tei/shakespeare/tei/` → `src/data/build_corpus.py` → `data/processed/shakespeare.db`
→ `src/kg/stage_tracker.py` (`turn_witnesses`) → `src/engine/prompt_engine.py` → Ollama or
Gemini. The prompt engine also uses `src/engine/scansion.py` to estimate verse regularity;
`src/ui/app.py` supplies the Streamlit interface.

The corpus builder extracts TEI play, scene, dialogue-turn, and stage-direction data into SQLite.
The stage tracker processes turns and entrances/exits to attribute witnesses. The prompt engine
uses prior speech and witnessed context to condition responses; scansion estimates syllable stress
and pentameter adherence. The standalone RAG module, root `app.py`, and broader evaluation metrics
remain incomplete—do not assume their planned responsibilities are implemented elsewhere.

## Correctness conventions

- Preserve the dramatic knowledge boundary: every retrieval or graph query must have an explicit
  act/scene or line-index limit and apply it before prompt construction. Never expose later events
  or dialogue to a character.
- Keep speaker identifiers canonical across plays; raw TEI speaker labels vary by edition and play.
- Preserve verse/prose/mixed distinctions. Asides and soliloquies must not become witnessed
  knowledge for other characters. Check the live schema before relying on speech-type fields:
  `src/data/build_corpus.py` currently stores `meter_type`, but does not persist `speech_type`.
- `src/kg/stage_tracker.py` owns the current witness logic. Inspect and extend it rather than
  duplicating witness behavior in the planned graph modules.
- Scansion must account for Early Modern elisions such as *e'en*, *ne'er*, *'tis*, and *o'er*;
  CMUdict does not reliably contain these forms.
- Treat benchmark and metric outputs as focused correctness signals, not validation of the full
  research claims.
