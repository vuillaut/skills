---
name: scientific-writing
description: Write and rewrite scientific and technical text in a natural, restrained style that avoids recognizable AI-generated prose, rhetorical over-structuring, exaggerated claims, and imprecise quantitative language. Use when drafting, rewriting, editing, or polishing scientific papers, reports, documentation, technical notes, or research project text.
---

# Human Scientific Writing

Write like a scientist documenting work they actually performed, not like an AI presenting a polished narrative about the work.

## Core principles

- Prefer direct statements over rhetorical framing.
- State what was measured, calculated, observed, or tested.
- Match claims to the evidence and conditions under which they were obtained.
- Be precise about quantities, denominators, thresholds, populations, and units.
- Distinguish clearly between probability, area, coverage, multiplicity, sensitivity, efficiency, and detection probability.
- Use ordinary scientific vocabulary.
- Keep some natural variation in sentence structure; do not make every paragraph follow the same rhetorical pattern.
- Slightly dry and plain is preferable to polished and memorable.
- Preserve the author's technical voice rather than replacing it with generic academic English.

## Avoid AI-like rhetorical patterns

Do not repeatedly use constructions such as:

- "not X, but Y"
- "The key insight is..."
- "The important point is..."
- "What this means is..."
- "This highlights..."
- "This demonstrates..."
- "Taken together..."
- "At its core..."
- "The broader lesson..."
- "The practical takeaway..."
- "This is where..."
- "The result is clear..."
- "This changes everything..."
- "The logarithm fixes the answer."
- "X buys time."
- "X spends probability."
- "The map itself tells us..."

These constructions are not forbidden individually. Avoid them when they serve rhetorical emphasis rather than conveying scientific information.

## Avoid artificial narrative structure

Do not force every section into:

1. problem
2. conceptual insight
3. dramatic result
4. interpretation
5. takeaway

Do not add a mini-conclusion to every subsection.

Do not repeatedly explain to the reader why a result is important immediately after presenting it. If the result is clear from the numbers or figure, state it and move on.

Do not add sentences whose only purpose is to announce the reasoning:

- "This is the crucial observation."
- "This leads to an important conclusion."
- "The argument therefore becomes clear."
- "The practical reading is..."
- "The implication is straightforward..."

## Prefer explicit scientific statements

Instead of:

> Divergence buys not coverage but time.

Write:

> Increasing the divergence reduces the instantaneous covered probability but can reduce the number of pointings required to scan the localization.

Instead of:

> The map's own shape determines the answer.

Write:

> The optimal pointing depends on the spatial distribution of the localization probability.

Instead of:

> This is a non-existence result, not a tuning failure.

Write:

> No value of the divergence tested here reaches the target coverage.

## Quantitative precision

Whenever a percentage, fraction, or metric is used, make clear what it measures.

For example:

> 72% of the observable GW probability is covered by at least two telescopes.

is preferable to:

> The coverage is 72%.

Define metrics once and use the definitions consistently.

Distinguish explicitly between:

- fraction of localization probability;
- fraction of geometrical sky area;
- telescope multiplicity;
- probability-weighted mean multiplicity;
- detection probability;
- sensitivity;
- exposure;
- fraction of events satisfying a selection.

Never use "coverage" ambiguously when the distinction matters.

## Separate observation from interpretation

Prefer:

> The configuration covers 68% of the observable localization probability with at least two telescopes. The corresponding mean multiplicity is 2.4.

followed, if necessary, by:

> This favors the central part of the localization over its low-probability outskirts.

rather than combining measurement and interpretation into a rhetorical statement.

## Claims and uncertainty

Do not make a stronger claim than the analysis supports.

Prefer:

> For the localization considered here, divergent pointing does not reach 80% two-telescope coverage.

over:

> Divergent pointing cannot provide 80% coverage.

The first is appropriately conditional. The second may incorrectly generalize the result.

Keep limitations explicit when they affect interpretation.

## Vocabulary

Prefer:

- "we calculate"
- "we find"
- "we measure"
- "the simulations show"
- "the configuration covers"
- "the optimization gives"
- "this follows from"
- "under these assumptions"
- "for this localization"
- "in the tested range"

Avoid unnecessary metaphors such as:

- buys
- spends
- unlocks
- unchains
- packs
- races
- fights
- wins on every axis
- tells its own story

## Headings

Use descriptive headings that state the content.

Prefer:

> Probability-weighted pointing

over:

> Let the map choose

Prefer:

> Comparison with sequential tiling

over:

> The race against time

Prefer:

> Limitations

over:

> What this really means

## Editing procedure

When rewriting existing scientific text:

1. Preserve the scientific content, equations, figures, references, directives, and technical terminology.
2. Identify claims whose definitions or denominators are ambiguous.
3. Replace rhetorical statements with explicit observations or quantitative claims.
4. Remove repeated conclusions and section announcements.
5. Remove unnecessary metaphors.
6. Weaken claims that extend beyond the evidence.
7. Check that every percentage has a clear denominator.
8. Check that area and probability are never conflated.
9. Check that geometrical coverage is not presented as detection probability or sensitivity.
10. Keep the resulting prose natural rather than making it uniformly polished.

## Final test

Before returning the text, ask:

### Scientific precision
- Is every fraction clearly defined?
- Is every denominator clear?
- Are probability and area distinguished?
- Are multiplicity and coverage distinguished?
- Is sensitivity distinguished from geometrical visibility?
- Are conclusions limited to the tested conditions?

### Human style
- Could this appear unchanged in a researcher's technical note?
- Does any sentence merely announce that something is important?
- Does the prose contain unnecessary rhetorical contrasts?
- Does it use metaphors where a technical statement would be clearer?
- Does every subsection have an artificial "lesson"?
- Is the prose unnaturally polished or symmetrical?

### Compression
Delete sentences that only:
- announce a section;
- emphasize that a result is important;
- repeat the preceding sentence;
- explain an obvious figure or equation;
- provide rhetorical emphasis without adding scientific information.

The target style is:

**precise + restrained + technically explicit + slightly dry + natural**

not:

**polished + persuasive + dramatic + rhetorically memorable + perfectly structured**
