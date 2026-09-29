import sqlite3
import re
from pathlib import Path
from lxml import etree

RAW_DATA_DIR = Path("data/raw_tei")  # Adjust if your XMLs are in another folder
DB_PATH = Path("data/processed/shakespeare.db")

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

def init_db(conn: sqlite3.Connection):
    """Initializes the relational schema for the Shakespeare canon."""
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS dialogue_turns;
        DROP TABLE IF EXISTS stage_directions;
        DROP TABLE IF EXISTS scenes;
        DROP TABLE IF EXISTS plays;

        CREATE TABLE plays (
            play_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            genre TEXT
        );

        CREATE TABLE scenes (
            scene_id TEXT PRIMARY KEY,
            play_id TEXT NOT NULL,
            act INTEGER NOT NULL,
            scene INTEGER NOT NULL,
            setting TEXT,
            FOREIGN KEY (play_id) REFERENCES plays (play_id)
        );

        CREATE TABLE dialogue_turns (
            turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            play_id TEXT NOT NULL,
            act INTEGER NOT NULL,
            scene INTEGER NOT NULL,
            turn_order INTEGER NOT NULL,
            speaker_id TEXT NOT NULL,
            speaker_raw TEXT,
            meter_type TEXT NOT NULL,  -- 'verse', 'prose', or 'mixed'
            line_count INTEGER,
            text TEXT NOT NULL,
            FOREIGN KEY (play_id) REFERENCES plays (play_id)
        );

        CREATE TABLE stage_directions (
            stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            play_id TEXT NOT NULL,
            act INTEGER NOT NULL,
            scene INTEGER NOT NULL,
            event_order INTEGER NOT NULL,
            stage_type TEXT,            -- 'entrance', 'exit', 'aside', 'general'
            text TEXT NOT NULL,
            FOREIGN KEY (play_id) REFERENCES plays (play_id)
        );

        CREATE INDEX idx_turns_lookup ON dialogue_turns(play_id, act, scene, speaker_id);
        CREATE INDEX idx_stage_lookup ON stage_directions(play_id, act, scene);
    """)
    conn.commit()

def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def parse_play(xml_file: Path, conn: sqlite3.Connection):
    """Parses a single DraCor TEI-XML file and inserts it into SQLite."""
    cursor = conn.cursor()
    tree = etree.parse(str(xml_file))
    root = tree.getroot()

    # Extract Play Metadata
    play_id = xml_file.stem.replace(".tei", "")
    title_elem = root.xpath("//tei:titleStmt/tei:title[1]/text()", namespaces=TEI_NS)
    title = clean_text(title_elem[0]) if title_elem else play_id.replace("-", " ").title()

    cursor.execute("INSERT OR REPLACE INTO plays (play_id, title) VALUES (?, ?)", (play_id, title))

    # Iterate Acts (div type="act")
    acts = root.xpath("//tei:body//tei:div[@type='act']", namespaces=TEI_NS)
    if not acts:
        # Fallback if acts are not explicitly grouped in div type="act"
        acts = [root.xpath("//tei:body", namespaces=TEI_NS)[0]]

    global_turn_order = 0
    global_event_order = 0

    for act_idx, act_div in enumerate(acts, start=1):
        act_num = act_idx
        # Check if @n attribute exists
        if act_div.get("n"):
            try:
                act_num = int(re.sub(r"\D", "", act_div.get("n")))
            except ValueError:
                pass

        # Iterate Scenes (div type="scene")
        scenes = act_div.xpath(".//tei:div[@type='scene']", namespaces=TEI_NS)
        if not scenes:
            scenes = [act_div]

        for scene_idx, scene_div in enumerate(scenes, start=1):
            scene_num = scene_idx
            if scene_div.get("n"):
                try:
                    scene_num = int(re.sub(r"\D", "", scene_div.get("n")))
                except ValueError:
                    pass

            scene_id = f"{play_id}_A{act_num}_S{scene_num}"
            head_elems = scene_div.xpath("./tei:head/text()", namespaces=TEI_NS)
            setting = clean_text(head_elems[0]) if head_elems else ""

            cursor.execute(
                "INSERT OR REPLACE INTO scenes (scene_id, play_id, act, scene, setting) VALUES (?, ?, ?, ?, ?)",
                (scene_id, play_id, act_num, scene_num, setting)
            )

            # Traverse child elements in strict sequential order
            for child in scene_div.xpath("./tei:sp | ./tei:stage", namespaces=TEI_NS):
                tag_name = etree.QName(child).localname
                global_event_order += 1

                if tag_name == "stage":
                    stage_text = clean_text(" ".join(child.itertext()))
                    stage_type = "general"
                    stage_lower = stage_text.lower()
                    if "enter" in stage_lower:
                        stage_type = "entrance"
                    elif "exit" in stage_lower or "exeunt" in stage_lower:
                        stage_type = "exit"
                    elif "aside" in stage_lower:
                        stage_type = "aside"

                    cursor.execute("""
                        INSERT INTO stage_directions (play_id, act, scene, event_order, stage_type, text)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (play_id, act_num, scene_num, global_event_order, stage_type, stage_text))

                elif tag_name == "sp":
                    global_turn_order += 1
                    speaker_raw = clean_text(" ".join(child.xpath("./tei:speaker//text()", namespaces=TEI_NS)))
                    who_attr = child.get("who", "").replace("#", "").strip()
                    speaker_id = who_attr.lower() if who_attr else speaker_raw.lower()

                    # Extract verse lines (<l>) and prose blocks (<ab> / <p>)
                    verse_lines = [clean_text(" ".join(l.itertext())) for l in child.xpath("./tei:l", namespaces=TEI_NS)]
                    prose_blocks = [clean_text(" ".join(p.itertext())) for p in child.xpath("./tei:ab | ./tei:p", namespaces=TEI_NS)]

                    if verse_lines and prose_blocks:
                        meter_type = "mixed"
                        speech_text = "\n".join(verse_lines + prose_blocks)
                        line_count = len(verse_lines)
                    elif verse_lines:
                        meter_type = "verse"
                        speech_text = "\n".join(verse_lines)
                        line_count = len(verse_lines)
                    else:
                        meter_type = "prose"
                        speech_text = "\n".join(prose_blocks)
                        line_count = len(speech_text.split(". "))

                    cursor.execute("""
                        INSERT INTO dialogue_turns 
                        (play_id, act, scene, turn_order, speaker_id, speaker_raw, meter_type, line_count, text)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (play_id, act_num, scene_num, global_turn_order, speaker_id, speaker_raw, meter_type, line_count, speech_text))

    conn.commit()

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Locate all XML files (recursively in case they are in subfolders)
    xml_files = sorted(list(RAW_DATA_DIR.rglob("*.xml")))
    if not xml_files:
        print(f"No XML files found in {RAW_DATA_DIR.resolve()}. Check your download path.")
        return

    print(f"Found {len(xml_files)} play XMLs. Beginning parsing...")

    for f in xml_files:
        try:
            parse_play(f, conn)
            print(f"  ✓ Ingested: {f.name}")
        except Exception as e:
            print(f"  ✗ Error parsing {f.name}: {e}")

    # Print summary statistics
    cursor = conn.cursor()
    total_plays = cursor.execute("SELECT COUNT(*) FROM plays").fetchone()[0]
    total_turns = cursor.execute("SELECT COUNT(*) FROM dialogue_turns").fetchone()[0]
    total_verse = cursor.execute("SELECT COUNT(*) FROM dialogue_turns WHERE meter_type = 'verse'").fetchone()[0]
    total_prose = cursor.execute("SELECT COUNT(*) FROM dialogue_turns WHERE meter_type = 'prose'").fetchone()[0]

    print("\n" + "="*45)
    print("CANON DATABASE INGESTION COMPLETE")
    print("="*45)
    print(f"Plays Ingested:      {total_plays}")
    print(f"Total Speech Turns:  {total_turns:,}")
    print(f"  - Verse Turns:     {total_verse:,} ({total_verse/total_turns:.1%})")
    print(f"  - Prose Turns:     {total_prose:,} ({total_prose/total_turns:.1%})")
    print(f"Database location:   {DB_PATH.resolve()}")

    conn.close()

if __name__ == "__main__":
    main()