import re
import nltk
from typing import List, Tuple, Dict

# Ensure CMUdict pronouncing dictionary is available
try:
    from nltk.corpus import cmudict
    cmu = cmudict.dict()
except Exception:
    nltk.download('cmudict')
    from nltk.corpus import cmudict
    cmu = cmudict.dict()

# Early Modern English contractions, elisions, and archaic monosyllabic forms
EME_SPECIAL_WORDS: Dict[str, List[str]] = {
    "'tis": ["1"],
    "tis": ["1"],
    "ne'er": ["1"],
    "o'er": ["1"],
    "e'en": ["1"],
    "heav'n": ["1"],
    "ta'en": ["1"],
    "thou": ["1"],
    "thee": ["1"],
    "thine": ["1"],
    "thy": ["1"],
    "doth": ["1"],
    "hath": ["1"],
    "art": ["1"],
    "wast": ["1"],
    "wert": ["1"],
    "i'faith": ["0", "1"]
}

def clean_word(word: str) -> str:
    """Removes trailing and leading punctuation, preserving interior apostrophes."""
    return re.sub(r"[^\w']", "", word.lower()).strip()

def get_word_stresses(word: str) -> List[str]:
    """
    Returns a list of stress digits ('0' for unstressed, '1' for stressed)
    for a given word, referencing EME overrides and CMUdict.
    """
    w_clean = clean_word(word)
    if not w_clean:
        return []

    # 1. Check Early Modern English dictionary
    if w_clean in EME_SPECIAL_WORDS:
        return EME_SPECIAL_WORDS[w_clean]

    # 2. Check CMU Pronouncing Dictionary
    if w_clean in cmu:
        phonemes = cmu[w_clean][0]
        stresses = [char for phone in phonemes for char in phone if char.isdigit()]
        # Map secondary stress ('2') to primary stress ('1') for binary scansion
        return ['1' if s == '2' else s for s in stresses]

    # 3. Fallback heuristic for unknown archaic words: count vowel nuclei
    vowels = len(re.findall(r"[aeiouy]+", w_clean))
    return ['1'] * max(1, vowels)

def scan_line(line: str) -> Tuple[int, str, float]:
    """
    Scans a single line of verse against an iambic pentameter template.
    Returns:
        syllables (int): Count of scanned syllables.
        pattern (str): Binary stress pattern (e.g., '0101010101').
        score (float): Metrical fidelity score between 0.0 and 1.0.
    """
    tokens = [w for w in line.strip().split() if clean_word(w)]
    if not tokens:
        return 0, "", 0.0

    stresses = []
    for token in tokens:
        stresses.extend(get_word_stresses(token))

    syllables = len(stresses)
    pattern = "".join(stresses)

    # Standard iambic pentameter reference (10 syllables: unstressed-stressed alternating)
    target = "0101010101"

    score = 0.0
    if syllables == 10:
        matches = sum(1 for a, b in zip(pattern, target) if a == b)
        score = matches / 10.0
    elif syllables == 11 and pattern.endswith("0"):
        # Permissible feminine ending (11 syllables ending unstressed)
        matches = sum(1 for a, b in zip(pattern[:10], target) if a == b)
        score = (matches / 10.0) * 0.95
    else:
        # Penalize line length deviation from 10 syllables
        score = max(0.0, 1.0 - abs(10 - syllables) * 0.2)

    return syllables, pattern, round(score, 2)

def evaluate_verse_passage(text: str) -> Dict[str, float]:
    """
    Evaluates a multiline speech passage for metrical regularity.
    Returns dictionary with line count, average syllables, and overall regularity score.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return {
            "line_count": 0, 
            "avg_syllables": 0.0, 
            "pentameter_regularity": 0.0
        }

    scores = []
    syllable_counts = []

    for line in lines:
        s_count, _, score = scan_line(line)
        syllable_counts.append(s_count)
        scores.append(score)

    return {
        "line_count": len(lines),
        "avg_syllables": round(sum(syllable_counts) / len(syllable_counts), 2),
        "pentameter_regularity": round(sum(scores) / len(scores), 2)
    }

if __name__ == "__main__":
    test_line = "A little more than kin, and less than kind."
    sylls, pat, sc = scan_line(test_line)
    print(f"Testing line: '{test_line}'")
    print(f"Syllables: {sylls} | Pattern: {pat} | Score: {sc:.0%}")