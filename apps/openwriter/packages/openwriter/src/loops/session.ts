import { suggestLoops } from './engine.js';
import type { ArgumentBlock, Suggestion } from './types.js';

export class ArticleSession {
  private blocks = new Map<string, ArgumentBlock>();
  private used = new Set<string>();
  private dismissed = new Set<string>();

  addBlock(block: ArgumentBlock): void {
    this.blocks.set(block.id, block);
  }

  getBlock(id: string): ArgumentBlock | undefined {
    return this.blocks.get(id);
  }

  useLoop(blockId: string, loopId: string): void {
    this.used.add(loopId);
    const block = this.blocks.get(blockId);
    if (!block) return;
    const existing = block.loops.find(l => l.id === loopId);
    if (existing) {
      existing.status = 'used';
      existing.role = 'primary';
    } else {
      block.loops.push({ id: loopId, role: 'primary', status: 'used' });
    }
  }

  dismissLoop(blockId: string, loopId: string): void {
    this.dismissed.add(loopId);
    const block = this.blocks.get(blockId);
    if (!block) return;
    const existing = block.loops.find(l => l.id === loopId);
    if (existing) {
      existing.status = 'dismissed';
      existing.role = 'dismissed';
    } else {
      block.loops.push({ id: loopId, role: 'dismissed', status: 'dismissed' });
    }
  }

  suggestFor(blockId: string): Suggestion[] {
    const block = this.blocks.get(blockId);
    if (!block) return [];
    const excluded = new Set([...this.used, ...this.dismissed]);
    return suggestLoops(block, excluded);
  }

  usedIds(): Set<string> {
    return new Set(this.used);
  }
}
