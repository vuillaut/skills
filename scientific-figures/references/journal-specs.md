# Journal figure specifications

Compiled 2026-10-19 from the publishers' own pages where available. **Specs change: always re-open the
journal's author guidelines before final submission.** "Third-party" = secondary summary, treat as a
hint and verify.

## Contents
- Quick table
- Per-journal notes
- Journal-independent rules
- Sources

## Quick table

| Journal / publisher | 1 column | 2 columns | Text size at final size | Font | Format / resolution | Source quality |
|---|---|---|---|---|---|---|
| Nature (Nature Research) | 89 mm | 183 mm (max height 170 mm) | **5-7 pt**; panel labels 8 pt bold lowercase | Arial/Helvetica, sans-serif only; embed (TrueType 42) | vector preferred (editable PDF/AI/EPS); raster max 300 dpi; RGB; <= 10 MB | official |
| A&A | 88 mm | 180 mm | not fixed; avoid thin lines; **lower-case words in figures**; limit empty space | any | eps, pdf, jpg, png, tiff; production reduces most figures to 88 mm | official |
| AAS journals (ApJ, AJ, ApJS...) | see Graphics Guide | see Graphics Guide | follow the Graphics Guide | - | see journals.aas.org/graphics-guide; colour-blind-friendly figures requested | official page, details not verified here |
| IUCr (Acta Cryst.) | - | - | labels about **8 pt** at final size; line weights 0.35-1.5 pt | Arial/Helvetica only | EPS/PS vector; colour raster >= 400 dpi; fonts embedded | official |
| IEEE | 3.5 in (88.9 mm) | 7.16 in (182 mm) | ~ 9-10 pt recommended | Helvetica, Times, Arial, Cambria, Symbol | - | official (Proc. IEEE) |
| AIAA | 3.25 in (stated for tables) | 7 in (stated for tables) | SI (or dual) units preferred in figures | - | line art >= 600 dpi, images >= 300 dpi | official |
| PLOS | - | - | - | - | 300-600 dpi | third-party summary |
| Science / Cell | 55 mm / 85 mm | 120 mm / 178 mm | Cell: 6-8 pt (Avenir/Arial) | - | - | third-party, verify |

## Per-journal notes

**Nature** (research-figure-guide.nature.com): submit at the smallest appropriate size so that all
text is 5-7 pt; do not outline or rasterise text (editors must be able to edit it); panels labelled
8 pt bold lowercase; RGB not CMYK; artificially upsampling does not improve quality; avoid coloured
text in legends; the site targets WCAG 2.1 AA accessibility.

**A&A** (aanda.org/for-authors/latex-issues/figures): avoid thin lines (figures are reduced);
limit empty space in and around figures; adjust the BoundingBox of EPS files that carry large
margins; lower-case words in figures.

**IUCr**: only Arial/Helvetica; ~ 8 pt at final size; line weights 0.35-1.5 pt; embed fonts.

**Reduction rule of thumb**: production reduces to column width; if your figure is wider than the
column, its text shrinks by (column width / figure width). Build at the real width.

## Journal-independent rules (converging across guides)

- Sans-serif font, one family, same sizes throughout the paper.
- Fonts embedded in PDF/EPS; text stays text.
- Vector for line art; >= 300 dpi at final size for raster; 600+ dpi for bitmap line art.
- Figure interpretable in greyscale and by colour-blind readers.
- Each figure cited in the text in numerical order; panels labelled a/b/c (or A/B/C per journal).
- Image-integrity: never selectively edit image regions; document processing in the caption.

## Axis-label convention (units)

ISO 80000-1 / IUPAP / IUPAC treat a quantity as number x unit, so the strict form is
`quantity / unit` (e.g. `E / TeV`); `quantity (unit)` (Nature, IEEE) and `quantity [unit]`
(common in astronomy) are widespread alternatives. There is no single universal convention
(see Nature 316:489, 1985 for the historical debate; bioblast.at/Units_in_figures_and_tables).
Rule: one convention per paper, unit always present.

## Sources

- Nature Research figure guide: https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications ,
  https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/ ,
  https://nature.com/documents/nature-final-artwork.pdf
- A&A figures: https://www.aanda.org/for-authors/latex-issues/figures
- AAS Graphics Guide: https://journals.aas.org/graphics-guide
- IUCr artwork: https://journals.iucr.org/services/help/artwork/guide.html
- IEEE: https://proceedingsoftheieee.ieee.org/resources/guidelines-for-figures-and-tables/
- AIAA: https://aiaa.org/publications/journals/journal-author/guidelines-for-journal-figures-and-tables
- Rougier et al. 2014: https://doi.org/10.1371/journal.pcbi.1003833
