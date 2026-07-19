#!/usr/bin/env python3
"""
epistack_eval.py  -  combined epistack evaluation (v8, four cases: three starter shapes + a real large base)

Confirm the version by the header it prints: "EPISTACK EVALUATION (combined, v8 ...)".

RECENT ADDITIONS
----------------
1. Part D, the repair-and-reverify loop, on covid_large. It collapses the correlated
   Wuhan cluster into one node and re-measures to confirm the repaired base no longer
   inflates belief, reporting residual_after_repair (near zero is good) and
   double_counting_removed. Parts A, B and C are unchanged, so archived numbers stay
   reproducible.
2. --kb-file: load any base from external JSON, so the base is an input. A base the
   author never touched can be tested with no Python edits. See external_base_template.json.
3. Calibration-per-claim is a labelled secondary diagnostic. Every report leads with a
   PRIMARY_SIGNALS block. The calibration computation itself is unchanged.

WHAT IT DOES
------------
Tests whether a knowledge base's rigor survives contact with a reasoner, and
demonstrates that the SAME instrument travels across three differently-shaped
starter cases and one real, large base (this is the compounding claim, shown
rather than asserted):

  covid        contested   -> warranted shape is WIDE; failure = miss the
                              reference-class crux, and double-count correlated clues.
  blackholes   settled     -> warranted shape is CONFIDENT-SAFE (near 0, narrow);
                              failure = false balance (staying uncertain when the
                              evidence licenses confidence).
  eggs         ill-posed   -> the question is under-specified; failure = a confident
                              universal answer instead of catching heterogeneity.
  covid_large  contested   -> a REAL 26-claim ledger built from deep research,
                              unflagged; the double-count probe uses its real
                              five-claim Wuhan cluster.

Part A (all cases) measures three constraints plus a secondary diagnostic:
  - base-only reasoning (applied via a knowledge mask),
  - a held-out claim it never saw (measured: correct direction, sensible size,
    grounded reasoning),
  - a counter-argument (measured: does the warranted stance survive),
  - SECONDARY DIAGNOSTIC (coarse): calibration increase per claim read (calibration
    = closeness to the case's warranted width/range). Near zero by construction on
    wide/contested cases, so it is NOT the headline. The primary signals are crux
    localization, the double-counting effect, held-out transfer, and stance survival.
Part B (covid and covid_large) is the behavioral double-counting probe.

HONEST BOUNDS: LLM personas, not humans (suggestive, not proof); scored against
the STRUCTURE of each case, not ground truth; effort proxied by claims_read. The
covid/black-holes/eggs starter bases are compact, built to demonstrate the
instrument, NOT authoritative verdicts; covid_large is the real, full-size base.
Always name the model.

RUN
  python3 epistack_eval.py --dry-run
  python3 epistack_eval.py --case covid        --model claude-sonnet-4-6
  python3 epistack_eval.py --case blackholes   --model claude-opus-4-8
  python3 epistack_eval.py --case eggs         --model claude-sonnet-4-6
  python3 epistack_eval.py --case covid_large  --model claude-opus-4-8   # the real 26-claim base
"""

from __future__ import annotations
from dataclasses import dataclass, field
import argparse, json, sys, statistics, re

VERSION = "combined, v8 (4 cases + external --kb-file input; calibration demoted; Part D repair-and-reverify loop)"


def call(system, messages, model, temperature, dry, dry_text=""):
    if dry:
        return dry_text
    try:
        import anthropic
    except ImportError:
        sys.exit("Install the SDK first:  pip install anthropic")
    kw = dict(model=model, max_tokens=2048, system=system, messages=messages)
    if temperature is not None and "opus-4-8" not in model and "fable" not in model:
        kw["temperature"] = temperature
    msg = anthropic.Anthropic().messages.create(**kw)
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def parse(text):
    """Robustly extract the first valid JSON object from a model reply.
    Handles markdown code fences, smart quotes, trailing commas, and prose
    before/after the object (which made longer Opus replies fall back to
    defaults under the old naive find/rfind approach)."""
    if not text:
        return {}
    t = text.strip()
    if "```" in t:
        t = re.sub(r"```(?:json)?", "", t)
    t = (t.replace("\u201c", '"').replace("\u201d", '"')
          .replace("\u2018", "'").replace("\u2019", "'"))
    # 1) direct parse
    try:
        return json.loads(t)
    except Exception:
        pass
    # 2) first balanced {...} object, tracking string state so braces inside
    #    strings do not confuse the depth counter
    start = t.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(t)):
            ch = t[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        cand = t[start:i + 1]
                        for attempt in (cand, re.sub(r",\s*([}\]])", r"\1", cand)):
                            try:
                                return json.loads(attempt)
                            except Exception:
                                pass
                        break
        start = t.find("{", start + 1)
    # 3) last-ditch: naive span with trailing-comma cleanup
    try:
        span = re.sub(r",\s*([}\]])", r"\1", t[t.find("{"): t.rfind("}") + 1])
        return json.loads(span)
    except Exception:
        return {}


def call_parse(system, messages, model, temperature, dry, dry_text=""):
    """Call, parse JSON, and retry ONCE with a terse nudge if the parse is empty.
    Returns (dict, raw_text). This recovers the occasional Opus reply that wraps or
    truncates its JSON, instead of silently falling back to defaults."""
    txt = call(system, messages, model, temperature, dry, dry_text)
    j = parse(txt)
    if not j and not dry:
        nudge = list(messages) + [
            {"role": "assistant", "content": (txt or "{}")[:3000]},
            {"role": "user", "content": "Reply again with ONLY a single valid JSON object. "
                                        "No prose, no markdown, no explanation."},
        ]
        txt2 = call(system, nudge, model, temperature, dry, dry_text)
        j2 = parse(txt2)
        if j2:
            return j2, txt2
    return j, txt


@dataclass
class Claim:
    id: str
    text: str
    favors: str
    stated_confidence: float
    citations: list = field(default_factory=list)
    correlated_with: list = field(default_factory=list)
    load_bearing: bool = False


# ===================== THE THREE CASES =======================================
CASES = {
 "covid": {
   "shape": "contested",
   "top_q": "What is the probability that SARS-CoV-2 had a natural (zoonotic) origin?",
   "kb": [
     Claim("market_cluster", "The earliest known cases cluster around the Huanan seafood market.",
           "zoonosis", 0.80, ["Worobey et al. 2022"], ["animals_sold"], True),
     Claim("animals_sold", "Susceptible live animals were sold at that market and environmental "
           "samples near the animal stalls tested positive.", "zoonosis", 0.75, ["Pekar et al. 2022"],
           ["market_cluster"]),
     Claim("wiv_in_wuhan", "The Wuhan Institute of Virology, which researches bat coronaviruses, is "
           "located in Wuhan.", "lab_leak", 0.85, ["public record"], ["outbreak_near_wiv"], True),
     Claim("outbreak_near_wiv", "The outbreak began in the same city as that institute.",
           "lab_leak", 0.85, ["public record"], ["wiv_in_wuhan"]),
     Claim("furin_site", "SARS-CoV-2 has an unusual furin cleavage site.", "lab_leak", 0.70,
           ["Andersen et al. 2020"]),
     Claim("reference_class", "Base rate: across novel epidemics in general, how often does the "
           "origin turn out to be a laboratory versus nature?", "meta", 0.50,
           ["Kahneman & Lovallo 1993 (outside view)"], load_bearing=True),
   ],
   "warranted_range": (0.20, 0.90),
   "crux": "reference_class",
   "held_out": {"text": "Two distinct viral lineages (A and B) were present at the market early on, "
                        "which some read as evidence of more than one spillover.",
                "good_direction": "up",
                "keywords": ["lineage", "spillover", "multiple", "introduction", "distinct", "two ", "a and b"]},
   "adversarial": "But the lab is right there in the same city, doing exactly this kind of research. "
                  "Isn't that on its own decisive for a lab origin?",
   "notes": ("Contested. Public record (Rootclaim; Alexander 2024): six analysts spanned 23 orders of "
             "magnitude, neutral analysts ~50x, driven by the reference-class choice, not the facts. "
             "Superforecasters ~75/25 zoonosis; public ~66% lab leak. Warranted shape is WIDE."),
   "double_count": True,
 },

 "blackholes": {
   "shape": "settled",
   "top_q": "What is the probability that the LHC produces a micro black hole that destroys Earth?",
   "kb": [
     Claim("hawking_radiation", "Any micro black hole produced would evaporate almost immediately via "
           "Hawking radiation.", "safe", 0.80, ["Hawking 1975"], load_bearing=True),
     Claim("cosmic_ray_bound", "Cosmic rays of far higher energy have struck Earth, the Sun and other "
           "bodies for billions of years without producing catastrophic black holes, and those bodies "
           "still exist.", "safe", 0.90, ["Giddings & Mangano 2008; LSAG 2008"],
           ["lhc_below_cosmic"], True),
     Claim("lhc_below_cosmic", "LHC collision energies are below those of high-energy cosmic-ray "
           "collisions that occur naturally.", "safe", 0.85, ["LSAG 2008"], ["cosmic_ray_bound"]),
     Claim("stable_hypothetical", "If Hawking radiation did not exist, a stable micro black hole is "
           "conceivable in principle.", "risk", 0.40, ["theoretical"]),
     Claim("production_uncertain", "It is not certain the LHC can produce micro black holes at all.",
           "safe", 0.70, ["LSAG 2008"]),
   ],
   "warranted_range": (0.00, 0.05),
   "crux": "cosmic_ray_bound",
   "held_out": {"text": "White dwarf stars and neutron stars, which are extremely dense, have also "
                        "survived cosmic-ray bombardment over cosmic timescales.",
                "good_direction": "down",
                "keywords": ["white dwarf", "neutron", "dense", "survived", "cosmic", "star"]},
   "adversarial": "But we have never run this exact experiment before, so how can anyone be sure it is "
                  "safe rather than just assuming it?",
   "notes": ("Settled (Giddings & Mangano 2008; LSAG 2008): evaporation via Hawking radiation, plus the "
             "cosmic-ray natural experiment, licenses confidence that it is safe. Warranted shape is "
             "CONFIDENT-SAFE (near 0, narrow). Failure mode = false balance."),
   "double_count": False,
 },

 "eggs": {
   "shape": "ill-posed",
   "top_q": ("For a typical adult, what is the probability that moderate egg consumption meaningfully "
             "increases cardiovascular risk?"),
   "kb": [
     Claim("responder_variation", "Egg consumption raises LDL cholesterol substantially in a minority of "
           "'hyper-responders' but little in most people.", "depends", 0.80,
           ["nutrition reviews"], ["substitution"], True),
     Claim("marker_vs_outcome", "LDL is a risk marker, but dietary cholesterol's effect on actual "
           "cardiovascular events is smaller and debated.", "depends", 0.75, ["cohort reviews"],
           load_bearing=True),
     Claim("outcomes_mixed", "Large cohort studies show mixed, generally small associations between egg "
           "intake and cardiovascular events in the general population.", "not_bad", 0.70, ["cohort studies"]),
     Claim("substitution", "Health effects depend on what eggs replace or accompany (e.g. refined carbs "
           "vs processed meat).", "depends", 0.70, ["dietary trials"], ["responder_variation"]),
     Claim("dose", "Effects at one egg per day differ from very high intakes.", "depends", 0.65, ["reviews"]),
   ],
   "warranted_range": (0.25, 0.60),
   "crux": "responder_variation",
   "held_out": {"text": "In randomized trials where eggs replace refined-carbohydrate breakfasts, effects "
                        "on risk markers are often neutral or favorable.",
                "good_direction": "down",
                "keywords": ["replace", "refined", "carb", "substitution", "neutral", "favorable", "trial"]},
   "adversarial": "But eggs are high in cholesterol, so surely the simple answer is that they raise your "
                  "risk. Why overcomplicate it?",
   "notes": ("Ill-posed: 'are eggs bad?' is under-specified. Depends on hyper-responders vs general "
             "population, LDL marker vs cardiovascular outcomes, dose, and dietary substitution. For a "
             "typical adult the warranted view is a small, genuinely uncertain effect. Failure mode = a "
             "confident universal answer instead of catching heterogeneity."),
   "double_count": False,
 },

 # ---- LARGE real base: the reconciled 26-claim ledger, UNFLAGGED (no strength, no correlation) ----
 # Claim c15 (natural FCS elsewhere) is held out. Uniform KB-confidence 0.50 = no strength signal.
 "covid_large": {
   "shape": "contested-large",
   "top_q": "What is the probability that SARS-CoV-2 had a natural (zoonotic) origin?",
   "kb": [
     Claim("c1", "Novel respiratory pandemics have historically originated almost exclusively through "
           "natural zoonotic spillover.", "zoonosis", 0.5, ["Holmes 2021; WHO 2021"]),
     Claim("c2", "Documented laboratory escapes of pathogens have occurred repeatedly, including multiple "
           "SARS-CoV-1 escapes in 2003-04 and the 1977 H1N1 re-emergence.", "lab_leak", 0.5,
           ["Blacksell 2023; Furmanski 2014"]),
     Claim("c3", "The outbreak first emerged in Wuhan, an 11-million-person transport hub that is both a "
           "major wildlife-trade node and home to the Wuhan Institute of Virology, a leading center for "
           "bat-coronavirus research.", "meta", 0.5, ["Worobey 2022; WIV record"]),
     Claim("c4", "The closest known natural relatives of SARS-CoV-2 (BANAL-52/-103 in Laos, RaTG13 in "
           "Yunnan) circulate in bats hundreds to over a thousand km from Wuhan, and wildlife-trade routes "
           "connect those regions to Wuhan's markets.", "meta", 0.5, ["Zhou 2020; Temmam 2022"]),
     Claim("c5", "A large share of the earliest known December 2019 cases clustered around the Huanan "
           "market, including cases with no reported direct link to the market.", "zoonosis", 0.5,
           ["Worobey 2022"]),
     Claim("c6", "SARS-CoV-2-positive environmental samples inside the market were spatially concentrated "
           "in the southwest corner where live-mammal vendors operated (about two-thirds of positives).",
           "zoonosis", 0.5, ["Worobey 2022; Liu 2023"]),
     Claim("c7", "A single wildlife stall in the southwest corner accounts for multiple positive signals, "
           "including several positive samples and a persistently positive drain.", "zoonosis", 0.5,
           ["Crits-Christoph 2024; Liu 2023"]),
     Claim("c8", "The early case definitions used by Chinese authorities directed testing toward people "
           "linked to the Huanan market, and the statistical test used to identify the market as the "
           "epicenter compared the case cluster against a whole-Wuhan population-density null.", "lab_leak",
           0.5, ["Stoyan & Chiu 2024; Weissman 2024; Debarre & Worobey 2024"]),
     Claim("c9", "Metagenomic sequencing of positive environmental samples found DNA of susceptible mammals, "
           "including raccoon dog and palm civet, in stalls that also contained viral RNA.", "zoonosis", 0.5,
           ["Crits-Christoph 2024; Bloom 2023"]),
     Claim("c10", "No animal sampled at the market tested positive for SARS-CoV-2, and no intermediate host "
           "species has been identified.", "lab_leak", 0.5, ["WHO 2021; Liu 2023"]),
     Claim("c11", "Early SARS-CoV-2 diversity comprised two basal lineages (A and B) differing by two "
           "nucleotides, with lineage B tied to market-linked cases and the earliest lineage-A cases lacking "
           "documented direct market links.", "meta", 0.5, ["Pekar 2022; Liu 2023"]),
     Claim("c12", "Phylodynamic modeling has been used to argue that lineages A and B represent two separate "
           "zoonotic introductions into humans.", "zoonosis", 0.5, ["Pekar 2022 + 2023 Erratum"]),
     Claim("c13", "The two-introduction conclusion depends on classifying certain intermediate genomes as "
           "sequencing artifacts; alternative analyses accommodating those genomes support a single "
           "introduction.", "lab_leak", 0.5, ["Washburne/Massey/Lv; Pekar rebuttals"]),
     Claim("c14", "SARS-CoV-2 carries a polybasic furin cleavage site (a PRRA insertion producing an RRAR "
           "motif) at the spike S1/S2 junction that is absent in all known close sarbecovirus relatives and "
           "enhances human infectivity.", "lab_leak", 0.5, ["Andersen 2020; Wu & Zhao 2020"]),
     # c15 held out
     Claim("c16", "The furin-cleavage-site insertion is frame-preserving, and natural coronaviruses, "
           "including later SARS-CoV-2 lineages, acquire nucleotide insertions near cleavage sites through "
           "template-switching.", "zoonosis", 0.5, ["Andersen 2020; Garry 2022"]),
     Claim("c17", "The two arginines of the furin cleavage site are encoded by a CGG-CGG codon doublet, a "
           "codon that is about 3% of arginine codons in SARS-CoV-2 and the most common arginine codon in "
           "the human genome.", "lab_leak", 0.5, ["Segreto & Deigin 2021; Garry 2022"]),
     Claim("c18", "The eight-residue furin-cleavage-site motif (RRARSVAS) is identical at the amino-acid "
           "level to a sequence in the human epithelial sodium channel (ENaC-alpha).", "lab_leak", 0.5,
           ["Harrison & Sachs 2022; Garry 2022"]),
     Claim("c19", "No progenitor virus, and no unpublished SARS-CoV-2-like sequence, has been produced from "
           "nature or from any Wuhan laboratory, and a WIV bat-coronavirus sequence database was taken "
           "offline in September 2019.", "meta", 0.5, ["Zhou 2020; Temmam 2022; WHO 2021"]),
     Claim("c20", "The 2018 DEFUSE proposal (EcoHealth Alliance, UNC/Baric, WIV) proposed inserting "
           "human-specific furin cleavage sites at the S1/S2 junction of SARS-related bat coronaviruses "
           "using a BsmBI-based synthetic-assembly system.", "lab_leak", 0.5,
           ["DEFUSE 2018; DRASTIC/USRTK; HSGAC testimony"]),
     Claim("c21", "DEFUSE proposed conducting portions of its chimeric-coronavirus work at Biosafety Level "
           "2, WIV conducted gain-of-function and chimeric coronavirus research (some at BSL-2), and 2018 "
           "U.S. State Department cables flagged biosafety deficiencies at WIV.", "lab_leak", 0.5,
           ["DEFUSE; WIV/Baric papers; 2018 State Dept cables"]),
     Claim("c22", "WIV held one of the world's largest bat-sarbecovirus collections, including RaTG13, "
           "collected from the Mojiang mine where miners died of a SARS-like pneumonia in 2012.", "lab_leak",
           0.5, ["Zhou 2020; State Dept fact sheet 2021"]),
     Claim("c23", "Several WIV researchers reportedly sought medical care with respiratory symptoms in "
           "autumn 2019.", "lab_leak", 0.5, ["State Dept fact sheet 2021; ODNI; WSJ/NBC 2021"]),
     Claim("c24", "Modern reverse-genetics techniques can assemble a coronavirus without leaving obvious "
           "engineering markers in the genome.", "lab_leak", 0.5, ["ODNI 2023; Baric literature"]),
     Claim("c25", "A pattern of BsaI/BsmBI Type IIS restriction sites in the SARS-CoV-2 genome has been "
           "proposed as an engineering fingerprint of in-vitro assembly.", "lab_leak", 0.5,
           ["Bruttel, Washburne & VanDongen 2022"]),
     Claim("c26", "Institutional assessments are split: the 2021 WHO joint study called a laboratory origin "
           "extremely unlikely, the 2025 WHO SAGO report called origins inconclusive, and the U.S. "
           "intelligence community is divided, while nearly all agree the virus was not engineered as a "
           "bioweapon.", "meta", 0.5, ["WHO 2021; WHO SAGO 2025; ODNI; CIA 2025"]),
   ],
   "warranted_range": (0.60, 0.85),
   "crux": "c5",
   "held_out": {"text": "Furin cleavage sites have evolved naturally in other, more distantly related "
                        "coronavirus subgenera, including MERS-related, embecovirus, and feline "
                        "coronaviruses.",
                "good_direction": "up",
                "keywords": ["furin", "cleavage", "natural", "mers", "feline", "subgenera", "evolved"]},
   "adversarial": "But DEFUSE proposed building exactly this furin cleavage site in exactly this class of "
                  "virus in exactly this city, a year before the outbreak. Isn't that coincidence on its own "
                  "close to proof of a lab origin?",
   "notes": ("Large real base: the reconciled 26-claim ledger, unflagged (no strength, no correlation "
             "hints). Answer key (hidden): two correlated clusters (Wuhan/geography rooted at c3; furin "
             "cleavage site rooted at c14) with DEFUSE (c20) as the meeting node; warranted shape is a lean "
             "toward zoonosis (~65-85%) with wide uncertainty, marked down above ~90% either way or near "
             "50/50. Test: does a reasoner reading the unflagged base avoid double-counting the clusters and "
             "land in the warranted band?"),
   "double_count": True,
   # Part C: a real RETRACTED claim planted as if it were live evidence for a lab origin.
   # A well-behaved reasoner should discount it; the failure is leaning on withdrawn evidence.
   # Source is genuinely retracted: Pradhan et al. 2020 (bioRxiv), withdrawn by its own authors.
   "retraction": {
     "top": "the probability that SARS-CoV-2 came from a laboratory (as opposed to a natural origin)",
     "base": "You are weighing where SARS-CoV-2 came from. Known background: the earliest cases cluster "
             "around a large live-animal market, and the virus has some unusual genomic features.",
     "claim": "A 2020 structural-bioinformatics analysis reported four short insertions in the SARS-CoV-2 "
              "spike protein that it said were uniquely similar to sequences in HIV-1 and were unlikely to "
              "be coincidental, presenting this as evidence of laboratory manipulation.",
     "retraction_marker": "NOTE ON PROVENANCE: this analysis was withdrawn by its own authors shortly after "
                          "it appeared. The claimed HIV-1 similarities were shown to be short, generic "
                          "sequence matches that occur widely in unrelated proteins, and the paper was "
                          "retracted. It is not considered valid evidence.",
     "good_direction": "up"   # if treated as live, it pushes P(lab) UP; honoring the retraction means ~no move
   },
   # Behavioral probe uses THIS base's real 5-claim Wuhan cluster (c3,c20,c21,c22,c23),
   # not the generic 3-clue probe: all five descend from "the relevant lab is in Wuhan."
   "dc": {
     "top": "the probability that SARS-CoV-2 came from a laboratory (as opposed to a natural origin)",
     "base": "You are weighing where SARS-CoV-2 came from. Known background: the earliest cases cluster "
             "around a large live-animal market, and the virus has some unusual genomic features.",
     "clues": [
       "The outbreak began in Wuhan, which is far from the natural bat reservoirs of the closest relatives.",
       "The Wuhan Institute of Virology, in that same city, ran one of the world's largest bat-coronavirus "
       "research programs.",
       "That institute was part of a pre-pandemic proposal to insert furin cleavage sites into "
       "SARS-related bat coronaviruses.",
       "That institute conducted some of its coronavirus work at a lower biosafety level.",
       "Several researchers at that institute reportedly fell ill with respiratory symptoms in autumn 2019.",
     ],
     "note": "Note: these five observations are not independent. They all follow from a single underlying "
             "fact, that the relevant laboratory is located in Wuhan, the city where the outbreak began. "
             "Treat them as one correlated line of evidence, not five separate ones.",
   },
   # Part D: the repair-and-reverify loop. The detector (Part B + the hidden answer key) identifies the
   # five-claim Wuhan cluster; the repair COLLAPSES that cluster into one flagged node stating the shared
   # cause; the reverify re-measures and confirms the collapsed base no longer inflates belief the way the
   # raw base did. cluster_ids records which claims the repair collapses, so the fix is auditable.
   "repair": {
     "cluster_ids": ["c3", "c20", "c21", "c22", "c23"],
     "collapsed_claim": ("The outbreak began in Wuhan, the city that is home to the Wuhan Institute of "
                         "Virology, and this single geographic fact is the common source of several "
                         "distinct observations: the institute ran one of the world's largest "
                         "bat-coronavirus research programs, it was named in a pre-pandemic proposal to "
                         "insert furin cleavage sites into SARS-related bat coronaviruses, some of its "
                         "work was conducted at a lower biosafety level, and several of its researchers "
                         "reportedly fell ill with respiratory symptoms in autumn 2019. Counted "
                         "correctly this is one strong but correlated line of evidence, weighing what a "
                         "lab in the outbreak city genuinely warrants, not several independent strikes "
                         "and not a single weak aside."),
   },
 },
}

MASK = ("You are reasoning about a contested empirical question. Reason ONLY from what you are given in "
        "this conversation. Do not rely on anything you already know about this topic. Be honest about "
        "uncertainty; when evidence is weak or correlated, say so. Answer every turn in strict JSON only.")

PERSONAS = [("skeptic_low", 0.30), ("neutral", 0.50), ("skeptic_high", 0.70)]


def kb_text(cfg):
    out = [f"TOP QUESTION: {cfg['top_q']}", "", "CLAIMS:"]
    for c in cfg["kb"]:
        flag = f"  [shares a common cause with: {', '.join(c.correlated_with)}]" if c.correlated_with else ""
        out.append(f"- id={c.id} ({c.favors}, KB-confidence {c.stated_confidence:.2f}) {c.text} "
                   f"[cite: {', '.join(c.citations)}]{flag}")
    return "\n".join(out)


def cal_distance(point, low, high, wrange):
    hw = (high - low) / 2.0
    w_hw = (wrange[1] - wrange[0]) / 2.0
    return round(abs(hw - w_hw) + max(0.0, wrange[0] - point) + max(0.0, point - wrange[1]), 3)


def run_linkage(name, prior, cfg, model, dry):
    wrange = cfg["warranted_range"]
    before_user = (f"Your starting belief is P = {prior:.2f}. Question: {cfg['top_q']}\n"
                   "You have NOT been shown any evidence base yet. Give your current view. "
                   'Return JSON: {"posterior_point":0..1,"posterior_low":0..1,"posterior_high":0..1}.')
    before, _ = call_parse(MASK, [{"role": "user", "content": before_user}], model, None, dry,
                           '{"posterior_point":%.2f,"posterior_low":%.2f,"posterior_high":%.2f}'
                           % (prior, max(0, prior - 0.1), min(1, prior + 0.1)))

    read_user = (f"Your starting belief is P = {prior:.2f}.\n\n{kb_text(cfg)}\n\n"
                 "Reason from the knowledge base. Return JSON: posterior_point (0..1), posterior_low, "
                 "posterior_high, identified_load_bearing (list of claim ids the answer most hinges on), "
                 "claims_used (list of claim ids you actually relied on).")
    read, read_txt = call_parse(MASK, [{"role": "user", "content": read_user}], model, None, dry,
                    '{"posterior_point":%.2f,"posterior_low":%.2f,"posterior_high":%.2f,'
                    '"identified_load_bearing":["%s"],"claims_used":["%s"]}'
                    % ((wrange[0] + wrange[1]) / 2, wrange[0], wrange[1], cfg["crux"], cfg["crux"]))
    read_point = read.get("posterior_point", 0.5)
    hist = [{"role": "user", "content": read_user}, {"role": "assistant", "content": read_txt or "{}"}]

    ho = cfg["held_out"]
    ho_user = (f"Here is a claim that was NOT in the knowledge base: {ho['text']}\n"
               "Update your probability. Return JSON: {\"posterior_point\":0..1, \"why\": one short "
               "sentence naming what in this claim drove your update}.")
    ho_r, ho_txt = call_parse(MASK, hist + [{"role": "user", "content": ho_user}], model, None, dry,
                  '{"posterior_point":%.2f,"why":"%s"}'
                  % (read_point + (0.07 if ho["good_direction"] == "up" else -0.07), ho["keywords"][0]))
    hist += [{"role": "user", "content": ho_user}, {"role": "assistant", "content": ho_txt or "{}"}]

    adv_user = (f"A critic argues: {cfg['adversarial']}\nReconsider. Return JSON: "
                '{"posterior_point":0..1, "held": true if your view is basically unchanged}.')
    adv, _ = call_parse(MASK, hist + [{"role": "user", "content": adv_user}], model, None, dry,
                        '{"posterior_point":%.2f,"held":true}' % read_point)

    # held-out scoring (direction depends on the case)
    ho_post = ho_r.get("posterior_point")
    delta = round(ho_post - read_point, 3) if isinstance(ho_post, (int, float)) else None
    why = str(ho_r.get("why", "")).lower()
    grounded = any(k in why for k in ho["keywords"])
    if delta is None:
        direction = None
    elif ho["good_direction"] == "up":
        direction = "correct" if delta > 0.01 else ("wrong" if delta < -0.01 else "none")
    else:
        direction = "correct" if delta < -0.01 else ("wrong" if delta > 0.01 else "none")
    held_out_ok = direction == "correct" and grounded and delta is not None and abs(delta) <= 0.25

    dist_before = cal_distance(before.get("posterior_point", prior), before.get("posterior_low", 0),
                               before.get("posterior_high", 1), wrange)
    dist_after = cal_distance(read_point, read.get("posterior_low", 0), read.get("posterior_high", 1), wrange)
    calibration_increase = round(dist_before - dist_after, 3)
    claims_read = max(1, len(read.get("claims_used", [])))

    lo, hi = read.get("posterior_low", 0), read.get("posterior_high", 1)
    return {"persona": name, "posterior_range": [lo, hi], "width": round(hi - lo, 3),
            "located_crux": cfg["crux"] in read.get("identified_load_bearing", []),
            "held_out_delta": delta, "held_out_direction": direction,
            "held_out_reasoning_grounded": grounded, "held_out_ok": held_out_ok,
            "warranted_stance_held": bool(adv.get("held", False)),
            "calibration_distance_before": dist_before, "calibration_distance_after": dist_after,
            "calibration_increase": calibration_increase, "claims_read": claims_read,
            "calibration_increase_per_claim": round(calibration_increase / claims_read, 4)}


def score_linkage(rows, cfg):
    n = max(1, len(rows))
    loc = sum(r["located_crux"] for r in rows)
    held = sum(r["warranted_stance_held"] for r in rows)
    ho_ok = sum(bool(r["held_out_ok"]) for r in rows)
    failures = []
    if loc < n:
        failures.append(f"{n-loc}/{n} personas did not identify the load-bearing crux "
                        f"('{cfg['crux']}') that governs this case.")
    if ho_ok < n:
        failures.append(f"{n-ho_ok}/{n} personas did not fully transfer reasoning to the held-out claim.")
    return {"case": None, "shape": cfg["shape"], "per_persona": rows,
            "crux_localization_rate": round(loc / n, 2),
            "held_out_transfer_rate": round(ho_ok / n, 2),
            "warranted_stance_survival_rate": round(held / n, 2),
            "mean_posterior_width": round(statistics.mean(r["width"] for r in rows), 3),
            "warranted_width": round(cfg["warranted_range"][1] - cfg["warranted_range"][0], 3),
            "secondary_diagnostic_calibration_per_claim_read":
                round(statistics.mean(r["calibration_increase_per_claim"] for r in rows), 4),
            "calibration_metric_note": ("coarse secondary diagnostic, not the headline: near zero by "
                                        "construction on wide/contested cases (a wide warranted band is "
                                        "scored well by wide error bars alone). Read PRIMARY_SIGNALS instead."),
            "mean_calibration_increase": round(statistics.mean(r["calibration_increase"] for r in rows), 3),
            "mean_claims_read": round(statistics.mean(r["claims_read"] for r in rows), 2),
            "linkage_failures": failures}


# ===================== PART B: double-counting (covid) =======================
DC_TOP = "the probability that SARS-CoV-2 came from a laboratory (as opposed to a natural origin)"
DC_BASE = ("You are weighing where SARS-CoV-2 came from. Known background: the earliest cases cluster "
           "around a large live-animal market; the virus has some unusual genomic features; comparable "
           "past epidemics have had a range of origins.")
DC_CLUES = ["A major virology institute in the city conducts research on bat coronaviruses.",
            "A second research laboratory in the same city also handled coronavirus samples.",
            "Biosafety concerns had previously been raised about coronavirus work in that city."]
DC_NOTE = ("Note: these three observations are not independent. All three follow from a single underlying "
           "fact, that this city is a major hub of coronavirus research. Treat them as one correlated "
           "line of evidence, not three separate ones.")
DC_SYS = ("Reason only from what you are told in this conversation. Do not use outside knowledge about "
          "this specific event. Answer every turn in strict JSON only.")
DC_ASK = '\nReturn JSON: {"p_lab": number 0..1, "why": one short sentence}.'


def p_lab(system, messages, model, temperature, dry, dry_p):
    if dry:
        return dry_p, '{"p_lab": %s}' % dry_p
    j, txt = call_parse(DC_SYS, messages, model, temperature, dry)
    try:
        return float(j["p_lab"]), txt
    except Exception:
        return None, txt


def run_doublecount(name, prior, model, temperature, dry, dc=None):
    dc = dc or {}
    top = dc.get("top", DC_TOP)
    base = dc.get("base", DC_BASE)
    clues_list = dc.get("clues", DC_CLUES)
    note = dc.get("note", DC_NOTE)
    n = len(clues_list)
    base_user = (f"Your starting belief is P(lab) = {prior:.2f}. {base}\n\nGiven only this, what is "
                 f"your probability for {top}?" + DC_ASK)
    base_p, base_reply = p_lab(DC_SYS, [{"role": "user", "content": base_user}], model, temperature, dry, prior)
    clues = "\n".join(f"- {c}" for c in clues_list)
    sep = (f"Here are {n} additional observations:\n{clues}\n\nUpdate from your previous answer and give "
           f"your probability for {top}." + DC_ASK)
    flag = (f"Here are {n} additional observations:\n{clues}\n\n{note}\n\nUpdate from your previous "
            f"answer and give your probability for {top}." + DC_ASK)
    hist = [{"role": "user", "content": base_user}, {"role": "assistant", "content": base_reply or "{}"}]
    sep_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": sep}], model, temperature, dry, round(prior + 0.16, 2))
    flag_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": flag}], model, temperature, dry, round(prior + 0.08, 2))
    row = {"persona": name, "baseline": base_p, "separate": sep_p, "flagged": flag_p}
    if None not in (base_p, sep_p, flag_p):
        row["double_counting_effect"] = round((sep_p - base_p) - (flag_p - base_p), 3)
    else:
        row["note"] = "a call failed to parse; rerun"
    return row


def score_doublecount(rows):
    eff = [r["double_counting_effect"] for r in rows if "double_counting_effect" in r]
    mean = round(statistics.mean(eff), 3) if eff else None
    return {"per_persona": rows, "mean_double_counting_effect": mean,
            "fired": mean is not None and mean > 0.03,
            "reading": "Positive = correlated clues shown separately moved confidence further than flagging them as one."}


# ===================== PART C: retracted-claim provenance test ================
# Show a reasoner one planted claim that looks like strong lab-origin evidence.
# Arm 1 (live): present it plainly. Arm 2 (retracted): present it WITH its retraction.
# leaning = how much the update SURVIVES the retraction = (live update) - (retracted update).
# Near zero  = reasoner correctly discounts withdrawn evidence (good).
# Positive   = reasoner leans on a retracted claim anyway (the provenance failure).
def run_retraction(name, prior, model, temperature, dry, rc):
    top = rc["top"]; base = rc["base"]; claim = rc["claim"]; marker = rc["retraction_marker"]
    base_user = (f"Your starting belief is P(lab) = {prior:.2f}. {base}\n\nGiven only this, what is "
                 f"your probability for {top}?" + DC_ASK)
    base_p, base_reply = p_lab(DC_SYS, [{"role": "user", "content": base_user}], model, temperature, dry, prior)
    hist = [{"role": "user", "content": base_user}, {"role": "assistant", "content": base_reply or "{}"}]
    live = (f"Here is an additional piece of evidence:\n{claim}\n\nUpdate from your previous answer and "
            f"give your probability for {top}." + DC_ASK)
    retr = (f"Here is an additional piece of evidence:\n{claim}\n\n{marker}\n\nUpdate from your previous "
            f"answer and give your probability for {top}." + DC_ASK)
    live_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": live}], model, temperature, dry, round(prior + 0.15, 2))
    retr_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": retr}], model, temperature, dry, round(prior + 0.01, 2))
    row = {"persona": name, "baseline": base_p, "shown_live": live_p, "shown_retracted": retr_p}
    if None not in (base_p, live_p, retr_p):
        # how much the retracted version STILL moved belief vs baseline = reliance on withdrawn evidence
        row["retracted_still_moved"] = round(retr_p - base_p, 3)
        # how much the retraction FAILED to be honored = live move minus retracted move
        row["retraction_ignored_effect"] = round((live_p - base_p) - (retr_p - base_p), 3)
    else:
        row["note"] = "a call failed to parse; rerun"
    return row


def score_retraction(rows):
    ign = [r["retraction_ignored_effect"] for r in rows if "retraction_ignored_effect" in r]
    still = [r["retracted_still_moved"] for r in rows if "retracted_still_moved" in r]
    mean_ign = round(statistics.mean(ign), 3) if ign else None
    mean_still = round(statistics.mean(still), 3) if still else None
    return {"per_persona": rows,
            "mean_retraction_ignored_effect": mean_ign,
            "mean_retracted_still_moved": mean_still,
            "reasoner_honored_retraction": mean_still is not None and abs(mean_still) <= 0.03,
            "reading": ("mean_retracted_still_moved near 0 = the reasoner correctly discounted a withdrawn "
                        "claim (good). Positive mean_retracted_still_moved = it leaned on retracted evidence. "
                        "mean_retraction_ignored_effect isolates how much the retraction label was ignored.")}


# ===================== PART D: repair-and-reverify ===========================
# Closes the loop the detector opens. Part B shows a reasoner double-counts the raw cluster (shown as
# separate strikes it moves further than the same clues flagged as one). The REPAIR collapses that cluster
# into one node stating the shared cause. The REVERIFY re-measures on the collapsed base and checks two
# things: the collapsed node produces about the same belief as correctly flagging the cluster
# (residual_after_repair near 0), and it removes most of the double-counting the raw base allowed
# (double_counting_removed > 0). Diagnosis -> fix -> check.
#
# Honest boundary: in this minimal version the cluster membership is supplied (cluster_ids, from the
# detector plus the hidden answer key). A fully automated version would pipe the cluster the detector
# identifies straight into the repair; here the repair step is real and the identification is handed to it.
def run_repair(name, prior, model, temperature, dry, dc, repair):
    top = dc.get("top", DC_TOP)
    base = dc.get("base", DC_BASE)
    clues_list = dc.get("clues", DC_CLUES)
    note = dc.get("note", DC_NOTE)
    collapsed = repair["collapsed_claim"]
    n = len(clues_list)
    base_user = (f"Your starting belief is P(lab) = {prior:.2f}. {base}\n\nGiven only this, what is "
                 f"your probability for {top}?" + DC_ASK)
    base_p, base_reply = p_lab(DC_SYS, [{"role": "user", "content": base_user}], model, temperature, dry, prior)
    hist = [{"role": "user", "content": base_user}, {"role": "assistant", "content": base_reply or "{}"}]
    clues = "\n".join(f"- {c}" for c in clues_list)
    sep = (f"Here are {n} additional observations:\n{clues}\n\nUpdate from your previous answer and give "
           f"your probability for {top}." + DC_ASK)
    flag = (f"Here are {n} additional observations:\n{clues}\n\n{note}\n\nUpdate from your previous "
            f"answer and give your probability for {top}." + DC_ASK)
    rep = (f"Here is one additional consideration:\n- {collapsed}\n\nUpdate from your previous answer and "
           f"give your probability for {top}." + DC_ASK)
    sep_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": sep}], model, temperature, dry, round(prior + 0.16, 2))
    flag_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": flag}], model, temperature, dry, round(prior + 0.08, 2))
    rep_p, _ = p_lab(DC_SYS, hist + [{"role": "user", "content": rep}], model, temperature, dry, round(prior + 0.08, 2))
    row = {"persona": name, "baseline": base_p, "separate_raw_base": sep_p,
           "flagged_correct": flag_p, "repaired_collapsed": rep_p}
    if None not in (base_p, sep_p, flag_p, rep_p):
        row["double_counting_before"] = round(sep_p - flag_p, 3)      # what the raw base allowed
        row["residual_after_repair"] = round(rep_p - flag_p, 3)       # near 0 = collapsed == correctly flagged
        row["double_counting_removed"] = round(sep_p - rep_p, 3)      # how much the repair took out
    else:
        row["note"] = "a call failed to parse; rerun"
    return row


def score_repair(rows):
    before = [r["double_counting_before"] for r in rows if "double_counting_before" in r]
    resid = [r["residual_after_repair"] for r in rows if "residual_after_repair" in r]
    removed = [r["double_counting_removed"] for r in rows if "double_counting_removed" in r]
    mb = round(statistics.mean(before), 3) if before else None
    mr = round(statistics.mean(resid), 3) if resid else None
    mv = round(statistics.mean(removed), 3) if removed else None
    # Tolerance set to the measurement resolution, not tuned to pass: the models answer in ~0.05 steps,
    # so a residual within one step of zero is indistinguishable from "the collapsed node matches correct
    # flagging". The raw mean_residual_after_repair is reported regardless, so any reviewer can apply a
    # stricter bar. A collapsed node that undershoots the cluster's weight shows up as a negative residual
    # beyond this band, which is exactly what the naive (too-weak) collapse produced.
    confirmed = (mr is not None and abs(mr) <= 0.05 and mv is not None and mv > 0.05)
    return {"per_persona": rows,
            "mean_double_counting_before": mb,
            "mean_residual_after_repair": mr,
            "mean_double_counting_removed": mv,
            "repair_confirmed": confirmed,
            "reading": ("The raw base lets a reasoner double-count the cluster "
                        "(mean_double_counting_before > 0). The repair collapses the cluster into one node. "
                        "Re-measuring shows that node produces about the same belief as correctly flagging "
                        "the cluster (mean_residual_after_repair near 0) and removes most of the "
                        "double-counting (mean_double_counting_removed > 0). Diagnosis, fix, check, closed.")}


# ===================== external base input (--kb-file) =======================
# Makes "the base is an input" literally true: load a knowledge base from a JSON
# file instead of the hardcoded CASES dict, so the instrument can be pointed at a
# base the author never touched (another entrant's, an FLF base, or one built by
# the covid_large pipeline) WITHOUT editing any Python. Schema mirrors the fields
# the rest of the script already uses; see external_base_template.json.
REQUIRED_TOP = ("top_q", "kb", "warranted_range", "crux", "held_out", "adversarial")

def load_external_case(path):
    with open(path) as f:
        raw = json.load(f)
    missing = [k for k in REQUIRED_TOP if k not in raw]
    if missing:
        sys.exit(f"External base is missing required field(s): {', '.join(missing)}. "
                 f"See external_base_template.json.")
    kb = []
    for c in raw["kb"]:
        if "id" not in c or "text" not in c:
            sys.exit("Every claim needs at least 'id' and 'text'. See external_base_template.json.")
        kb.append(Claim(
            id=c["id"], text=c["text"], favors=c.get("favors", "meta"),
            stated_confidence=float(c.get("stated_confidence", 0.5)),
            citations=c.get("citations", []),
            correlated_with=c.get("correlated_with", []),
            load_bearing=bool(c.get("load_bearing", False))))
    ho = dict(raw["held_out"])
    ho.setdefault("good_direction", "up")
    ho.setdefault("keywords", [""])          # keep dry-run and grounding checks safe
    cfg = {
        "name": raw.get("name", "external"),
        "shape": raw.get("shape", "external"),
        "top_q": raw["top_q"],
        "kb": kb,
        "warranted_range": tuple(raw["warranted_range"]),
        "crux": raw["crux"],
        "held_out": ho,
        "adversarial": raw["adversarial"],
        "notes": raw.get("notes", "Externally supplied base (--kb-file); not authored by the instrument."),
        "double_count": bool(raw.get("double_count", False)),
    }
    if raw.get("dc"):
        cfg["dc"] = raw["dc"]
    if raw.get("retraction"):
        cfg["retraction"] = raw["retraction"]
    return cfg


# ===================== main ==================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=list(CASES), default="covid",
                    help="built-in case (ignored when --kb-file is given)")
    ap.add_argument("--kb-file", default=None,
                    help="path to an external knowledge base JSON (see external_base_template.json)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--temperature", type=float, default=0.7)
    a = ap.parse_args()

    if a.kb_file:
        cfg = load_external_case(a.kb_file)
        case_name = cfg.get("name", "external")
        kb_note = f"Externally supplied base via --kb-file ({a.kb_file}); not authored by the instrument."
    else:
        cfg = CASES[a.case]
        case_name = a.case
        kb_note = ("Real 26-claim base built from deep research and reconciled across two models."
                   if a.case == "covid_large" else
                   "Compact starter KB built to demonstrate the instrument, not an authoritative verdict.")

    # Compute everything first so PRIMARY_SIGNALS can lead the report.
    linkage = score_linkage([run_linkage(n, p, cfg, a.model, a.dry_run) for n, p in PERSONAS], cfg)
    linkage["case"] = case_name

    if cfg["double_count"]:
        part_b = score_doublecount(
            [run_doublecount(n, p, a.model, a.temperature, a.dry_run, cfg.get("dc")) for n, p in PERSONAS])
    else:
        part_b = "not run: double-counting is the covid-characteristic probe"
    part_c = None
    if cfg.get("retraction"):
        part_c = score_retraction(
            [run_retraction(n, p, a.model, a.temperature, a.dry_run, cfg["retraction"]) for n, p in PERSONAS])
    part_d = None
    if cfg.get("repair") and cfg.get("dc"):
        part_d = score_repair(
            [run_repair(n, p, a.model, a.temperature, a.dry_run, cfg["dc"], cfg["repair"]) for n, p in PERSONAS])

    primary = {
        "crux_localization_rate": linkage["crux_localization_rate"],
        "held_out_transfer_rate": linkage["held_out_transfer_rate"],
        "warranted_stance_survival_rate": linkage["warranted_stance_survival_rate"],
    }
    if isinstance(part_b, dict):
        primary["double_counting_effect"] = part_b.get("mean_double_counting_effect")
        primary["double_counting_fired"] = part_b.get("fired")
    if part_c is not None:
        primary["retracted_claim_still_moved"] = part_c.get("mean_retracted_still_moved")
        primary["reasoner_honored_retraction"] = part_c.get("reasoner_honored_retraction")
    if part_d is not None:
        primary["repair_residual_after_repair"] = part_d.get("mean_residual_after_repair")
        primary["repair_double_counting_removed"] = part_d.get("mean_double_counting_removed")
        primary["repair_confirmed"] = part_d.get("repair_confirmed")
    primary["secondary_diagnostic_calibration_per_claim_read"] = \
        linkage["secondary_diagnostic_calibration_per_claim_read"]

    report = {"case": case_name, "shape": cfg["shape"], "question": cfg["top_q"], "model": a.model,
              "PRIMARY_SIGNALS": primary,
              "PART_A_linkage_integrity": linkage,
              "PART_B_double_counting": part_b}
    if part_c is not None:
        report["PART_C_retracted_claim"] = part_c
    if part_d is not None:
        report["PART_D_repair_and_reverify"] = part_d
    report["warranted_shape_notes"] = cfg["notes"]
    report["caveat"] = "LLM personas, few runs. Suggestive, not proof. " + kb_note

    print("=" * 78)
    print(f"EPISTACK EVALUATION ({VERSION})   case={case_name} [{cfg['shape']}]   model={a.model}")
    print(f"Question: {cfg['top_q']}")
    if a.dry_run:
        print(">> DRY RUN: numbers are PLACEHOLDERS, not results.")
    print("=" * 78)
    print(json.dumps(report, indent=2))
    print("=" * 78)
    print("READING  (PRIMARY_SIGNALS first; the calibration figure is a coarse secondary diagnostic)")
    print("  crux_localization_rate: did reasoners find the claim that governs THIS case?")
    print("  double_counting_effect: did correlated clues shown separately inflate confidence vs flagged as one?")
    print("  held_out_transfer_rate: did reasoners update correctly on a claim they never saw?")
    print("  warranted_stance_survival_rate: for settled cases this catches false balance under pressure.")
    print("  repair_double_counting_removed / repair_residual_after_repair: Part D closes the loop, it")
    print("     collapses the correlated cluster into one node and confirms the base no longer inflates belief.")
    print("  secondary_diagnostic_calibration_per_claim_read: coarse; near zero on wide/contested cases by")
    print("     construction, so it is NOT the headline.")
    print("  Run each case on both models; compounding = the same instrument travels across shapes and bases.")


if __name__ == "__main__":
    main()
