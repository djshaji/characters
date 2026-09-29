# "Characters": Shakespeare's Complete Dramatic Canon (1590–1613)

## Epistemic State Modeling, Verse–Prose Alternation, and Sociolect Alignment in Computational Literary Studies

**Project Title:** Characters: An Epistemic and Stylometric Dialogue System for the Shakespearean Canon  
**Working Paper Title:** *Dramatis Personae in Silico: Modeling Dramatic Irony, Verse–Prose Alternation, and Sociolect Alignment in Shakespeare’s Complete Dramatic Canon (1590–1613)*  
**Primary Discipline:** Computational Literary Studies (CLS), Digital Humanities (DH), Natural Language Processing (NLP)  
**Corpus Scope:** The complete 37-play canonical corpus of William Shakespeare (Tragedies, Comedies, Histories, and Late Romances)

---

## 1\. Research Objectives & Scholarly Significance

Standard LLM roleplay systems suffer from three primary failures when applied to classic literature:

1. **Omniscient Anachronism:** The agent knows future plot events (e.g., Hamlet knowing Claudius' guilt before the Ghost's testimony, or Othello knowing Iago's duplicity).  
2. **Metrical Collapse:** Inability to dynamically navigate the structural boundary between blank verse (unrhymed iambic pentameter) and comic/colloquial prose.  
3. **Sociolinguistic Inaccuracy:** Flattening historical pronominal address registers (*thou/thee* vs. *you/ye*).

By bounding this study to the **complete 37-play Shakespearean dramatic canon (1590–1613)**, this project establishes a formal framework in Computational Literary Studies:

* **Corpus Scale:** \~37 plays, \~110,000 lines of verse and prose, \~900 named characters.  
* **Core Hypothesis:** Coupling stage-presence bipartite graphs with chronologically filtered retrieval allows an LLM to accurately respect dramatic irony, reproduce Shakespearean metrical patterns, and adhere to Early Modern sociolinguistic norms.

---

## 2\. Target Corpus & Primary Representative Testbed

While the entire 37-play canon is ingested and indexed, the evaluation benchmark focuses on four canonical anchor plays spanning distinct genres and periods:

| Play | Period & Genre | Benchmark Characters | Key Research Focus |
| :---- | :---- | :---- | :---- |
| ***Hamlet*** (c. 1600–1601) | High Tragedy | Hamlet, Claudius, Horatio, Ophelia | Epistemic doubt, ghost testimony, feigned madness, soliloquies vs. dialogue. |
| ***Henry IV, Part 1*** (c. 1597\) | History | Prince Hal, Falstaff, Hotspur, King Henry IV | The ultimate verse–prose sociolect boundary (Eastcheap tavern prose vs. Westminster court blank verse). |
| ***Twelfth Night*** (c. 1601\) | Romantic Comedy | Viola (Cesario), Olivia, Orsino, Malvolio | Dramatic irony through disguise; pronominal shifts (*thou* vs. *you*) based on assumed gender/status. |
| ***Othello*** (c. 1603–1604) | Jacobean Tragedy | Othello, Iago, Desdemona, Emilia | Asymmetric information manipulation; private villain asides vs. public deference. |

---

## 3\. System Architecture & Technical Specifications

                       \[Shakespeare DraCor TEI-XML (37 Plays)\]

                                         │

                             \[parse\_shakespeare\_tei.py\]

                                         │

                     ┌───────────────────┴───────────────────┐

                     ▼                                       ▼

           \[Stage-Presence Tracker\]               \[Relational SQLite DB\]

         (Enter / Exit / Aside Parsing)         (Turns, Lines, Meter Tags)

                     │                                       │

                     ▼                                       ▼

         \[Witness Bipartite Graph\]               \[Vector Database (Chroma)\]

      Facts Tagged with Witness Lists        Utterances Tagged with (Act, Scene, Line)

                     └───────────────────┬───────────────────┘

                                         │

                                         ▼

                           \[Chronological RAG Engine\]

                     Filter: Facts & Turns with tau \<= t\_current

                                         │

                                         ▼

                           \[Early Modern Orchestrator\]

                      \- Pronominal Address (Thou vs. You)

                      \- Dynamic Meter Selector (Verse vs. Prose)

                      \- Lexical Constraint Enforcement

                                         │

                                         ▼

                               \[LLM Inference (Gemini)\]

                                         │

                                         ▼

                          \[Automated Evaluation Suite\]

                     \- Burrows' Delta Distance

                     \- CMUdict / G2P Iambic Pentameter Scansion

                     \- 50-Probe Dramatic Irony Benchmark

---

## 4\. Phased Implementation Roadmap (Local Linux Environment)

### Phase 1: Canon Acquisition, XML Parsing & Database Ingestion (Weeks 1–3)

* **Corpus Ingestion:** Download the 37 TEI-XML plays from the official [Shakespeare DraCor](https://dracor.org/shake) repository (`https://github.com/dracor-org/shakedracor`).  
* **XML Extraction (`src/data/parse_tei.py`):**  
  * Parse speaker turns (`<sp>`), speaker labels (`<speaker>`), verse lines (`<l>`), prose blocks (`<ab>`), and stage directions (`<stage>`).  
  * Normalize \~900 speaker identifiers to unified canonical IDs across the canon.  
* **Database Architecture (`src/data/build_db.py`):**  
  * Build `data/shakespeare.db` (SQLite/DuckDB) with tables:  
    * `plays`: metadata, composition date, genre classification.  
    * `scenes`: act, scene, setting description.  
    * `dialogue_turns`: `turn_id`, `play_id`, `act`, `scene`, `line_start`, `line_end`, `speaker_id`, `meter_type` (`verse`, `prose`, `mixed`), `speech_type` (`dialogue`, `soliloquy`, `aside`), `text`.

### Phase 2: Stage-Presence Epistemic Graph & Bounded Vector Indexing (Weeks 4–6)

* **Stage-Presence Bipartite Graph (`src/kg/stage_presence.py`):**  
  * Line-by-line simulation of stage presence: parsing `<stage type="entrance">` and `<stage type="exit">`.  
  * Compute active witness vector \$\\mathbf{W}(L) \= {c\_1, c\_2, \\dots}\$ for each line \$L\$.  
  * Exclude characters who are absent or instances where speech is tagged `<aside>`.  
* **Chronological Knowledge Graph (`src/kg/epistemic_kg.py`):**  
  * Ingest scene-by-scene factual propositions: \$\\langle \\text{Subject}, \\text{Predicate}, \\text{Object}, \\text{Play}, \\text{Act}, \\text{Scene}, \\mathbf{Witnesses} \\rangle\$.  
  * Fact access is strictly conditional on character presence during or prior to the queried scene.  
* **Vector Indexing (`src/kg/index_chroma.py`):**  
  * Embed all character dialogue turns in local ChromaDB using `bge-large-en` or `text-embedding-3`.  
  * Store metadata filters: `play_id`, `speaker_id`, `act`, `scene`, `global_line_index`.

### Phase 3: Dialogue Engine & Shakespearean Conditioning (Weeks 7–9)

* **Chronologically Bounded Retrieval (`src/engine/retriever.py`):**  
  * Query only facts and speech turns satisfying \$\\text{line\_index} \\le L\_{\\text{current}}\$.  
* **Dynamic Form Selector & Prompt Engine (`src/engine/prompt.py`):**  
  * Determine whether the character should respond in verse or prose:  
    * *Default Noble/Tragic Register:* Blank verse.  
    * *Comic/Low-Status/Tavern Register:* Prose.  
    * *Feigned Madness / Collapsed State:* Transition to prose.  
  * **Pronominal Address Enforcement:**  
    * Injected rule: Use *thou/thee* when addressing a subordinate or intimate kin; use *you/ye* when addressing social superiors or strangers.  
  * **Negative Lexical Suppression:** Filter modernisms and post-1650 vocabulary.

### Phase 4: Computational Evaluation Suite (Weeks 10–12)

* **1\. Epistemic Integrity & Dramatic Irony Probes (`src/eval/eval_anachronism.py`):**  
  * 50 curated probe questions per anchor play testing future revelations (e.g., asking Hamlet in Act 1 about the duel with Laertes, or asking Othello in Act 2 about Desdemona's fidelity).  
  * Metric: Leakage error rate (\$E\_{\\text{leak}} \\to 0%\$).  
* **2\. Metrical Scansion & Prosodic Entropy (`src/eval/eval_scansion.py`):**  
  * Automated stress scansion via [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) adapted for Shakespearean contractions (*e'en*, *ne'er*, *'tis*, *o'er*).  
  * Metrics: Iambic pentameter regularity percentage and Shannon prosodic entropy \$H(X)\$.  
* **3\. Stylometric Distance (`src/eval/eval_stylometry.py`):**  
  * Compute Burrows' Delta (\$\\Delta\$) comparing generated character utterances against authentic Shakespearean speech versus out-of-corpus Early Modern baselines.  
* **4\. Sociolinguistic Pronominal Audit (`src/eval/eval_sociolect.py`):**  
  * Measure precision of *thou* vs. *you* usage across varied assigned user social tiers.  
* **5\. Expert Scholar Study (`src/eval/expert_study.py`):**  
  * Double-blind assessment by literature scholars rating voice authenticity and psychological plausibility.

### Phase 5: Local Streamlit Application & Open Science (Weeks 13–14)

* **Interactive UI (`src/ui/app.py`):**  
  * Dropdown: Select any of the 37 Shakespeare plays.  
  * Dropdown: Select any character in the dramatis personae.  
  * Timeline Slider: Set active Act and Scene (updates active stage presence and active knowledge).  
  * User Role Selector: Define user identity (Monarch, Peer, Commoner, Servant) to test T-V pronoun responses.  
  * Hermeneutic Sidebar: Real-time display of active stage witnesses, retrieved textual sources, and scansion scores.  
* **Archival:** Zenodo repository with dataset, SQLite database, scripts, and reproducibility benchmarks.

### Phase 6: Academic Manuscript & Publication (Weeks 15–18)

* **Target Venues:**  
  * *Computational Humanities Research (CHR)*  
  * *Digital Scholarship in the Humanities (DSH)*  
  * *LaTeCH-CLfL Workshop (ACL / EMNLP)*