# Start here: fastest path in and where to look

This points at the roughly two pages that matter. The most useful commands to try are below, along with the most interesting parts of the code to inspect.

## See the shape in 30 seconds, with no API key

```bash
python3 epistack_eval.py --dry-run
```

This prints the full report structure with placeholder numbers, so the layout is clear before running anything. The Colab notebook `epistack_eval_colab.ipynb` has a dry-run cell that also needs no key.

## One-click runnable demo

In Colab, open `epistack_eval_colab.ipynb`, run the Setup and Dry run cells with no key, then paste a key into the Key cell to run the real cases. With Docker the flow is a fresh machine to a running process in about five minutes, most of which is the image pull.

```bash
docker build -t epistack .
docker run --rm epistack --dry-run
docker run --rm -e ANTHROPIC_API_KEY=sk-... epistack --case covid_large --model claude-opus-4-8
```

## The two commands that carry the submission

```bash
python3 epistack_eval.py --case covid_large --model claude-opus-4-8
python3 epistack_eval.py --case blackholes  --model claude-opus-4-8
python3 epistack_eval.py --case eggs        --model claude-opus-4-8
```

The first is the headline. It runs the real 26-claim base, unflagged. Part B independently re-derives the five-claim Wuhan-cluster double-count that reconciliation had removed by hand. Part D then collapses that cluster into one node and, on the stronger model, confirms the repaired base lands at the warranted weight. The second and third show the same instrument travels. The settled case catches false balance and the ill-posed case catches heterogeneity, so only the base and the warranted shape change.

Read the `PRIMARY_SIGNALS` block at the top of each report first. It carries crux localization, the double-counting effect, held-out transfer, warranted-stance survival and the Part D repair result. The `secondary_diagnostic_calibration_per_claim_read` figure is a coarse diagnostic that sits near zero on wide cases, so it is deliberately not the headline.

## Run it on a base I never touched

The base is an input, so the instrument runs on any base with no code editing.

```bash
python3 epistack_eval.py --kb-file your_base.json --model claude-opus-4-8
```

The schema is in `external_base_template.json`. It works on another entrant's base, an FLF base, or a base built the covid_large way, which is deep research on two models reconciled into one ledger.

## Most interesting code to inspect

The `covid_large` base and its hidden answer key are the place to start. The flat 26-claim ledger and, in its notes, the two correlated clusters rooted at c3 and c14 were held back as the key the instrument was scored against. Part B, in `run_doublecount`, targets this base's real five-claim Wuhan cluster (c3, c20, c21, c22, c23). Part C, in `run_retraction`, plants the withdrawn 2020 HIV-1-insertions preprint and measures whether a reasoner leans on it. Part D, in `run_repair`, collapses the correlated cluster into one node and re-measures the fix. The functions `cal_distance` and `run_linkage` show how calibration, crux localization, held-out transfer and stance survival are scored per persona.

## What to read alongside the code

The run outputs, seven per model, with the honest noise reporting are in `README.txt`. The new repair runs are in `partD_run_outputs.txt`.

## Limitations

These are LLM personas across a few runs, so the results are more pointing than proving. The models are always named. The scoring is against each case's structure, effort is proxied by claims read. The double-counting probe passes temperature 0.7 to the lighter model while the stronger model runs at its default, so the two are not matched on sampling temperature, which is constant across runs. The calibration computation is unchanged from the earlier runs, so every archived run number remains reproducible.
