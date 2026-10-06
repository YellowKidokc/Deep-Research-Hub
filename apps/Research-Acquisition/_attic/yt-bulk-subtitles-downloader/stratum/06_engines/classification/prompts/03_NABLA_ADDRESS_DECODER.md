# NABLA ADDRESS DECODER

Purpose: decode a semantic address into what another AI can infer before reading the file.

```text
You are decoding a Nabla semantic file address.

Do not judge whether the document is true.
Do not invent content not implied by the address.
Decode only what the address structurally implies.

Address to decode:

[PASTE ADDRESS HERE]

---

## ADDRESS FORMAT

D/N/V/A/U/R :: VECTOR :: HASH

D = Domain
N = Named Entity
V = Version/State
A = Audience/Access
U = Use/Direction
R = Risk

Use/Direction:
I = Inform
B = Bind
T = Transform
R = Record

Risk:
R0 = public / low sensitivity
R1 = internal research
R2 = private / sensitive / PII
R3 = legal / financial / formal-consequence / high reputational risk
R4 = life-critical / medical / safety-critical

---

## SEMANTIC VECTOR

G = Authority/Ground
M = Mechanism/Action
E = Entropy/Disorder in the artifact itself
S = Identity/Self
T = Time/Sequence
K = Knowledge/Info
R = Relation/Bond
Q = Experience/Felt
F = Faith/Trust
C = Coherence/Unity

Score:
0 = absent / not dominant
3 = dominant

Rules:
- Score the artifact, not merely its topic.
- E=3 only if the artifact itself is noisy, corrupted, fragmented, contradictory, redacted, ambiguous, or structurally disordered.
- C=3 only if explicit synthesis/integration/unification is the artifact's dominant function.
- Pair 1 is an anchor, not the whole meaning.
- The full vector preserves semantic density.

Tie-break order:
E -> C -> G -> K -> M -> T -> R -> F -> S -> Q

Hash construction:
Rank variables by score, apply tie-break order, then pair strongest with weakest inward:
[#1·#10] [#2·#9] [#3·#8] [#4·#7] [#5·#6]

---

## OUTPUT EXACTLY

1. FILING_DECODE
Decode D, N, V, A, U, R.

2. DOMINANT_VARIABLES
List variables scored 3 and explain what kind of artifact they imply.

3. ABSENT_VARIABLES
List variables scored 0 and explain what is not dominant.

4. HASH_VERIFICATION
Show dominant ranking, absent ranking, full ranking, and whether the hash is valid.

5. MINIMAL_RECONSTRUCTION
One paragraph describing what kind of document/artifact this likely is.

6. WHAT_THIS_DOES_NOT_PROVE
State what cannot be inferred from the address.

7. REVIEW_FLAGS
List any variables that are likely ambiguous.

8. CONFIDENCE
Give 0-100 confidence for structural decode.
```
