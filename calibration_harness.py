#!/usr/bin/env python3
"""
calibration_harness.py ,  reference prototype for the FLF Epistack submission
"Calibration, Not Comprehension: The Transfer Layer"

WHAT THIS IS
------------
A dependency-free, single-command reference implementation of the calibration
harness in section 5 of the submission. It scores an epistemic *artifact* not by
whether readers reach the "right answer," but by whether the artifact moves
readers toward the WARRANTED SHAPE OF UNCERTAINTY, the right centre AND the
right WIDTH. Beliefs are therefore intervals, not points: overconfidence shows
up as an interval that is too NARROW for a crux that genuinely warrants width.
That is exactly "performed settling," made measurable.

Run with zero setup:

    python3 calibration_harness.py

To use real LLM personas or a human cohort, implement the one `_real_elicit`
hook and set USE_MOCK = False. Everything else is model-agnostic.

KEY IDEAS (mapped to the submission)
------------------------------------
* WARRANTED SHAPE, not point answer. Each crux carries a warranted interval
  [low, high]; for the contested driver crux this interval is deliberately WIDE.
  A calibrated reader must reproduce its centre AND its width.
* KNOWLEDGE MASKING. Readers start OVERCONFIDENT (narrow interval) and only gain
  grounded movement on a crux when the artifact supplies that crux's
  prerequisites and ran the generative loop (elicit-prior-then-reveal).
* FLUENCY ILLUSION. A summary that asserts a verdict makes readers MORE
  overconfident (interval shrinks) without moving the centre where prerequisites
  are missing, so it can score NEGATIVE on width calibration.
* TRANSFER. A held-out sibling crux (never walked) improves only for readers who
  learned the underlying reasoning elsewhere (shared prerequisite), i.e. the
  artifact taught reasoning, not a verdict.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import statistics

USE_MOCK = True
START_HALFWIDTH = 0.08          # people start overconfident (narrow), per the literature
SETTLED, DRIVER = "settled", "driver"


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Crux:
    cid: str
    question: str
    low: float                  # warranted interval [low, high]
    high: float
    load_bearing: float
    prerequisites: list[str] = field(default_factory=list)
    walked: bool = True         # False => held out, used only for the transfer metric
    drives_disagreement: bool = False

    @property
    def w_centre(self): return (self.low + self.high) / 2
    @property
    def w_halfwidth(self): return (self.high - self.low) / 2


@dataclass
class Artifact:
    name: str
    builds_prerequisites: set
    elicits_prior: bool          # the generative loop (Step 3)
    teaches_width: bool          # preserves the warranted spread vs. flattening to a verdict


@dataclass
class Belief:
    centre: float
    halfwidth: float
    def error_vs(self, c: Crux) -> float:
        # penalise wrong centre AND wrong width (too-narrow = overconfident)
        return abs(self.centre - c.w_centre) + abs(self.halfwidth - c.w_halfwidth)
    def overconfidence_vs(self, c: Crux) -> float:
        return max(0.0, c.w_halfwidth - self.halfwidth)   # only too-narrow counts


@dataclass
class ReaderModel:
    rid: str
    prior: dict                  # cid -> starting centre
    known_prerequisites: set
    minutes: float = 0.0

    def _grounded(self, c: Crux, a: Artifact):
        have = set(c.prerequisites).issubset(self.known_prerequisites | a.builds_prerequisites)
        grounded = have and (a.elicits_prior or not c.prerequisites)
        return have, grounded

    def read(self, c: Crux, a: Artifact, stage: str) -> Belief:
        """stage in {'before','after','adversarial'}; returns an interval Belief.
        For held-out cruxes we call with stage='transfer'."""
        if not USE_MOCK:
            return _real_elicit(self, c, a, stage)

        start = Belief(self.prior.get(c.cid, 0.5), START_HALFWIDTH)
        if stage == "before":
            self.minutes += 0.5
            return start

        have, grounded = self._grounded(c, a)
        self.minutes += 2.0 + 1.5 * len(c.prerequisites) + (1.0 if a.elicits_prior else 0.0)
        close = 0.92 if grounded else (0.35 if have else 0.08)   # centre gap closed
        centre = start.centre + close * (c.w_centre - start.centre)

        # width dynamics: the heart of calibration
        if a.teaches_width and grounded:
            halfwidth = start.halfwidth + 0.9 * (c.w_halfwidth - start.halfwidth)  # learn right width
        else:
            halfwidth = max(0.04, start.halfwidth * 0.7)         # fluency illusion: gets narrower

        if stage == "after":
            return Belief(centre, halfwidth)
        if stage == "adversarial":                                # post-hoc counter-narrative
            if grounded:
                return Belief(centre, halfwidth)                  # holds
            snap = start.centre + 0.2 * (centre - start.centre)   # fluent belief snaps back
            return Belief(snap, max(0.04, halfwidth))
        if stage == "transfer":                                   # held-out sibling crux
            close_t = 0.75 if grounded else 0.05
            centre_t = start.centre + close_t * (c.w_centre - start.centre)
            hw_t = start.halfwidth + (0.8 if grounded else 0.0) * (c.w_halfwidth - start.halfwidth)
            return Belief(centre_t, hw_t)
        raise ValueError(stage)


def _real_elicit(reader, crux, artifact, stage):  # pragma: no cover
    raise NotImplementedError("Wire to an LLM persona or human-cohort UI; return a Belief(centre, halfwidth).")


# --------------------------------------------------------------------------- #
# Scoring (section 5)
# --------------------------------------------------------------------------- #
def score_artifact(artifact: Artifact, cruxes, readers) -> dict:
    walked = [c for c in cruxes if c.walked]
    held = [c for c in cruxes if not c.walked]
    up, rob, settle, loc, tr = [], [], [], [], []

    for r in readers:
        for c in walked:
            b0 = r.read(c, artifact, "before")
            b1 = r.read(c, artifact, "after")
            ba = r.read(c, artifact, "adversarial")
            up.append((c.load_bearing, b0.error_vs(c) - b1.error_vs(c)))
            rob.append((c.load_bearing, b0.error_vs(c) - ba.error_vs(c)))
            settle.append((c.load_bearing, b1.overconfidence_vs(c)))
            if c.drives_disagreement:
                # localised = ended near the warranted centre WITH appropriate width
                ok = (c.low <= b1.centre <= c.high) and (b1.halfwidth >= 0.7 * c.w_halfwidth)
                loc.append(1.0 if ok else 0.0)
        for c in held:
            b0 = Belief(r.prior.get(c.cid, 0.5), START_HALFWIDTH)
            bt = r.read(c, artifact, "transfer")
            tr.append((c.load_bearing, b0.error_vs(c) - bt.error_vs(c)))

    def wmean(pairs):
        num = sum(w * x for w, x in pairs); den = sum(w for w, _ in pairs)
        return num / den if den else 0.0

    minutes = statistics.mean(r.minutes for r in readers) or 1.0
    return {
        "artifact": artifact.name,
        "calibration_uplift": round(wmean(up), 3),
        "effort_adjusted_per_10min": round(wmean(up) / minutes * 10, 4),
        "crux_localisation_rate": round(sum(loc) / len(loc), 2) if loc else None,
        "adversarial_robustness": round(wmean(rob), 3),
        "held_out_transfer": round(wmean(tr), 3),
        "performed_settling_flag": round(wmean(settle), 3),
        "avg_reader_minutes": round(minutes, 1),
    }


# --------------------------------------------------------------------------- #
# Worked COVID example (full graph + warranted shapes in the Appendix)
# Probabilities are P(zoonosis-consistent reading of this crux).
# --------------------------------------------------------------------------- #
def covid_cruxes():
    return [
        Crux("geo", "Early-case clustering at Huanan market, net of ascertainment bias?",
             0.60, 0.80, 1.0, ["ascertainment_bias", "spatial_case_control"]),
        Crux("fcs", "Furin cleavage site better explained as natural than engineered?",
             0.45, 0.70, 0.9, ["prosecutors_fallacy", "fcs_in_coronaviruses"]),
        Crux("refclass", "Under a defensible reference class & prior, P(zoonosis)?",
             0.20, 0.90, 1.5, ["bayes_likelihood_vs_prior", "reference_class", "conditional_independence"],
             drives_disagreement=True),
        Crux("lineages", "Two early lineages (A & B) at market => multiple spillovers? [HELD OUT]",
             0.55, 0.75, 0.7, ["spatial_case_control"], walked=False),
    ]


def covid_readers():
    return [
        ReaderModel("novice_blank", {"geo":.5,"fcs":.5,"refclass":.5,"lineages":.5}, set()),
        ReaderModel("lab_leak_lean", {"geo":.4,"fcs":.3,"refclass":.3,"lineages":.45},
                    {"bayes_likelihood_vs_prior"}),
        ReaderModel("stats_literate", {"geo":.55,"fcs":.5,"refclass":.5,"lineages":.55},
                    {"bayes_likelihood_vs_prior", "conditional_independence"}),
    ]


def demo():
    cruxes = covid_cruxes()
    all_prereqs = {p for c in cruxes for p in c.prerequisites}
    summary = Artifact("A) Summary 'deep research' (states the verdict)",
                       set(), elicits_prior=False, teaches_width=False)
    transfer = Artifact("B) Transfer-layer artifact (crux-first, prerequisite-scaffolded)",
                        all_prereqs, elicits_prior=True, teaches_width=True)

    print("=" * 76)
    print("CALIBRATION HARNESS, worked COVID-origins comparison")
    print("Scoring is for CALIBRATION (match the warranted SHAPE: centre AND width).")
    print("=" * 76)
    for art in (summary, transfer):
        rep = score_artifact(art, cruxes, covid_readers())
        print(f"\n{rep['artifact']}")
        for k, v in rep.items():
            if k != "artifact":
                print(f"   {k:30s} {v}")
    print("\nINTERPRETATION")
    print("  Summary: barely moves centres where prerequisites are missing, and the")
    print("  fluency illusion makes readers MORE overconfident -> high performed-settling")
    print("  flag, fails localisation, collapses adversarially, ~0 transfer.")
    print("  Transfer: moves centre AND teaches the warranted WIDTH (incl. the wide")
    print("  reference-class crux that drives the 23-OOM spread), so readers localise the")
    print("  real driver, hold up under a counter-narrative, and transfer to a held-out")
    print("  crux. That delta is the thesis, in numbers, and a builder reads it as a")
    print("  gradient: 'build these prerequisites; run the generative loop.'")
    print("=" * 76)


if __name__ == "__main__":
    demo()
