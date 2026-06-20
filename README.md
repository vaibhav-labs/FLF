# Calibration : The Transfer Layer

A submission to the [FLF Epistemic Case Study Competition](https://flf.org/epistack-competition/) ("Epistack").

**The one-line claim:** the binding constraint in an epistemic investigation is not the artifact's fidelity, it is the reader's calibration, and the two come apart in a way you can measure. This repo holds the reference prototype that measures it.

## What this is

The competition decomposes an investigation into ingestion, structure, and assessment. Each of those makes the *artifact* better. But the stated goal is that a tool "would help someone reason better," which is a property of the *reader*, not the artifact. The submission adds a fourth layer, **Transfer**: the gap between what a reader believes before an artifact and after it. The right objective is **calibration uplift per unit of reader effort**, not comprehension.

`calibration_harness.py` is a dependency-free reference implementation that scores any artifact by simulating knowledge-masked reader priors and measuring how their beliefs move toward the warranted *shape* of uncertainty (the right centre and the right width), not toward a single "correct answer."

## Run it

No dependencies, no API key, one command:

```bash
python3 calibration_harness.py
```

It scores two artifacts on the COVID-origins cruxes: a summary-style "deep research" output, and a Transfer-layer artifact (crux-first, prerequisite-scaffolded). Representative output:

| metric | A) Summary | B) Transfer layer |
|---|---|---|
| calibration_uplift | **-0.012** | **+0.264** |
| effort_adjusted_per_10min | -0.003 | +0.059 |
| crux_localisation_rate | 0.0 | 1.0 |
| adversarial_robustness | -0.022 | +0.264 |
| held_out_transfer | 0.007 | 0.129 |
| performed_settling_flag | **0.161** | 0.014 |

The headline result is deliberately uncomfortable: the summary scores **negative** on calibration. It nudges readers' point estimates while making their confidence intervals narrower than the evidence warrants (the fluency illusion), so on net it leaves them worse calibrated, and that miscalibration collapses under a single counter-narrative. This is the "meaningfully better than off-the-shelf deep research" bar made concrete rather than asserted.

## How it works (the short version)

- **Warranted shape, not a point answer.** For a contested case the target is the centre *and the width* the evidence supports. Overconfidence shows up as an interval that is too narrow, which is exactly Moore and Healy's "overprecision."
- **Knowledge-masked readers.** Personas are given explicit priors and a prerequisite mask that hides downstream facts, so they have to reason *from the artifact*, not from memorized answers. This is the defense against "the model already knows the answer."
- **Metrics that separate teaching reasoning from teaching answers:** calibration uplift, crux-localization, adversarial robustness (a counter-narrative injected after reading), and transfer to a held-out crux.

## Make it real

The shipped readers are deterministic mocks so the harness runs anywhere. To use live LLM personas or a human cohort, set `USE_MOCK = False` and implement the single `_real_elicit` hook to return a `Belief(centre, halfwidth)`. Everything else (the warranted-shape table, the prerequisite graph, the metrics) is reused unchanged.

## Full writeup

The ten-page argument, the worked COVID appendix (prerequisite graph, warranted-shape table, reader transcript), and the bibliography are in the submission documents. See the Primary Document link in the competition entry.

## Reuse

This is a cooperative competition, and the harness and prerequisite graphs are meant to be picked up and extended. Released under the MIT License (see `LICENSE`). If you build on it, no need to ask, though I would enjoy hearing about it: hi@vj9.org
