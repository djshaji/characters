characters/
├── data/
│   ├── raw_tei/shakespeare/  # 37 TEI-XML plays from DraCor
│   ├── shakespeare.db        # SQLite schema (acts, scenes, turns, meter)
│   └── chroma_index/         # Vector embeddings of all speech turns
├── src/
│   ├── data/
│   │   └── parse_shakespeare.py  # Extracts speaker tags, asides, meter (<l> vs <ab>)
│   ├── kg/
│   │   ├── stage_presence.py     # Tracks who is on stage per line (Enter/Exit)
│   │   └── epistemic_graph.py    # Facts tagged with witness lists
│   ├── engine/
│   │   ├── shakespeare_rag.py    # Chronologically bounded RAG (scene-level)
│   │   └── scansion.py           # CMUdict modified for Shakespearean elisions
│   └── eval/
│       ├── eval_scansion.py      # Iambic pentameter adherence
│       ├── eval_sociolect.py     # Thou vs. You evaluation
│       └── eval_anachronism.py   # Spoilers & dramatic irony leaks
└── app.py                        # Streamlit app for chatting with Shakespearean personas