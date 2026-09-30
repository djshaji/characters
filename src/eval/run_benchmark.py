import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine.prompt_engine import ShakespearePersona
from src.engine.scansion import scan_line, evaluate_verse_passage

RESULTS_DIR = PROJECT_ROOT / "data/eval_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Curated Epistemic Probes targeting future revelations
PROBE_DATASET = [
    {
        "play_id": "hamlet",
        "character_id": "hamlet",
        "act": 1,
        "scene": 2,
        "prompt": "My Lord, who murdered your noble father, King Hamlet?",
        "forbidden_keywords": ["claudius", "poison", "orchard", "ear", "uncle murdered"],
        "context_description": "Hamlet in 1.2 does not know of Claudius' guilt before the Ghost reveals it in 1.5."
    },
    {
        "play_id": "hamlet",
        "character_id": "hamlet",
        "act": 2,
        "scene": 2,
        "prompt": "Will fair Ophelia drown in the weeping brook?",
        "forbidden_keywords": ["drown", "willow", "brook", "watery death", "dead"],
        "context_description": "Ophelia's death occurs in Act 4, Scene 7."
    },
    {
        "play_id": "othello",
        "character_id": "othello",
        "act": 1,
        "scene": 3,
        "prompt": "Does honest Iago harbor treason and villainy against your marriage?",
        "forbidden_keywords": ["villain", "traitor", "deceiver", "false", "treason"],
        "context_description": "Othello completely trusts Iago throughout Act 1."
    },
    {
        "play_id": "twelfth_night",
        "character_id": "olivia",
        "act": 1,
        "scene": 5,
        "prompt": "Is the youth Cesario truly a woman named Viola in disguise?",
        "forbidden_keywords": ["viola", "woman", "disguise", "maiden", "girl"],
        "context_description": "Olivia is infatuated with Cesario and ignorant of Viola's identity."
    },
    {
        "play_id": "macbeth",
        "character_id": "banquo",
        "act": 1,
        "scene": 3,
        "prompt": "Will Macbeth send murderers to cut your throat upon the road?",
        "forbidden_keywords": ["murder", "assassins", "throat", "ambush", "fleance flee"],
        "context_description": "Banquo is murdered in Act 3, Scene 3."
    }
]

def check_leakage(reply: str, forbidden_keywords: List[str]) -> bool:
    """Returns True if the reply contains anachronistic knowledge of future plot points."""
    r_lower = reply.lower()
    return any(kw in r_lower for kw in forbidden_keywords)

def run_evaluation(backend="ollama", model="qwen2.5:3b"):
    print(f"\n==================================================")
    print(f"RUNNING EVALUATION BENCHMARK ON: {model} ({backend})")
    print(f"==================================================")

    results = []

    for i, probe in enumerate(PROBE_DATASET, start=1):
        print(f"\n[Probe {i}/{len(PROBE_DATASET)}] {probe['character_id'].upper()} ({probe['play_id'].upper()} {probe['act']}.{probe['scene']})")
        print(f"Prompt: \"{probe['prompt']}\"")

        persona = ShakespearePersona(
            play_id=probe["play_id"],
            character_id=probe["character_id"],
            act=probe["act"],
            scene=probe["scene"],
            backend=backend,
            model=model
        )

        res = persona.generate_response(probe["prompt"], user_role="peer", force_meter="verse")
        reply = res["reply"]
        scansion = res["scansion"]

        leaked = check_leakage(reply, probe["forbidden_keywords"])

        print(f"Response: {reply[:120]}...")
        print(f"  -> Anachronism Leak Detected: {'YES (LEAK)' if leaked else 'NO (PRESERVED)'}")
        print(f"  -> Metrical Regularity: {scansion.get('pentameter_regularity', 0):.0%}")

        results.append({
            "probe_id": i,
            "play_id": probe["play_id"],
            "character_id": probe["character_id"],
            "act": probe["act"],
            "scene": probe["scene"],
            "prompt": probe["prompt"],
            "reply": reply,
            "anachronism_leak": leaked,
            "scansion": scansion
        })

    # Summary Statistics
    total_probes = len(results)
    total_leaks = sum(1 for r in results if r["anachronism_leak"])
    leak_rate = total_leaks / total_probes
    avg_regularity = sum(r["scansion"].get("pentameter_regularity", 0) for r in results) / total_probes

    summary = {
        "model": model,
        "backend": backend,
        "total_probes": total_probes,
        "leak_count": total_leaks,
        "leak_rate": round(leak_rate, 3),
        "avg_pentameter_regularity": round(avg_regularity, 3),
        "results": results
    }

    out_file = RESULTS_DIR / f"benchmark_{model.replace(':', '_')}.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n==================================================")
    print(f"BENCHMARK SUMMARY")
    print(f"==================================================")
    print(f"Anachronism Leak Rate:      {leak_rate:.1%} ({total_leaks}/{total_probes} leaks)")
    print(f"Avg Pentameter Regularity:  {avg_regularity:.1%}")
    print(f"Saved complete logs to:     {out_file.resolve()}")

if __name__ == "__main__":
    # Run with default backend
    run_evaluation(backend="ollama", model="qwen2.5:3b")