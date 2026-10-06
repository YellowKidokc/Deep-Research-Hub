# Truth Stack Architecture Note

This note captures the missing layer between raw claims and chi-based coherence scoring.

## Core sentence

Truth is not one score. Truth is claim-type plus attestation plus coherence under stated assumptions.

In system language:

- chi tells whether the claim coheres
- truth mode tells what kind of reality the claim belongs to
- attestation mode tells how that kind of claim can be known

## The bug this fixes

If a truth engine jumps straight to:

- true
- false

it flattens unlike things into the same category.

That breaks:

- institutional claims
- moral claims
- symbolic claims
- theological claims
- experiential reports
- classification claims
- pre-assumptions

## The stack

Layer 0 - Raw claim

What sentence is being tested?

Layer 1 - Claim type

What kind of truth claim is it?

Layer 2 - Assumption load

Which assumptions must be accepted before this claim can be evaluated?

Layer 3 - Attestation type

Who or what can verify it?

Layer 4 - Domain fit

Which of the ten variables does it depend on?

Layer 5 - Evidence bridge

What connects the evidence to the claim?

Layer 6 - Coherence / chi profile

Does it integrate cleanly or produce contradiction?

Layer 7 - Truth status

Possible statuses:

- true
- false
- partial
- symbolic
- conventional
- contested
- unknown

## Truth modes

Use one or more:

- AXIOM
- PRE_ASSUMPTION
- EMPIRICAL_EVENT
- INSTRUMENT_MEASUREMENT
- HISTORICAL_RECORD
- INSTITUTIONAL_FACT
- LEGAL_FACT
- MATHEMATICAL_PROOF
- FORMAL_DERIVATION
- CLASSIFICATION
- INTERPRETATION
- SYMBOLIC_TRUTH
- MORAL_CLAIM
- THEOLOGICAL_CLAIM
- EXPERIENTIAL_REPORT
- PREDICTION
- UNKNOWN

## Attestation modes

Use one or more:

- direct_observation
- instrument_measurement
- public_record
- legal_record
- institutional_recognition
- mathematical_proof
- scriptural_authority
- expert_consensus
- self_report
- statistical_inference
- model_prediction

## Assumption load

- A0 = direct / minimal assumption
- A1 = requires ordinary background assumptions
- A2 = requires institutional definitions
- A3 = requires theoretical framework
- A4 = requires metaphysical/theological axiom
- A5 = highly dependent / worldview-bound

## Why this matters

Different claims live in different truth-regimes.

Examples:

- a solar eclipse date is an empirical / historical event claim
- a party affiliation claim is partly institutional and partly classificatory
- a proof result is mathematical
- a legal status is jurisdiction-bound
- a moral judgment is not the same kind of thing as an instrument reading
- a theological claim may be coherent within an axiom-set without being empirically measurable

The engine must not flatten these.

## Relationship to the ten variables

The ten-variable system measures dependency and coherence burden.

It helps answer:

- what the claim relies on
- where it becomes unstable
- whether support is actually relevant
- which bridges are missing

It does not by itself determine claim type or attestation mode.

## Recommended output shape for claim review

CLAIM:
TRUTH_MODE:
ASSUMPTION_LOAD:
ATTESTATION_MODE:
REQUIRED_DEFINITIONS:
TEN_VARIABLE_DEPENDENCY:
EVIDENCE_BRIDGE:
CHI_PROFILE:
STATUS:
WHY:
FAILURE_POINT:
WHAT_WOULD_CHANGE_STATUS:

## Operational rule

Before chi:

1. identify claim type
2. identify assumption load
3. identify attestation mode

Then:

4. test evidence bridge
5. evaluate coherence
6. assign truth-status under stated definitions
