# NABLA-CHI Classification Quick Reference

This is the short operational version of the Stratum classification standard.

## Core posture

Classify what the artifact is and does, not merely what it talks about.

Keep these layers separate:

1. artifact identity
2. semantic orientation
3. claim type
4. evidence and attestation
5. coherence
6. risk
7. repair path

## Canonical address

Use:

`D/N/V/A/U/R :: VECTOR :: HASH`

Where:

- `D` = domain
- `N` = named entity
- `V` = version/state
- `A` = audience/access
- `U` = use/direction
- `R` = risk

## Domain values

`THEOPHYSICS, SCIENCE, LAW, MEDICINE, FINANCE, PERSONAL, TECH, EDUCATION, GOVERNANCE, ART, BUSINESS, RELIGION, HISTORY, MDA, DATA, UNKNOWN`

## Version/state values

`D, W, F, P, A, X, U`

Meaning:

- `D` draft
- `W` working
- `F` final
- `P` published
- `A` archived
- `X` deprecated
- `U` unknown

## Audience/access values

`SELF, INTERNAL, TEAM, AI_RESEARCH, PUBLIC, PUBLIC_RESEARCH, ACADEMIC, CLIENT, RESTRICTED, LEGAL, UNKNOWN`

## Use/direction values

Use one primary value only:

- `I` inform
- `B` bind
- `T` transform
- `R` record

## Risk values

- `R0` public / low sensitivity
- `R1` internal research
- `R2` private / sensitive
- `R3` legal / financial / formal consequence / reputational
- `R4` life-critical / medical / safety-critical

## Semantic vector

Score each variable only `0` or `3` for the address.

- `G` authority / ground
- `M` mechanism / action
- `E` artifact disorder
- `S` identity / self
- `T` time / sequence
- `K` knowledge / information
- `R` relation / bond
- `Q` experience / felt
- `F` faith / trust
- `C` coherence / unity

## Six no-drift rules

1. Classify artifact, not topic.
2. Use binary orientation for the address.
3. Put uncertainty in confidence, not in `1` or `2`.
4. `E` means artifact disorder only.
5. `C` means explicit synthesis function, not mere good writing.
6. Address is not truth.

## Claim gate

Identify claim type before truth status.

Examples:

- `AXIOM`
- `EMPIRICAL_EVENT`
- `HISTORICAL_RECORD`
- `MATHEMATICAL_PROOF`
- `FORMAL_DERIVATION`
- `CLASSIFICATION`
- `INTERPRETATION`
- `MORAL_CLAIM`
- `THEOLOGICAL_CLAIM`
- `EXPERIENTIAL_REPORT`
- `PREDICTION`

## Four grades

Never collapse into one truth score:

1. academic readiness
2. framework coherence
3. public communication
4. risk

## Final rule

Return structure first.
If uncertain, flag review instead of inventing certainty.
