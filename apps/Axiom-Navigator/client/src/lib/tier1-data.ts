export interface Tier1Category {
  id: string;
  name: string;
  range: string;
  count: number;
  description: string;
  status: "complete" | "in-progress" | "draft";
  color: string;
}

export interface AxiomDefinition {
  id: string;
  tier: string;
  category: string;
  name: string;
  status: "complete" | "template";
  type: "Primitive" | "Derived" | "Empirical" | "Theological" | "Stance" | "Constraint";
  content?: {
    formal_statement: string;
    description: string;
    analogy: string;
    proof?: string;
    question?: string;
    objections?: { objection: string; response: string }[];
    dependencies?: string[];
  };
}

export const TIER_1_CATEGORIES: Tier1Category[] = [
  {
    id: "primordial",
    name: "Tier 0: Primordial",
    range: "AX-001 to AX-004",
    count: 4,
    description: "The absolute foundational primitives of existence.",
    status: "complete",
    color: "bg-emerald-500"
  },
  {
    id: "ontological",
    name: "Tier 1: Ontological Categories",
    range: "AX-005 to AX-017",
    count: 13,
    description: "Information, Form, Actuality, and Agency categories.",
    status: "in-progress",
    color: "bg-amber-500"
  },
  {
    id: "divine",
    name: "Tier 2: Divine Foundation",
    range: "AX-018 to AX-062",
    count: 45,
    description: "Trinity structure, Creation, Providence, and Divine Attributes.",
    status: "draft",
    color: "bg-purple-500"
  },
  {
    id: "spiritual",
    name: "Tier 3: Spiritual Realm",
    range: "AX-063 to AX-077",
    count: 15,
    description: "Angels, Demons, and spiritual dynamics.",
    status: "draft",
    color: "bg-blue-500"
  },
  {
    id: "human",
    name: "Tier 4: Human Nature",
    range: "AX-078 to AX-112",
    count: 35,
    description: "Consciousness, Soul/Spirit, Body, and human dynamics.",
    status: "draft",
    color: "bg-rose-500"
  },
  {
    id: "material",
    name: "Tier 5: Material Realm",
    range: "AX-113 to AX-122",
    count: 10,
    description: "Spacetime and Matter/Energy.",
    status: "draft",
    color: "bg-slate-500"
  },
  {
    id: "relational",
    name: "Tier 6: Relational Dynamics",
    range: "AX-123 to AX-137",
    count: 15,
    description: "Sin, Grace, Faith, and Redemption.",
    status: "draft",
    color: "bg-orange-500"
  },
  {
    id: "universal-laws",
    name: "Tier A: Universal Laws",
    range: "AX-138 to AX-147",
    count: 10,
    description: "The Ten Laws - Core dynamics of the system.",
    status: "draft",
    color: "bg-red-600"
  },
  {
    id: "master-equation",
    name: "Tier B: Master Equation",
    range: "AX-148 to AX-160",
    count: 13,
    description: "Defining the Master Equation structure and components.",
    status: "draft",
    color: "bg-indigo-600"
  },
  {
    id: "eschatology",
    name: "Tier 7: Eschatology",
    range: "AX-161 to AX-175",
    count: 15,
    description: "Omega Point, Resurrection, Judgment, and Final State.",
    status: "draft",
    color: "bg-teal-500"
  },
  {
    id: "falsification",
    name: "Tier 8: Falsification",
    range: "AX-176 to AX-188",
    count: 13,
    description: "Testability, Predictions, and Falsification protocols.",
    status: "draft",
    color: "bg-cyan-600"
  }
];

export const FULL_AXIOMS: AxiomDefinition[] = [
  // --- TIER 0: PRIMORDIAL ---
  {
    id: "AX-001",
    tier: "primordial",
    category: "Primitive",
    name: "Existence",
    status: "complete",
    type: "Primitive",
    content: {
      formal_statement: "Something exists rather than nothing. ∃x (x exists)",
      description: "Before we can talk about anything—God, the universe, math, even ourselves—we have to start with the most basic fact: something is here. You can't argue against this because arguing requires you to exist.",
      analogy: "It's like trying to prove you don't exist by writing a note that says 'I don't exist.' The note proves you wrong just by existing.",
      question: "Why is there something rather than nothing?",
      objections: [
        { objection: "This is trivially true", response: "Correct. Trivial truths are the strongest foundations. All non-trivial truths rest on trivial ones." },
        { objection: "Existence is a brute fact", response: "Agreed. That's what Primitive means. Existence is the terminus of explanation." }
      ]
    }
  },
  {
    id: "AX-002",
    tier: "primordial",
    category: "Primitive",
    name: "Distinction",
    status: "complete",
    type: "Primitive",
    content: {
      formal_statement: "Existence requires distinguishability—differences that make differences. ∀x (∃x → x ≠ ∅)",
      description: "Imagine trying to describe a world where everything is exactly the same. No differences anywhere. That world would be the same as nothing at all. For something to exist, it has to be different from nothing.",
      analogy: "It's like a blank white canvas. If you paint white on white, you haven't painted anything. To create, you need contrast.",
      question: "Can something exist without being distinguishable from nothing?",
      objections: [
        { objection: "What about the quantum vacuum?", response: "The vacuum has energy, fluctuations, and structure. It is distinguished from true nothing." },
        { objection: "Distinction requires an observer", response: "No. Distinction is ontological (in reality) before it is epistemological (in the mind)." }
      ],
      dependencies: ["AX-001"]
    }
  },
  {
    id: "AX-003",
    tier: "primordial",
    category: "Primitive",
    name: "Information Primacy",
    status: "complete",
    type: "Primitive",
    content: {
      formal_statement: "Distinguishability IS information; therefore information is ontologically primitive. I ≡ Distinguishability",
      description: "At the deepest level, reality isn't 'stuff'—it's data. Atoms are made of quantum fields, which are defined by information. The universe is more like a computer program than a machine.",
      analogy: "Think of a video game. The characters aren't made of physical atoms—they're made of code. Matter is what information 'looks like' when you zoom out.",
      question: "Is information just a description of matter, or is matter made of information?",
      objections: [
        { objection: "Information requires a mind", response: "That's meaning, not information. Information is distinction, which exists independently of observers." },
        { objection: "Matter is fundamental", response: "Physics shows matter emerges from information (holographic principle, landauer's principle)." }
      ],
      dependencies: ["AX-001", "AX-002"]
    }
  },
  {
    id: "AX-004",
    tier: "primordial",
    category: "Primitive",
    name: "Intelligibility",
    status: "complete",
    type: "Primitive",
    content: {
      formal_statement: "Reality is in principle intelligible—it can be understood, modeled, and predicted. ∀x (∃x → ∃M(x))",
      description: "Imagine if the universe were completely random. You couldn't learn anything. But our universe follows rules. Intelligibility means the universe makes sense—it is readable.",
      analogy: "It's the difference between a book written in a language you can learn versus random scribbles. The universe is a book written in mathematics.",
      question: "Is the universe fundamentally rational or chaotic?",
      objections: [
        { objection: "Quantum mechanics is random", response: "Randomness follows probability laws. It is mathematically intelligible." },
        { objection: "Chaos is unpredictable", response: "Unpredictable ≠ unintelligible. Chaotic systems follow deterministic rules we can model." }
      ],
      dependencies: ["AX-003"]
    }
  },

  // --- TIER 1: ONTOLOGICAL ---
  { id: "AX-005", tier: "ontological", category: "Information", name: "Substrate Requirement", status: "template", type: "Primitive" },
  { id: "AX-006", tier: "ontological", category: "Information", name: "Self-Grounding", status: "template", type: "Stance" },
  { id: "AX-007", tier: "ontological", category: "Information", name: "Information Conservation", status: "template", type: "Constraint" },
  { id: "AX-008", tier: "ontological", category: "Form", name: "Order Requirement", status: "template", type: "Primitive" },
  { id: "AX-009", tier: "ontological", category: "Form", name: "Coherence Measure", status: "template", type: "Derived" },
  { id: "AX-010", tier: "ontological", category: "Form", name: "Parsimony", status: "template", type: "Constraint" },
  { id: "AX-011", tier: "ontological", category: "Actuality", name: "Potentiality", status: "template", type: "Primitive" },
  { id: "AX-012", tier: "ontological", category: "Actuality", name: "Actualization", status: "template", type: "Primitive" },
  { id: "AX-013", tier: "ontological", category: "Actuality", name: "Irreducibility", status: "template", type: "Stance" },
  { id: "AX-014", tier: "ontological", category: "Agency", name: "Causal Power", status: "template", type: "Primitive" },
  { id: "AX-015", tier: "ontological", category: "Agency", name: "Agency Requires Selection", status: "template", type: "Derived" },
  { id: "AX-016", tier: "ontological", category: "Agency", name: "Agency Affects Coherence", status: "template", type: "Derived" },
  { id: "AX-017", tier: "ontological", category: "Agency", name: "Moral Realism", status: "template", type: "Stance" },

  // --- TIER 2: DIVINE ---
  // (Placeholder for AX-018 to AX-062)
  { id: "AX-018", tier: "divine", category: "Trinity", name: "Divine Unity", status: "template", type: "Theological" },
  { id: "AX-026", tier: "divine", category: "Attribute", name: "Aseity", status: "template", type: "Theological" },
  { id: "AX-042", tier: "divine", category: "Creation", name: "Creatio Ex Nihilo", status: "template", type: "Theological" },
  { id: "AX-062", tier: "divine", category: "Providence", name: "Divine Sovereignty", status: "template", type: "Theological" },

  // --- TIER 3: SPIRITUAL ---
  // (Placeholder for AX-063 to AX-077)
  { id: "AX-063", tier: "spiritual", category: "Beings", name: "Angelic Existence", status: "template", type: "Theological" },
  { id: "AX-070", tier: "spiritual", category: "Conflict", name: "Spiritual Warfare", status: "template", type: "Theological" },

  // --- TIER 4: HUMAN ---
  { id: "AX-078", tier: "human", category: "Consciousness", name: "Consciousness Substrate", status: "template", type: "Primitive" },
  { id: "AX-079", tier: "human", category: "Consciousness", name: "Observer Required", status: "template", type: "Primitive" },
  { id: "AX-080", tier: "human", category: "Soul", name: "Soul as Information Structure", status: "template", type: "Derived" },
  { id: "AX-095", tier: "human", category: "Body", name: "Somatic Integration", status: "template", type: "Empirical" },

  // --- TIER 5: MATERIAL ---
  { id: "AX-113", tier: "material", category: "Spacetime", name: "Spacetime Emergence", status: "template", type: "Derived" },
  { id: "AX-115", tier: "material", category: "Matter", name: "Mass-Information Equivalence", status: "template", type: "Empirical" },

  // --- TIER 6: RELATIONAL ---
  { id: "AX-123", tier: "relational", category: "Sin", name: "Sin as Decoherence", status: "template", type: "Derived" },
  { id: "AX-124", tier: "relational", category: "Grace", name: "Entropy Opposition", status: "template", type: "Derived" },
  { id: "AX-128", tier: "relational", category: "Grace", name: "Grace Priority", status: "template", type: "Theological" },

  // --- TIER A: UNIVERSAL LAWS ---
  { id: "AX-138", tier: "universal-laws", category: "Laws", name: "Law of Coherence", status: "template", type: "Derived" },
  { id: "AX-139", tier: "universal-laws", category: "Laws", name: "Law of Conservation", status: "template", type: "Derived" },
  { id: "AX-140", tier: "universal-laws", category: "Laws", name: "Law of Amplification", status: "template", type: "Derived" },
  { id: "AX-141", tier: "universal-laws", category: "Laws", name: "Law of Observer Influence", status: "template", type: "Derived" },
  { id: "AX-142", tier: "universal-laws", category: "Laws", name: "Law of Sign", status: "template", type: "Derived" },
  { id: "AX-143", tier: "universal-laws", category: "Laws", name: "Law of Binding", status: "template", type: "Derived" },
  { id: "AX-144", tier: "universal-laws", category: "Laws", name: "Law of Resurrection", status: "template", type: "Derived" },
  { id: "AX-145", tier: "universal-laws", category: "Laws", name: "Law of Eschatology", status: "template", type: "Derived" },
  { id: "AX-146", tier: "universal-laws", category: "Laws", name: "Law of Judgment", status: "template", type: "Derived" },
  { id: "AX-147", tier: "universal-laws", category: "Laws", name: "Law of Unity", status: "template", type: "Derived" },

  // --- TIER B: MASTER EQUATION ---
  { id: "AX-148", tier: "master-equation", category: "Equation", name: "Master Equation Form", status: "template", type: "Constraint" },
  { id: "AX-150", tier: "master-equation", category: "Equation", name: "Grace Term", status: "template", type: "Constraint" },

  // --- TIER 7: ESCHATOLOGY ---
  { id: "AX-161", tier: "eschatology", category: "Final State", name: "Omega Point", status: "template", type: "Stance" },
  { id: "AX-162", tier: "eschatology", category: "Final State", name: "Resurrection of the Body", status: "template", type: "Theological" },
  { id: "AX-163", tier: "eschatology", category: "Judgment", name: "Final Judgment", status: "template", type: "Theological" },

  // --- TIER 8: FALSIFICATION ---
  { id: "AX-176", tier: "falsification", category: "Testing", name: "Falsifiability Requirement", status: "template", type: "Constraint" },
  { id: "AX-177", tier: "falsification", category: "Testing", name: "Testability", status: "template", type: "Constraint" },
  { id: "AX-178", tier: "falsification", category: "Testing", name: "External Consistency", status: "template", type: "Constraint" },
  { id: "AX-188", tier: "falsification", category: "Protocol", name: "Falsification Axiom 188", status: "template", type: "Constraint" }
];

export const SAMPLE_AXIOMS = FULL_AXIOMS; // Alias for backward compatibility
