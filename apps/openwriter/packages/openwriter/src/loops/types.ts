export type LoopFamily =
  | 'A' // Argument obligation
  | 'K' // Kait move
  | 'P' // Psychology
  | 'S' // Story
  | 'V' // Visual / presentation
  | 'H' // Hook / opening
  | 'C'; // Compression

export type ObligationId = `A${number}`;

export interface Loop {
  id: string;
  name: string;
  family: LoopFamily;
  category: string;
  purpose: string;
  applicableWhen: string[];
  scaffold?: string;
  autoInsert: false;
  maxPerArticle?: number;
  /** Minimum claim grade this loop can ethically support. Default: speculative. */
  claimGrade?: ClaimGrade;
}

export interface LoopLibrary {
  version: string;
  loops: Loop[];
  obligations: ObligationId[];
}

export type ClaimGrade = 'established' | 'probable' | 'speculative' | 'unsupported';

export type ObligationStatus = 'pending' | 'complete' | 'na';

export interface BlockLoopUsage {
  id: string;
  role: 'primary' | 'support' | 'dismissed';
  status: 'used' | 'suggested' | 'dismissed';
}

export interface ArgumentBlock {
  id: string;
  claim: string;
  text: string;
  claimGrade?: ClaimGrade;
  loops: BlockLoopUsage[];
  obligations: Record<ObligationId, ObligationStatus>;
  /** IDs of blocks this block depends on; those must appear earlier in the article. */
  dependsOn?: string[];
  /** IDs of blocks this block sets up for later payoff. */
  setsUp?: string[];
}

export interface BlockOrderValidation {
  ok: boolean;
  /** Blocks referenced by dependsOn that do not exist. */
  missing: string[];
  /** Cycles in the dependency graph. */
  cycles: string[][];
  /** Blocks that appear before their dependencies in the supplied order. */
  misordered: Array<{ block: string; mustFollow: string }>;
}

export interface CoverageAudit {
  blockId: string;
  complete: ObligationId[];
  missing: ObligationId[];
  skipped: ObligationId[];
  ok: boolean;
}

export interface Suggestion extends Loop {
  reason: string;
}
