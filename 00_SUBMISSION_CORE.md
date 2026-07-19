# Calibration as Linkage Integrity

### Does a knowledge base's rigor survive contact with a reasoner?

Author: VJ, Head of Design and Learning Transformation at a global financial firm. Contact: hi@vj9.org. Repository: https://github.com/vaibhav-labs/Epistack_Eval

---

## A note on what this is

This is an update to my earlier submission. I sent an earlier version for the early feedback round and received important feedback from Oly. I took that direction and kept building on it and the compute support from FLF covered my additional runs. The core idea is unchanged. What has changed is that it now runs on a real 26-claim knowledge base, it has a retracted-claim provenance probe and it now has a repair-and-reverify loop that reshapes the base to fix the failure it finds and re-measures to confirm the fix. I am updating my earlier work and carrying it forward so this document and the files with it replace what I sent before.

## 1. The claim

The real test of the rigor of a knowledge base is how well it survives contact with a reasoner. Ideally the reasoner leaning only on the base should be as confident as the evidence in the base warrants. Any more or less confidence is a failure of the base and not a failure of the reader.

A base can have a very well organised structure and confident-sounding claims and still leave the reasoner who leans on it believing things the evidence does not support. That gap is invisible when we only inspect the artifact, because the failure shows up somewhere else, in the reasoner who used it. Structure and provenance still matter on the input side and they certify the quality of what goes in. But even with them, the result may still lead to the reasoner double-counting correlated evidence, missing the one choice the answer actually hinges on, or leaning on a claim that has been withdrawn. That is why the base has to be tested by what it does to a reasoner and not only by how it looks.

This is also why the instrument sits one layer above deep research. Is it beating off-the-shelf deep research? In fact it is not competing with deep research; in terms of layers, it sits one layer above it. Deep research can produce the artifact, which is the set of claims and the knowledge base. My instrument measures whether that artifact survives contact with the reasoner. You can even run deep research to build the base, then point the instrument at it to see where a reasoner ends up more or less confident than the evidence warrants, which claims are load-bearing and where correlated evidence gets double-counted. That is a very important gap that deep research doesn't fill.

## Self-evaluation against the judging criteria

Before the rest of the argument, I have checked my own work against the seven criteria, so it is easy to see where each one is addressed.

| Criterion | What it asks | Where I address it |
|---|---|---|
| **1. Epistemic uplift** | Better than off-the-shelf deep research on the same sub-question and makes the load-bearing evidence visible | Section 3 is a head-to-head. Deep research built the base and the instrument caught the double-counting it left in, which deep research cannot check on its own output. Per-claim crux and load-bearing detection are in Part A. |
| **2. Generalizability** | Works across differently-shaped cases and applies beyond the three provided | Section 4 runs the same instrument across contested, settled and ill-posed shapes and one real large base. `--kb-file` (Section 2) makes any external base an input, so it is not tied to the three cases. |
| **3. Compounding and shareability** | Produces structured, interrogable outputs another team can extend | The output is machine-readable JSON led by a primary-signals block and since the base is an input, any base including another entrant's is testable with no code edits. |
| **4. Scalability** | Improves with stronger models, more compute and more scrutiny | Section 5 shows the metric is model-dependent, so the stronger model pulls more warranted calibration from the same base. The reasoning comes from a real model, so the instrument benefits as capability rises. |
| **5. Methodological transparency** | Well-specified, with tradeoffs and uncertainty named | Sections 7 and 8 name every bound, including personas, structure-based scoring, effort proxied by claims read, a temperature mismatch, a demoted metric and the tests I considered and left unbuilt. |
| **6. Adversarial robustness** | Holds up under motivated reading and interrogation and bounds its failure modes | The instrument tests robustness directly, through a counter-argument probe and the retracted-claim probe in Section 6. Every bound is named. |
| **7. Insight contribution** | Shifts how the problem is seen, with a potent counterexample | Section 1 states the claim, that rigor is a property of what a base does to a reasoner. Section 3 is the counterexample, a hand-de-correlated expert base that still makes a reasoner double-count. |

## 2. The instrument

`epistack_eval.py` is a dependency-light script that runs the evaluation and it runs in one command from the linked repository. It sends real reasoners, LLM personas, through the knowledge base. Its reasoning comes from a real model and not mockup answers, so the result is not baked in.

The evaluation is one script with four probes and each measures a different failure.

| Probe | What it measures |
|---|---|
| **Part A**, linkage integrity | Reasoning only from the base, updating on a held-out claim it never saw and holding up under a counter-argument. It also reports a coarse secondary diagnostic, the calibration gained per claim read. |
| **Part B**, double-counting | Whether correlated claims shown separately move a reasoner further than the same claims flagged as one shared cause. |
| **Part C**, retracted-claim provenance | Whether a reasoner leans on evidence that has been withdrawn. |
| **Part D**, repair-and-reverify | Reshapes the base to collapse the correlated cluster into one node, then re-measures to confirm the repaired base no longer inflates belief. |

The instrument runs each test through three reasoner personas that differ only in the starting belief.

| Reasoner persona | Where it starts |
|---|---|
| Leans toward a lab origin | a low prior on a natural origin |
| Neutral | a middle prior |
| Leans toward zoonosis | a high prior on a natural origin |

The three priors spanning the range is the smallest set that tests what matters here, whether the base claims pull the reasoner toward the warranted answer irrespective of where they start.

For a contested question there is no single true answer to calibrate against, so the instrument does not use one. The target is not a probability. It is the structure of the disagreement, which is a fact about the debate, not a verdict on it.

One thing I want to call out upfront. The knowledge base is an input to this instrument and is not a part of it. So it can be pointed at anyone's knowledge base and not just mine. That means any other entrants or any base FLF itself wants to check. `--kb-file your_base.json` points the instrument at any base with no code changes.

## 3. The head-to-head with deep research on a real base

I built a real, large knowledge base the way a serious investigator and reasoner would and then tested it. Here is what I did, in order.

```text
 [1]  Deep research on COVID origins, run on two independent models
        |
        v
 [2]  Reconcile the two outputs into one 26-claim evidence ledger
        |
        v
 [3]  Strip the ledger into a flat, unflagged claim list
      (correlation structure and strengths held back as a hidden answer key)
        |
        v
 [4]  Run the instrument on the unflagged list
```

This directly answered whether this beats off-the-shelf deep research. Deep research built the base and the instrument tested whether that base's rigor survives a reasoner.

The instrument caught a double-counting failure in the base, reproducibly. The base contains a cluster of five claims that all reduce to one underlying fact, that the relevant lab is in Wuhan, the city where the COVID outbreak began. Those claims are c3, c20, c21, c22 and c23. When those five correlated claims are shown to a reasoner as separate strikes and not flagged as one shared cause, the reasoner moved further toward a lab origin. On the stronger model this effect averaged about 0.116 across seven separate runs, ranging 0.093 to 0.137. On the lighter model it averaged about 0.082, ranging 0.060 to 0.107. It was positive in every run on both models and on every persona. The correlation had been removed beforehand and the instrument, reading the unflagged version, independently caught that a reasoner still double-counts it. The measurement is coarse: models answer in roughly 0.05 steps, so with three personas one persona moving a single step shifts the run mean by about 0.017. I report the noisy reads, as the direction is still robust.

Flagging correlations in a base does not cover the reasoner who reads the claims. That is a failure that does not come out purely by inspecting the base and it is exactly what an output-side instrument is for. The base it tested was generated externally by deep research and is not something I wrote, so the failure is not manufactured by a base built to fail. All fourteen run outputs, seven per model, are in the repository and Part B uses this base's real five-claim Wuhan cluster (c3, c20, c21, c22, c23), so a reviewer can see exactly which claims are involved.

## 4. It also travels across three starter shapes

The headline above is the large base. The same instrument also runs on three smaller, differently-shaped starter cases, which is how I checked it travels and does not just fit one artifact. Only the knowledge base and the warranted shape change. COVID is contested and wide uncertainty is warranted. Black holes is settled, confident-safe is warranted and the failure to catch is false balance. Eggs is ill-posed and the failure is a confident universal answer instead of catching that the effect depends on who you are.

| Case | Shape | Model | Found the crux | Held-out transfer | Confidence survived | Secondary calibration per claim |
|---|---|---|---|---|---|---|
| COVID | contested | Sonnet | 0.67 | 1.0 | 1.0 | about -0.01 |
| COVID | contested | Opus | 1.0 | 1.0 | 1.0 | about +0.005 |
| Black holes | settled | Sonnet | 1.0 | 0.0 (note) | 1.0 | about +0.09 |
| Black holes | settled | Opus | 1.0 | 0.0 (note) | 1.0 | about +0.11 |
| Eggs | ill-posed | Sonnet | 0.0 | 1.0 | 1.0 | about +0.009 |
| Eggs | ill-posed | Opus | 1.0 | 1.0 | 1.0 | about +0.004 |

Two results held across every run on both models. Reasoner personas transferred reasoning to the held-out claim, updating in the correct direction, by a sensible amount and for a reason that used the claim. Their confidence held under a direct counter-argument and it did not collapse. The crux localization is model-dependent. It was patchy on the lighter Sonnet model and very reliable on the stronger Opus model, which is exactly what the instrument aims to show. The black-holes and eggs knowledge bases are compact, defensible starters, meant to show the instrument travels and not authoritative verdicts on those cases. One caveat, the held-out transfer for black holes scored 0.0 on both models. The held-out claim reinforced an answer that is already at zero, so there was actually no room left to deviate and the instrument reported no update as there was no transfer. I note it rather than dress it up.

## 5. Stronger the model, cleaner the metric

The settled case, black holes, gave the clearest positive result. On the stronger Opus model the mean calibration increase was about 0.57 and the most skeptical persona gained the most at 0.75. None of the personas fell for false balance when the counter-argument pushed them to doubt a settled answer. The metric is model-dependent. It came out cleaner and more positive on the stronger model and weaker on the lighter one. It pointed to the fact that a better reasoner extracts more warranted calibration from the same base. Because the reasoning comes from a real model, the instrument benefits as base-model capability rises and that is the scalability the competition asks for, shown here on real runs.

## 6. The retracted-claim probe

It is possible that a base carries a claim that was later retracted. A reasoner reading the base needs to notice the retraction and should not lean on the withdrawn evidence. So I built a probe on the large base to test that. I planted one genuinely retracted claim as if it were live evidence for a lab origin, the 2020 preprint that reported HIV-1 like insertions in the spike protein and was later withdrawn by its own authors after the claimed similarities were shown to be too generic. I showed it to the reasoner two ways, once plainly and once carrying an explicit note that it had been retracted and is not valid evidence. What I measure here is how much belief still moves when the claim is labelled as retracted.

Across the three runs per model, both models correctly discounted the retracted claim. Shown live, they moved toward a lab origin by about 0.04 to 0.10. Shown with the retraction, that movement essentially vanished. The mean residual move was 0.00 on the stronger Opus model and about minus 0.01 on the lighter Sonnet one. There are two limitations here. The retraction was explicitly labelled, so this shows models honor a clear retraction and it does not show that they would catch a quietly withdrawn claim with no marker. The lighter Sonnet model returned unparseable output on a few cells, so its numbers rest on fewer observations than the stronger model's. Provenance matters as an input-side tag and whether a reasoner actually respects it only shows up downstream, which is what this probe reads.

## 7. From detector to repair: closing the loop

A detector that only flags a failure still leaves the base builder with the problem. So I built the repair-and-reverify loop as Part D. The instrument already locates the correlation structure a reasoner is blind to. The repair uses that to reshape the base, collapse the correlated cluster into one node that states the shared cause and then re-measure to confirm the double-counting actually dropped. That closes the loop from diagnosis to fix to check. The re-measurement reports two numbers, the residual after repair (how far the collapsed node's belief still sits from correctly flagging the cluster) and the double-counting removed (how much of the inflation the repair took out). A faithful repair removes about as much as the double-counting effect and leaves the residual near zero, because it takes out the duplication and stops there.

I ran this and the re-measurement did real work. My first collapsed node was a single short sentence and across six runs it overshot on both models, pulling belief about 0.11 below the correctly-flagged weight on the stronger model and about 0.23 below on the lighter one, so the check did not confirm it. The negative residual told me what was wrong, that the one-sentence node read as a minor aside and carried less weight than five correlated but real observations deserve, so it removed the duplication and kept going past the warranted weight. I rewrote the collapsed node to carry the cluster's full weight while still stating it as one correlated line and I re-ran it six more times.

The second result is clean and it is model-dependent, the same pattern the rest of the submission shows. On the stronger model the repair landed. The residual was about 0.017, sitting on zero and it confirmed in all three runs. The amount removed, about 0.085, sat close to the double-counting effect of about 0.111 on those same runs. On the lighter model the same node still fell short. The residual was about minus 0.11, tight across all three runs and it did not confirm. It removed about 0.195, more than the double-counting effect, taking out some genuine weight along with the duplication. The lighter reasoner leans harder on the raw separate strikes and carries the single collapsed statement lower than the cluster deserves, so the same fix that lands on the stronger model falls short on the lighter one. The double-counting effect itself re-confirmed on all of these runs, about 0.111 on the stronger model and 0.103 on the lighter one.

So the loop does what a repair tool has to do. The check caught the first collapse overshooting on both models, it confirmed the weight-preserving collapse on the stronger model and it flagged that the same fix still falls short on the lighter one. A check that passes one repair and fails another, reproducibly, is doing its job. This turns the detector into a repair tool and it runs in the same one command.

Two boundaries I want to state plainly. Between the two nodes I also opened the confirm tolerance from a residual of 0.03 to 0.05, because the models answer in roughly 0.05 steps, so a residual within one step of zero cannot be told apart from a match. The stronger model's residual of 0.017 confirms under either threshold, so the pass there does not depend on that change and the instrument reports the raw residual throughout so anyone can apply a stricter bar. And in this minimal version the cluster membership is handed to the repair from the detector together with the hidden answer key. A fully automated version would pipe the cluster the detector identifies straight into the repair and that is the obvious next step.

## 8. What it does not show

These are its limitations.

- These are LLM personas across a few runs and not a cohort of humans, so the results are more pointing than proving. I always name the models.
- The instrument scored against the structure of each case.
- Effort is proxied by claims read and not real human time.
- The double-counting probe is not matched on sampling temperature across the two models. Sonnet runs at 0.7 and Opus does not accept a temperature parameter, so it runs at its default. This is constant across every run and I name it rather than hide it.
- The calibration-per-claim figure is a coarse secondary diagnostic. On a wide warranted band a reasoner scores well by holding wide error bars alone, so it sits near zero on contested cases. I demoted it so every report leads with the primary signals.
- The retraction is labelled. A harder unlabelled version is the next step, built on a synthetic claim the model has never seen, so the knowledge mask does not leak into recall.

I considered these further constraints and did not build them.

- Order sensitivity, present the same evidence in a different order and see if the conclusion changes.
- A plausible distractor, add an irrelevant but plausible claim and see if it moves the needle.
- Consistency across restarts, run the same persona twice and measure the variance.
- Authority pressure, tell the reasoner most experts think X and see if it caves.
- Missing-evidence awareness, ask what it would need to resolve the question.

I have called and listed them here purposely, because knowing which tests would extend the instrument or contain it is my intentional effort to show methodological transparency for this submission. The planted retracted claim was the most valuable of these and I built it as Part C.

## 9. Where this goes: from a detector to the Epistack Eval Standard

What I have built is a detector pointed at one base, which measures whether a reasoner leaning on that base double counts correlated evidence, misses the crux, or leans on a withdrawn evidence, together with a minimal repair loop that reshapes the base and re-measures the fix. This is a demonstrated result on a real base and it is bounded. The direction it opens follows from a property the instrument already has.

Since the base is an input, the instrument runs unchanged across many bases which are built by different people or systems, on the same question. You move from "does this base hold up under a reasoner" to "of every base anyone has built on this question, which hold up and which collapses". That moves this from an instrument to a standard, an Epistack Eval Standard, a single reusable score any base can be measured against, so that bases built by wholly different methods and people become comparable on the important thing, whether their rigor survives a reasoner. This is the direction Oly pointed at in his early feedback, being interested to see how this gets operationalised and might end up as an Epistack Eval and it is exactly what I want to build.

The sharpest version of that score is adversarial in nature, which does not measure calibration just once. It measures how well a reasoner leaning on a base holds its calibration under sustained, targeted cross examination and ranks bases by which one produces a reasoner that decays under pressure. A base whose linkages are sound should hold, while a base that only looked sound should come apart when pressed.

There is a problem that sits between here and there though. To rank bases against each other, the measurement has to be steadier than the differences between the bases, which right now is not the case. My own runs moved from one run to the next, the same base reads from 0.09 to 0.14. That deviation is fine when I report a single range, which is what I do now. It is not fine for ranking, because the gap between two bases could be smaller than the wobble inside one base itself. So the core research problem of the comparative version is driving the measurement deviation below the signal between bases. More runs narrow it slowly. A less coarse metric that aggregates over many probe points instead of differencing two coarse outputs could narrow it faster. It needs to be solved before any ranking means anything.

The second arm is repairing and Part D is its proof of concept on one cluster in one base. The repair reshapes the base and re-measures the fix. Confirming the fix needs a measurement stable enough to trust, which ties it back to the same obstacle. What is built is the detector, the minimal repair loop and the evidence that the failure it catches is a real one on a real base. I am submitting the proof point and showing where it leads.

## Why I made it

Influencing and leading people from data, to information, to sound decisions under ambiguity and uncertainty at corporate scale is my job in learning design and employee transformation. That is where the instinct comes from, that rigor is only impactful if it survives contact with the recipient. I built this instrument to make that instinct measurable.

This is a working instrument that measures whether a knowledge base's rigor survives a reasoner, on real cases, with reproducible results a reviewer can run. We now have an instrument that can test calibration. That is the difference between an argument about calibration and an instrument that tests it.
