"""Reusable Matplotlib style helpers for the scientific-python-figures Claude Code skill."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt

PALETTE = {
    "blue": "#2878B5",
    "orange": "#D97732",
    "green": "#2E7D32",
    "purple": "#7861BF",
    "teal": "#168C8C",
    "charcoal": "#263238",
    "grey": "#7A8793",
    "light_grey": "#D9E0E5",
}

# Keep colors stable across figures. Use marker/linestyle differences as well.
SERIES_COLORS = [PALETTE[k] for k in ("blue", "orange", "green", "purple", "teal", "grey")]


def apply_style(*, base_font_size: float = 9, grid: bool = True) -> None:
    """Apply the shared figure style to Matplotlib's rcParams."""
    mpl.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "text.color": PALETTE["charcoal"],
        "axes.labelcolor": PALETTE["charcoal"],
        "xtick.color": PALETTE["charcoal"],
        "ytick.color": PALETTE["charcoal"],
        "axes.edgecolor": PALETTE["grey"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": grid,
        "axes.axisbelow": True,
        "grid.color": PALETTE["light_grey"],
        "grid.linewidth": 0.6,
        "grid.alpha": 0.8,
        "lines.linewidth": 2.0,
        "lines.markersize": 5,
        "font.family": "sans-serif",
        "font.size": base_font_size,
        "axes.labelsize": base_font_size + 1,
        "axes.titlesize": base_font_size + 1,
        "xtick.labelsize": max(7, base_font_size - 1),
        "ytick.labelsize": max(7, base_font_size - 1),
        "legend.fontsize": max(7, base_font_size - 1),
        "legend.frameon": False,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def get_color(name: str) -> str:
    """Return a named palette color, raising a useful error for unknown names."""
    try:
        return PALETTE[name]
    except KeyError as exc:
        choices = ", ".join(PALETTE)
        raise ValueError(f"Unknown color {name!r}. Choose one of: {choices}") from exc


def new_figure(
    *,
    figsize: tuple[float, float] = (6.8, 4.2),
    nrows: int = 1,
    ncols: int = 1,
    sharex: bool = False,
    sharey: bool = False,
    **kwargs: Any,
):
    """Create a consistently styled figure and axes with constrained layout."""
    apply_style()
    return plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=figsize,
        sharex=sharex,
        sharey=sharey,
        layout="constrained",
        **kwargs,
    )


def save_figure(
    fig,
    path: str | Path,
    *,
    formats: tuple[str, ...] | None = None,
    dpi: int = 300,
) -> list[Path]:
    """Save a figure in one or more formats and return the written paths."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower().lstrip(".")
    stem = path.with_suffix("") if suffix else path
    selected = formats or ((suffix,) if suffix else ("pdf", "png"))
    written = []
    for fmt in selected:
        output = stem.with_suffix(f".{fmt}")
        kwargs = {"bbox_inches": "tight"}
        if fmt.lower() not in {"pdf", "svg", "ps", "eps"}:
            kwargs["dpi"] = dpi
        fig.savefig(output, format=fmt, **kwargs)
        written.append(output)
    return written
