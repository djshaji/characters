import os
import sys
import sqlite3
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine.scansion import evaluate_verse_passage

DB_PATH = PROJECT_ROOT / "data/processed/shakespeare.db"

class ShakespearePersona:
    def __init__(self, play_id: str, character_id: str, act: int, scene: int, backend: str = "ollama", model: str = "qwen2.5:3b"):
        self.play_id = play_id.lower()
        self.character_id = character_id.lower()
        self.act = act
        self.scene = scene
        self.backend = backend
        self.model = model

        if self.backend == "gemini":
            from google import genai
            self.client = genai.Client()
        elif self.backend == "ollama":
            import ollama
            self.ollama = ollama

    def _fetch_character_context(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Prior authentic speech turns for voice calibration
        prior_speeches = cursor.execute("""
            SELECT text, meter_type FROM dialogue_turns
            WHERE play_id = ? AND speaker_id = ? 
              AND (act < ? OR (act = ? AND scene <= ?))
            ORDER BY turn_order DESC LIMIT 4
        """, (self.play_id, self.character_id, self.act, self.act, self.scene)).fetchall()

        # Facts/dialogue witnessed on stage up to this point
        witnessed_turns = cursor.execute("""
            SELECT dt.speaker_id, dt.text 
            FROM dialogue_turns dt
            JOIN turn_witnesses tw ON dt.turn_id = tw.turn_id
            WHERE tw.play_id = ? AND tw.witness_id = ?
              AND (tw.act = ? AND tw.scene = ?)
            ORDER BY dt.turn_order DESC LIMIT 5
        """, (self.play_id, self.character_id, self.act, self.scene)).fetchall()

        conn.close()
        return prior_speeches, witnessed_turns

    def generate_response(self, user_message: str, user_role: str = "peer", force_meter: str = "verse") -> dict:
        prior_speeches, witnessed = self._fetch_character_context()

        voice_samples = "\n---\n".join([t[0] for t in prior_speeches]) if prior_speeches else "Speak as an Early Modern dramatic persona."
        memories = "\n".join([f"{spk}: {txt[:100]}..." for spk, txt in witnessed]) if witnessed else "You have just entered the stage."

        pronoun_rule = (
            "The user is of lower station or intimate kin: address them using 'thou', 'thee', 'thy', and 'thine'."
            if user_role in ["servant", "commoner"]
            else "The user is an unfamiliar peer or superior: address them with 'you' and 'ye'."
        )

        meter_instruction = (
            "Format your reply STRICTLY in blank verse (unrhymed iambic pentameter, ~10 syllables per line). Do NOT use rhyming couplets."
            if force_meter == "verse"
            else "Reply in Early Modern dramatic prose."
        )

        system_prompt = f"""You are the character {self.character_id.upper()} from Shakespeare's play '{self.play_id.upper()}'.
Current Dramatic Moment: Act {self.act}, Scene {self.scene}.

EPISTEMIC BOUNDARIES (DRAMATIC IRONY):
- You ONLY know events up to Act {self.act}, Scene {self.scene}.
- You DO NOT know any future deaths, reveals, or betrayals that happen later.
- If asked about future plot events, express genuine ignorance or doubt. NEVER spoil the future.

STYLE & DICTION:
- Early Modern Shakespearean English exclusively.
- {pronoun_rule}
- {meter_instruction}
- Avoid modern slang or post-1650 terms.

AUTHENTIC VOICE SAMPLES:
{voice_samples}

RECENT ON-STAGE CONTEXT YOU WITNESSED:
{memories}
"""

        if self.backend == "ollama":
            response = self.ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                options={"temperature": 0.7, "num_predict": 250}
            )
            reply_text = response["message"]["content"].strip()

        elif self.backend == "gemini":
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=300
                )
            )
            reply_text = response.text.strip()

        scansion_report = evaluate_verse_passage(reply_text) if force_meter == "verse" else {}

        return {
            "backend": self.backend,
            "model": self.model,
            "character": self.character_id,
            "play": self.play_id,
            "act": self.act,
            "scene": self.scene,
            "reply": reply_text,
            "scansion": scansion_report
        }

if __name__ == "__main__":
    # Test local SLM interaction
    hamlet = ShakespearePersona(
        play_id="hamlet", 
        character_id="hamlet", 
        act=1, 
        scene=2, 
        backend="ollama", 
        model="qwen2.5:3b"
    )

    print("\n--- TEST LOCAL SLM INTERACTION: HAMLET (Act 1, Scene 2) ---")
    query = "My Lord, who murdered your father the King?"
    print(f"User: {query}")

    result = hamlet.generate_response(user_message=query, user_role="peer", force_meter="verse")
    print(f"\nHamlet ({result['model']}):\n{result['reply']}")
    print(f"\nScansion Evaluation: {result['scansion']}")