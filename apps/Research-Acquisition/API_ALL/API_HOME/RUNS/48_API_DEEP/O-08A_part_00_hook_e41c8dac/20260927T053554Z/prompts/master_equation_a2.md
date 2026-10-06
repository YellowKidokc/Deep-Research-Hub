## SYSTEM

# MASTER_EQUATION station V2: what in this paper plays the role of the master equation?

Replaces the main task of `API_DEEP\MASTER_EQUATION\PROMPT.md`. V1 only listed a paper's own equations;
keep that as optional **Part B** for papers that contain math.
David's spec, 2026-09-24: for every paper, ask what is analogous to the master equation. This is subjective,
so the station is built to show where it is subjective.

## The reference (send this block with every call)

χ_total = ∫_{t0}^{t1} ∫_Ω G·M·E·S_eff·T·K·R·Q·F·C d³x dt  (ME-EQ-001). Locally, χ = G·M·E·S_eff·T·K·R·Q·F·C (ME-EQ-002).
The factors multiply, so if any required factor is zero the whole collapses (zero-collapse, ME-EQ-006).

| Slot | Meaning (canonical pill ME-01-020..029) |
|---|---|
| G | External negentropy influx: coherence can't sustain itself in a closed system and needs an outside source |
| M | Alignment: coupling is strongest when the system is aligned with its reference |
| E | Signal fidelity: whether truth survives transmission through noise |
| S_eff | Effective entropy: entropy enters as what lowers coherence |
| T | Temporal integration: time turns possibility into accumulated consequence |
| K | Compression: ordered meaning compresses and noise does not |
| R | Phase transition: some thresholds change state, not just degree |
| Q | Superposition: open possibility stays unresolved until actualized |
| F | Non-local correlation: related systems are no longer independent |
| C | Integration: the local integrator inside the product |

Source: `D:\GitHub\Faith-through-physics-atoms\mothership\pills\master-equation\01_canonical\`. The runner
should read the slot meanings from those pills at run time rather than hard-coding this table.

## Part A: the analog (every paper)

1. **The paper's own core relation**: in one sentence, what does everything else in this paper depend on?
   It may be verbal, e.g. "restoration requires confession AND grace AND time together". Quote the span that
   comes closest to stating it.
2. **The product test** (the most objective step, weighted most heavily): if one ingredient of that relation is
   zero or missing, does the paper's conclusion fail entirely (**multiplicative**, like χ) or only weaken
   (**additive**)? Quote the evidence. Answer `multiplicative | additive | threshold | unclear`.
3. **Slot mapping**: for each of the 10 slots, say what in the paper plays that role, with a quoted span, and
   rate the fit `direct | analogous | stretched | absent`. Absent is a normal answer. Do not fill slots to look complete.
4. **Where it breaks**: the places the analogy stops working, e.g. a slot the paper treats as optional,
   or a factor the paper adds that has no slot.
5. **Overall**: an analog strength of 0-5, a confidence of low/medium/high, and a one-line statement of the analog.
   Always labeled as an analogy proposal, never a derivation.

```json
{"paper": "", "core_relation": {"sentence": "", "quote": ""},
 "product_test": {"answer": "multiplicative", "quote": "", "reason": ""},
 "slots": [{"slot": "G", "plays_role": "", "quote": "", "fit": "analogous"}],
 "breaks": [], "extra_factors": [],
 "analog_strength": 3, "confidence": "medium", "one_line": ""}
```

## Handling the subjectivity

Run Part A **twice independently**: two calls with different seeds (temperature 0.7), or two models when available.
The runner, not the model, then compares the results:
- product-test answers and slot fits that agree are marked `agreed`
- disagreements are marked `contested` and listed at the top of the report for David to rule on
- the reported analog strength is the lower of the two, with the spread shown (e.g. `3 (3-4)`)

Across a series, add a roll-up: which slots every paper fills, which are never filled, and whether the product
test holds for the series as a whole.

## Part B (optional: papers with equations)

The V1 equation extraction (exact expression, symbols, units, dimensional check, relationship to
χ: instantiates | approximates | contradicts | independent). Run it only when Part A finds at least one equation.


## USER

Run PART A (the analog) for this paper. Return the Part A JSON object exactly as specified, with all 10 slots (G, M, E, S_eff, T, K, R, Q, F, C); quotes are exact source text followed by the sentence id in brackets. Also add "equations_present": true|false.

PAPER TITLE: THE META ARGUMENT

SOURCE (paragraphs [P01].., sentences S001..; cite these ids wherever a schema asks for a span or location):
[P01]
S001 # THE META ARGUMENT
S002 ## Part 0 — The Hook

[P02]
S003 ### David Lowe | POF 2828 | July 2026

[P03]
S004 Pick your fight.

[P04]
S005 Immigration.
S006 Guns.
S007 Abortion.
S008 Healthcare.
S009 Criminal justice.
S010 Climate.
S011 AI.
S012 The culture war.
S013 Whether Trump is saving the country or burning it down.
S014 Whether the system is rigged or you just aren't trying hard enough.
S015 Whether the left is compassionate or naive.
S016 Whether the right is principled or cruel.
S017 Whether the libertarians have a point or just don't want to pay for anything.

[P05]
S018 You've been arguing about your issue for years.
S019 So has the other side.
S020 Nothing resolves.
S021 The arguments get louder.
S022 The positions get harder.
S023 And underneath it all, something you can feel but can't name: the sense that everybody is fighting about the wrong thing.

[P06]
S024 This document makes one claim: **they are.**

[P07]
S025 Every one of those fights is an argument about where to sit on a line.
S026 And nobody in the argument knows the line exists.
S027 The line has a mathematical structure.
S028 It has a constraint that makes resolution impossible from inside.
S029 It has a history that shows the same pattern repeating across civilizations that never communicated.
S030 And it has exactly one exit — which is not a better position on the line, but a point off the line entirely.

[P08]
S031 We are going to walk through this.
S032 It will take time.
S033 This is not a one-page fix, and anyone offering you a one-page fix is selling you something.
S034 The problems are real.
S035 The math is real.
S036 The history is real.
S037 And the resolution — if it exists — requires you to understand the problem deeply enough that you can verify the answer yourself, not take our word for it.

[P09]
S038 Here is what we will show you:

[P10]
S039 1.
S040 That good and bad are structural properties of reality, as invariant as electric charge — not cultural opinions that shift with the century.
S041 2.
S042 That no system can determine its own moral direction from inside itself — this is mathematics, not philosophy, and it has been proven.
S043 3.
S044 That an external reference point must exist for the distinction between good and bad to be meaningful — and that such a reference point has maintained a continuous, accessible record throughout human history.
S045 4.
S046 That institutions get captured in a specific, documented, ordered sequence — money first, then government, then education, then the people who interpret reality for everyone else, then the moral language itself.
S047 5.
S048 That the enforcement mechanism is not force but shame — and that governments have been deploying it as official policy since at least 2015.
S049 6.
S050 That the population sorts into two classes over time, defined not by any demographic variable but by one structural feature: whether their connection to truth runs through the captured institutions or directly to the source.
S051 7.
S052 That every communication technology in history — writing, the printing press, radio, television, the internet, social media — follows the same pattern: a brief window where truth spreads, followed by institutional capture of the infrastructure.
S053 8.
S054 That there is a mathematical constraint — provable by algebra — showing that justice and mercy cannot both be fully satisfied inside any closed system.
S055 Someone always eats the deficit.
S056 The only question is who, and whether they chose to.
S057 9.
S058 That the historical trajectory across every measurable dimension — food sovereignty, information access, medical autonomy, educational independence, financial sovereignty, community structure — follows the same curve, in the same direction, with the same acceleration.
S059 10.
S060 That there is exactly one event in the recorded history of the world where this trajectory reversed without the system collapsing — and that event has measurable features that no other candidate in history matches.

[P11]
S061 If those ten claims hold up under examination, they form a single structure — and that structure explains not just the fights you're having, but why you're having them, why they don't resolve, and what the resolution would require.

[P12]
S062 We are not asking you to believe anything at the outset.
S063 We are asking you to follow the argument, check the evidence, and see where it lands.
S064 If it lands somewhere you don't like, show us where it breaks.
S065 We'll publish the break alongside the argument, because a framework that can't survive honest criticism isn't worth defending.

[P13]
S066 If it lands somewhere that changes how you see everything — well, that's between you and the evidence.

[P14]
S067 Let's start.

[P15]
S068 *[Continue to Part 1: The Two Premises →]*
