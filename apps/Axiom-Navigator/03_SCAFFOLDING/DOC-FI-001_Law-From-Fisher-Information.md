---
id: SC-0921
phase: scaffolding
role: node
depends_on: []
authority: human
status: draft
---

# DOC-FI-001: Physical Law from Fisher Information

## The Apparent Circularity

**Claim:** "Information and physical law are mutually dependent - laws need information to be meaningful, but information is instantiated through physical law. This is circular."

## Why This Is Wrong

### The Variational Principle Resolution

Physical law emerges from information via **extremization**, not mutual grounding.

The Extreme Physical Information (EPI) principle:

```
δ(I - Q) = 0
```

Where:
- I = Fisher Information (what we CAN know)
- Q = Bound Information (what IS there)
- δ = Variational operator

**Key insight:** This is a ONE-WAY derivation:
1. Start with information-theoretic constraints
2. Extremize the functional
3. Physical laws FALL OUT as Euler-Lagrange equations

The Schrödinger equation, Maxwell's equations, Dirac equation, Klein-Gordon equation - ALL derivable from EPI.

### No Mutual Explanation Required

| Direction | Type | Status |
|-----------|------|--------|
| Information → Law | Derivation (variational) | ✅ Valid |
| Law → Information | Instantiation (physical) | ✅ Valid |
| Information ↔ Law (mutual grounding) | Circular | ❌ NOT CLAIMED |

We never claim laws GROUND information. We claim:
- Information is primitive (A1.3)
- Laws are DERIVED from information constraints
- Physical systems INSTANTIATE information

These are different arrows with different meanings.

### The Fixed Point Argument

Laws can be understood as **fixed points** of measurement dynamics:

```
L* = argmin_L [ I(L) - Q(L) ]
```

A fixed point is not circular - it's a stable solution to a dynamical process.

## Formal Derivation Sketch

### Step 1: Fisher Information Definition
For a parameter θ estimated from data x:

```
I(θ) = E[(∂/∂θ log p(x|θ))²]
```

### Step 2: EPI Principle
Nature minimizes the gap between Fisher information and bound information:

```
I - Q → extremum
```

### Step 3: Euler-Lagrange Equations
Applying calculus of variations yields:

```
∂L/∂q - d/dt(∂L/∂q̇) = 0
```

This IS the structure of physical law.

### Step 4: Specific Laws
- Q = kinetic bound → Schrödinger equation
- Q = electromagnetic bound → Maxwell's equations
- Q = relativistic bound → Klein-Gordon, Dirac

## Defeat Condition

This resolution fails if:
1. A physical law is found that CANNOT be derived from EPI
2. Information requires physical law for its DEFINITION (not just instantiation)
3. The variational principle is shown to be circular

## References

- Frieden, B.R. (1998). Physics from Fisher Information
- Frieden, B.R. (2004). Science from Fisher Information
- [[A1.3-Information-Primacy]]
- [[LN1.2-It-From-Bit]]

## Cross-Links

- [[RECURSIVE_ONTOLOGY_MAP]] - LOOP-1
- [[LOAD_BEARING_VARIABLES]] - Information Field (H)
