Run outputs for epistack_eval.py (combined, v5 - 4 cases, incl covid_large).

covid_large is the real 26-claim COVID-origins ledger, unflagged: built by deep
research on two independent models, reconciled into one ledger, then stripped of
strength ratings and correlation flags before the instrument ever saw it. The
correlation map and warranted shape were held back as a separate hidden answer key.

Part B on this case uses the base's REAL five-claim Wuhan cluster (c3, c20, c21,
c22, c23), all of which descend from the single fact that the relevant laboratory
is in Wuhan, the city where the outbreak began. It is not a generic probe.

-------------------------------------------------------------------------------
HEADLINE: mean_double_counting_effect, seven runs per model, none discarded
-------------------------------------------------------------------------------

  Run        Opus     Sonnet
   1         0.127     0.077
   2         0.117     0.060
   3         0.127     0.083
   4         0.107     0.107
   5         0.107     0.067
   6         0.137     0.083
   7         0.093     0.100
  ----------------------------
  mean       0.116     0.082
  range   0.093-0.137  0.060-0.107
  sd         0.015     0.017

Read honestly: the effect fired in 14 of 14 runs and was positive on every
persona, so the DIRECTION is robust. The MAGNITUDE is noisy. The stronger model
shows the larger effect on average (+0.034 mean gap), but the ranges overlap
between 0.093 and 0.107, and in run 7 Sonnet was slightly higher than Opus.

The measurement is coarse. The models answer in roughly 0.05 steps, so with three
personas one persona moving a single step shifts a run mean by about 0.017. An
earlier draft claimed a tight 0.12 to 0.13 band on Opus; only 2 of 7 runs land
there, so that claim was replaced with the mean and the full range.

Part A across the same runs: held-out transfer 1.0 on every persona in every run
on both models. Crux localization ran 1.0 on Sonnet and 0.67 to 1.0 on Opus.
Warranted-stance survival ran 1.0 on Opus and 0.67 to 1.0 on Sonnet. Calibration
per claim read stayed small on this base, about 0.003 on both models.

Comparability note: the double-counting probe passes temperature 0.7 to Sonnet;
Opus does not accept a temperature parameter and runs at its default. The two
models are therefore not matched on sampling temperature. Constant across all runs.

-------------------------------------------------------------------------------
PART C: retracted-claim provenance probe (covid_large), three runs per model
-------------------------------------------------------------------------------

Plants one genuinely retracted claim (the withdrawn 2020 HIV-1-insertions
preprint) as apparent lab-origin evidence, in two arms: shown live, and shown
with an explicit retraction note. mean_retracted_still_moved is how much belief
still moved when the claim was labelled retracted; near zero = the reasoner
correctly discounted the withdrawn claim.

  Run        Opus     Sonnet
   1         0.00     -0.015
   2         0.00     -0.005
   3         0.00     -0.010
  ----------------------------
  mean       0.00     -0.010
  mean_retraction_ignored_effect: Opus ~0.057, Sonnet ~0.032

Reading: both models correctly discounted the retracted claim. Shown live,
belief moved toward a lab origin by about 0.04 to 0.10; shown with the
retraction, that movement essentially vanished. Caveats: the retraction was
explicitly labelled (so this shows models honoring a clear retraction, not
catching a quietly withdrawn claim); and Sonnet returned unparseable output on
three cells across the three runs, so its means rest on fewer observations than
Opus (which had none). Part A and Part B were unchanged in these runs.

Part C run files: covid_large_opus_partC1..3.txt, covid_large_sonnet_partC1..3.txt

-------------------------------------------------------------------------------
FILES
-------------------------------------------------------------------------------

  covid_large_opus_run1..run3.txt     runs 1-3, transcribed from the session output
  covid_large_sonnet_run1..run3.txt   runs 1-3, transcribed from the session output
  covid_large_opus.txt                run 4, raw capture
  covid_large_sonnet.txt              run 4, raw capture
  covid_large_opus_r1..r3.txt         runs 5-7, raw captures
  covid_large_sonnet_r1..r3.txt       runs 5-7, raw captures

Provenance is stated plainly: runs 1-3 are reformatted transcriptions of the
original session output; runs 4-7 are raw stdout captures.

-------------------------------------------------------------------------------
TO REPRODUCE
-------------------------------------------------------------------------------

  pip install anthropic
  export ANTHROPIC_API_KEY=sk-...
  python3 epistack_eval.py --case covid_large --model claude-opus-4-8
  python3 epistack_eval.py --case covid_large --model claude-sonnet-4-6

Expect the effect to fire every time. Expect the magnitude to move run to run,
roughly 0.09 to 0.14 on Opus and 0.06 to 0.11 on Sonnet.

LLM personas, seven runs per model. Suggestive, not proof. Models are named.
