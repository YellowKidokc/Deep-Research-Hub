import { describe, it } from 'node:test';
import assert from 'node:assert';
import { auditBlock, suggestLoops, validateBlockOrder } from './engine.js';

describe('auditBlock', () => {
  it('flags missing objection', () => {
    const audit = auditBlock({
      id: 'B1',
      claim: 'X',
      text: 'X is true because Y.',
      loops: [],
      obligations: {
        A01: 'complete',
        A02: 'complete',
        A03: 'complete',
        A04: 'pending',
        A05: 'pending',
      },
    });
    assert.strictEqual(audit.missing[0], 'A04');
    assert.strictEqual(audit.ok, false);
  });

  it('passes when obligations are complete or explicitly skipped', () => {
    const audit = auditBlock({
      id: 'B2',
      claim: 'X',
      text: 'X is true because Y, despite objection Z.',
      loops: [],
      obligations: {
        A01: 'complete',
        A02: 'complete',
        A03: 'complete',
        A04: 'complete',
        A05: 'na',
      },
    });
    assert.strictEqual(audit.missing.length, 0);
    assert.strictEqual(audit.skipped[0], 'A05');
    assert.strictEqual(audit.ok, true);
  });
});

describe('suggestLoops', () => {
  it('does not suggest a used loop', () => {
    const used = new Set(['K01']);
    const suggestions = suggestLoops(
      {
        id: 'B1',
        claim: 'Morality is not opinion',
        text: '...',
        loops: [],
        obligations: {},
      },
      used,
    );
    assert.ok(!suggestions.some(s => s.id === 'K01'));
  });

  it('returns empty when the block gives no signal', () => {
    const suggestions = suggestLoops({
      id: 'B2',
      claim: '',
      text: '',
      loops: [],
      obligations: {},
    });
    assert.strictEqual(suggestions.length, 0);
  });

  it('excludes loops that would oversell a speculative claim', () => {
    const suggestions = suggestLoops({
      id: 'B4',
      claim: 'Maybe consciousness is quantum',
      text: 'compress truth bomb one sentence',
      loops: [],
      obligations: {},
      claimGrade: 'speculative',
    });
    assert.ok(!suggestions.some(s => s.id === 'C01'), 'truth bomb should not be suggested for speculative claim');
    assert.ok(!suggestions.some(s => s.id === 'K12'), 'binary framing should not be suggested for speculative claim');
  });

  it('allows strong loops when the claim grade is high enough', () => {
    const suggestions = suggestLoops({
      id: 'B5',
      claim: 'Either moral realism is true or nihilism follows',
      text: 'compress truth bomb one sentence',
      loops: [],
      obligations: {},
      claimGrade: 'established',
    });
    assert.ok(suggestions.some(s => s.id === 'C01'), 'truth bomb should be available for established claim');
  });

  it('boosts objection-handling loops when A04 is missing', () => {
    const suggestions = suggestLoops({
      id: 'B3',
      claim: 'Free will is compatible with determinism',
      text: 'objection counter skeptic however',
      loops: [],
      obligations: { A04: 'pending' },
    });
    const top = suggestions[0];
    assert.ok(top, 'expected at least one suggestion');
    assert.ok(
      top.id === 'K42' || top.id === 'P14',
      `expected objection-handling loop, got ${top?.id}`,
    );
  });
});

describe('validateBlockOrder', () => {
  it('flags a block that appears before its dependency', () => {
    const result = validateBlockOrder([
      { id: 'B2', claim: 'payoff', text: '...', dependsOn: ['B1'], loops: [], obligations: {} },
      { id: 'B1', claim: 'setup', text: '...', loops: [], obligations: {} },
    ]);
    assert.strictEqual(result.ok, false);
    assert.strictEqual(result.misordered[0].block, 'B2');
    assert.strictEqual(result.misordered[0].mustFollow, 'B1');
  });

  it('flags a missing dependency', () => {
    const result = validateBlockOrder([
      { id: 'B1', claim: 'x', text: '...', dependsOn: ['B0'], loops: [], obligations: {} },
    ]);
    assert.strictEqual(result.ok, false);
    assert.ok(result.missing.includes('B0'));
  });

  it('flags a dependency cycle', () => {
    const result = validateBlockOrder([
      { id: 'B1', claim: 'x', text: '...', dependsOn: ['B2'], loops: [], obligations: {} },
      { id: 'B2', claim: 'y', text: '...', dependsOn: ['B1'], loops: [], obligations: {} },
    ]);
    assert.strictEqual(result.ok, false);
    assert.strictEqual(result.cycles.length, 1);
  });

  it('passes for a well-ordered chain', () => {
    const result = validateBlockOrder([
      { id: 'B1', claim: 'setup', text: '...', setsUp: ['B2'], loops: [], obligations: {} },
      { id: 'B2', claim: 'payoff', text: '...', dependsOn: ['B1'], loops: [], obligations: {} },
    ]);
    assert.strictEqual(result.ok, true);
  });
});
