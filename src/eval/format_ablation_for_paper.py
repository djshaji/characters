import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLOTS_DIR = PROJECT_ROOT / "paper"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

labels = ["Unconstrained\n(Baseline)", "Chronological\nRAG", "Full Characters\n(Stage Witness)"]

# Reconciled empirical numbers from Table 2 audit
els = [50, 40, 20]
ler = [20, 30, 30]
reg = [16, 4, 8]

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
print(f"Saved reconciled Figure 1 to: {out_pdf.resolve()}")