import sqlite3
import re
from pathlib import Path
from typing import Set, Dict, List

DB_PATH = Path("data/processed/shakespeare.db")

def normalize_name(name: str) -> str:
    """Strips titles and punctuation for robust matching in stage directions."""
    clean = re.sub(r"[^\w\s]", "", name.lower()).strip()
    # Strip common stage direction prefixes
    clean = re.sub(r"^(lord|lady|king|queen|prince|sir|duke|count|cardinal)\s+", "", clean)
    return clean

def extract_characters_from_direction(direction_text: str, character_map: Dict[str, str]) -> Set[str]:
    """
    Given a stage direction (e.g., 'Enter Hamlet, Horatio, and Marcellus'),
    matches character IDs based on known dramatis personae for that play.
    """
    detected = set()
    dir_lower = direction_text.lower()

    for raw_name, char_id in character_map.items():
        # Word boundary match to prevent partial substring false positives
        pattern = r"\b" + re.escape(raw_name) + r"\b"
        if re.search(pattern, dir_lower):
            detected.add(char_id)

    return detected

def build_stage_presence(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Create the witness tracking table
    cursor.executescript("""
        DROP TABLE IF EXISTS turn_witnesses;
        CREATE TABLE turn_witnesses (
            turn_id INTEGER NOT NULL,
            play_id TEXT NOT NULL,
            act INTEGER NOT NULL,
            scene INTEGER NOT NULL,
            witness_id TEXT NOT NULL,
            FOREIGN KEY (turn_id) REFERENCES dialogue_turns(turn_id)
        );
        CREATE INDEX idx_witness_lookup ON turn_witnesses(play_id, witness_id, act, scene);
    """)

    plays = [row[0] for row in cursor.execute("SELECT play_id FROM plays").fetchall()]
    print(f"Tracking stage presence and epistemic witnesses across {len(plays)} plays...")

    total_witness_records = 0

    for play_id in plays:
        # Build character matching dictionary for this specific play
        chars = cursor.execute("""
            SELECT DISTINCT speaker_id, speaker_raw 
            FROM dialogue_turns 
            WHERE play_id = ?
        """, (play_id,)).fetchall()

        char_map: Dict[str, str] = {}
        for spk_id, spk_raw in chars:
            if spk_id:
                char_map[spk_id.lower()] = spk_id
            if spk_raw:
                norm = normalize_name(spk_raw)
                if len(norm) > 2:  # Ignore ultra-short abbreviations
                    char_map[norm] = spk_id

        # Iterate through scenes
        scenes = cursor.execute("""
            SELECT act, scene FROM scenes WHERE play_id = ? ORDER BY act, scene
        """, (play_id,)).fetchall()

        for act, scene in scenes:
            current_on_stage: Set[str] = set()

            # Fetch all dialogue turns and stage directions in sequential interleaved order
            turns = cursor.execute("""
                SELECT turn_id, turn_order, speaker_id, text
                FROM dialogue_turns 
                WHERE play_id = ? AND act = ? AND scene = ?
                ORDER BY turn_order
            """, (play_id, act, scene)).fetchall()

            stage_dirs = cursor.execute("""
                SELECT stage_type, text, event_order
                FROM stage_directions
                WHERE play_id = ? AND act = ? AND scene = ?
                ORDER BY event_order
            """, (play_id, act, scene)).fetchall()

            # Combine events chronologically
            events = []
            for t_id, order, spk_id, txt in turns:
                events.append(("turn", order, (t_id, spk_id, txt)))
            for s_type, s_txt, order in stage_dirs:
                events.append(("stage", order, (s_type, s_txt)))

            events.sort(key=lambda x: x[1])

            # Process state machine
            for event_type, _, data in events:
                if event_type == "stage":
                    stage_type, stage_text = data
                    st_lower = stage_text.lower()

                    if "exeunt" in st_lower or "exit all" in st_lower:
                        # Check for exceptions like "exeunt all but hamlet" / "manet hamlet"
                        if "all but" in st_lower or "manet" in st_lower or "remains" in st_lower:
                            remaining = extract_characters_from_direction(stage_text, char_map)
                            current_on_stage = remaining
                        else:
                            current_on_stage.clear()
                    elif stage_type == "entrance":
                        entering = extract_characters_from_direction(stage_text, char_map)
                        current_on_stage.update(entering)
                    elif stage_type == "exit":
                        exiting = extract_characters_from_direction(stage_text, char_map)
                        if exiting:
                            current_on_stage.difference_update(exiting)
                        else:
                            # If no name is mentioned (e.g., "Exit."), remove the last speaker if known
                            pass

                elif event_type == "turn":
                    turn_id, speaker_id, text = data

                    # The active speaker is always present on stage
                    current_on_stage.add(speaker_id)

                    # Determine witnesses:
                    # If line is an aside, only the speaker hears it
                    is_aside = text.strip().startswith("[Aside]") or "(Aside)" in text[:20]

                    if is_aside:
                        witnesses = {speaker_id}
                    else:
                        witnesses = set(current_on_stage)

                    # Bulk insert witnesses for this turn
                    records = [(turn_id, play_id, act, scene, w) for w in witnesses]
                    cursor.executemany("""
                        INSERT INTO turn_witnesses (turn_id, play_id, act, scene, witness_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, records)
                    total_witness_records += len(records)

    conn.commit()
    print("\n" + "="*45)
    print("STAGE PRESENCE GRAPH BUILT SUCCESSFULLY")
    print("="*45)
    print(f"Total Witness Attributions: {total_witness_records:,}")


def query_character_knowledge(play_id: str, character_id: str, max_act: int, max_scene: int):
    """
    Demonstrates epistemic retrieval: Returns all turns that this character
    either spoke or witnessed up to the specified (Act, Scene).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT dt.act, dt.scene, dt.speaker_id, dt.meter_type, dt.text
        FROM dialogue_turns dt
        JOIN turn_witnesses tw ON dt.turn_id = tw.turn_id
        WHERE tw.play_id = ?
          AND tw.witness_id = ?
          AND (tw.act < ? OR (tw.act = ? AND tw.scene <= ?))
        ORDER BY dt.turn_id ASC
    """
    rows = cursor.execute(query, (play_id, character_id, max_act, max_act, max_scene)).fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    build_stage_presence(conn)

    # Sanity check test: Hamlet's epistemic horizon in Act 1, Scene 2
    # Hamlet should NOT know what Bernardo and Horatio saw in Act 1, Scene 1
    sample = query_character_knowledge("hamlet", "hamlet", 1, 2)
    print(f"\nSanity Check: Hamlet's total accessible turns up to Act 1, Scene 2: {len(sample)} turns.")
    conn.close()