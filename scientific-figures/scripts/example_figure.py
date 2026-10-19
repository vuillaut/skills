"""Reference example: a 2-panel double-column figure that passes scifig.check().

Run:  python example_figure.py [outdir] [profile]
Copy the patterns, not the data.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import scifig  # noqa: E402

outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("figures")
profile = sys.argv[2] if len(sys.argv) > 2 else "journal"
scifig.use(profile)
C = scifig.OKABE_ITO

rng = np.random.default_rng(1)
E = np.logspace(-1, 2, 25)                       # energy grid
model = 3e-11 * E ** -2.3
data = model * rng.normal(1.0, 0.08, E.size)
err = 0.08 * model

fig, (ax1, ax2) = scifig.figure("double", height=70, ncols=2,
                                gridspec_kw={"width_ratios": [1.15, 1]})

# ---- panel a: log-log spectrum, labelled with units ----------------------
ax1.errorbar(E, data, yerr=err, fmt="o", color=C["blue"], label="Data")
ax1.plot(E, model, "-", color=C["vermillion"], label="Power-law fit")
ax1.set(xscale="log", yscale="log")
scifig.set_labels(ax1, x=("Energy", "TeV"), y=("Flux", "cm$^{-2}$ s$^{-1}$ TeV$^{-1}$"))
ax1.legend(loc="upper right")
scifig.panel_label(ax1, index=0)

# ---- panel b: image with a labelled colorbar -----------------------------
x, y = np.meshgrid(np.linspace(-2, 2, 120), np.linspace(-2, 2, 120))
z = np.exp(-(x ** 2 + y ** 2) / 0.8) + 0.05 * rng.normal(size=x.shape)
im = ax2.imshow(z, extent=(-2, 2, -2, 2), origin="lower", cmap=scifig.cmap("sequential"))
scifig.set_labels(ax2, x=("Offset in RA", "deg"), y=("Offset in Dec", "deg"))
cb = fig.colorbar(im, ax=ax2, pad=0.02)
cb.set_label("Excess counts (counts per pixel)")
scifig.panel_label(ax2, index=1)

issues = scifig.save(fig, outdir / "example_figure")
sys.exit(1 if issues else 0)
