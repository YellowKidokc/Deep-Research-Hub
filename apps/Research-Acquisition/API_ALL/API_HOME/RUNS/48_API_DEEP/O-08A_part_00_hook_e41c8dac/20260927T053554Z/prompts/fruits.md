## SYSTEM

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


## USER

Evaluate the source below. Return JSON conforming to the schema.

AGGREGATION MODE: gated_profile
TARGET STUB: {"type": "paper", "title": "O-08A_part_00_hook_e41c8dac", "domain": "unknown; infer conservatively", "unit": "complete supplied document", "comparison_class": "paper of similar purpose and evidence burden", "population_boundary": "persons and groups explicitly represented in the supplied document; report omissions", "time_window": null}

RUBRIC: {"rubric_id": "fruits.epistemic.v0.3.0", "title": "Fruits of the Spirit Epistemic and Institutional Rating Rubric", "default_mode": "gated_profile", "score_scale": {"0": "inverse: repeated material anti-fruit", "1": "deficient: mostly absent, performative, or contradicted by consequential behavior", "2": "mixed_or_unknown: genuine positive and negative evidence, or insufficient evidence", "3": "present: repeated evidence across more than one context with manageable exceptions", "4": "robust: persists across time, cost, pressure, power, correction, and affected-party review"}, "fruits": [{"id": "fruit.love", "name": "Love", "mechanism": "truth-aligned relational cohesion seeking the good of the whole and each member while bearing cost and preserving agency", "anti_fruit": "hatred, exploitation, possession, disposability", "counterfeit": "attachment, validation, or control called love while truth or agency is sacrificed"}, {"id": "fruit.joy", "name": "Joy", "mechanism": "durable participation in real good not dependent on denial, spectacle, status, or constant stimulation", "anti_fruit": "envy, despair, emptiness, compulsive stimulation", "counterfeit": "euphoria, novelty, or triumphal display that collapses when reward disappears"}, {"id": "fruit.peace", "name": "Peace", "mechanism": "reintegrated order in which relevant tensions are truthfully addressed without suppression", "anti_fruit": "fragmentation, hostility, anxiety, unresolved conflict", "counterfeit": "silence, avoidance, sedation, or unity imposed by fear"}, {"id": "fruit.patience", "name": "Patience", "mechanism": "preservation of persons and processes across the time required for truth, growth, correction, or convergence while acting when action is due", "anti_fruit": "impulsivity, premature closure, abandonment, neglect", "counterfeit": "passivity or indefinite postponement that leaves preventable harm in place"}, {"id": "fruit.kindness", "name": "Kindness", "mechanism": "low-friction repair and assistance that reduces needless barriers without erasing truth or responsibility", "anti_fruit": "cruelty, contempt, indifference, humiliation", "counterfeit": "approval or niceness that refuses necessary correction"}, {"id": "fruit.goodness", "name": "Goodness", "mechanism": "truth-aligned action producing real non-malign benefit after costs and externalities are counted", "anti_fruit": "corruption, predation, parasitism, exported harm", "counterfeit": "moral display or reputation management while costs are exported"}, {"id": "fruit.faithfulness", "name": "Faithfulness", "mechanism": "invariant fidelity across time, audiences, incentives, and pressure, joined to correction when the object of loyalty is false", "anti_fruit": "betrayal, opportunism, selective standards, cover-up", "counterfeit": "tribal loyalty, stubbornness, or commitment to error over truth"}, {"id": "fruit.gentleness", "name": "Gentleness", "mechanism": "power precisely restrained to the minimum force sufficient for the good while protecting the vulnerable", "anti_fruit": "domination, humiliation, uncontrolled force, needless damage", "counterfeit": "powerlessness or appeasement that leaves victims unprotected"}, {"id": "fruit.self_control", "name": "Self-control", "mechanism": "boundary integrity and governance of appetite, impulse, scope, and optimization under the true good", "anti_fruit": "compulsion, addiction, scope creep, mission capture", "counterfeit": "repression, rigid suppression, or image management with hidden rebound"}], "gates": [{"id": "gate.truth_evidence", "hard": true, "question": "Are factual claims supported by relevant traceable evidence?"}, {"id": "gate.contradiction", "hard": true, "question": "Are contradictions load-bearing and unresolved, or local, acknowledged, bounded, and potentially productive?"}, {"id": "gate.scope", "hard": false, "question": "Does the conclusion remain within the evidence and method's domain?"}, {"id": "gate.falsifiability", "hard": false, "question": "Does the source identify what counts against it and permit correction?"}, {"id": "gate.bridge_validity", "hard": false, "question": "For cross-domain claims, are mapping, invariants, bridge law, recovery, prediction, alternatives, and kill condition explicit?"}, {"id": "gate.provenance", "hard": false, "question": "Can evidence, quotations, authorship, dependencies, and formal artifacts be traced?"}, {"id": "gate.agency_noncoercion", "hard": true, "question": "Are apparent outcomes produced without concealed compulsion or destruction of agency?"}], "stress_tests": ["source", "cost", "endurance", "relation", "power", "correction", "outsider", "succession"], "veto_conditions": ["material deception", "coercion presented as consent", "severe exported harm hidden from the evaluation boundary", "refusal of correction in a load-bearing claim", "counterfeit mechanism that repeatedly produces the anti-fruit"], "invariants": ["No assessment without cited evidence or explicit unknown state.", "No overall score without all nine raw dimensions.", "No positive verdict after an unresolved hard-gate failure.", "No inference about hidden motives, salvation status, or divine origin.", "Intent, mechanism, process, immediate output, and delayed outcome remain distinct.", "Insider, outsider, benefited-party, and harmed-party observations remain separable.", "Vocabulary is not character evidence.", "Contradiction is classified by location, severity, acknowledgement, resolution, and consequence; it is not automatically anti-fruit.", "Uncertainty and missing evidence are returned rather than converted into invented precision."]}

JSON SCHEMA: {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://faiththroughphysics.local/schema/fruits_report_v0.3.0.schema.json","title":"Fruits of the Spirit Evaluation Report","type":"object","required":["spec_version","target","gate_results","fruit_profile","contradictions","aggregation","epistemic_status","system_status","confidence","missing_evidence","repair_path","falsifier","limitations"],"properties":{"spec_version":{"const":"0.3.0"},"target":{"type":"object","required":["type","title","domain","unit","comparison_class","population_boundary"],"properties":{"type":{"type":"string"},"title":{"type":"string"},"domain":{"type":"string"},"unit":{"type":"string"},"comparison_class":{"type":"string"},"population_boundary":{"type":"string"},"time_window":{"type":["string","object","null"]}}},"gate_results":{"type":"array","minItems":7,"items":{"type":"object","required":["gate_id","status","hard","rationale","evidence_refs"],"properties":{"gate_id":{"type":"string"},"status":{"enum":["PASS","WARN","FAIL","UNKNOWN"]},"hard":{"type":"boolean"},"rationale":{"type":"string"},"evidence_refs":{"type":"array","items":{"type":"string"}},"resolution":{"type":["string","null"]}}}},"fruit_profile":{"type":"array","minItems":9,"maxItems":9,"items":{"type":"object","required":["fruit_id","score","confidence","mechanism","positive_evidence","counterevidence","evidence_coverage","stress_tests","counterfeit","rationale"],"properties":{"fruit_id":{"type":"string"},"score":{"type":"integer","minimum":0,"maximum":4},"confidence":{"type":"number","minimum":0,"maximum":1},"mechanism":{"type":"string"},"positive_evidence":{"type":"array","items":{"$ref":"#/$defs/evidence"}},"counterevidence":{"type":"array","items":{"$ref":"#/$defs/evidence"}},"evidence_coverage":{"type":"number","minimum":0,"maximum":1},"stress_tests":{"type":"object"},"counterfeit":{"type":"object","required":["flag","claimed_label","missing_companion","anti_fruit_output"],"properties":{"flag":{"type":"boolean"},"claimed_label":{"type":["string","null"]},"missing_companion":{"type":["string","null"]},"anti_fruit_output":{"type":["string","null"]},"severity":{"enum":["NONE","LOW","MODERATE","SEVERE"]}}},"rationale":{"type":"string"}}}},"contradictions":{"type":"array","items":{"type":"object","required":["classification","load_bearing","resolved","evidence_refs","fruit_relation","consequence"],"properties":{"classification":{"enum":["APPARENT","LOCAL","DIALECTICAL_PRODUCTIVE","ACKNOWLEDGED_REPAIRED","UNRESOLVED","LOAD_BEARING"]},"load_bearing":{"type":"boolean"},"resolved":{"type":"boolean"},"evidence_refs":{"type":"array","items":{"type":"string"}},"fruit_relation":{"type":"string"},"consequence":{"type":"string"}}}},"counterfeit_flags":{"type":"array"},"anti_fruit_pressure":{"type":"array"},"stakeholder_divergence":{"type":"array"},"aggregation":{"type":"object","required":["mode"],"properties":{"mode":{"enum":["profile","multiplicative","gated_profile"]},"arithmetic_summary":{"type":["number","null"]},"geometric_balance":{"type":["number","null"]},"multiplicative_coherence":{"type":["number","null"]},"minimum_fruit":{"type":["object","null"]},"vetoes":{"type":"array","items":{"type":"string"}}}},"epistemic_status":{"enum":["SUPPORTED","CONDITIONAL","MODEL_WITNESSED","UNRESOLVED","CONTRADICTED"]},"system_status":{"enum":["ROBUST","COHERENT_BUT_FRAGILE","REPAIRABLE","HIGH_SIGNAL_DECEPTION","BLOCKED"]},"confidence":{"type":"number","minimum":0,"maximum":1},"missing_evidence":{"type":"array","items":{"type":"string"}},"repair_path":{"type":"array","items":{"type":"string"}},"falsifier":{"type":"string"},"limitations":{"type":"array","items":{"type":"string"}},"formal_receipt":{"type":"object"}},"$defs":{"evidence":{"type":"object","required":["ref_id","quote_or_event","location","evidence_type","link_reason"],"properties":{"ref_id":{"type":"string"},"quote_or_event":{"type":"string"},"location":{"type":"string"},"evidence_type":{"enum":["STATED_INTENT","MECHANISM","PROCESS","OUTPUT","DOWNSTREAM_OUTCOME","COUNTEREXAMPLE","MISSING"]},"link_reason":{"type":"string"},"source_ref":{"type":["string","null"]},"time_window":{"type":["string","null"]}}}}}

SOURCE FILE: O-08A_part_00_hook_e41c8dac.md
SOURCE SHA256: 98981051040bb37e9acea8c7afc74db6e0f02d1431eb01dbfc452ce522645dae

--- BEGIN SOURCE ---
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
--- END SOURCE ---


SENTENCE-LEVEL SUMMARY (from the per-sentence pass):
{"note": "per-sentence pass not run in copy mode"}
