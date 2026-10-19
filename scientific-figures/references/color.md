# Colour reference

## Contents
- Categorical palette (Okabe-Ito / Wong)
- Measured behaviour (CVD and greyscale)
- Continuous colormaps
- Rules

## Categorical palette (Okabe & Ito 2008; popularised by Wong 2011, Nature Methods 8:441)

Default cycle order in `scifig` (strongest contrast on white first, yellow last):

| # | name | hex |
|---|---|---|
| 1 | blue | `#0072B2` |
| 2 | vermillion | `#D55E00` |
| 3 | bluish green | `#009E73` |
| 4 | orange | `#E69F00` |
| 5 | sky blue | `#56B4E9` |
| 6 | reddish purple | `#CC79A7` |
| 7 | black | `#000000` |
| 8 | yellow | `#F0E442` (poor contrast on white: use for fills/markers, not thin lines) |

## Measured behaviour (computed for this skill, Machado et al. 2009 matrices, CIE76 dE)

- Minimum pairwise dE among the 8 colours: normal 26, protanopia 21, deuteranopia 17, tritanopia 16
  -> all pairs remain distinguishable (dE > ~10 is clearly separable).
- **Greyscale (relative luminance)**: black 0.00, blue 0.15, vermillion 0.22, green 0.26, purple 0.29,
  sky 0.41, orange 0.42, yellow 0.74. Pairs closer than 0.08: orange~sky (0.01), vermillion~green
  (0.04), green~purple (0.04), blue~vermillion (0.07), vermillion~purple (0.07).
  => colour alone fails in B&W print: add linestyle/marker (`scifig.series_styles`).

## Continuous colormaps (Crameri, Shephard & Heron 2020, Nat Commun 11:5444)

Rainbow-like maps (jet, hsv, rainbow) create artificial boundaries, hide real structure, and are
unreadable for colour-vision-deficient readers. Red-green maps likewise.

| Data | Use | Avoid |
|---|---|---|
| ordered magnitude (flux, counts, density) | `viridis`, `cividis`, Crameri `batlow`, `lajolla`, `oslo` | jet, rainbow, hsv, hot-as-default |
| diverging around a meaningful centre (residual, significance, correlation) | Crameri `vik`/`berlin`, matplotlib `berlin` (>= 3.10), `RdBu_r` as fallback; centre with `CenteredNorm`/`TwoSlopeNorm` | red-green, asymmetric limits that shift the zero colour |
| cyclic (phase, angle, RA) | Crameri `romaO`, matplotlib `twilight` | linear maps whose ends differ |
| sky maps with many dim features | sequential map + clipped, stated colour limits | autoscale driven by a single hot pixel |

`pip install cmcrameri` then `from cmcrameri import cm; cm.batlow`. `scifig.cmap()` uses it if present.

For a greyscale-safe sequential map, check that lightness increases monotonically (viridis, batlow do).

## Rules

1. Colour encodes a variable; do not use it for decoration.
2. Same entity = same colour across all figures of a paper.
3. Do not rely on hue alone for >2 categories: add linestyle/marker/direct labels.
4. Text and thin lines >= 3:1 contrast with background (WCAG graphical-object threshold).
5. Simulate before submission: colour-blindness simulators (e.g. Coblis) or the Machado matrices;
   also convert the PNG to greyscale and look at it.
6. Fill colours with transparency (alpha 0.2-0.4) for overlapping bands, and outline them.
