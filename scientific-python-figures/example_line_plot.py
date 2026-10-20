"""Example: publication-style line plot with a supplied uncertainty interval.

Replace the illustrative arrays and uncertainty definition with real measurements.
Never infer or fabricate uncertainty values for real data.
"""
import numpy as np
import matplotlib.pyplot as plt

from scientific_style import PALETTE, apply_style, save_figure

# Illustrative synthetic data only.
x = np.logspace(1, 4, 18)
y = 0.18 * (x / 10) ** -0.28
uncertainty = 0.15 * y

apply_style()
fig, ax = plt.subplots(figsize=(3.5, 2.8), layout="constrained")
ax.plot(x, y, color=PALETTE["blue"], marker="o", markersize=4, label="Model A")
ax.fill_between(
    x, y - uncertainty, y + uncertainty,
    color=PALETTE["blue"], alpha=0.18, linewidth=0,
    label="Illustrative uncertainty band",
)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Energy [GeV]")
ax.set_ylabel("Fractional energy resolution")
ax.legend()
ax.grid(True, which="major")
ax.grid(False, which="minor")
save_figure(fig, "figures/example.pdf", formats=("pdf", "png"))
plt.close(fig)
