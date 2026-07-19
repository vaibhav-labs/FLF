# Calibration as Linkage Integrity

Submission to the FLF Epistemic Case Study Competition ("Epistack"). This is an update to my earlier submission, carried forward with the additional runs the FLF compute support covered, a retracted-claim probe and a repair-and-reverify loop.

The real test of the rigor of a knowledge base is how well it survives contact with a reasoner. Ideally the reasoner leaning only on the base should be as confident as the evidence in the base warrants. Any more or less confidence is a failure of the base and not a failure of the reader. This instrument measures that deviation, on real cases. It caught a real failure on a real 26-claim base.

## Start here

For the fastest path in, read [`START_HERE.md`](START_HERE.md): a no-key dry run, the one-click demo and the two commands that carry the submission. For the written argument, read [`00_SUBMISSION_CORE.md`](00_SUBMISSION_CORE.md); its first pages give the claim, then a self-evaluation against the seven criteria. For what to submit and in what order, read [`SUBMISSION_MANIFEST.md`](SUBMISSION_MANIFEST.md). The instrument is [`epistack_eval.py`](epistack_eval.py).

Since the knowledge base is an input to the instrument, it can be pointed at any base, not just mine. That includes other entrants' bases or any base FLF itself wants to check.

## Run it

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
python3 epistack_eval.py --case covid_large --model claude-opus-4-8
python3 epistack_eval.py --case covid        --model claude-sonnet-4-6
python3 epistack_eval.py --case blackholes   --model claude-opus-4-8
python3 epistack_eval.py --case eggs         --model claude-sonnet-4-6
```

With no key, see the report shape first with `python3 epistack_eval.py --dry-run`, which prints placeholders. For a one-click run, build the `Dockerfile`, or open `epistack_eval_colab.ipynb` in Colab, whose dry-run cell needs no key. To run it on a base built yourself, with no code edits, use `python3 epistack_eval.py --kb-file your_base.json --model claude-opus-4-8`. The schema is in `external_base_template.json`.

## What it measures

The evaluation is one script with four probes and each measures a different failure. Part A, the linkage-integrity test, checks reasoning from the base only, updating on a held-out claim it never saw and holding up under a counter-argument. Part B, the double-counting probe, checks whether correlated claims shown separately move a reasoner further than the same claims flagged as one. Part C, the retracted-claim probe, checks whether a reasoner leans on evidence that has been withdrawn. Part D, the repair-and-reverify loop, reshapes the base to collapse the correlated cluster and re-measures the fix. Every report leads with a machine-readable `PRIMARY_SIGNALS` block.

## The cases

The same instrument runs on three differently-shaped starter cases and one real, large base. Only the knowledge base and the warranted shape change. COVID is contested, so wide uncertainty is warranted. Black holes is settled, so confident-safe is warranted and the failure to catch is false balance. Eggs is ill-posed, so the failure is a confident universal answer instead of catching that the effect depends on who you are. covid_large is the real one, at 26 claims, built by deep research on two models, reconciled, then stripped of correlation flags and strengths before the instrument saw it.

## The headline result

Reading the unflagged large base, the instrument reproducibly caught a double-counting failure. Showing the five correlated Wuhan-cluster claims (c3, c20, c21, c22, c23) as separate strikes and not flagged as one shared cause moved a reasoner further toward a lab origin in every one of fourteen runs, seven per model. The effect averaged about 0.116 on the stronger model (ranging 0.093 to 0.137) and about 0.082 on the lighter one (ranging 0.060 to 0.107). I report the noisy reads, as the direction is still robust. The correlation had been removed by hand during reconciliation. The instrument, reading the unflagged version, independently caught that a reasoner still double-counts it. Part C plants a genuinely retracted claim, the withdrawn 2020 HIV-1-insertions preprint. Both models correctly discounted it when the retraction was labelled. Part D then collapses the cluster into one node and, on the stronger model, confirms the repaired base lands at the warranted weight, while the check flags that the same fix falls short on the lighter one. Full detail is in `README.txt`, `partD_run_outputs.txt` and the core document.

## Limitations

These are LLM personas across a few runs and not a cohort of humans, so the results are more pointing than proving. The instrument scored against the structure of each case. Effort is proxied by claims read. The double-counting probe is not matched on sampling temperature across the two models, which is constant across runs and named. The calibration-per-claim figure is a coarse secondary diagnostic. The full bounds are in the core document, Section 8.

## Reuse

Cooperative competition, so reuse is welcome. Released under the MIT License (see `LICENSE`). Questions: hi@vj9.org
