export type Phase = 
  | "01_Ontology" 
  | "02_Substrate" 
  | "03_Coherence" 
  | "04_Compression" 
  | "05_Observer" 
  | "06_Collapse" 
  | "07_Boundary" 
  | "08_Syzygy" 
  | "09_Grace" 
  | "10_Soul" 
  | "11_Morality" 
  | "12_Destiny" 
  | "13_Unification";

export const PHASES: Phase[] = [
  "01_Ontology", 
  "02_Substrate", 
  "03_Coherence", 
  "04_Compression", 
  "05_Observer", 
  "06_Collapse", 
  "07_Boundary", 
  "08_Syzygy", 
  "09_Grace", 
  "10_Soul", 
  "11_Morality", 
  "12_Destiny", 
  "13_Unification"
];

export type Role = "Axiom" | "Theorem" | "Definition" | "Lemma" | "Equation" | "Property" | "Corollary";
export type Status = "Canonical" | "Derived" | "Empirical" | "Theological";
export type Authority = "Universal" | "Contextual" | "Divine";

export interface Axiom {
  id: string; // ID like A1.1
  uuid: string;
  title: string;
  phase: Phase;
  role: Role;
  authority: Authority;
  status: Status;
  tier: number;
  collapse_radius: string; 
  depends_on: string[];
  content: string;
  justification?: string;
  collapse_test?: string;
  mathematical_form?: string;
  tags: string[];
  falsification?: string;
}

export const AXIOMS: Axiom[] = [
  // STAGE 1: ONTOLOGICAL FOUNDATION
  {
    id: "A1.1",
    uuid: "4d1152fe-1249-41f9-bbfa-a003e30baf7b",
    title: "Existence",
    phase: "01_Ontology",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 0,
    collapse_radius: "Total Reality",
    depends_on: [],
    content: "Something exists rather than nothing.",
    justification: "The negation is self-refuting—to deny existence requires an existent denier.",
    collapse_test: "If no existence, no discourse is possible. System collapses.",
    falsification: "Discovery of absolute non-existence (logical impossibility).",
    mathematical_form: "∃x (existence is not empty)",
    tags: ["existence", "primordial", "root"]
  },
  {
    id: "A1.2",
    uuid: "ae6ad6cd-9016-49f2-b246-03a2201a3221",
    title: "Distinction",
    phase: "01_Ontology",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 0,
    collapse_radius: "Information",
    depends_on: ["A1.1"],
    content: "Existence requires distinguishability—differences that make differences.",
    justification: "Without distinction, existence collapses into undifferentiated void—indistinguishable from nothing.",
    falsification: "Existence of a featureless, undifferentiated monad that supports information.",
    mathematical_form: "∃x,y : x ≠ y",
    tags: ["distinction", "differentiation"]
  },
  {
    id: "A1.3",
    uuid: "3be01ba9-330f-4038-957e-3b03bf294fc1",
    title: "Information Primacy",
    phase: "01_Ontology",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 0,
    collapse_radius: "Ontology",
    depends_on: ["A1.2"],
    content: "Distinguishability IS information; therefore information is ontologically primitive.",
    justification: "Matter and energy reduce to informational patterns; information cannot reduce further.",
    falsification: "Demonstration that physics works without information concept (e.g. pure materialism).",
    mathematical_form: "H(X) > 0",
    tags: ["information", "primacy", "it-from-bit"]
  },

  // STAGE 2: INFORMATIONAL SUBSTRATE
  {
    id: "A2.1",
    uuid: "ae1a16c6-078b-4883-980b-f447aa26a3e0",
    title: "Substrate Requirement",
    phase: "02_Substrate",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 1,
    collapse_radius: "Reality",
    depends_on: ["A1.3"],
    content: "Information requires a substrate for instantiation.",
    justification: "Abstract patterns require medium to exist in reality.",
    falsification: "Observation of 'naked' information existing without a medium.",
    tags: ["substrate", "instantiation"]
  },
  {
    id: "D2.1",
    uuid: "1b23c1dc-0025-4dfe-9b30-c2bd15433938",
    title: "Logos Field",
    phase: "02_Substrate",
    role: "Definition",
    authority: "Universal",
    status: "Canonical",
    tier: 1,
    collapse_radius: "Spacetime",
    depends_on: ["A2.1"],
    content: "The Logos Field χ(x,t) is the self-grounding informational substrate of reality. It is ontologically prior to spacetime and carries semantic content.",
    mathematical_form: "χ = ∫(G · K)dΩ",
    tags: ["logos", "field-theory", "geometry"]
  },

  // STAGE 3: COHERENCE FUNCTIONAL
  {
    id: "A3.1",
    uuid: "df8bd1d3-eca3-4b37-a27e-b15e03193548",
    title: "Order Requirement",
    phase: "03_Coherence",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 1,
    collapse_radius: "Meaning",
    depends_on: ["D2.1"],
    content: "Information must be organized to be meaningful; random noise carries zero semantic content.",
    falsification: "Generation of semantic meaning from pure random noise (Boltzmann Brains).",
    tags: ["order", "meaning"]
  },
  {
    id: "D3.1",
    uuid: "765a746d-580c-418b-bd22-eeea5e977ded",
    title: "Coherence Measure",
    phase: "03_Coherence",
    role: "Definition",
    authority: "Universal",
    status: "Canonical",
    tier: 1,
    collapse_radius: "Value",
    depends_on: ["A3.1"],
    content: "Coherence C[χ] is the measure of organized information density in the Logos Field.",
    mathematical_form: "C[χ] = ∫d⁴x√(-g)[½g^μν∂_μχ∂_νχ - V(χ)]",
    tags: ["coherence", "measure", "density"]
  },

  // STAGE 4: COMPRESSION THEORY
  {
    id: "A4.1",
    uuid: "f317c705-1b48-40a6-961c-33f2116101e3",
    title: "Parsimony",
    phase: "04_Compression",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 1,
    collapse_radius: "Laws",
    depends_on: ["D3.1"],
    content: "Nature prefers minimal description (Occam's razor as physical principle).",
    mathematical_form: "dK/dt = -αχ(t)",
    tags: ["parsimony", "compression", "occam"]
  },
  {
    id: "T4.1",
    uuid: "5ce76a0b-8f72-49f9-bb48-6cbb23bee044",
    title: "Algorithmic Depth",
    phase: "04_Compression",
    role: "Theorem",
    authority: "Universal",
    status: "Derived",
    tier: 1,
    collapse_radius: "Complexity",
    depends_on: ["A4.1"],
    content: "Physical laws are low-K descriptions generating high-complexity outputs. The universe is a compression algorithm.",
    tags: ["complexity", "laws", "algorithm"]
  },

  // STAGE 5: OBSERVER THEORY
  {
    id: "A5.1",
    uuid: "b095e68f-9184-4e24-a1f9-4dc978735c7d",
    title: "Observation Requirement",
    phase: "05_Observer",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 4,
    collapse_radius: "Actuality",
    depends_on: ["D3.1"],
    content: "Information requires an observer to be instantiated as actual (vs. potential).",
    falsification: "A universe with no observers that still possesses definite properties.",
    tags: ["observer", "actuality"]
  },
  {
    id: "D5.2",
    uuid: "2b6dd65a-b627-408f-86a6-47b7f0c8a581",
    title: "Integrated Information",
    phase: "05_Observer",
    role: "Definition",
    authority: "Universal",
    status: "Canonical",
    tier: 4,
    collapse_radius: "Consciousness",
    depends_on: ["A5.1"],
    content: "Integrated Information Φ is the measure of observer capacity. The Observer participates in actualizing reality.",
    tags: ["phi", "tononi", "consciousness"]
  },

  // STAGE 6: COLLAPSE
  {
    id: "A6.2",
    uuid: "812d6d7e-1bf8-4546-938a-6cce071f1eef",
    title: "Collapse Dynamics",
    phase: "06_Collapse",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 4,
    collapse_radius: "Quantum State",
    depends_on: ["A5.1"],
    content: "Observation induces transition from superposition to definite eigenstate. The collapse rate γ is proportional to Φ.",
    falsification: "Consciousness-independent collapse demonstrated (e.g. GRW theory proven).",
    mathematical_form: "d|Ψ⟩/dt = -(i/ℏ)Ĥ|Ψ⟩ - γ(χ)P̂|Ψ⟩",
    tags: ["collapse", "quantum", "wavefunction"]
  },

  // STAGE 7: BOUNDARY CONDITIONS
  {
    id: "T7.1",
    uuid: "boundary-conditions-001",
    title: "Necessary Boundaries",
    phase: "07_Boundary",
    role: "Theorem",
    authority: "Universal",
    status: "Canonical",
    tier: 0,
    collapse_radius: "Coherence",
    depends_on: ["A6.2"],
    content: "Eight boundary conditions are jointly necessary for coherent observer physics, including the existence of a Terminal Observer and external Grace.",
    tags: ["boundaries", "constraints", "necessity"]
  },

  // STAGE 8: SYZYGY
  {
    id: "A8.1",
    uuid: "9ce891c6-051b-4cb8-bda9-f2d9ae60395c",
    title: "Binary Distinction",
    phase: "08_Syzygy",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 6,
    collapse_radius: "Orientation",
    depends_on: ["A1.2"],
    content: "Fundamental orientation admits only two values: aligned (+1) or opposed (-1).",
    falsification: "Discovery of a third 'neutral' orientation in fundamental moral thermodynamics.",
    tags: ["binary", "alignment", "orientation"]
  },
  {
    id: "T8.1",
    uuid: "1136c7f5-1597-490b-a5d8-62ef22369062",
    title: "Sign Invariance",
    phase: "08_Syzygy",
    role: "Theorem",
    authority: "Universal",
    status: "Derived",
    tier: 6,
    collapse_radius: "Salvation",
    depends_on: ["A8.1"],
    content: "Self-generated operations cannot change sign. Works-based salvation is mathematically impossible.",
    falsification: "Observation of a closed system spontaneously reversing its own entropy.",
    mathematical_form: "[σ̂, Û] = 0",
    tags: ["sign", "invariance", "soteriology"]
  },

  // STAGE 9: GRACE DYNAMICS
  {
    id: "A9.2",
    uuid: "2738643c-ec09-4158-9663-355358e2b7d7",
    title: "Grace Operator",
    phase: "09_Grace",
    role: "Definition",
    authority: "Divine",
    status: "Theological",
    tier: 6,
    collapse_radius: "Redemption",
    depends_on: ["T8.1"],
    content: "The Grace Operator Ĝ is an external, non-unitary operator capable of flipping sign from -1 to +1.",
    falsification: "Self-generated sign change observed without external input.",
    mathematical_form: "Ĝ = |+1⟩⟨-1| + |+1⟩⟨+1|",
    tags: ["grace", "operator", "non-unitary"]
  },

  // STAGE 10: SOUL FIELD
  {
    id: "D10.1",
    uuid: "f45d197a-0729-4aed-b8e1-d17c331ce2dc",
    title: "Soul Field",
    phase: "10_Soul",
    role: "Definition",
    authority: "Universal",
    status: "Canonical",
    tier: 4,
    collapse_radius: "Identity",
    depends_on: ["D2.1"],
    content: "The Soul Field Ψ_S is a real scalar field carrying individual consciousness. It is effectively massless and conserved.",
    mathematical_form: "(□ + m_S²)Ψ_S = 0",
    tags: ["soul", "field", "immortality"]
  },

  // STAGE 11: MORAL COHERENCE
  {
    id: "A11.2",
    uuid: "de563a93-f590-4ec0-8d1f-bbd9c7e2a2ff",
    title: "Moral Identity",
    phase: "11_Morality",
    role: "Axiom",
    authority: "Universal",
    status: "Canonical",
    tier: 6,
    collapse_radius: "Ethics",
    depends_on: ["D3.1"],
    content: "Moral goodness is identical to coherence maximization; evil is coherence destruction.",
    tags: ["morality", "coherence", "ethics"]
  },

  // STAGE 12: DESTINY EQUATION
  {
    id: "E12.1",
    uuid: "destiny-eq-001",
    title: "Asymptotic Fate",
    phase: "12_Destiny",
    role: "Equation",
    authority: "Universal",
    status: "Canonical",
    tier: 6,
    collapse_radius: "Eternity",
    depends_on: ["A8.1"],
    content: "All trajectories asymptote to either maximal coherence (Heaven) or maximal decoherence (Hell) based on Sign.",
    mathematical_form: "lim(t→∞) Ψ = { Coherent if σ=+1, Decoherent if σ=-1 }",
    tags: ["destiny", "asymptote", "eternity"]
  },

  // STAGE 13: UNIFICATION
  {
    id: "E13.1",
    uuid: "unification-eq-001",
    title: "χ-Mediation",
    phase: "13_Unification",
    role: "Equation",
    authority: "Universal",
    status: "Canonical",
    tier: 5,
    collapse_radius: "Physics",
    depends_on: ["D2.1"],
    content: "Unification of gravity and quantum mechanics occurs through the Logos Field as the common substrate.",
    mathematical_form: "G_μν + Λg_μν = 8πT_μν + κχ_μν",
    tags: ["unification", "gravity", "logos"]
  }
];

export function getAxiom(id: string) {
  return AXIOMS.find(a => a.id === id);
}

export function getAxiomsByPhase(phase: Phase) {
  return AXIOMS.filter(a => a.phase === phase);
}

export function getDownstreamDependencies(id: string) {
  return AXIOMS.filter(a => a.depends_on.includes(id));
}

export function getUpstreamDependencies(id: string) {
  const axiom = getAxiom(id);
  if (!axiom) return [];
  return axiom.depends_on.map(depId => getAxiom(depId)).filter(Boolean) as Axiom[];
}

export function getNextPhase(current: Phase): Phase | null {
  const index = PHASES.indexOf(current);
  if (index === -1 || index === PHASES.length - 1) return null;
  return PHASES[index + 1];
}

export function getPrevPhase(current: Phase): Phase | null {
  const index = PHASES.indexOf(current);
  if (index <= 0) return null;
  return PHASES[index - 1];
}

