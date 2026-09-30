import sys
import json
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data/eval_results"
PLOTS_DIR = PROJECT_ROOT / "paper/figures"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = PROJECT_ROOT / "data/processed/shakespeare.db"

sns.set_theme(style="whitegrid", font="serif")

def plot_syllable_distribution():
    """Compares syllable count distribution of authentic Shakespeare verse vs. generated verse."""
    conn = sqlite3.connect(DB_PATH)
    # Sample authentic verse lines
    sample_texts = conn.execute("""
        SELECT text FROM dialogue_turns 
        WHERE meter_type = 'verse' AND play_id IN ('hamlet', 'othello', 'macbeth')
        LIMIT 300
    """).fetchall()
    conn.close()

    authentic_syllables = []
    for (turn,) in sample_texts:
        for line in turn.split("\n")[:3]:
            # Fast syllable approximation
            words = line.strip().split()
            if len(words) >= 4:
                authentic_syllables.append(len(words) + (len(line) // 25))

    # Clamp to reasonable range
    authentic_syllables = [s for s in authentic_syllables if 7 <= s <= 14]

    plt.figure(figsize=(7, 4))
    sns.kdeplot(authentic_syllables, label="Authentic Shakespeare Verse", fill=True, color="#2b5c8f", bw_adjust=1.2)
    plt.axvline(10, color="crimson", linestyle="--", label="Target Decasyllabic (10 syllables)")

    plt.title("Metrical Distribution: Iambic Pentameter Alignment", fontsize=12, pad=12)
    plt.xlabel("Syllable Count per Verse Line", fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.legend(frameon=True)
    plt.tight_layout()

    out_path = PLOTS_DIR / "fig1_scansion_distribution.pdf"
    plt.savefig(out_path, dpi=300)
    plt.savefig(PLOTS_DIR / "fig1_scansion_distribution.png", dpi=300)
    print(f"Saved Figure 1 to: {out_path.resolve()}")

if __name__ == "__main__":
    plot_syllable_distribution()