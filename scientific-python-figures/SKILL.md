---
name: scientific-python-figures
description: Create, review, or refactor publication-quality scientific figures in Python. Use when working with Matplotlib, Seaborn, scientific plots, statistical visualizations, instrument schematics, or figure export for papers, reports, and presentations.
---

# Scientific Python Figures

Create scientific figures that are accurate, legible, accessible, reproducible, and visually consistent. Use a restrained modern-journal aesthetic: white background, charcoal text, a small colorblind-aware palette, clean typography, light visual scaffolding, and explicit communication of uncertainty.

Visual polish must never obscure, exaggerate, or alter the scientific evidence.

## Workflow

1. **Understand the scientific task**
   - Identify the claim or comparison the figure should communicate, the audience, and the final medium (paper, slides, report, web).
   - Inspect the data and plotting code before changing them. Preserve scientific calculations unless asked to audit them.
   - Determine whether observations are independent, paired, grouped, weighted, censored, or otherwise structured. Do not assume an ordinary mean or independent errors are appropriate.
   - Ask a concise clarification only if a missing detail changes the scientific meaning. Otherwise choose sensible defaults and state material assumptions.

2. **Choose the right visual encoding**
   - Trends over an ordered continuous variable: line or scatter plot; show uncertainty where available.
   - Distributions: histogram, ECDF, or density plot. State normalization and binning choices where they affect interpretation.
   - Relationships: scatter plot; avoid connecting unrelated observations. Use transparency or density summaries for overplotting.
   - Model performance: use domain-appropriate metrics and baselines; show uncertainty or repeated-run variation where available.
   - Classification: confusion matrix with labeled axes and explicit normalization; report class order.
   - Spatial or image-like data: use a perceptually uniform sequential map for ordered values and a diverging map only when a meaningful center exists.
   - Instrument or architecture diagrams: use vector shapes, consistent line weights, clear labels, and a legend only when necessary.
   - Prefer the simplest plot that answers the scientific question. Do not add a chart type merely for visual variety.

3. **Apply the shared style**
   - Prefer the supplied `scientific_style.py` helper when it is available in the project. Otherwise implement the specification below using Matplotlib `rcParams`.
   - Keep the same meaning-to-color mapping across a paper, notebook, or project. Never assign colors based on incidental plotting order.
   - Use `constrained_layout=True` or `layout="constrained"` for new figures; use `tight_layout()` only when it behaves better for a specific figure.
   - Keep plot functions focused on visualization. Put data transformations and scientific calculations in separately testable functions.

4. **Validate the figure**
   - Check axis labels, units, scales, legend text, panel labels, color mapping, and uncertainty definitions.
   - Check whether log axes are justified and whether zero or negative values are valid. Never silently drop nonpositive data to make a log plot work.
   - Check for misleading axis limits, hidden data, inappropriate smoothing, overplotting, and ambiguous normalization.
   - Render at the final intended size and inspect the output. If possible, inspect both vector and raster exports.
   - Do not invent values, error bars, confidence intervals, statistical significance, or metadata absent from the data.

5. **Export and make reproducible**
   - Prefer PDF or SVG for line art, text, and mixed vector plots. Use PNG for raster-heavy plots or when required by a submission system.
   - For raster output, use at least 300 dpi for print; use higher resolution when small text or fine detail requires it.
   - Set output dimensions deliberately. Do not rely on the notebook display size.
   - Use deterministic plotting settings and explicit inputs. Avoid relying on hidden global state or whichever color cycle happens to be active.
   - Save figures and, when useful, the plotting script, configuration, and data provenance alongside the result.

## Style specification

### Overall look
- Background: white (`#FFFFFF`); no decorative gradients, shadows, 3D effects, or chartjunk.
- Text: charcoal (`#263238`); secondary text and spines should be muted, not low-contrast.
- Grid: subtle horizontal/major gridlines only when they help read values. Grid behind data.
- Spines: hide top and right spines by default; keep remaining spines thin.
- Ticks: restrained tick count; inward/outward direction may follow the target journal, but be consistent.
- Line widths: typical data line 1.8–2.2 pt; reference line 1.2–1.5 pt; axes/spines around 0.7–0.9 pt.
- Markers: typical size 4–6 pt; use distinct shapes as well as colors when comparisons matter.
- Error bars: use readable caps and line widths; avoid obscuring data. Consider translucent bands for dense curves.
- Legends: remove unnecessary borders; place so they do not cover data. Prefer direct labels when they are unambiguous and do not clutter.
- Panels: use consistent sizes, aligned axes, shared scales when comparison requires them, and panel labels `(a)`, `(b)`, … for multi-panel figures.
- Titles: use a short descriptive title only when it helps standalone interpretation. For papers, let the caption carry context if that matches the venue's conventions.

### Color palette

Use this fixed palette unless the project already has an established, scientifically meaningful palette:

| Name | Hex | Intended use |
|---|---|---|
| Science blue | `#2878B5` | Primary series / proposed method |
| Warm orange | `#D97732` | Main comparison |
| Green | `#2E7D32` | Positive/control series when semantically appropriate |
| Purple | `#7861BF` | Additional series |
| Teal | `#168C8C` | Additional series |
| Charcoal | `#263238` | Text / neutral data |
| Mid grey | `#7A8793` | Baselines / secondary data |
| Light grey | `#D9E0E5` | Grid / uncertainty backgrounds |

Rules:
- Check the palette in the actual context and at final size; do not assume a palette is accessible just because it looks muted.
- For categorical data, use distinct hues and redundant encodings (markers, line styles, labels). Do not use a continuous colormap for categories.
- For ordered numeric data, use a perceptually uniform sequential colormap such as `viridis`, `cividis`, or `magma`.
- For signed deviations around a meaningful center, use a diverging map such as `RdBu_r` or `coolwarm`, centered at the scientifically meaningful reference.
- Avoid `jet`/rainbow maps, red–green-only distinctions, and color as the sole encoding.
- Preserve semantic mappings across figures: e.g. the same class, model, or dataset keeps the same color throughout the project.
- Do not imply that green means “good” or red means “bad” unless that meaning is appropriate and explained.

### Typography and sizing
- Use a widely available sans-serif font for labels and annotations (Matplotlib default sans-serif is acceptable); use LaTeX math rendering only when it improves notation and the build environment supports it.
- Keep typography consistent. A good starting point at final size:
  - axis labels: 9–11 pt
  - tick labels: 8–9 pt
  - legend: 8–9 pt
  - annotations: 8–10 pt
  - panel labels: 10–12 pt, semibold
- Figure size must match its destination. A common single-column width is about 3.3–3.6 in and double-column width about 6.8–7.2 in, but always follow the target venue's guidelines.
- Avoid text below 7 pt at final size unless there is a strong reason.
- Include units in axis labels, preferably with clear notation: `Energy [GeV]`, `Time [s]`, `Angular resolution [deg]`.
- Use math text consistently: `$E_{\mathrm{reco}}$ [GeV]`, not a mix of ad hoc Unicode symbols and inconsistent notation.

### Axes and statistics
- Label axes with the quantity and units; explain dimensionless quantities where not obvious.
- Use log scales only when justified by the data and scientific question. Label powers/ticks clearly and state transformations where needed.
- Do not truncate axes to exaggerate differences. Nonzero baselines can be valid for some metrics, but should be intentional and obvious.
- Choose histogram bins and normalization deliberately. For comparisons, align bin edges; use density normalization only when it answers the question.
- State whether uncertainty means standard deviation, standard error, confidence/credible interval, quantile range, or run-to-run variation.
- Distinguish statistical and systematic uncertainty when relevant. Do not combine them without justification.
- Do not present a confidence interval as a prediction interval or vice versa.
- Show sample sizes where they materially affect interpretation; report counts after filtering when relevant.
- Report aggregation choices (macro/micro averaging, weighting, event selection) in the caption or methods.
- For ROC/PR curves, include the baseline and a meaningful summary metric when useful; ensure class imbalance is considered.
- For confusion matrices, label true/predicted axes, fix class order, state row/column normalization, and use a legible scale. Annotate cells only if text remains readable.
- For residuals and calibration, include reference lines and axes that reveal the relevant failure modes.
- For comparisons across panels, share scales only when that makes comparisons valid; do not force shared scales when it hides meaningful structure.

### Captions and annotations
- A figure should answer one main question.
- Use annotations to identify important features, not to narrate every point.
- Explain colors, symbols, bands, sample selection, and non-obvious normalization in the caption.
- Distinguish measured data, simulations, model predictions, and reference/baseline curves.
- Do not place a result claim in the plot unless it is supported by the plotted data and statistical analysis.

## Accessibility and scientific integrity
- Design for grayscale printing and common color-vision deficiencies. Check contrast and use line styles/markers as backup.
- Use readable font sizes, descriptive labels, and uncluttered legends.
- Do not smooth, filter, bin, or omit data without making the choice scientifically defensible and documenting it when relevant.
- Do not use area, radius, perspective, or 3D depth to encode quantities unless the encoding is justified and accurately perceived.
- Keep raw observations visible when feasible; when using summaries, state what is summarized.
- Never manufacture uncertainty, statistical significance, baselines, sample sizes, or missing observations.
- For images, state the physical meaning, units, and range of the color scale. Use the same range for panels intended for direct comparison.
- Avoid dual y-axes unless they are essential; if used, explain why and ensure the visual relationship is not misleading.

## Recommended implementation

If a style helper exists, import it rather than copying style definitions into every script. A minimal Matplotlib baseline:

```python
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

mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "text.color": PALETTE["charcoal"],
    "axes.labelcolor": PALETTE["charcoal"],
    "xtick.color": PALETTE["charcoal"],
    "ytick.color": PALETTE["charcoal"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": PALETTE["grey"],
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": PALETTE["light_grey"],
    "grid.linewidth": 0.6,
    "grid.alpha": 0.8,
    "lines.linewidth": 2.0,
    "lines.markersize": 5,
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
```

Use this as a starting point, not a substitute for inspecting the exported figure.

## Common figure patterns

### Line plot with uncertainty
- Plot the central estimate and an interval that accurately represents the data.
- Prefer a translucent band for dense curves or error bars for sparse points.
- Label the interval type in the legend or caption.
- Keep the same x grid and axis scale for comparisons where appropriate.

### Scatter plot
- Use alpha for overplotting; do not interpret transparency as a statistical density estimate unless justified.
- For dense data, consider hexbin or 2D histograms.
- If adding a fit, explain the fitting method and show a confidence or prediction interval only if computed correctly.
- Report sample size and meaningful statistics; do not infer correlation from a visually sloped line alone.

### Histograms and distributions
- Use common bins for direct comparisons.
- Clearly label count, probability, or density.
- Avoid excessive smoothing; show the actual distribution where possible.
- Consider ECDFs or quantile summaries when bin choice dominates the story.

### Multi-panel figures
- Use one coherent visual grammar across panels.
- Align axes and panel labels; share axes when comparison requires it.
- Avoid repeating legends and labels unnecessarily, but retain enough information for each panel to remain interpretable.
- Ensure panel labels and all text survive export at final dimensions.

### Heatmaps
- Select colormap by data semantics; set `vmin`/`vmax` deliberately.
- Use a diverging map only when the center has meaning.
- Add cell annotations only if legible; use contrasting text based on cell luminance.
- Label both axes and state normalization.

## Final checklist

Before delivering a figure, verify:

- [ ] The plot type answers the scientific question.
- [ ] Quantities, units, and scales are correct and explicit.
- [ ] No data or uncertainty is silently removed or invented.
- [ ] Color mapping is consistent, accessible, and not the only distinction.
- [ ] Axes, legend, markers, line widths, and fonts are consistent.
- [ ] Binning, normalization, sample size, and interval meanings are clear where relevant.
- [ ] The figure remains readable at its final size and in grayscale where applicable.
- [ ] Multi-panel comparisons use appropriate scales and shared semantics.
- [ ] PDF/SVG or sufficiently high-resolution raster output is exported.
- [ ] The output is reproducible from the supplied code and data.

When reviewing existing figures, prioritize scientific correctness and interpretability over cosmetic changes. Explain any change that could affect how a result is perceived. Do not rewrite the scientific conclusion to fit the visual design.
