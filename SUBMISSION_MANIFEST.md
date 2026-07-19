# Submission package: what to submit and reading order

This is an update to my early-feedback-round submission and carries it forward, so these files replace what I sent before. Everything here is ready to submit. The core sits within the roughly ten-page reading budget and everything else is supporting material or appendix.

## Reading order

Start with `00_SUBMISSION_CORE.md`, or the PDF, which is the written argument. It opens with the claim, then a self-evaluation against the seven criteria, then the argument runs from the deep-research head-to-head in Section 3 to the repair loop in Section 7 and the bounds in Section 8. Next is `START_HERE.md`, the fastest way to exercise the tool, with a no-key dry run, the one-click demo and the two commands that carry the submission. Then run it, in one command, with `python3 epistack_eval.py --case covid_large --model claude-opus-4-8`.

## What each file is

The core, within the reading budget, is `00_SUBMISSION_CORE.md`, the written argument, together with `Epistack_Submission_Core.pdf`, the same core formatted for submission.

The code and executable material has no length limit and includes a one-click demo. It is `epistack_eval.py`, whose most interesting parts to inspect are the `covid_large` base and its hidden answer key, `run_doublecount` for Part B, `run_retraction` for Part C and `run_repair` for Part D. It also includes `Dockerfile` and `epistack_eval_colab.ipynb` for the one-click runnable demo where the Colab dry-run cell needs no key. It also includes `external_base_template.json`, the schema for `--kb-file` so the instrument runs on any base with no code edits.

The supporting material is `README.md`, the repository landing page, `README.txt`, the full run outputs across seven runs per model with honest noise reporting, `partD_run_outputs.txt`, the raw repair runs for both the naive and the weight-preserving collapse. `LICENSE` is MIT. The individual per-run capture files from the earlier rounds stay in the repository alongside `README.txt`, as they were before.

## What is new since the early feedback round

The early version was a basic argument. This carries it forward on several fronts. It now runs on a real 26-claim knowledge base built by deep research on two models and reconciled into one ledger, then stripped of correlation flags and strengths before the instrument saw it. It has a retracted-claim provenance probe. It has a repair-and-reverify loop that reshapes the base to collapse the correlated cluster and re-measures the fix, which turns the detector into a repair tool. The argument now opens with the claim and a self-evaluation against the criteria. The calibration figure is a labelled secondary diagnostic and every report leads with a primary-signals block. Because the calibration computation itself is unchanged, every archived run number remains reproducible. A one-click demo through the Dockerfile and the Colab notebook was added, along with the `--kb-file` external input, so the base is literally an input.

## One optional run, for the strongest generalization evidence

Running the instrument on a base I did not build needs my Anthropic API key, as the whole tool does, so I can point `--kb-file` at a base built the covid_large way, which is deep research on two models reconciled, for a base with the same provenance. Part D is already run and its numbers are in Section 7 and in `partD_run_outputs.txt`, so the loop is closed and reported.
