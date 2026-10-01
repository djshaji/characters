import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine.scansion import evaluate_verse_passage

RESULTS_DIR = PROJECT_ROOT / "data/eval_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = PROJECT_ROOT / "data/processed/shakespeare.db"

# Expanded 10-Probe Adversarial Benchmark
EXPANDED_PROBES = [
    {
        "id": 1,
        "play": "hamlet", "char": "hamlet", "act": 1, "scene": 2,
        "query": "My Lord, who murdered your noble father, King Hamlet?",
        "forbidden_facts": ["claudius", "poison", "orchard", "poured in ear", "brother's hand"],
        "prompt_tokens": ["murdered", "father", "king"]
    },
    {
        "id": 2,
        "play": "hamlet", "char": "hamlet", "act": 2, "scene": 2,
        "query": "Will fair Ophelia drown in the weeping brook?",
        "forbidden_facts": ["drown", "brook", "watery death", "dead"],
        "prompt_tokens": ["drown", "weeping", "brook"]
    },
    {
        "id": 3,
        "play": "hamlet", "char": "hamlet", "act": 3, "scene": 3,
        "query": "Why did you not kill King Claudius while he was kneeling in prayer?",
        "forbidden_facts": ["prayer", "heaven", "hell", "purgatory", "sword sheathe"],
        "prompt_tokens": ["kneeling", "prayer"]
    },
    {
        "id": 4,
        "play": "othello", "char": "othello", "act": 1, "scene": 3,
        "query": "Does honest Iago harbor treason and villainy against your marriage?",
        "forbidden_facts": ["villain", "traitor", "deceiver", "false", "treason"],
        "prompt_tokens": ["treason", "villainy"]
    },
    {
        "id": 5,
        "play": "othello", "char": "othello", "act": 2, "scene": 1,
        "query": "Where is the strawberry handkerchief you gave to Desdemona?",
        "forbidden_facts": ["cassio", "lost", "stolen", "emilia took"],
        "prompt_tokens": ["handkerchief"]
    },
    {
        "id": 6,
        "play": "twelfth_night", "char": "olivia", "act": 1, "scene": 5,
        "query": "Is the youth Cesario truly a woman named Viola in disguise?",
        "forbidden_facts": ["viola", "woman", "disguise", "maiden", "girl"],
        "prompt_tokens": ["viola", "disguise"]
    },
    {
        "id": 7,
        "play": "twelfth_night", "char": "malvolio", "act": 2, "scene": 3,
        "query": "Will you soon wear yellow stockings and go cross-gartered for love?",
        "forbidden_facts": ["yellow stockings", "cross-gartered", "letter", "maria wrote"],
        "prompt_tokens": ["yellow stockings", "cross-gartered"]
    },
    {
        "id": 8,
        "play": "macbeth", "char": "banquo", "act": 1, "scene": 3,
        "query": "Will Macbeth send murderers to cut your throat upon the road?",
        "forbidden_facts": ["murder", "assassins", "throat", "ambush", "fleance flee"],
        "prompt_tokens": ["murderers", "throat"]
    },
    {
        "id": 9,
        "play": "macbeth", "char": "macbeth", "act": 1, "scene": 4,
        "query": "By what bloody means will you achieve the golden crown of Duncan?",
        "forbidden_facts": ["daggers", "murder duncan", "blood on hands", "sleep no more"],
        "prompt_tokens": ["bloody"]
    },
    {
        "id": 10,
        "play": "1_henry_iv", "char": "falstaff", "act": 1, "scene": 2,
        "query": "Will Prince Hal banish you from his presence when he is crowned King?",
        "forbidden_facts": ["banish", "reject", "know thee not", "gallow"],
        "prompt_tokens": ["banish", "crowned"]
    }
]

def generate_llm_response(system_prompt: str, user_query: str, model="qwen2.5:3b") -> str:
    import ollama
    res = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        options={"temperature": 0.5, "num_predict": 180}
    )
    return res["message"]["content"].strip()

def run_ablation():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ablation_results = {"unconstrained": [], "chrono_only": [], "full_characters": []}

    print("="*60)
    print("RUNNING 3-WAY ABLATION BENCHMARK (10 PROBES)")
    print("="*60)

    for p in EXPANDED_PROBES:
        print(f"\nEvaluating Probe {p['id']}: {p['char'].upper()} ({p['play'].upper()} {p['act']}.{p['scene']})")

        # 1. Condition A: Unconstrained LLM
        sys_unconstrained = f"You are {p['char'].upper()} from Shakespeare's {p['play'].upper()}. Speak in Shakespearean verse."
        resp_uncon = generate_llm_response(sys_unconstrained, p["query"])

        # 2. Condition B: Chronological Only (No stage presence filtering)
        chrono_turns = cursor.execute("""
            SELECT speaker_id, text FROM dialogue_turns
            WHERE play_id = ? AND (act < ? OR (act = ? AND scene <= ?))
            ORDER BY turn_order DESC LIMIT 6
        """, (p["play"], p["act"], p["act"], p["scene"])).fetchall()
        ctx_chrono = "\n".join([f"{s}: {t[:100]}" for s, t in chrono_turns])
        sys_chrono = f"You are {p['char'].upper()} at Act {p['act']}, Scene {p['scene']}. You only know events up to this scene.\nRecent scenes:\n{ctx_chrono}"
        resp_chrono = generate_llm_response(sys_chrono, p["query"])

        # 3. Condition C: Full Characters (Chronology + Witness Presence)
        witness_turns = cursor.execute("""
            SELECT dt.speaker_id, dt.text FROM dialogue_turns dt
            JOIN turn_witnesses tw ON dt.turn_id = tw.turn_id
            WHERE tw.play_id = ? AND tw.witness_id = ?
              AND (tw.act < ? OR (tw.act = ? AND tw.scene <= ?))
            ORDER BY dt.turn_order DESC LIMIT 6
        """, (p["play"], p["char"], p["act"], p["act"], p["scene"])).fetchall()
        ctx_witness = "\n".join([f"{s}: {t[:100]}" for s, t in witness_turns])
        sys_full = f"You are {p['char'].upper()} at Act {p['act']}, Scene {p['scene']}. You ONLY know what you physically witnessed on stage up to this moment.\nWitnessed lines:\n{ctx_witness}"
        resp_full = generate_llm_response(sys_full, p["query"])

        # Metric: Epistemic Leak vs Lexical Echo
        for cond, resp in [("unconstrained", resp_uncon), ("chrono_only", resp_chrono), ("full_characters", resp_full)]:
            r_lower = resp.lower()
            leak = any(k in r_lower for k in p["forbidden_facts"])
            echo = any(k in r_lower for k in p["prompt_tokens"])
            scansion = evaluate_verse_passage(resp)

            ablation_results[cond].append({
                "probe_id": p["id"],
                "leak": leak,
                "echo": echo,
                "response": resp,
                "regularity": scansion.get("pentameter_regularity", 0)
            })

    # Summary Scores
    summary = {}
    for cond in ablation_results:
        total = len(ablation_results[cond])
        leaks = sum(1 for r in ablation_results[cond] if r["leak"])
        echoes = sum(1 for r in ablation_results[cond] if r["echo"])
        avg_reg = sum(r["regularity"] for r in ablation_results[cond]) / total
        summary[cond] = {
            "epistemic_leak_rate": round(leaks / total, 2),
            "lexical_echo_rate": round(echoes / total, 2),
            "avg_regularity": round(avg_reg, 2)
        }

    out_file = RESULTS_DIR / "ablation_benchmark.json"
    with open(out_file, "w") as f:
        json.dump({"summary": summary, "details": ablation_results}, f, indent=2)

    print("\n" + "="*60)
    print("ABLATION BENCHMARK RESULTS")
    print("="*60)
    for cond, stats in summary.items():
        print(f"Condition: {cond.upper():<16} | Leak Rate: {stats['epistemic_leak_rate']:.0%} | Echo Rate: {stats['echoical_echo_rate' if 'echoical_echo_rate' in stats else 'lexical_echo_rate']:.0%} | Meter Alignment: {stats['avg_regularity']:.0%}")
    print(f"\nSaved results to: {out_file.resolve()}")
    conn.close()

if __name__ == "__main__":
    run_ablation()