"""scifig — publication-grade matplotlib figures with enforced axis units.

Usage
-----
    import sys; sys.path.insert(0, "<skill_dir>/scripts")
    import scifig

    scifig.use("journal")                       # apply the style profile
    fig, ax = scifig.figure("single")           # 88 mm wide, real physical size
    ax.plot(E, F)
    scifig.set_labels(ax, x=("Energy", "TeV"), y=("Flux", "cm$^{-2}$ s$^{-1}$"))
    scifig.save(fig, "figures/spectrum")        # vector PDF + 300 dpi PNG, then lint

Design rules enforced here (see SKILL.md):
  * every numeric axis must carry a quantity AND a unit (``set_labels`` refuses otherwise);
    categorical/index axes are declared explicitly with ``NO_UNIT``;
  * font sizes are specified at FINAL printed size (figure is created at real size);
  * colour-vision-deficiency-safe default cycle (Okabe-Ito / Wong);
  * fonts embedded as TrueType (Type 42) so journals can edit text.

Only depends on matplotlib + numpy. astropy / cmcrameri are used if present.
"""
from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

__all__ = [
    "OKABE_ITO", "PROFILES", "NO_UNIT", "use", "figure", "set_labels", "unit_str",
    "panel_label", "cmap", "series_styles", "check", "save", "mm", "write_mplstyle",
]

MM_PER_INCH = 25.4


def mm(x: float) -> float:
    """Millimetres -> inches."""
    return x / MM_PER_INCH


# --------------------------------------------------------------------------
# Colour: Okabe & Ito (2008) / Wong (2011, Nature Methods 8:441) palette.
# Order is chosen for line plots on white: strongest contrast first,
# yellow (low contrast on white) last.
# --------------------------------------------------------------------------
OKABE_ITO = {
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "green": "#009E73",
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "purple": "#CC79A7",
    "black": "#000000",
    "yellow": "#F0E442",
}
CYCLE = list(OKABE_ITO.values())


# --------------------------------------------------------------------------
# Profiles. All sizes in points AT FINAL PRINTED SIZE.
# widths in mm. `min_font` is the floor used by check().
# --------------------------------------------------------------------------
PROFILES = {
    # Generic journal figure (A&A, AAS/ApJ, MNRAS, PRD, IEEE-like): 88 mm / 180 mm
    "journal": dict(
        single=88, double=180, max_height=230,
        font=8.0, label=9.0, tick=8.0, legend=8.0, panel=10.0, panel_case="upper",
        lw=1.4, axes_lw=0.8, marker=4.5, min_font=7.0,
        unit_style="paren",
    ),
    # Nature portfolio: text must be 5-7 pt, panel labels 8 pt bold lowercase.
    "nature": dict(
        single=89, double=183, max_height=170,
        font=6.0, label=7.0, tick=6.0, legend=6.0, panel=8.0, panel_case="lower",
        lw=1.0, axes_lw=0.6, marker=3.5, min_font=5.0,
        unit_style="paren",
    ),
    # Slides / posters: viewed from a distance -> big text, thick lines.
    "slide": dict(
        single=160, double=300, max_height=170,
        font=14.0, label=16.0, tick=14.0, legend=14.0, panel=18.0, panel_case="upper",
        lw=2.5, axes_lw=1.5, marker=8.0, min_font=12.0,
        unit_style="paren",
    ),
}

_ACTIVE = {"name": "journal"}  # profile currently applied


def _font_stack():
    # Arial/Helvetica requested by Nature/IUCr/etc.; fall back to metric-compatible clones.
    return ["Arial", "Helvetica", "Liberation Sans", "Nimbus Sans", "DejaVu Sans"]


def use(profile: str = "journal", *, frame: bool = True, usetex: bool = False) -> dict:
    """Apply a style profile to matplotlib rcParams. Returns the profile dict.

    frame=True  : full box with inward ticks on all four sides (astro/physics look).
    frame=False : open axes (top/right spines removed) — better for bar/box plots.
    """
    if profile not in PROFILES:
        raise KeyError(f"unknown profile {profile!r}; choose from {list(PROFILES)}")
    p = PROFILES[profile]
    _ACTIVE["name"] = profile

    rc = {
        # fonts ---------------------------------------------------------------
        "font.family": "sans-serif",
        "font.sans-serif": _font_stack(),
        "font.size": p["font"],
        "axes.labelsize": p["label"],
        "axes.titlesize": p["label"],
        "xtick.labelsize": p["tick"],
        "ytick.labelsize": p["tick"],
        "legend.fontsize": p["legend"],
        "figure.labelsize": p["label"],
        "mathtext.fontset": "custom",           # math in the same sans font as text
        "mathtext.rm": "sans",
        "mathtext.it": "sans:italic",
        "mathtext.bf": "sans:bold",
        "mathtext.cal": "sans",
        "mathtext.sf": "sans",
        "mathtext.tt": "monospace",
        "mathtext.default": "regular",
        "text.usetex": usetex,
        "pdf.fonttype": 42,                      # embed TrueType (editable text)
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        # lines & markers -------------------------------------------------------
        "lines.linewidth": p["lw"],
        "lines.markersize": p["marker"],
        "lines.markeredgewidth": 0.0,
        "errorbar.capsize": 2.0,
        "patch.linewidth": 0.8,
        "hatch.linewidth": 0.6,
        # axes ------------------------------------------------------------------
        "axes.linewidth": p["axes_lw"],
        "axes.prop_cycle": cycler(color=CYCLE),
        "axes.labelpad": 3.0,
        "axes.titlepad": 4.0,
        "axes.spines.top": frame,
        "axes.spines.right": frame,
        "axes.grid": False,
        "axes.axisbelow": True,
        "axes.unicode_minus": True,
        # ticks: inward, major + minor, on all sides (when framed) --------------
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": frame,
        "ytick.right": frame,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "xtick.major.size": 3.5 * p["axes_lw"] / 0.8 + 0.5,
        "ytick.major.size": 3.5 * p["axes_lw"] / 0.8 + 0.5,
        "xtick.minor.size": 2.0 * p["axes_lw"] / 0.8,
        "ytick.minor.size": 2.0 * p["axes_lw"] / 0.8,
        "xtick.major.width": p["axes_lw"],
        "ytick.major.width": p["axes_lw"],
        "xtick.minor.width": p["axes_lw"] * 0.75,
        "ytick.minor.width": p["axes_lw"] * 0.75,
        "xtick.major.pad": 3.0,
        "ytick.major.pad": 3.0,
        # legend ----------------------------------------------------------------
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "legend.borderaxespad": 0.4,
        # image / colour --------------------------------------------------------
        "image.cmap": "viridis",
        "image.interpolation": "nearest",
        # figure & export --------------------------------------------------------
        "figure.dpi": 150,                       # on-screen preview only
        "savefig.dpi": 300,
        "savefig.transparent": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 3.0 / 72,
        "figure.constrained_layout.w_pad": 3.0 / 72,
    }
    mpl.rcParams.update(rc)
    return p


def active_profile() -> dict:
    return PROFILES[_ACTIVE["name"]]


# --------------------------------------------------------------------------
# Figure creation at REAL physical size
# --------------------------------------------------------------------------
def figure(width="single", height=None, *, aspect=0.75, nrows=1, ncols=1, **kw):
    """Create fig, axes at true print size.

    width  : "single" | "double" | number in mm
    height : mm; default = width*aspect (capped at the profile's max height)
    Extra kwargs go to ``plt.subplots`` (sharex, gridspec_kw, ...).
    """
    p = active_profile()
    w = p[width] if isinstance(width, str) else float(width)
    h = float(height) if height is not None else w * aspect
    h = min(h, p["max_height"])
    return plt.subplots(nrows, ncols, figsize=(mm(w), mm(h)), **kw)


# --------------------------------------------------------------------------
# Units & labels
# --------------------------------------------------------------------------
class _NoUnit:
    """Sentinel: this axis has no unit because it is categorical / nominal / an index."""
    def __repr__(self):
        return "NO_UNIT"


NO_UNIT = _NoUnit()


def unit_str(unit) -> str:
    """Return a printable unit. Accepts str or an astropy Unit/Quantity-like object.

    Raises ValueError for None / empty string: a unit (or an explicit
    'dimensionless', 'a.u.', 'counts') is MANDATORY.
    """
    if unit is None:
        raise ValueError("unit is mandatory; pass 'dimensionless', 'a.u.' or 'counts' if truly unitless")
    if hasattr(unit, "to_string"):  # astropy.units.Unit
        s = unit.to_string("latex_inline")
        if s.strip("$ ") == "":
            return "dimensionless"
        return s
    s = str(unit).strip()
    if not s:
        raise ValueError("empty unit string; use 'dimensionless', 'a.u.' or 'counts' explicitly")
    return s


def _fmt(quantity: str, unit, style: str) -> str:
    u = unit_str(unit)
    if style == "paren":
        return f"{quantity} ({u})"
    if style == "bracket":
        return f"{quantity} [{u}]"
    if style == "slash":   # ISO 80000-1 "quantity / unit"
        return f"{quantity} / {u}" if " " not in u and "/" not in u else f"{quantity} / ({u})"
    raise ValueError("style must be 'paren', 'bracket' or 'slash'")


def set_labels(ax, x=None, y=None, *, style=None, **kw):
    """Label axes. x and y are (quantity, unit) tuples.

    Measured quantity      -> ("Energy", "TeV")            => "Energy (TeV)"
    Unitless but numeric   -> ("Efficiency", "dimensionless" | "a.u." | "counts")
    Categorical / index    -> ("Model", NO_UNIT)           => "Model"  (no brackets)

    NO_UNIT is ONLY for axes whose ticks are names, classes or indices (bar chart of
    models, telescope ID, bin index). For any numeric measured quantity a unit is
    mandatory and None/"" raises. Pass x=None / y=None only for an axis that is
    intentionally unlabeled (e.g. inner axes of a shared grid).
    """
    style = style or active_profile()["unit_style"]
    for axis, spec in (("x", x), ("y", y)):
        if spec is None:
            continue
        if not (isinstance(spec, (tuple, list)) and len(spec) == 2):
            raise TypeError(f"{axis}= must be a (quantity, unit) tuple, got {spec!r}; "
                            "use (quantity, NO_UNIT) for a categorical/index axis")
        if spec[1] is NO_UNIT:
            text = str(spec[0]).strip()
            if not text:
                raise ValueError(f"{axis}-axis quantity name is empty")
            marked = getattr(ax, "_scifig_nounit", set())
            marked.add(axis)
            ax._scifig_nounit = marked
        else:
            text = _fmt(spec[0], spec[1], style)
        getattr(ax, f"set_{axis}label")(text, **kw)
    return ax


def panel_label(ax, text=None, *, index=0, offset=(0, 3)):
    """Add a bold panel letter above the top-left corner of an axes.

    Case follows the active profile (Nature: lowercase; others: uppercase).
    """
    p = active_profile()
    if text is None:
        text = "abcdefghijklmnopqrstuvwxyz"[index]
    text = text.lower() if p["panel_case"] == "lower" else text.upper()
    return ax.annotate(
        text, xy=(0, 1), xycoords="axes fraction", xytext=offset,
        textcoords="offset points", ha="left", va="bottom",
        fontsize=p["panel"], fontweight="bold", annotation_clip=False,
    )


def cmap(kind="sequential"):
    """Perceptually-uniform, CVD-safe colormap. Never rainbow/jet.

    sequential -> cmcrameri 'batlow' if installed, else 'viridis'
    diverging  -> cmcrameri 'vik' if installed, else matplotlib 'berlin' (>=3.10) else 'RdBu_r'
    cyclic     -> cmcrameri 'romaO' if installed, else 'twilight'
    """
    try:
        import cmcrameri.cm as cmc
        return {"sequential": cmc.batlow, "diverging": cmc.vik, "cyclic": cmc.romaO}[kind]
    except Exception:
        pass
    names = {"sequential": ["viridis"], "diverging": ["berlin", "RdBu_r"], "cyclic": ["twilight"]}[kind]
    for n in names:
        try:
            return mpl.colormaps[n]
        except KeyError:
            continue
    raise KeyError(kind)


def series_styles(n: int) -> list[dict]:
    """Return n kwargs dicts (color + linestyle + marker) that stay distinguishable
    in greyscale and under colour-vision deficiency.

    Colour alone is NOT enough: measured in greyscale, orange/sky are identical
    (dL=0.01) and vermillion/green/purple collide. Use for any plot with > 2 series
    or whenever the figure may be printed in black and white:

        for st, (label, y) in zip(scifig.series_styles(len(curves)), curves.items()):
            ax.plot(x, y, label=label, **st)
    """
    if n > len(CYCLE):
        raise ValueError(f"{n} series > {len(CYCLE)} distinguishable colours: split into panels or use direct labels / small multiples")
    ls = ["-", "--", "-.", (0, (4, 1.5, 1, 1.5)), (0, (1, 1)), (0, (6, 2)), (0, (3, 1, 1, 1, 1, 1)), "-"]
    mk = ["o", "s", "^", "D", "v", "P", "X", "*"]
    return [dict(color=CYCLE[i], linestyle=ls[i], marker=mk[i], markevery=None) for i in range(n)]


# --------------------------------------------------------------------------
# Linter
# --------------------------------------------------------------------------
_UNIT_RE = re.compile(r"(\([^()]+(\([^()]*\))?[^()]*\)|\[[^\[\]]+\]|\s/\s\S+)\s*$")


def _has_unit(label: str) -> bool:
    return bool(_UNIT_RE.search(label.strip()))


_MARKUP_RE = re.compile(r"\\(mathdefault|mathrm|mathit|times|cdot|,|;|!)|[${}^_\\]")


def _is_categorical_axis(axis) -> bool:
    """True for axes whose ticks are names/classes rather than numbers (no unit possible)."""
    conv = axis.get_converter() if hasattr(axis, "get_converter") else getattr(axis, "converter", None)
    if conv is not None and "Category" in type(conv).__name__:
        return True
    texts = [t.get_text() for t in axis.get_ticklabels() if t.get_text()]
    if not texts:
        return False
    # categorical if every tick text contains a real word (>=2 consecutive letters) once
    # mathtext markup is stripped; numbers like 10^{-1} or 1e3 do not.
    def wordy(t):
        t = _MARKUP_RE.sub("", t)
        t = re.sub(r"(?<![A-Za-z])[eE](?=[+\-\u2212]?\d)", "", t)   # exponent marker
        return bool(re.search(r"[A-Za-z]{2,}", t))
    return all(wordy(t) for t in texts)


def _unit_exempt(ax, which: str) -> bool:
    """Axis legitimately has no unit: declared with NO_UNIT, or detected categorical."""
    if which in getattr(ax, "_scifig_nounit", set()):
        return True
    return _is_categorical_axis(ax.xaxis if which == "x" else ax.yaxis)


def _is_colorbar(ax) -> bool:
    return getattr(ax, "_colorbar", None) is not None or ax.get_label() == "<colorbar>"


def _axis_is_used(ax, which: str) -> bool:
    if not ax.axison:
        return False
    axis = ax.xaxis if which == "x" else ax.yaxis
    return any(t.get_visible() for t in axis.get_major_ticks()) or bool(axis.get_label().get_text())


def _shares_labeled(fig, ax, which: str) -> bool:
    """True if another axes shares this axis and carries a label (inner axes of a grid)."""
    grp = ax.get_shared_x_axes() if which == "x" else ax.get_shared_y_axes()
    for other in fig.axes:
        if other is not ax and grp.joined(ax, other):
            lab = other.get_xlabel() if which == "x" else other.get_ylabel()
            if lab:
                return True
    return False


def check(fig, profile=None, *, verbose=True, strict=False):
    """Lint a figure against the skill's hard rules. Returns list of issue strings.

    Checks: axis labels present with units, minimum font size, figure width,
    overlapping tick labels, text outside the canvas, hairline lines.
    strict=True raises ValueError if any issue is found.
    """
    p = PROFILES[profile] if profile else active_profile()
    issues: list[str] = []
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # width
    w_mm = fig.get_figwidth() * MM_PER_INCH
    if w_mm > p["double"] + 1.0:
        issues.append(f"figure is {w_mm:.0f} mm wide > double-column {p['double']} mm: it will be downscaled, shrinking all text")
    h_mm = fig.get_figheight() * MM_PER_INCH
    if h_mm > p["max_height"] + 1.0:
        issues.append(f"figure is {h_mm:.0f} mm tall > max {p['max_height']} mm")

    for i, ax in enumerate(fig.axes):
        tag = f"axes[{i}]"
        cbar = _is_colorbar(ax)
        for which in ("x", "y"):
            if not _axis_is_used(ax, which):
                continue
            # colorbars label only their long axis; the other is an empty scale
            if cbar and ((which == "x" and getattr(ax, "_colorbar", None) is not None and ax._colorbar.orientation == "vertical") or
                         (which == "y" and getattr(ax, "_colorbar", None) is not None and ax._colorbar.orientation == "horizontal")):
                continue
            lab = ax.get_xlabel() if which == "x" else ax.get_ylabel()
            if not lab:
                if _shares_labeled(fig, ax, which):
                    continue
                # image axes with ticks hidden are skipped by _axis_is_used
                issues.append(f"{tag}: {which}-axis has NO label (quantity + unit required)")
            elif not _has_unit(lab) and not _unit_exempt(ax, which):
                issues.append(f"{tag}: {which}-label {lab!r} has no unit — write 'Quantity (unit)'; use '(dimensionless)', '(a.u.)' or '(counts)' if unitless, or (name, NO_UNIT) if the axis is categorical/an index")

        # font sizes
        texts = list(ax.get_xticklabels()) + list(ax.get_yticklabels())
        texts += [ax.xaxis.label, ax.yaxis.label, ax.title]
        leg = ax.get_legend()
        if leg:
            texts += leg.get_texts()
        texts += list(ax.texts)
        for t in texts:
            if t.get_text() and t.get_visible() and t.get_fontsize() < p["min_font"] - 1e-6:
                issues.append(f"{tag}: text {t.get_text()[:25]!r} is {t.get_fontsize():.1f} pt < min {p['min_font']} pt")
                break

        # hairlines
        for ln in ax.get_lines():
            if ln.get_visible() and ln.get_linestyle() != "None" and ln.get_linewidth() < 0.5:
                issues.append(f"{tag}: line width {ln.get_linewidth():.2f} pt < 0.5 pt (disappears in print)")
                break

        # overlapping tick labels
        for which, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            boxes = [t.get_window_extent(renderer) for t in axis.get_ticklabels() if t.get_visible() and t.get_text()]
            for a in range(len(boxes)):
                for b in range(a + 1, len(boxes)):
                    if boxes[a].overlaps(boxes[b]) and boxes[a].width > 0 and boxes[b].width > 0:
                        # tolerate 1px
                        ix = min(boxes[a].x1, boxes[b].x1) - max(boxes[a].x0, boxes[b].x0)
                        iy = min(boxes[a].y1, boxes[b].y1) - max(boxes[a].y0, boxes[b].y0)
                        if ix > 1 and iy > 1:
                            issues.append(f"{tag}: {which} tick labels overlap — reduce ticks, rotate, or enlarge the figure")
                            break
                else:
                    continue
                break

        # axis labels / texts clipped by canvas
        fb = fig.bbox
        for t in (ax.xaxis.label, ax.yaxis.label):
            if t.get_text():
                bb = t.get_window_extent(renderer)
                if bb.x0 < fb.x0 - 1 or bb.y0 < fb.y0 - 1 or bb.x1 > fb.x1 + 1 or bb.y1 > fb.y1 + 1:
                    issues.append(f"{tag}: label {t.get_text()[:25]!r} is clipped by the figure edge")

    if verbose:
        if issues:
            print(f"[scifig.check] {len(issues)} issue(s):", file=sys.stderr)
            for s in issues:
                print("  - " + s, file=sys.stderr)
        else:
            print("[scifig.check] OK — units, sizes, overlaps all pass", file=sys.stderr)
    if strict and issues:
        raise ValueError("figure failed lint:\n" + "\n".join(issues))
    return issues


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
def save(fig, stem, formats=("pdf", "png"), *, dpi=300, lint=True, strict=False):
    """Save ``stem.pdf`` (vector, fonts embedded) and ``stem.png`` (300 dpi).

    Does NOT use bbox_inches='tight' (it silently changes the physical size).
    Runs check() first unless lint=False.
    """
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    issues = check(fig, strict=strict) if lint else []
    for fmt in formats:
        kw = {"dpi": dpi} if fmt.lower() in {"png", "tif", "tiff", "jpg", "jpeg"} else {}
        fig.savefig(f"{stem}.{fmt}", format=fmt, **kw)
    return issues


def write_mplstyle(path, profile="journal", **kw):
    """Dump the current profile as a .mplstyle file (for `plt.style.use(path)`)."""
    use(profile, **kw)
    keys = [
        "font.family", "font.sans-serif", "font.size", "axes.labelsize", "axes.titlesize",
        "xtick.labelsize", "ytick.labelsize", "legend.fontsize", "mathtext.fontset", "mathtext.rm",
        "mathtext.it", "mathtext.bf", "mathtext.default", "pdf.fonttype", "ps.fonttype",
        "lines.linewidth", "lines.markersize", "axes.linewidth", "axes.spines.top", "axes.spines.right",
        "xtick.direction", "ytick.direction", "xtick.top", "ytick.right", "xtick.minor.visible",
        "ytick.minor.visible", "xtick.major.size", "ytick.major.size", "xtick.minor.size",
        "ytick.minor.size", "xtick.major.width", "ytick.major.width", "legend.frameon",
        "image.cmap", "savefig.dpi", "figure.constrained_layout.use",
    ]
    lines = [f"# scifig profile: {profile} (auto-generated by scifig.write_mplstyle)"]
    for k in keys:
        v = mpl.rcParams[k]
        if isinstance(v, list):
            v = ", ".join(map(str, v))
        lines.append(f"{k}: {v}")
    # '#' starts a comment in .mplstyle files -> hex colours must be written WITHOUT it
    lines.append("axes.prop_cycle: cycler('color', [" + ", ".join(f"'{c.lstrip('#')}'" for c in CYCLE) + "])")
    Path(path).write_text("\n".join(lines) + "\n")
    return path


if __name__ == "__main__":
    # `python scifig.py out.mplstyle [profile]`
    out = sys.argv[1] if len(sys.argv) > 1 else "scifig-journal.mplstyle"
    prof = sys.argv[2] if len(sys.argv) > 2 else "journal"
    print(write_mplstyle(out, prof))
