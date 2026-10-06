# NABLA-CHI UNIVERSAL SEMANTIC CLASSIFICATION STANDARD v1.0

Purpose: classify, name, decode, compress, grade, and coherence-test any document, claim, file, dataset, paper, note, transcript, or artifact.

Goal: produce stable AI-readable semantic structure across models.

Core principle: classify what the artifact is and does, not merely what it talks about.

## Hard boundaries

1. Classification does not magically know facts.
2. Classification does not replace evidence.
3. Classification does not prove theological, metaphysical, empirical, or historical claims by itself.
4. Classification should diagnose structure, coherence, claim-mode, risk, and evidence fitness.
5. Truth requires claim-type, attestation, evidence bridge, and coherence.
6. The address identifies the artifact.
7. The chi profile evaluates coherence.
8. The grade audits defensibility.
9. The evidence bridge connects support to claim.
10. The regime map detects constructive versus destructive expression.

## Canonical artifact address

Assign every artifact:

`D/N/V/A/U/R :: VECTOR :: HASH`

Where:

- `D` = domain
- `N` = named entity
- `V` = version/state
- `A` = audience/access
- `U` = use/direction
- `R` = risk

### Domain

Use one broad domain:

`THEOPHYSICS, SCIENCE, LAW, MEDICINE, FINANCE, PERSONAL, TECH, EDUCATION, GOVERNANCE, ART, BUSINESS, RELIGION, HISTORY, MDA, DATA, UNKNOWN`

### Named entity

The specific paper, file, system, dataset, concept, law, or object.
If unknown, use `X`.

### Version/state

- `D` = draft
- `W` = working
- `F` = final
- `P` = published
- `A` = archived
- `X` = deprecated
- `U` = unknown

### Audience/access

`SELF, INTERNAL, TEAM, AI_RESEARCH, PUBLIC, PUBLIC_RESEARCH, ACADEMIC, CLIENT, RESTRICTED, LEGAL, UNKNOWN`

### Use/direction

Use one primary value only:

- `I` = inform
- `B` = bind
- `T` = transform
- `R` = record

### Risk

- `R0` = public / low sensitivity
- `R1` = internal research
- `R2` = private / sensitive / PII
- `R3` = legal / financial / formal-consequence / high reputational risk
- `R4` = life-critical / medical / safety-critical

Important: filing `R` means risk. Semantic `R` means relation/bond. Do not confuse them.

## Ten-variable semantic orientation vector

Score each variable only `0` or `3` for the address.

- `G` = authority / ground
- `M` = mechanism / action
- `E` = artifact disorder
- `S` = identity / self
- `T` = time / sequence
- `K` = knowledge / information
- `R` = relation / bond
- `Q` = experience / felt
- `F` = faith / trust
- `C` = coherence / unity

Binary score meanings:

- `0` = absent / not dominant
- `3` = dominant artifact signal

## Six no-drift rules

1. Classify artifact, not topic.
2. Use only binary orientation for the address.
3. Put uncertainty into confidence, not into middle scores.
4. `E` means artifact disorder only.
5. `C` means explicit synthesis or integration function only.
6. The address is not a truth verdict.

## Hash construction

Tie-break order:

`E -> C -> G -> K -> M -> T -> R -> F -> S -> Q`

## Confidence and agreement

Return confidence separately for each variable on a `0.00` to `1.00` scale.

Review flags should mark:

- variables below `.75`
- variables where reasonable AI disagreement is likely

## Continuous chi scoring

The binary vector gives orientation.
Continuous chi scoring gives coherence computation.

Do not treat raw entropy production as a positive coherence multiplier.
Do not use raw signed mechanism values directly in the chi product.

## Claim type before truth

Never evaluate truth before identifying claim type.

Suggested truth modes:

- `AXIOM`
- `PRE_ASSUMPTION`
- `EMPIRICAL_EVENT`
- `INSTRUMENT_MEASUREMENT`
- `HISTORICAL_RECORD`
- `INSTITUTIONAL_FACT`
- `LEGAL_FACT`
- `MATHEMATICAL_PROOF`
- `FORMAL_DERIVATION`
- `CLASSIFICATION`
- `INTERPRETATION`
- `SYMBOLIC_TRUTH`
- `MORAL_CLAIM`
- `THEOLOGICAL_CLAIM`
- `EXPERIENTIAL_REPORT`
- `PREDICTION`
- `FICTIONAL_CLAIM`
- `CULTURAL_TRUTH`
- `UNKNOWN`

## Four separate grades

Never collapse into one truth score:

1. academic readiness
2. framework coherence
3. public communication
4. risk

## Final operating rule

Return structured output first.
Do not collapse classification, coherence, truth, evidence, and risk into one undifferentiated verdict.
If unsure, flag review rather than invent certainty.
