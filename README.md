# Calibration as Linkage Integrity

Submission to the FLF Epistemic Case Study Competition ("Epistack").

**Start here:** the full writeup and run results are in [`FLF-Submission-Combined.pdf`](FLF-Submission-Combined.pdf). The runnable instrument is [`epistack_eval.py`](epistack_eval.py).

## The core submission

The real test of the rigor of a knowledge base is how well it survives contact with a reasoner. Ideally the reasoner leaning only on the base should be as confident as the evidence in the base warrants. Any more or less confidence is a failure of the base and not a failure of the reader. This instrument measures that deviation, on real cases.

Since the knowledge base is an input to the instrument, it can be pointed at any base, not just mine, including other entrants bases or any base FLF wants to audit.

**Where this goes:** the detector is the first step. Since the base is only an input, the same instrument can become an Epistack Eval Standard, a single score any base can be measured against, and then a repair tool that fixes the failures it finds. I want to build in that direction, and it is laid out at the end of the combined PDF.

## Run it

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
python3 epistack_eval.py --case covid        --model claude-sonnet-4-6
python3 epistack_eval.py --case blackholes   --model claude-opus-4-8
python3 epistack_eval.py --case eggs         --model claude-sonnet-4-6
python3 epistack_eval.py --case covid_large  --model claude-opus-4-8   # the real 26-claim base
```

No key? See the shape first with `python3 epistack_eval.py --dry-run` (prints placeholders, not results).

## What it measures

The evaluation runs as one script with three probes: a linkage-integrity test, a behavioral double-counting test, and a retracted-claim provenance test (Part C, on the large base). Each measures a different failure.

The linkage test measures all three constraints it applies: reasoning from the base only, updating on a held-out claim it never saw, and holding up under a counter-argument. The first is enforced by instruction; the next two are measured directly. It also reports the objective metric, calibration gained per claim read. The double-counting probe checks whether correlated claims shown separately inflate confidence, and the retracted-claim probe checks whether a reasoner leans on evidence that has been withdrawn.

## The cases

The same instrument runs on three differently-shaped starter cases, and then on a real, large 26-claim base. Only the knowledge base and the warranted shape change.

- **covid** (contested): wide uncertainty is warranted.
- **blackholes** (settled): confident-safe is warranted, and the failure to catch is false balance.
- **eggs** (ill-posed): the failure is a confident universal answer instead of catching that the effect depends on who you are.

## What the results say

Following are the results from running the instrument on the three starter cases using two models (Sonnet and Opus). It was done using LLM personas, so the results are pointing and not proving. The real large-base result is reported below the table.

| Case | Shape | Model | Found the crux | Held-out transfer | Confidence survived | Metric (calibration / claim read) |
|---|---|---|---|---|---|---|
| COVID | contested | Sonnet | 0.67 | 1.0 | 1.0 | about -0.01 |
| COVID | contested | Opus | 1.0 | 1.0 | 1.0 | about +0.005 |
| Black holes | settled | Sonnet | 1.0 | 0.0 (see note) | 1.0 | about +0.09 |
| Black holes | settled | Opus | 1.0 | 0.0 (see note) | 1.0 | about +0.11 |
| Eggs | ill-posed | Sonnet | 0.0 | 1.0 | 1.0 | about +0.009 |
| Eggs | ill-posed | Opus | 1.0 | 1.0 | 1.0 | about +0.004 |

Note on the black-holes held-out score: the held-out claim reinforced an answer that was already at zero, so there was no room left to move, and the instrument recorded no update as no transfer. It is a scoring edge, not a reasoning failure.

For the settled case of black holes, it gave the clearest positive result (rightfully so). On Opus the mean calibration increase was 0.57, and the most skeptical persona gained the most (0.75). None of the personas fell for false balance when the counter-argument pushed them to doubt a settled answer.

The metric pointed to being model-dependent. It came out cleaner and more positive on the stronger model, and weaker and slightly negative on the lighter one. Which again proved the point that a better reasoner pulls more warranted calibration out of the same base.

Even the crux localization is model-dependent. It was more reliable on Opus and patchy on Sonnet, and it kept moving between different runs.

For the eggs case, it showed its characteristic failure. On the Sonnet model the reasoners missed that the effect is heterogeneous across people, while on Opus they caught it.

The honest bounds are in `FLF-Submission-Combined.pdf`.

I also ran the instrument on a real, large, 26-claim COVID-origins ledger base built from deep research and reconciled across two models. Reading the unflagged version, the instrument reproducibly caught a double-counting failure: showing the five correlated Wuhan-cluster claims as separate strikes rather than one shared cause moved a reasoner further toward a lab origin in every single run. Across seven runs per model the effect averaged about 0.12 on Opus (range 0.09 to 0.14) and about 0.08 on Sonnet (range 0.06 to 0.11). The direction is robust; the magnitude is noisy, and the ranges overlap. Full detail is in the combined PDF.

The instrument also runs a retracted claim provenance probe on the large base. It plants a genuinely withdrawn claim and checks whether a reasoner is leaning on it. Across the three runs per model, both models correctly discounted it when the retraction was labelled.

## Limitations

1. It used LLM personas and not a human cohort, though it had multiple runs.
2. It scored against the structure of each case.
3. The effort metric is proxied by the claims it read.
4. The black-holes and eggs knowledge bases are compact, defensible starters, meant to show the instrument travels, and not authoritative verdicts. The large COVID base is the real, full-size one.

## Reuse

Cooperative competition, so reuse is welcome. Released under the MIT License (see `LICENSE`). Repository: https://github.com/vaibhav-labs/Epistack_Eval . Questions: hi@vj9.org
