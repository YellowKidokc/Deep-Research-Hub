## SYSTEM

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


## USER

paper_uuid: O-08A_part_00_hook_e41c8dac
run_uuid: 20260927T053554Z
The Lean corpus was NOT searched in this run: leave existing_matches empty, mark verification controls NOT_RUN and verification_status NOT_ATTEMPTED or CANDIDATE. Give at most 5 formal candidates, the strongest first; leave reproduction_receipt and corpus_links fields empty.
EXTRACTED ATOMS: none available for this run.

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

Return ONLY one JSON object. No markdown fences, no commentary.
