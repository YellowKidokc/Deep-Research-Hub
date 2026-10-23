import { describe, it } from 'node:test';
import assert from 'node:assert';
import { loadLoops } from './engine.js';

describe('loadLoops', () => {
  it('loads the Kait backbone and all required families', () => {
    const lib = loadLoops();
    assert.ok(lib.loops.some(l => l.id === 'K01'), 'K01 missing');
    assert.ok(lib.loops.some(l => l.family === 'A'), 'argument family missing');
    assert.ok(lib.loops.some(l => l.family === 'S'), 'story family missing');
    assert.ok(lib.loops.some(l => l.family === 'H'), 'hook family missing');
    assert.ok(lib.loops.some(l => l.family === 'C'), 'compression family missing');
  });
});
