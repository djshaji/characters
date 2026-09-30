import sys
import re
import sqlite3
import numpy as np
from pathlib import Path
from collections import Counter
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data/processed/shakespeare.db"

def tokenize(text: str) -> List[str]:
    return re.findall(r"\b[a-z']+\b", text.lower())

def get_mfw_table(corpus_words: List[str], n_words: int = 100) -> List[str]:
    """Extracts the n Most Frequent Words (MFW) from the primary corpus."""
    counts = Counter(corpus_words)
    return [word for word, _ in counts.most_common(n_words)]

def get_word_frequencies(words: List[str], mfw_list: List[str]) -> np.ndarray:
    """Calculates relative frequencies (per thousand words) for the MFW list."""
    total = max(1, len(words))
    counts = Counter(words)
    return np.array([(counts[w] / total) * 1000.0 for w in mfw_list])

def calculate_burrows_delta(candidate_freqs: np.ndarray, corpus_mean: np.ndarray, corpus_std: np.ndarray) -> float:
    """
    Computes classic Burrows' Delta:
    Delta = (1/n) * sum( | z_candidate - z_corpus | )
    """
    # Avoid division by zero
    std_safe = np.where(corpus_std == 0, 1.0, corpus_std)
    z_candidate = (candidate_freqs - corpus_mean) / std_safe
    # Since corpus reference z-score is 0:
    delta = np.mean(np.abs(z_candidate))
    return round(float(delta), 4)

def run_stylometry_experiment():
    print("="*50)
    print("RUNNING BURROWS' DELTA STYLOMETRIC EXPERIMENT")
    print("="*50)

    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load Shakespeare Canon words
    print("Loading Shakespeare Canon reference baseline...")
    rows = conn.execute("SELECT text FROM dialogue_turns LIMIT 3000").fetchall()
    all_text = " ".join([r[0] for r in rows])
    canon_tokens = tokenize(all_text)
    
    # Extract 100 Most Frequent Words
    mfw = get_mfw_table(canon_tokens, n_words=100)
    
    # Compute baseline distribution across 20 distinct play chunks
    chunk_size = len(canon_tokens) // 20
    chunk_matrix = []
    for i in range(20):
        chunk = canon_tokens[i*chunk_size : (i+1)*chunk_size]
        chunk_matrix.append(get_word_frequencies(chunk, mfw))
        
    chunk_matrix = np.array(chunk_matrix)
    corpus_mean = np.mean(chunk_matrix, axis=0)
    corpus_std = np.std(chunk_matrix, axis=0)

    # 2. Modern English Benchmark Baseline
    modern_sample = """
    I really think that we need to understand how the system works before jumping to conclusions.
    The data suggests that the results are consistent with our original hypothesis, although some
    discrepancies exist. We should meet tomorrow morning to discuss the next steps in our research project.
    """ * 10
    modern_tokens = tokenize(modern_sample)
    modern_freqs = get_word_frequencies(modern_tokens, mfw)
    delta_modern = calculate_burrows_delta(modern_freqs, corpus_mean, corpus_std)

    # 3. Authentic Shakespeare Sample (Hamlet excerpt)
    hamlet_rows = conn.execute("SELECT text FROM dialogue_turns WHERE play_id = 'hamlet' AND speaker_id = 'hamlet' LIMIT 30").fetchall()
    hamlet_tokens = tokenize(" ".join([r[0] for r in hamlet_rows]))
    hamlet_freqs = get_word_frequencies(hamlet_tokens, mfw)
    delta_authentic = calculate_burrows_delta(hamlet_freqs, corpus_mean, corpus_std)

    conn.close()

    print(f"\nStylometric Results (Burrows' Delta - Lower = Closer to Canon):")
    print(f"  • Authentic Hamlet vs. Canon:  Delta = {delta_authentic:.4f} (Gold standard internal variance)")
    print(f"  • Modern English Text vs. Canon: Delta = {delta_modern:.4f} (Control baseline)")
    print(f"\nCondition for Model Success: Delta(Generated) should be significantly lower than Modern ({delta_modern:.4f}).")

if __name__ == "__main__":
    run_stylometry_experiment()