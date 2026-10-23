/**
 * Word-level diff for the Story tab's variant cycler: shows how a rewrite
 * variant differs from the span's current text. Tokenizes on whitespace,
 * runs an LCS over the word tokens, then merges consecutive same-type runs.
 * Pure function, no dependencies.
 */

export interface WordDiffPart {
  type: 'same' | 'add' | 'del';
  text: string;
}

export function wordDiff(oldText: string, newText: string): WordDiffPart[] {
  const a = oldText.split(/\s+/).filter(Boolean);
  const b = newText.split(/\s+/).filter(Boolean);

  // LCS table; dp[i][j] = length of the longest common subsequence of
  // a.slice(i) and b.slice(j).
  const dp: number[][] = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }

  const parts: WordDiffPart[] = [];
  let i = 0;
  let j = 0;
  const push = (type: WordDiffPart['type'], word: string) => {
    const last = parts[parts.length - 1];
    if (last && last.type === type) last.text += ' ' + word;
    else parts.push({ type, text: word });
  };
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { push('same', a[i]); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { push('del', a[i]); i++; }
    else { push('add', b[j]); j++; }
  }
  while (i < a.length) { push('del', a[i]); i++; }
  while (j < b.length) { push('add', b[j]); j++; }
  return parts;
}
