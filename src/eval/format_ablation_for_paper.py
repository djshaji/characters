import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
JSON_PATH = PROJECT_ROOT / "data/eval_results/ablation_benchmark.json"
PLOTS_DIR = PROJECT_ROOT / "paper"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def export_results():
    if not JSON_PATH.exists():
        print(f"Error: {JSON_PATH} not found. Run 'python src/eval/run_ablation_benchmark.py' first.")
        return

    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    conditions = ["unconstrained", "chrono_only", "full_characters"]
    labels = ["Unconstrained\n(Baseline)", "Chronological\nRAG", "Full Characters\n(Witness Graph)"]

    els = [summary.get(c, {}).get("epistemic_leak_rate", 0) * 100 for c in conditions]
    ler = [summary.get(c, {}).get("lexical_echo_rate", 0) * 100 for c in conditions]
    reg = [summary.get(c, {}).get("avg_regularity", 0) * 100 for c in conditions]

    # --- 1. PRINT LATEX TABLE (No formatting conflicts with braces) ---
    print("\n" + "="*50)
    print("LATEX TABLE SNIPPET (Copy into Section 4.2 of sn-article.tex):")
    print("="*50)
    
    table_tex = (
        r"\begin{table}[ht]" + "\n"
        r"\caption{Ablation study across 10 adversarial dramatic irony probes}\label{tab:ablation}%" + "\n"
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccc@{\extracolsep{\fill}}}" + "\n"
        r"\toprule" + "\n"
        r"\textbf{System Configuration} & \textbf{Epistemic Leak ($ELS$)} & \textbf{Lexical Echo ($LER$)} & \textbf{Iambic Alignment} \\" + "\n"
        r"\midrule" + "\n"
        f"Condition A: Unconstrained Baseline          & {els[0]:.0f}\\% & {ler[0]:.0f}\\% & {reg[0]:.0f}\\% \\\\\n"
        f"Condition B: Chronological RAG (Scene only)  & {els[1]:.0f}\\% & {ler[1]:.0f}\\% & {reg[1]:.0f}\\% \\\\\n"
        f"Condition C: Full \\textsc{{Characters}} (Stage Witness) & \\textbf{{{els[2]:.0f}\\%}} & {ler[2]:.0f}\\% & \\textbf{{{reg[2]:.0f}\\%}} \\\\\n"
        r"\botrule" + "\n"
        r"\end{tabular*}" + "\n"
        r"\end{table}"
    )
    print(table_tex)

    # --- 2. GENERATE FIGURE 2 (GROUPED BAR CHART) ---
    x = np.arange(len(labels))
    width = 0.25

    plt.figure(figsize=(7.5, 4.2))
    plt.bar(x - width, els, width, label="Epistemic Leak Rate (ELS)", color="#c93b2b")
    plt.bar(x, ler, width, label="Lexical Echo Rate (LER)", color="#e69f00")
    plt.bar(x + width, reg, width, label="Iambic Alignment", color="#2b5c8f")

    plt.ylabel("Percentage (%)", fontsize=11)
    plt.title("Ablation Analysis: Epistemic Leakage vs. Metrical Regularity", fontsize=12, pad=12)
    plt.xticks(x, labels, fontsize=10)
    plt.ylim(0, 100)
    plt.legend(frameon=True, loc="upper right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    out_pdf = PLOTS_DIR / "fig2_ablation_comparison.pdf"
    plt.savefig(out_pdf, dpi=300)
    print(f"\nSaved Figure 2 to: {out_pdf.resolve()}")

if __name__ == "__main__":
    export_results()