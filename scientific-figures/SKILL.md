---
name: scientific-figures
description: Produce publication-grade scientific figures (matplotlib) that meet journal standards - mandatory units on every axis, large readable labels, colour-blind-safe palette, correct physical size, embedded fonts, vector export. Use this skill whenever the user asks for a plot, figure, chart, spectrum, histogram, light curve, map, multi-panel figure, or any visualisation intended for a paper, preprint, thesis, poster, slide or report - even if they do not say "publication quality". Also use it when reviewing, restyling or fixing an existing figure script, choosing colours or colormaps, or preparing figures for Nature, A&A, AAS/ApJ, MNRAS, PRD, IEEE or similar journals.
---

# Scientific figures

A figure is a graphical interface between people and data (Rougier et al. 2014). It must be
readable at **final printed size**, honest, accessible to colour-blind readers, and every axis must
say **what** is plotted and **in which unit**.

This skill ships a tested helper module, `scripts/scifig.py`, that applies the style and **refuses or
flags** the mistakes that most often get figures bounced by referees and art editors.

## Workflow (follow in order)

1. **Pin down the message and the target.** One figure = one message. Ask (once, only if unknown):
   which journal / column width? colour or print? If unknown, use profile `journal` (88 mm / 180 mm).
   Nature-family journals -> profile `nature`. Slides/posters -> profile `slide`.
2. **Write one script per figure**, data in -> figure out, fixed random seed, no manual editing
   afterwards. The script is the figure's provenance.
3. **Build with `scifig`** (below): `use()` -> `figure()` -> plot -> `set_labels()` -> `save()`.
4. **Lint.** `scifig.save()` runs `scifig.check()`; fix every reported issue. Never silence it.
5. **Look at the result.** Open the PNG with the image viewer at its actual size and verify the
   checklist in `references/checklist.md`. A passing linter is necessary, not sufficient (it cannot
   judge clutter, misleading scales or a confusing message).
6. **Deliver** `figure.pdf` (vector, fonts embedded) + `figure.png` (300 dpi) + the script, and
   propose a caption (template at the end).

## The non-negotiable rules

### R1 - Axes: quantity AND unit, every axis, always
- Every labelled **numeric** axis reads `Quantity (unit)`, e.g. `Energy (TeV)`, `Time (s)`,
  `Flux (cm$^{-2}$ s$^{-1}$)`. `scifig.set_labels()` **raises** if the unit is missing.
- **No physical unit? Decide by axis type** (never guess, never invent a fake unit):

  | Axis type | Write | Call |
  |---|---|---|
  | measured quantity | `Energy (TeV)` | `("Energy", "TeV")` |
  | counts | `Counts per bin (counts)` | `("Counts per bin", "counts")` |
  | arbitrary-scale intensity | `Normalised intensity (a.u.)` | `("Normalised intensity", "a.u.")` |
  | ratio / efficiency / fraction | `Data / model (dimensionless)`, or `Efficiency (%)` | `("Data / model", "dimensionless")` |
  | significance | `Significance ($\sigma$)` | `("Significance", r"$\sigma$")` |
  | pixels | `x (px)` | `("x", "px")` |
  | **categorical** (model names, telescope types, classes) or an **index** (bin index, run ID) | `Model`, `Bin index` - no brackets | `("Model", scifig.NO_UNIT)` |

  `NO_UNIT` is *only* for axes whose ticks are names, classes or indices. It is never a way to skip a
  unit on a measured number: if the ticks are values of a quantity, a unit (or `dimensionless`/`a.u.`)
  is required. The linter also auto-detects string-category axes (e.g. `ax.bar(["A","B"], ...)`), but
  a **label is still mandatory** on them (the name of the variable).
- Pick **one** unit convention per paper and keep it: parentheses `E (TeV)` (default, Nature/IEEE
  style), brackets `E [TeV]` (common in astronomy), or ISO 80000-1 `E / TeV`. There is no universal
  rule; consistency matters (`style="bracket"` / `"slash"` in `set_labels`). Follow the target
  journal if it states one.
- Use SI or the field's standard units; use the symbol, not the word (`TeV`, not `tera-electronvolts`).
- Log axes: label the *physical* quantity and unit (`Energy (TeV)`), not `log10(E)`, unless the
  plotted variable really is a logarithm (`$\log_{10}(E / \mathrm{TeV})$`). Keep minor ticks on.
- Avoid matplotlib's invisible offset text (`1e-12` in the corner): fold the scale into the data or
  the unit (`Flux ($10^{-12}$ cm$^{-2}$ s$^{-1}$)`).
- Colorbars are axes: they need `Quantity (unit)` too. Images with a world coordinate system need
  labelled, unit-bearing axes (`RA (deg)`, `Offset (arcmin)`); never ship an image with bare pixel
  ticks unless the unit is `px`.
- Shared axes in a grid: label the outer axes only; the linter understands `sharex/sharey`.
- Ticks must be **clear and well-defined**: inward major + minor ticks on a full frame (default
  style), 4-6 major ticks per axis, tick labels never overlapping, axis limits that end on
  sensible values, a reference line (zero, unity) for residuals/ratios.

### R2 - Legibility: design at the final size
- Create the figure at its **real physical width** (`scifig.figure("single")` = 88 mm,
  `"double"` = 180 mm) and set font sizes *in points at that size*. Never draw a 12-inch figure and
  shrink it in LaTeX: text then ends up unreadable.
- Sizes (pt at final size), from the bundled profiles:

  | Element | `journal` | `nature` | `slide` |
  |---|---|---|---|
  | axis labels | 9 | 7 | 16 |
  | tick labels | 8 | 6 | 14 |
  | legend / annotations | 8 | 6 | 14 |
  | panel letters (bold) | 10 | 8 | 18 |
  | data line width | 1.4 | 1.0 | 2.5 |
  | **linter floor** | 7 | 5 | 12 |

  Journal guides converge on ~8 pt at final size (IUCr; ASA/CSSA/SSSA handbook); Nature mandates
  5-7 pt and 8 pt bold panel labels. Use the *largest* size the target allows - "large enough to be
  read" is the rule, so default to the `journal` sizes unless Nature-family.
- One sans-serif family everywhere (Arial/Helvetica; the module falls back to metric-compatible
  Liberation/Nimbus Sans). Math is set in the same family. No titles inside the figure: put them in
  the caption. No text rotated except the y-label.
- Lines >= 0.5 pt (data 1-2 pt), markers 3-6 pt larger than the line width, error bars visible.
- Words in figure text: sentence case. A&A requires **lower case** for words in figures.

### R3 - Colour: safe, meaningful, redundant
- Categorical data: the Okabe-Ito/Wong palette, already the default cycle
  (`scifig.OKABE_ITO`). Measured with a colour-vision-deficiency simulation: all 8 colours stay
  distinguishable under deuteranopia, protanopia and tritanopia (min dE76 >= 16).
- **But** in greyscale several pairs collide (orange ~ sky blue, vermillion ~ green ~ purple).
  So for > 2 series, or any figure that may be printed in B&W, **add a second channel**:
  `for st, ... in zip(scifig.series_styles(n), ...): ax.plot(..., **st)` (colour + linestyle + marker).
- Continuous data: **perceptually uniform** maps only - `scifig.cmap("sequential")` (batlow if
  `cmcrameri` is installed, else viridis), `"diverging"` only when the data has a meaningful centre
  (use `TwoSlopeNorm`/`CenteredNorm` to pin it), `"cyclic"` for phase/angle.
- **Never** jet/rainbow/hsv, **never** red-green as the only contrast (Crameri et al. 2020).
- Same quantity/model/instrument = same colour in every figure of the paper.
- Text/lines need >= 3:1 contrast against the background; avoid pale yellow on white for thin lines.

### R4 - Honesty of the data (Rougier rule 7)
- Show uncertainty (error bars/bands) and state what it is (1 sigma, 68 % CL, std, SEM) and `n` in
  the caption. Show the raw data when n is small (points over box/violin).
- Bars start at zero. No truncated axes without a visible break. No 3-D bars/pies, no dual y-axes
  unless unavoidable (then colour-match each axis to its curve).
- Compared panels share axis limits (`sharex/sharey`) or say loudly that they don't.
- Binning, smoothing, clipping and colour-scale limits are part of the result: state them.
- Upper limits: arrows/markers distinct from measurements. Log scale: no zeros/negatives silently dropped.

### R5 - Layout and economy
- Panel letters via `scifig.panel_label(ax, index=i)` (bold; lowercase for `nature`).
  Panels in alphabetical reading order.
- Remove chartjunk: no gridlines by default (a light one only if readers must read off values),
  no background fills, no shadows, no decorative frames. Prefer **direct labels** to legends when
  <= 4 curves. Cut empty space around the axes (journals reduce figures, wasted margins shrink text).
- Related panels share style, size and scales. Same fonts, same line weights across the whole paper.
- Complex figure -> split in two, or move details to a supplementary figure.

### R6 - Export
- `scifig.save(fig, "figures/name")` -> `name.pdf` (vector, fonts TrueType-42 embedded, editable)
  + `name.png` (300 dpi). Do **not** use `bbox_inches="tight"`: it silently changes the physical
  size and invalidates R2.
- Rasterise only genuinely raster content (images, millions of points: `rasterized=True`), keep
  text and axes as vector. RGB colour space. Line art 600+ dpi if a journal wants a bitmap.
- Name files `Fig1_description.pdf`-style if the journal asks; keep < 10 MB (Nature limit).
- Re-check the journal page: specs change (see `references/journal-specs.md`).

## Using the module

```python
import sys; sys.path.insert(0, ".claude/skills/scientific-figures/scripts")  # or ~/.claude/skills/...
import numpy as np, scifig

scifig.use("journal")                       # or "nature", "slide"; frame=False for open axes
fig, (a, b) = scifig.figure("double", height=70, ncols=2)

a.errorbar(E, F, yerr=dF, fmt="o", color=scifig.OKABE_ITO["blue"], label="Data")
a.set(xscale="log", yscale="log")
scifig.set_labels(a, x=("Energy", "TeV"), y=("Flux", "cm$^{-2}$ s$^{-1}$ TeV$^{-1}$"))
scifig.panel_label(a, index=0)

im = b.imshow(Z, cmap=scifig.cmap("sequential"))
scifig.set_labels(b, x=("RA offset", "deg"), y=("Dec offset", "deg"))
fig.colorbar(im, ax=b).set_label("Excess (counts per pixel)")
scifig.panel_label(b, index=1)

scifig.save(fig, "figures/fig_spectrum")    # lint + PDF + PNG; returns list of issues
```

- Full working reference (passes the linter): `scripts/example_figure.py`.
- With astropy: `scifig.set_labels(ax, x=("Energy", u.TeV), ...)` accepts `Unit` objects.
- Export the style for non-Python use: `python scripts/scifig.py my.mplstyle journal` then
  `plt.style.use("my.mplstyle")` (unit enforcement and the linter need the module, not the file).
- If the project cannot import the module (other plotting library: R/ggplot2, Plotly, TikZ/pgfplots),
  apply the **same rules and numbers** from this document; see `references/color.md` for hex codes.
- `scifig.check(fig)` can be run on any matplotlib figure, including those built without `scifig`.

## Anti-patterns -> fix

| Seen in the wild | Fix |
|---|---|
| `ax.set_xlabel("Energy")` | `set_labels(ax, x=("Energy","TeV"), ...)` |
| 10 x 6 in figure shrunk to a column | `scifig.figure("single")`, size fonts at final size |
| default matplotlib blue/orange, `jet`, `rainbow` | Okabe-Ito + `scifig.cmap()` |
| legend of 8 near-identical colours | small multiples, direct labels, or `series_styles` (max 8) |
| `1e-12` offset text in the corner | scale data, put factor in the unit |
| rotated, crowded tick labels | fewer ticks, `MaxNLocator(5)`, wider figure |
| title inside the plot | move to the caption |
| `bbox_inches="tight"` | drop it; fix margins via constrained layout |
| raster-only PDF with fuzzy text | vector text; `rasterized=True` only on dense artists |
| red-green only contrast | blue/vermillion + redundant marker/linestyle |

## Caption template (Rougier rule 4: captions are not optional)

> **Short declarative title (the message).** What is plotted (symbols/colours/line styles ->
> quantities and units); data source and selection; what error bars/bands mean (e.g. 1 sigma) and
> `n`; binning/smoothing/colour-scale choices; panel-by-panel notes (a), (b); pointer to the
> script/data (DOI or repository path).

## References (load on demand)

- `references/journal-specs.md` - column widths, font/size/resolution rules per journal, with sources.
- `references/color.md` - palettes, hex codes, colormap choice, CVD/greyscale measurements.
- `references/checklist.md` - final pre-submission checklist to run through on the PNG.

Sources: Rougier, Droettboom & Bourne (2014) *Ten Simple Rules for Better Figures*, PLOS Comput Biol
10(9):e1003833; Wong (2011) Nat Methods 8:441; Crameri, Shephard & Heron (2020) Nat Commun 11:5444;
Nature Research figure guide; A&A figure instructions; ISO 80000-1 quantity calculus.
