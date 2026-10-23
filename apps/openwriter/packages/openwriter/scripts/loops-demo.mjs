// Demo: 3-block argument article spine using the OpenWriter loops engine.
// Run with: node --import tsx scripts/loops-demo.mjs

const { ArticleSession } = await import('../src/loops/session.js');
const { auditBlock, validateBlockOrder } = await import('../src/loops/engine.js');

const session = new ArticleSession();

// Block 1: opening hook + claim
session.addBlock({
  id: 'intro',
  claim: 'Morality is not mere opinion; it is a real feature of the world.',
  text:
    'Most people act as if some things are truly wrong. That intuition is the starting point. ' +
    'If morality were only opinion, we could no more disagree about cruelty than we disagree about ice cream.',
  claimGrade: 'probable',
  setsUp: ['evidence'],
  loops: [],
  obligations: {
    A01: 'complete',
    A02: 'pending',
    A03: 'pending',
    A04: 'pending',
    A05: 'pending',
  },
});

// Block 2: evidence + reasoning
session.addBlock({
  id: 'evidence',
  claim: 'Across cultures, humans converge on core moral truths.',
  text:
    'Studies in moral psychology find that even infants distinguish helpful from harmful actions. ' +
    'This convergence suggests a shared moral reality, not an arbitrary cultural construct.',
  claimGrade: 'established',
  dependsOn: ['intro'],
  setsUp: ['objection'],
  loops: [],
  obligations: {
    A01: 'complete',
    A02: 'complete',
    A03: 'complete',
    A04: 'pending',
    A05: 'pending',
  },
});

// Block 3: objection + boundary
session.addBlock({
  id: 'objection',
  claim: 'Moral disagreement does not prove moral relativism.',
  text:
    'Skeptics point to cultural disagreement. But disagreement about physics does not make physics relative. ' +
    'The existence of hard cases shows only that morality is complex, not that it is unreal.',
  claimGrade: 'probable',
  dependsOn: ['intro', 'evidence'],
  loops: [],
  obligations: {
    A01: 'complete',
    A02: 'complete',
    A03: 'complete',
    A04: 'complete',
    A05: 'complete',
  },
});

console.log('=== OpenWriter Loops Demo ===\n');

for (const blockId of ['intro', 'evidence', 'objection']) {
  const block = session.getBlock(blockId);
  console.log(`-- Block: ${blockId} --`);
  console.log(`Claim: ${block.claim}`);

  const before = session.suggestFor(blockId);
  console.log(`Suggestions before using loops (${before.length}):`);
  for (const s of before.slice(0, 5)) {
    console.log(`  - ${s.id} ${s.name} (${s.family}): ${s.reason}`);
  }

  // Use the top suggestion as the author's choice
  if (before.length > 0) {
    const chosen = before[0];
    session.useLoop(blockId, chosen.id);
    console.log(`Author used: ${chosen.id} ${chosen.name}`);
  }

  const after = session.suggestFor(blockId);
  console.log(`Suggestions after using loops (${after.length}):`);
  for (const s of after.slice(0, 5)) {
    console.log(`  - ${s.id} ${s.name} (${s.family})`);
  }

  const audit = auditBlock(block);
  console.log(`Audit: ${audit.ok ? 'PASS' : 'NEEDS WORK'} missing=${audit.missing.join(',') || 'none'}`);
  console.log();
}

console.log('Global used loop IDs:', [...session.usedIds()].sort().join(', '));

console.log('\n=== Block order validation ===');
const order = validateBlockOrder([session.getBlock('intro'), session.getBlock('evidence'), session.getBlock('objection')]);
console.log(`Order ${order.ok ? 'VALID' : 'INVALID'}`);
if (order.misordered.length) console.log('Misordered:', order.misordered);
if (order.missing.length) console.log('Missing:', order.missing);
if (order.cycles.length) console.log('Cycles:', order.cycles);

console.log('\n=== Claim-grade guard demo ===');
const speculative = session.suggestFor('intro');
console.log('Intro (probable) suggestions include truth bomb?', speculative.some(s => s.id === 'C01'));
session.getBlock('intro').claimGrade = 'speculative';
const guarded = session.suggestFor('intro');
console.log('Intro (changed to speculative) suggestions include truth bomb?', guarded.some(s => s.id === 'C01'));
console.log('Guard active:', !guarded.some(s => s.id === 'C01'));

// Show a deliberately bad order
console.log('\n=== Deliberately bad order (intro after objection) ===');
const bad = validateBlockOrder([session.getBlock('objection'), session.getBlock('intro'), session.getBlock('evidence')]);
console.log(`Order ${bad.ok ? 'VALID' : 'INVALID'}`, bad.misordered);
