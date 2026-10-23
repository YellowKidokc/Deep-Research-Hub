import { describe, it } from 'node:test';
import assert from 'node:assert';
import { ArticleSession } from './session.js';

describe('ArticleSession', () => {
  it('crosses out a loop once used anywhere', () => {
    const session = new ArticleSession();
    session.addBlock({
      id: 'B1',
      claim: '...',
      text: '...',
      loops: [],
      obligations: {},
    });
    session.useLoop('B1', 'K01');
    const suggestions = session.suggestFor('B1');
    assert.ok(!suggestions.some(s => s.id === 'K01'));
  });

  it('tracks used loop IDs globally', () => {
    const session = new ArticleSession();
    session.addBlock({
      id: 'B1',
      claim: '...',
      text: '...',
      loops: [],
      obligations: {},
    });
    session.useLoop('B1', 'K10');
    assert.ok(session.usedIds().has('K10'));
  });

  it('does not suggest dismissed loops', () => {
    const session = new ArticleSession();
    session.addBlock({
      id: 'B1',
      claim: '...',
      text: '...',
      loops: [],
      obligations: {},
    });
    session.dismissLoop('B1', 'K01');
    const suggestions = session.suggestFor('B1');
    assert.ok(!suggestions.some(s => s.id === 'K01'));
  });
});
