import { LIBRARY } from './loops.js';
import type { ArgumentBlock, BlockOrderValidation, ClaimGrade, CoverageAudit, Loop, LoopLibrary, ObligationId, Suggestion } from './types.js';

const GRADE_RANK: Record<ClaimGrade, number> = {
  unsupported: 0,
  speculative: 1,
  probable: 2,
  established: 3,
};

export function loadLoops(): LoopLibrary {
  const ids = new Set<string>();
  for (const loop of LIBRARY.loops) {
    if (ids.has(loop.id)) {
      throw new Error(`Duplicate loop id: ${loop.id}`);
    }
    ids.add(loop.id);
  }
  return LIBRARY;
}

export function validateBlockOrder(blocks: ArgumentBlock[]): BlockOrderValidation {
  const ids = new Set(blocks.map(b => b.id));
  const missing: string[] = [];
  const misordered: Array<{ block: string; mustFollow: string }> = [];

  blocks.forEach((block, index) => {
    for (const dep of block.dependsOn ?? []) {
      if (!ids.has(dep)) {
        missing.push(dep);
      } else {
        const depIndex = blocks.findIndex(b => b.id === dep);
        if (depIndex >= index) {
          misordered.push({ block: block.id, mustFollow: dep });
        }
      }
    }
  });

  // cycle detection via DFS
  const cycles: string[][] = [];
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const stack: string[] = [];
  const deps: Record<string, string[]> = Object.fromEntries(blocks.map(b => [b.id, b.dependsOn ?? []]));

  function visit(id: string) {
    if (visiting.has(id)) {
      const cycleStart = stack.indexOf(id);
      cycles.push(stack.slice(cycleStart).concat(id));
      return;
    }
    if (visited.has(id)) return;
    visiting.add(id);
    stack.push(id);
    for (const dep of deps[id] ?? []) {
      if (deps[dep]) visit(dep);
    }
    stack.pop();
    visiting.delete(id);
    visited.add(id);
  }
  for (const b of blocks) visit(b.id);

  return {
    ok: missing.length === 0 && misordered.length === 0 && cycles.length === 0,
    missing: [...new Set(missing)],
    misordered,
    cycles,
  };
}

export function auditBlock(block: ArgumentBlock): CoverageAudit {
  const complete: ObligationId[] = [];
  const missing: ObligationId[] = [];
  const skipped: ObligationId[] = [];

  for (const obligation of LIBRARY.obligations) {
    const status = block.obligations[obligation] ?? 'pending';
    if (status === 'complete') {
      complete.push(obligation);
    } else if (status === 'na') {
      skipped.push(obligation);
    } else {
      missing.push(obligation);
    }
  }

  return {
    blockId: block.id,
    complete,
    missing,
    skipped,
    ok: missing.length === 0,
  };
}

export function suggestLoops(
  block: ArgumentBlock,
  usedIds: Set<string> = new Set(),
): Suggestion[] {
  const text = `${block.claim} ${block.text}`.toLowerCase();
  const audit = auditBlock(block);
  const missingObligations = new Set(audit.missing);

  const scored: Array<{ loop: Loop; reason: string; score: number }> = [];
  const blockGrade = block.claimGrade ?? 'speculative';
  for (const loop of LIBRARY.loops) {
    if (usedIds.has(loop.id)) continue;
    if (loop.family === 'A') continue; // obligations are audited, not suggested
    const loopGrade = loop.claimGrade ?? 'speculative';
    if (GRADE_RANK[blockGrade] < GRADE_RANK[loopGrade]) continue; // loop would oversell the claim

    let score = 0;
    const reasons: string[] = [];

    // keyword matches — required baseline; no signal means no suggestion
    for (const keyword of loop.applicableWhen) {
      if (text.includes(keyword.toLowerCase())) {
        score += 1;
        reasons.push(`matches "${keyword}"`);
      }
    }

    if (score === 0) continue;

    // obligation-based boosts
    if (missingObligations.has('A04') && (loop.id === 'K42' || loop.id === 'P14')) {
      score += 3;
      reasons.push('block needs an objection addressed');
    }
    if (missingObligations.has('A02') && (loop.category === 'evidence' || loop.family === 'S')) {
      score += 2;
      reasons.push('block needs evidence');
    }
    if (missingObligations.has('A03') && (loop.category === 'structure' || loop.category === 'turn')) {
      score += 2;
      reasons.push('block needs reasoning connector');
    }

    if (score > 0) {
      scored.push({
        loop,
        reason: reasons.join('; ') || 'general fit',
        score,
      });
    }
  }

  // apply per-family caps
  const familyCounts: Record<string, number> = {};
  const result: Suggestion[] = [];
  scored
    .sort((a, b) => b.score - a.score)
    .forEach(({ loop, reason }) => {
      const cap = loop.maxPerArticle ?? Infinity;
      familyCounts[loop.family] = (familyCounts[loop.family] ?? 0) + 1;
      if (familyCounts[loop.family] <= cap) {
        result.push({ ...loop, reason });
      }
    });

  return result;
}
