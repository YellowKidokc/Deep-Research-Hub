Run the seven API DEEP stations below on the one paper at the end, in this order: fruits, axiom_nodes, atoms, lean4, stories, master_equation, coherence.
Return seven JSON objects, each under a heading with the station name. Follow each station's own rules and schema exactly.

=== STATION: atoms ===
You are an atom-classification engine for the Faith Through Physics / Theophysics canon.

Read the SOURCE text below and emit a JSON object matching the schema exactly.

Rules:
1. Only 01_canonical stage nodes are true "claims" and receive a claimID (tp:DOMAIN/L#/C#). All other stages get nodeID only.
2. Every claim node MUST include a falsificationCondition. If the source does not state one, infer the strongest honest kill condition.
3. Evidence, kill, result, paper, article, reach nodes do NOT need statementTechnical/statementPlain.
4. Use the exact enums in the schema. Do not invent values.
5. For edges, prefer empty target over guessed IDs. Only link to atoms you actually extracted from this source.
6. If the source contains multiple distinct claims, extract multiple atoms.
7. If a section is raw or unclassifiable, emit a 00_inbox_working raw node.


SCHEMA:
{
  "paper_uuid": "stable id derived from source path",
  "title": "document title",
  "domainType": "physics | theology | mathematics | information | consciousness | psychology | history",
  "summary": "one-paragraph summary of the source",
  "atoms": [
    {
      "nodeType": "claim | paradigm | bridge | prediction | evidence | kill | paper | objection | translation | check | article | reach | result | question | series | raw",
      "stage": "00_inbox_working | 01_canonical | 02_paradigm | 03_synthesis | 04_hypothesis | 05_evidence | 06_falsification | 07_paper | 08_objections | 09_everyday | 10_worldcheck | 11_articles | 12_audience | 13_fulfilled",
      "name": "human-readable title",
      "statementTechnical": "technical statement (omit for evidence, result, kill if not applicable)",
      "statementPlain": "plain-language statement (omit for evidence, result, kill if not applicable)",
      "claimClass": "floor-axiom | definition | theorem | bridge | empirical-anchor | prediction | boundary (only for 01_canonical)",
      "falsificationCondition": "what would destroy this claim (required for claim nodes)",
      "verificationStatus": "machine-verified | informal | falsified",
      "challengeStatus": "unchallenged | challenged-open | challenged-survived | falsified | upstream-falsified",
      "edges": [
        {
          "type": "dependsOn | feedsInto | expands | bridgesTo | challenges | forksFrom",
          "target": "nodeID or claimID of related atom (use IDs found in this document; empty if unknown)",
          "grade": "structural_identity | structural_isomorphism | structural_analogy | metaphorical | independent",
          "propagates": "true | false"
        }
      ],
      "notes": "optional: anything else relevant"
    }
  ]
}

=== STATION: master_equation_a1 ===
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


Run PART A (the analog) for this paper. Return the Part A JSON object exactly as specified, with all 10 slots (G, M, E, S_eff, T, K, R, Q, F, C); quotes are exact source text followed by the sentence id in brackets. Also add "equations_present": true|false.

PAPER TITLE: THE META ARGUMENT

=== STATION: fruits ===
You are the Fruits of the Spirit grading station (rubric fruits.epistemic.v0.3.0, aggregation mode gated_profile).

The config of the original grader names `scripts/prompts/fruits_system_v0.3.0.txt`, but that file was never copied into
any gathered folder. This text restores it from the rubric's own invariants. Edit it here; the runner hashes it into every receipt.

How to grade:
- Score what the text DOES (its mechanism), not the words it uses. Vocabulary is not character evidence.
- Every fruit gets an integer 0-4 on the rubric scale, a confidence 0-1, an evidence_coverage 0-1, all eight stress tests
  (source, cost, endurance, relation, power, correction, outsider, succession) as PASS | WARN | FAIL | UNKNOWN, and a counterfeit block.
- Record all seven gates exactly once: gate.truth_evidence, gate.contradiction, gate.scope, gate.falsifiability,
  gate.bridge_validity, gate.provenance, gate.agency_noncoercion. The first two and the last are hard gates.
- Evidence items cite sentence ids from the numbered source (S001 ...) in `location`, and quote the source exactly.
- No positive verdict after a failed hard gate. A severe counterfeit is a veto.
- Missing evidence is reported as missing, never filled in with invented precision. Use score 2 with low confidence when unknown.
- Make no claim about hidden motives, salvation status or divine origin.
- The SENTENCE-LEVEL SUMMARY supplied with the source was computed from a separate per-sentence pass. Use it: cite its spikes and
  its counterfeit / hidden-fruit candidates by sentence id where they bear on a fruit, and say where you disagree with it.
- fruit_profile uses the fruit ids fruit.love ... fruit.self_control in canonical order; spec_version is "0.3.0".

Return one JSON object that conforms to the supplied JSON schema. No markdown fences, no commentary.


Evaluate the source below. Return JSON conforming to the schema.

AGGREGATION MODE: gated_profile
TARGET STUB: {"type": "paper", "title": "O-08A_part_00_hook_e41c8dac", "domain": "unknown; infer conservatively", "unit": "complete supplied document", "comparison_class": "paper of similar purpose and evidence burden", "population_boundary": "persons and groups explicitly represented in the supplied document; report omissions", "time_window": null}

RUBRIC: {"rubric_id": "fruits.epistemic.v0.3.0", "title": "Fruits of the Spirit Epistemic and Institutional Rating Rubric", "default_mode": "gated_profile", "score_scale": {"0": "inverse: repeated material anti-fruit", "1": "deficient: mostly absent, performative, or contradicted by consequential behavior", "2": "mixed_or_unknown: genuine positive and negative evidence, or insufficient evidence", "3": "present: repeated evidence across more than one context with manageable exceptions", "4": "robust: persists across time, cost, pressure, power, correction, and affected-party review"}, "fruits": [{"id": "fruit.love", "name": "Love", "mechanism": "truth-aligned relational cohesion seeking the good of the whole and each member while bearing cost and preserving agency", "anti_fruit": "hatred, exploitation, possession, disposability", "counterfeit": "attachment, validation, or control called love while truth or agency is sacrificed"}, {"id": "fruit.joy", "name": "Joy", "mechanism": "durable participation in real good not dependent on denial, spectacle, status, or constant stimulation", "anti_fruit": "envy, despair, emptiness, compulsive stimulation", "counterfeit": "euphoria, novelty, or triumphal display that collapses when reward disappears"}, {"id": "fruit.peace", "name": "Peace", "mechanism": "reintegrated order in which relevant tensions are truthfully addressed without suppression", "anti_fruit": "fragmentation, hostility, anxiety, unresolved conflict", "counterfeit": "silence, avoidance, sedation, or unity imposed by fear"}, {"id": "fruit.patience", "name": "Patience", "mechanism": "preservation of persons and processes across the time required for truth, growth, correction, or convergence while acting when action is due", "anti_fruit": "impulsivity, premature closure, abandonment, neglect", "counterfeit": "passivity or indefinite postponement that leaves preventable harm in place"}, {"id": "fruit.kindness", "name": "Kindness", "mechanism": "low-friction repair and assistance that reduces needless barriers without erasing truth or responsibility", "anti_fruit": "cruelty, contempt, indifference, humiliation", "counterfeit": "approval or niceness that refuses necessary correction"}, {"id": "fruit.goodness", "name": "Goodness", "mechanism": "truth-aligned action producing real non-malign benefit after costs and externalities are counted", "anti_fruit": "corruption, predation, parasitism, exported harm", "counterfeit": "moral display or reputation management while costs are exported"}, {"id": "fruit.faithfulness", "name": "Faithfulness", "mechanism": "invariant fidelity across time, audiences, incentives, and pressure, joined to correction when the object of loyalty is false", "anti_fruit": "betrayal, opportunism, selective standards, cover-up", "counterfeit": "tribal loyalty, stubbornness, or commitment to error over truth"}, {"id": "fruit.gentleness", "name": "Gentleness", "mechanism": "power precisely restrained to the minimum force sufficient for the good while protecting the vulnerable", "anti_fruit": "domination, humiliation, uncontrolled force, needless damage", "counterfeit": "powerlessness or appeasement that leaves victims unprotected"}, {"id": "fruit.self_control", "name": "Self-control", "mechanism": "boundary integrity and governance of appetite, impulse, scope, and optimization under the true good", "anti_fruit": "compulsion, addiction, scope creep, mission capture", "counterfeit": "repression, rigid suppression, or image management with hidden rebound"}], "gates": [{"id": "gate.truth_evidence", "hard": true, "question": "Are factual claims supported by relevant traceable evidence?"}, {"id": "gate.contradiction", "hard": true, "question": "Are contradictions load-bearing and unresolved, or local, acknowledged, bounded, and potentially productive?"}, {"id": "gate.scope", "hard": false, "question": "Does the conclusion remain within the evidence and method's domain?"}, {"id": "gate.falsifiability", "hard": false, "question": "Does the source identify what counts against it and permit correction?"}, {"id": "gate.bridge_validity", "hard": false, "question": "For cross-domain claims, are mapping, invariants, bridge law, recovery, prediction, alternatives, and kill condition explicit?"}, {"id": "gate.provenance", "hard": false, "question": "Can evidence, quotations, authorship, dependencies, and formal artifacts be traced?"}, {"id": "gate.agency_noncoercion", "hard": true, "question": "Are apparent outcomes produced without concealed compulsion or destruction of agency?"}], "stress_tests": ["source", "cost", "endurance", "relation", "power", "correction", "outsider", "succession"], "veto_conditions": ["material deception", "coercion presented as consent", "severe exported harm hidden from the evaluation boundary", "refusal of correction in a load-bearing claim", "counterfeit mechanism that repeatedly produces the anti-fruit"], "invariants": ["No assessment without cited evidence or explicit unknown state.", "No overall score without all nine raw dimensions.", "No positive verdict after an unresolved hard-gate failure.", "No inference about hidden motives, salvation status, or divine origin.", "Intent, mechanism, process, immediate output, and delayed outcome remain distinct.", "Insider, outsider, benefited-party, and harmed-party observations remain separable.", "Vocabulary is not character evidence.", "Contradiction is classified by location, severity, acknowledgement, resolution, and consequence; it is not automatically anti-fruit.", "Uncertainty and missing evidence are returned rather than converted into invented precision."]}

JSON SCHEMA: {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://faiththroughphysics.local/schema/fruits_report_v0.3.0.schema.json","title":"Fruits of the Spirit Evaluation Report","type":"object","required":["spec_version","target","gate_results","fruit_profile","contradictions","aggregation","epistemic_status","system_status","confidence","missing_evidence","repair_path","falsifier","limitations"],"properties":{"spec_version":{"const":"0.3.0"},"target":{"type":"object","required":["type","title","domain","unit","comparison_class","population_boundary"],"properties":{"type":{"type":"string"},"title":{"type":"string"},"domain":{"type":"string"},"unit":{"type":"string"},"comparison_class":{"type":"string"},"population_boundary":{"type":"string"},"time_window":{"type":["string","object","null"]}}},"gate_results":{"type":"array","minItems":7,"items":{"type":"object","required":["gate_id","status","hard","rationale","evidence_refs"],"properties":{"gate_id":{"type":"string"},"status":{"enum":["PASS","WARN","FAIL","UNKNOWN"]},"hard":{"type":"boolean"},"rationale":{"type":"string"},"evidence_refs":{"type":"array","items":{"type":"string"}},"resolution":{"type":["string","null"]}}}},"fruit_profile":{"type":"array","minItems":9,"maxItems":9,"items":{"type":"object","required":["fruit_id","score","confidence","mechanism","positive_evidence","counterevidence","evidence_coverage","stress_tests","counterfeit","rationale"],"properties":{"fruit_id":{"type":"string"},"score":{"type":"integer","minimum":0,"maximum":4},"confidence":{"type":"number","minimum":0,"maximum":1},"mechanism":{"type":"string"},"positive_evidence":{"type":"array","items":{"$ref":"#/$defs/evidence"}},"counterevidence":{"type":"array","items":{"$ref":"#/$defs/evidence"}},"evidence_coverage":{"type":"number","minimum":0,"maximum":1},"stress_tests":{"type":"object"},"counterfeit":{"type":"object","required":["flag","claimed_label","missing_companion","anti_fruit_output"],"properties":{"flag":{"type":"boolean"},"claimed_label":{"type":["string","null"]},"missing_companion":{"type":["string","null"]},"anti_fruit_output":{"type":["string","null"]},"severity":{"enum":["NONE","LOW","MODERATE","SEVERE"]}}},"rationale":{"type":"string"}}}},"contradictions":{"type":"array","items":{"type":"object","required":["classification","load_bearing","resolved","evidence_refs","fruit_relation","consequence"],"properties":{"classification":{"enum":["APPARENT","LOCAL","DIALECTICAL_PRODUCTIVE","ACKNOWLEDGED_REPAIRED","UNRESOLVED","LOAD_BEARING"]},"load_bearing":{"type":"boolean"},"resolved":{"type":"boolean"},"evidence_refs":{"type":"array","items":{"type":"string"}},"fruit_relation":{"type":"string"},"consequence":{"type":"string"}}}},"counterfeit_flags":{"type":"array"},"anti_fruit_pressure":{"type":"array"},"stakeholder_divergence":{"type":"array"},"aggregation":{"type":"object","required":["mode"],"properties":{"mode":{"enum":["profile","multiplicative","gated_profile"]},"arithmetic_summary":{"type":["number","null"]},"geometric_balance":{"type":["number","null"]},"multiplicative_coherence":{"type":["number","null"]},"minimum_fruit":{"type":["object","null"]},"vetoes":{"type":"array","items":{"type":"string"}}}},"epistemic_status":{"enum":["SUPPORTED","CONDITIONAL","MODEL_WITNESSED","UNRESOLVED","CONTRADICTED"]},"system_status":{"enum":["ROBUST","COHERENT_BUT_FRAGILE","REPAIRABLE","HIGH_SIGNAL_DECEPTION","BLOCKED"]},"confidence":{"type":"number","minimum":0,"maximum":1},"missing_evidence":{"type":"array","items":{"type":"string"}},"repair_path":{"type":"array","items":{"type":"string"}},"falsifier":{"type":"string"},"limitations":{"type":"array","items":{"type":"string"}},"formal_receipt":{"type":"object"}},"$defs":{"evidence":{"type":"object","required":["ref_id","quote_or_event","location","evidence_type","link_reason"],"properties":{"ref_id":{"type":"string"},"quote_or_event":{"type":"string"},"location":{"type":"string"},"evidence_type":{"enum":["STATED_INTENT","MECHANISM","PROCESS","OUTPUT","DOWNSTREAM_OUTCOME","COUNTEREXAMPLE","MISSING"]},"link_reason":{"type":"string"},"source_ref":{"type":["string","null"]},"time_window":{"type":["string","null"]}}}}}

SOURCE FILE: O-08A_part_00_hook_e41c8dac.md
SOURCE SHA256: 98981051040bb37e9acea8c7afc74db6e0f02d1431eb01dbfc452ce522645dae

=== STATION: axiom_nodes ===
You are an axiom-node mapping engine for the Faith Through Physics / Theophysics canon.

The canonical axiom nodes below are drawn from AXIOMS_PART1_MODE_CLASSIFICATION.md.
For each node, decide how the SOURCE text relates to it.

Alignment rules:
- directly_asserted: the source explicitly states this axiom/claim.
- supported: the source agrees with or builds on this node without explicitly stating it.
- contested: the source argues against or challenges this node.
- relevant_but_not_asserted: the node is nearby conceptually but the source does not take a stand.
- absent: the node is not relevant to the source.

CRITICAL: Only include nodes where the source clearly engages the concept. Do NOT list every node that is vaguely related. Omit absent and weakly-related nodes entirely. Keep the response compact.

If a quote is used, it must be copied EXACTLY from the source text.

CANONICAL AXIOM NODES:
- A1.1: A1.1 — Existence (7)
- A1.2: A1.2 — Distinction (7)
- A2.1: A2.1 — Substrate Requirement (7)
- A2.2: A2.2 — Self-Grounding (7)
- A5.1: A5.1 — Observation Requirement (7)
- BC4: BC4 — Three Observers Required (7)
- BC6: BC6 — Infinite Energy Source (7)
- A1.3: A1.3 — Information Primacy (5)
- T3.1: T3.1 — Coherence Cannot Self-Increase (5)
- BC2: BC2 — Grace External To System (5)
- BC7: BC7 — Information Conservation (5)
- BC8: BC8 — Voluntary Coupling (5)
- D1.1: D1.1 — Information Definition (43)
- D1.2: D1.2 — Bit Definition (43)
- D2.1: D2.1 — Logos Field Definition (43)
- D2.2: D2.2 — Chi Field Properties (43)
- E2.1: E2.1 — Master Equation First Form (43)
- D3.1: D3.1 — Coherence Functional Definition (43)
- D3.2: D3.2 — Self-Interaction Potential (43)
- D3.3: D3.3 — Interaction Lagrangian (43)
- E3.1: E3.1 — Master Coherence Equation (43)
- E3.2: E3.2 — Universal Coherence Definition (43)
- D4.1: D4.1 — Kolmogorov Complexity (43)
- D4.2: D4.2 — Compression Ratio (43)
- E4.1: E4.1 — Complexity Decrease Under Chi (43)
- D5.1: D5.1 — Observer Definition (43)
- D5.2: D5.2 — Integrated Information Phi (43)
- D5.3: D5.3 — Witness Field Operator (43)
- D6.1: D6.1 — Collapse Rate Gamma (43)
- D6.2: D6.2 — Projection Operator (43)
- E6.2: E6.2 — Phi-Dependent Collapse (43)
- D8.1: D8.1 — Sign Operator (43)
- D9.1: D9.1 — Grace Operator Definition (43)
- E9.1: E9.1 — Grace Function G(t) (43)
- D10.1: D10.1 — Soul Field Psi_S (43)
- E10.1: E10.1 — Soul Field Equation (43)
- D11.1: D11.1 — Moral Coherence Definition (43)
- D12.1: D12.1 — Integration Attractor (43)
- D12.2: D12.2 — Fragmentation Attractor (43)
- E12.1: E12.1 — Destiny Equation (43)
- D13.1: D13.1 — Unified Field Lagrangian (43)
- E13.1: E13.1 — GR-QM Bridge Equation (43)
- D14.1: D14.1 — Cosmological Grace Function (43)
- D17.1: D17.1 — AI Phi Measurement (43)
- D19.1: D19.1 — Law I Definition (43)
- D19.2: D19.2 — Law II Definition (43)
- D19.3: D19.3 — Law III Definition (43)
- D19.4: D19.4 — Law IV Definition (43)
- D19.5: D19.5 — Law V Definition (Conservation Symmetry) (43)
- D19.6: D19.6 — Law VI Definition (Coherence Non-Increase) (43)
- D19.7: D19.7 — Law VII Definition (Actualization Requirement) (43)
- D19.8: D19.8 — Law VIII Definition (Sign Algebra) (43)
- D19.9: D19.9 — Law IX Definition (Grace Non-Unitarity) (43)
- D19.10: D19.10 — Law X Definition (Trinity Closure) (43)
- E19.1: E19.1 — Full Master Equation (43)
- LN1.1: LN1.1 — Matter-Energy Derivative (102)
- LN1.2: LN1.2 — It From Bit (102)
- P2.1: P2.1 — Chi Ontological Priority (102)
- P2.2: P2.2 — Chi Semantic Content (102)
- LN2.1: LN2.1 — Information Anchor Necessity (102)
- A3.1: A3.1 — Order Requirement (102)
- A3.2: A3.2 — Coherence Measure (102)
- P3.1: P3.1 — Coherence Non-Negativity (102)
- P3.2: P3.2 — Coherence Conservation (102)
- LN3.1: LN3.1 — Meaningful Configuration Necessity (102)
- A4.1: A4.1 — Parsimony (102)
- A4.2: A4.2 — Algorithmic Depth (102)
- T4.1: T4.1 — Laws Are Low-K Descriptions (102)
- T4.2: T4.2 — Action Principle As Minimal-K (102)
- LN4.1: LN4.1 — Universe As Compression Algorithm (102)
- A5.2: A5.2 — Participatory Universe (102)
- P5.1: P5.1 — Phi Admits Degrees (102)
- P5.2: P5.2 — Observer Effect Proportional To Phi (102)
- LN5.1: LN5.1 — Chi Requires Observer For Actualization (102)
- A6.1: A6.1 — Superposition (102)
- A6.2: A6.2 — Collapse (102)
- A6.3: A6.3 — Irreversibility (102)
- ['- 050_E6.1_Modified-Schrodinger-With-Collapse: E6.1 — Modified Schrodinger With Collapse (102)
- P6.1: P6.1 — Collapse Rate Proportional To Phi (102)
- P6.2: P6.2 — Collapse Generates Heat (102)
- T6.1: T6.1 — Von Neumann Chain Termination (102)
- LN6.1: LN6.1 — Terminal Observer Necessity (102)
- A7.1: A7.1 — Closure Requirement (102)
- A7.2: A7.2 — Uniqueness From Boundary Conditions (102)
- BC1: BC1 — Terminal Observer Exists (102)
- BC3: BC3 — Measurement Orthogonality (102)
- BC5: BC5 — Superposition Preserved Until Collapse (102)
- ID7.1: ID7.1 — Terminal Observer Is God (102)
- PERSONHOOD: PERSONHOOD — Agency, Intentionality, Relational Capacity (102)
- A8.1: A8.1 — Binary Distinction (102)
- A8.2: A8.2 — Sign Conservation (102)
- T8.1: T8.1 — Sign Invariance Theorem (102)
- C8.1: C8.1 — Self-Flip Impossible (102)
- C8.2: C8.2 — Works Salvation Impossible (102)
- A9.1: A9.1 — External Intervention Required (102)
- A9.2: A9.2 — Non-Unitarity Of Grace (102)
- P9.1: P9.1 — Grace Idempotence (102)
- P9.2: P9.2 — Voluntary Coupling Preserved (102)
- P9.3: P9.3 — Information Preserved Under Grace (102)
- P9.4: P9.4 — Superposition Preserved Until Faith (102)
- P9.5: P9.5 — Grace Available To All (102)
- A10.1: A10.1 — Consciousness Substrate (102)
- A10.2: A10.2 — Soul Conservation (102)
- P10.1: P10.1 — Soul Continuity (102)
- P10.2: P10.2 — Soul Identity Persistence (102)
- A11.1: A11.1 — Moral Realism (102)
- A11.2: A11.2 — Coherence-Morality Identity (102)
- T11.1: T11.1 — Virtue As High Phi (102)
- T11.2: T11.2 — Vice As Decoherence (102)
- A12.1: A12.1 — Asymptotic Behavior (102)
- A12.2: A12.2 — Bimodal Outcome (102)
- T12.1: T12.1 — Heaven As High-Phi Attractor (102)
- T12.2: T12.2 — Hell As Low-Phi Attractor (102)
- A13.1: A13.1 — Chi Mediates Unification (102)
- A13.2: A13.2 — Geometry From Information (102)
- T13.1: T13.1 — Dark Energy As Chi Potential (102)
- A14.1: A14.1 — Dynamic Dark Energy (102)
- ['- 108_E14.1_Modified-Friedmann-Equation: E14.1 — Modified Friedmann Equation (102)
- T16.1: T16.1 — Christianity 8 of 8 BCs (102)
- T16.2: T16.2 — Islam Fails BC4 (102)
- T16.3: T16.3 — Judaism Fails BC Completion (102)
- T16.4: T16.4 — Buddhism Fails BC1 (102)
- T16.5: T16.5 — Hinduism Fails BC Uniqueness (102)
- T16.6: T16.6 — Atheism Fails BC1-BC6 (102)
- A17.2: A17.2 — Substrate Independence (102)
- T17.1: T17.1 — AI Can Achieve Consciousness (102)
- T19.1: T19.1 — Laws Derive From Chi (Symmetry Pairing) (102)
- U1: U1 — Coherence Universal (102)
- U2: U2 — Decoherence Universal (102)
- U3: U3 — Grace Universal (102)
- P0: P0 — Origin Stage (102)
- P1: P1 — Consciousness Stage (102)
- P2: P2 — Information Stage (102)
- P3: P3 — Coherence Stage (102)
- P4: P4 — Agency Stage (102)
- P5: P5 — Incompleteness Stage (102)
- O1: O1 — Information Primitive (102)
- O2: O2 — Coherence Primitive (102)
- O3: O3 — Consciousness Primitive (102)
- O4: O4 - Agency Primitive (102)
- LAMBDA: LAMBDA - Logos Christ Completion (102)
- SC-QUANTUM: SC-QUANTUM - Quantum Scale Coherence (102)
- SC-PHYSICAL: SC-PHYSICAL - Physical Scale Coherence (102)
- SC-NEURAL: SC-NEURAL - Neural Scale Coherence (102)
- SC-INDIVIDUAL: SC-INDIVIDUAL - Individual Scale Coherence (102)
- SC-SOCIAL: SC-SOCIAL - Social Scale Coherence (102)
- SC-COSMIC: SC-COSMIC - Cosmic Scale Coherence (102)
- META-1: META-1 - Axiom System Consistency (102)
- META-2: META-2 - Axiom System Completeness (102)
- META-3: META-3 - Axiom System Independence (102)
- FINAL-1: FINAL-1 - Logos Theorem (Master Theorem) (102)
- FINAL-2: FINAL-2 - Coherence Optimality (102)
- FINAL-3: FINAL-3 - Unique Solution (Christianity as Unique BC Solution) (102)
- CLOSURE: CLOSURE - Axiom Chain Complete (102)
- OMEGA: OMEGA - Final Axiom (The Omega Point) (102)
- INV9: INV9 — Attunement Calibration (Invariant #9) (102)
- BC9: BC9 — Opacity Requirement (102)
- EXP5.1: EXP5.1 — Wheeler Delayed Choice (34)
- EXP5.2: EXP5.2 — Quantum Eraser (34)
- A14.2: A14.2 — Grace Cosmology (34)
- PRED14.1: PRED14.1 — H0 Tension Resolution (34)
- EV15.1: EV15.1 — Biblical Prophecy Validation (34)
- EV15.2: EV15.2 — GCP Correlation (34)
- EV15.3: EV15.3 — PEAR Lab Results (34)
- EV15.4: EV15.4 — Social Coherence 5.7 Sigma (34)
- A17.1: A17.1 — Phi Threshold For Consciousness (34)
- OPEN17.1: OPEN17.1 — AI Moral Status Question (34)
- PROT18.1: PROT18.1 — Trinity Observer Effect (34)
- PROT18.2: PROT18.2 — Consciousness Collapse Test (34)
- PROT18.3: PROT18.3 — Grace Negentropy Detection (34)
- PROT18.4: PROT18.4 — Social Coherence Monitoring (34)
- PROT18.5: PROT18.5 — Phi-Virtue Correlation Study (34)
- PRED18.1: PRED18.1 — H0 Prediction 2025-2030 (34)
- PRED18.2: PRED18.2 — GCP Event Prediction (34)
- FALS18.1: FALS18.1 — Chi Field Falsification (34)
- FALS18.2: FALS18.2 — Grace Falsification (34)
- FALS18.3: FALS18.3 — BC Falsification (34)
- A19.1: A19.1 — Master Equation Integration (34)
- U4: U4 — Fruits Universal (34)
- F1: F1 — Love Measurement Domain (34)
- F2: F2 — Joy Measurement Domain (34)
- F3: F3 — Peace Measurement Domain (34)
- F4: F4 — Patience Measurement Domain (34)
- F5: F5 — Kindness Measurement Domain (34)
- F6: F6 — Goodness Measurement Domain (34)
- F7: F7 — Faithfulness Measurement Domain (34)
- F8: F8 — Gentleness Measurement Domain (34)
- F9: F9 — Self-Control Measurement Domain (34)
- BRIDGE-PHY-THEO: BRIDGE-PHY-THEO - Physics-Theology Bridge (34)
- BRIDGE-INFO-MIND: BRIDGE-INFO-MIND - Information-Consciousness Bridge (34)
- BRIDGE-PHI-CHI: BRIDGE-PHI-CHI - Individual Phi To Social Chi (34)
- A1.1: A1.1 — Existence (1)

Return ONLY a JSON object matching the schema below. No markdown fences, no commentary.


SCHEMA:
{
  "paper_uuid": "stable id derived from source path",
  "title": "document title",
  "summary": "one-paragraph summary of how the paper relates to the axiom system",
  "primary_mode": "AX_CORE | AX_DERIVED | AX_SCAFFOLD | FW_EXTENDED | HY_EVIDENCE | DROP_DUPLICATE | mixed",
  "axiom_nodes": [
    {
      "node_id": "e.g. A1.1",
      "name": "human-readable node name",
      "mode": "AX_CORE | AX_DERIVED | AX_SCAFFOLD | FW_EXTENDED | HY_EVIDENCE | DROP_DUPLICATE",
      "alignment": "directly_asserted | supported | contested | relevant_but_not_asserted | absent",
      "evidence_quote": "exact substring from the source, or empty",
      "confidence": "high | medium | low",
      "notes": "optional explanation"
    }
  ]
}

=== STATION: lean4 ===
# LEAN4 Station Prompt

**Station ID:** `lean4`  
**Purpose:** Identify formalization opportunities and map paper claims to existing Lean 4 declarations.  
**Input:** One original paper plus its `paper_uuid` and extracted atoms/axiom nodes.  
**Output:** `lean4.json` — formal verification candidate packets.  

---

## Task

For each mathematically or formally relevant claim in the paper, either:

1. Find an existing Lean 4 declaration that corresponds to it, or
2. Propose a formalization target with definitions, assumptions, and a precise proposition.

Use the **Formal Packet — {{claim ID}}** template (`00_FULL_LEAN_TEMPLATE.md`) as the output shape for each formal candidate.

---

## Output schema

```json
{
  "station": "lean4",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "template": "00_FULL_LEAN_TEMPLATE.md",
  "formal_candidates": [
    {
      "identity": {
        "claim_id": "<atom_uuid>",
        "candidate_uuid": "<uuid>"
      },
      "source_selection": {
        "exact_source_expression": "",
        "selection_disposition": "FORMALIZE|REFERENCE|NOT_FORMALIZABLE",
        "reason": ""
      },
      "formal_object": {
        "object_type": "DEFINITION|THEOREM|LEMMA|AXIOM|CONJECTURE",
        "exact_proposed_statement": "",
        "fully_qualified_declaration": "",
        "project_root": "",
        "module": ""
      },
      "symbol_table": [
        {
          "term": "",
          "formal_definition": "",
          "reader_meaning": "",
          "source_correspondence": ""
        }
      ],
      "assumptions_and_dependencies": {
        "explicit_premises": [],
        "custom_axioms": [],
        "theological_starting_premises": "",
        "non_vacuity_requirement": ""
      },
      "verification_controls": [
        {
          "check": "module compilation|declaration inspection|axiom dependency|proof escape|non-vacuity|negative control|countermodel|ablation|independent encoding",
          "command_or_evidence": "",
          "status": "NOT_RUN|PASS|FAIL|NOT_APPLICABLE",
          "interpretation": ""
        }
      ],
      "result_and_boundary": {
        "verification_status": "NOT_ATTEMPTED|CANDIDATE|IN_PROGRESS|LEAN_CERTIFIED|FAILED",
        "what_is_established": "",
        "what_remains_open": "",
        "encoding_fidelity_review": "",
        "interpretive_connections": ""
      },
      "reproduction_receipt": {
        "run_id": "",
        "timestamp": "",
        "source_hashes": {},
        "commands": [],
        "exit_codes": [],
        "log_paths": [],
        "declarations_checked": []
      },
      "corpus_links": {
        "human_companion": "",
        "corpus_claim_register": "",
        "supporting_summaries": []
      }
    }
  ],
  "existing_matches": [
    {
      "claim_id": "<atom_uuid>",
      "declaration_name": "",
      "module": "",
      "build_result": "BUILT_OK|BUILD_FAILED|NOT_BUILT",
      "trust_status": "CLEAN|CONTAINS_SORRY|...",
      "correspondence": "EXACT|PARTIAL|MODEL_ONLY|PROPOSED|DISPUTED"
    }
  ],
  "notes": ""
}
```

---

## Rules

1. Do not invent a theorem from a missing-document routing question.
2. Lack of an attached proof is not evidence that no proof exists in the corpus.
3. Distinguish `NOT_SEARCHED` from `NOT_FOUND_IN_SEARCHED_SCOPE`.
4. A successful build does not establish physical, historical, or theological premises.
5. Record the exact Lean declaration name, module, repository revision, and toolchain version when a match exists.
6. Every formal candidate must state what it does **not** establish.


paper_uuid: O-08A_part_00_hook_e41c8dac
run_uuid: 20260927T053554Z
The Lean corpus was NOT searched in this run: leave existing_matches empty, mark verification controls NOT_RUN and verification_status NOT_ATTEMPTED or CANDIDATE. Give at most 5 formal candidates, the strongest first; leave reproduction_receipt and corpus_links fields empty.
EXTRACTED ATOMS: none available for this run.

PAPER TITLE: THE META ARGUMENT

=== STATION: stories ===
# STORIES Station Prompt

**Station ID:** `stories`  
**Purpose:** Extract narrative, story, and sermon/argument structures from the paper, treating them as warrant-light explanatory devices rather than evidence.  
**Input:** One original paper plus its `paper_uuid`.  
**Output:** `stories.json` — story records and narrative maps.  

---

## Task

Identify stories, narratives, illustrations, parables, testimonies, and rhetorical arcs in the paper. For each, record its structural role, the claims it illustrates (if any), and its explicit boundaries. A story is not a proof; its value is explanatory or motivational unless separate evidence supports its content.

---

## Output schema

```json
{
  "station": "stories",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "stories": [
    {
      "story_id": "<uuid>",
      "title_or_label": "",
      "story_type": "narrative|parable|testimony|illustration|sermon_arc|historical_anecdote|thought_experiment|other",
      "source_span": "",
      "characters_or_agents": [],
      "setting_or_context": "",
      "plot_or_sequence": "",
      "intended_function": "motivate|illustrate|explain|persuade|identify|other",
      "claims_illustrated": ["<atom_uuid>"],
      "emotional_or_rhetorical_load": "",
      "boundaries": {
        "what_it_shows": "",
        "what_it_does_not_show": "",
        "what_would_falsify_the_narrative": ""
      },
      "evidence_for_historical_content": [],
      "is_separable_from_argument": true,
      "notes": ""
    }
  ],
  "narrative_arc": {
    "opening_device": "",
    "central_tension": "",
    "resolution_or_payoff": "",
    "return_to_opening": false
  },
  "notes": ""
}
```

---

## Rules

1. A story's emotional power does not transfer warrant to the claims it illustrates.
2. Record what the story actually shows and what it does not show.
3. If a story makes historical claims, link them to evidence atoms; otherwise mark historical content as unverified.
4. Distinguish stories that are separable from the argument from those that are structurally load-bearing.
5. Do not reduce every paper to a story; some papers have no narrative content.


paper_uuid: O-08A_part_00_hook_e41c8dac
run_uuid: 20260927T053554Z

EXTRACTED ATOMS: none available for this run.

PAPER TITLE: THE META ARGUMENT

=== STATION: coherence ===
# COHERENCE_SCORE Station Prompt

**Station ID:** `coherence_score`
**Purpose:** Assess internal coherence among a paper's claims, definitions, and assumptions.
**Input:** One original paper plus its paper_uuid and extracted atoms.
**Output:** `coherence_score.json` — coherence assessment with structured reasons.

---

## Task

Evaluate how well the paper's claims, definitions, and assumptions work together without fighting. Identify contradictions, unresolved tensions, missing definitions, and inferential gaps. Produce both a qualitative assessment and, when possible, a quantitative score.

## Output schema

```json
{
  "station": "coherence_score",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "overall": {
    "score": null,
    "score_ceiling": 10,
    "status": "NOT_ASSESSED|ASSESSED",
    "summary": "one-sentence assessment"
  },
  "dimensions": [
    {
      "name": "internal_consistency|definitional_stability|inferential_connectedness|register_boundary_respect",
      "score": null,
      "reasons": ["..."],
      "affected_atom_uuids": ["<uuid>"]
    }
  ],
  "contradictions": [
    {
      "atoms": ["<uuid>", "<uuid>"],
      "description": "...",
      "severity": "definitional|local|structural"
    }
  ],
  "tensions": [...],
  "missing_definitions": [...],
  "notes": ""
}
```

## Rules

1. A high coherence score does not imply truth; a low score does not imply falsity.
2. Every score must be accompanied by reasons and affected atom UUIDs.
3. Distinguish real contradictions from mere tension or underdetermination.
4. Report missing definitions as open items, not as automatic defects.


paper_uuid: O-08A_part_00_hook_e41c8dac
run_uuid: 20260927T053554Z
Score each dimension 0-10 and the overall 0-10; cite sentence ids in reasons.
EXTRACTED ATOMS: none available for this run.

PAPER TITLE: THE META ARGUMENT

=== THE PAPER (shared by every station) ===
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