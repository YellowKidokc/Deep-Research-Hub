
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

SOURCE:
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

Return ONLY the JSON object. No markdown fences, no commentary.
For every atom also add "source_sentences": [sentence ids].
