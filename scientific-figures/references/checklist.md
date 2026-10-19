# Pre-submission figure checklist

Run this on the exported PNG viewed at 100 % (≈ final printed size), then on the PDF.

## Axes and units (hard fail if any is unchecked)
- [ ] Every numeric axis has **quantity + unit**; unitless ones say `(dimensionless)`, `(a.u.)` or `(counts)`.
- [ ] Categorical/index axes (model names, bin index) carry a variable name (`Model`, `Bin index`), declared with `NO_UNIT`.
- [ ] Colorbars labelled with quantity + unit.
- [ ] One unit convention (paren / bracket / slash) used across the paper.
- [ ] No hidden offset text (`1e-12`); scale folded into the unit.
- [ ] Tick labels readable, not overlapping; 4-6 majors; minor ticks on log axes.
- [ ] Axis ranges sensible; zero/unity reference line where relevant.

## Legibility
- [ ] Figure built at the real column width (88/180 mm or journal-specific).
- [ ] Smallest text >= journal minimum (profile floor: journal 7 pt, nature 5 pt, slide 12 pt).
- [ ] Labels larger than ticks; panel letters bold and larger than labels.
- [ ] Lines >= 0.5 pt (data 1-2 pt); markers visible; error bars not hidden by markers.
- [ ] Same font/size/line weight as the other figures of the paper.

## Colour
- [ ] Okabe-Ito / uniform colormap; no jet/rainbow/red-green-only.
- [ ] Still readable in greyscale (linestyle/marker redundancy present).
- [ ] Same quantity = same colour across figures.
- [ ] Diverging map centred on the meaningful value.

## Honesty
- [ ] Uncertainties shown and defined in the caption; n given.
- [ ] Bars start at zero; no misleading truncation, 3-D, or unflagged dual axes.
- [ ] Compared panels share ranges (or the caption says they don't).
- [ ] Binning/smoothing/colour limits stated.

## Layout and export
- [ ] No in-figure title; caption written (title sentence, symbols, error definition, source).
- [ ] No chartjunk; little empty margin; panels labelled in order.
- [ ] Vector PDF with embedded fonts (`pdffonts fig.pdf` -> emb = yes, TrueType); PNG at 300 dpi.
- [ ] File size within the journal limit; file names as requested.
- [ ] Script + data pointer saved next to the figure (reproducible, seeded).
