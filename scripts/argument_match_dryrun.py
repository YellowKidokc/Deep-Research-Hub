"""
argument_match_dryrun.py  --  READ-ONLY dry run of "Lane B" (corpus -> debate-map questions).

What it does
  1. Reads the question list from Canon\\DEBATE_MAP\\DEBATE_MAP.md  (lines like:  - `Q-ID` question text)
  2. Maps each Q-ID to its folder under the restacked P00..P10 tree.
  3. Scans text-like files (.md/.txt) in the vault roots, scores each file against every question
     (idf-weighted keyword overlap; filename/first-heading hits count full weight).
  4. Writes a CSV + a short Markdown report. NOTHING is written inside the vault or DEBATE_MAP.

Run:  python -X utf8 argument_match_dryrun.py
"""
import os, re, csv, math, sys, collections, datetime

CANON = r'C:\Users\David\Documents\faiththruphysics.com\Canon\DEBATE_MAP'
VAULT = r'C:\Users\David\Documents\faiththruphysics.com\10_VAULTS\_ Theophysics_Case_for_Christ'
ROOTS = ['01_Tik Tok', '01-Historical-Jesus', '02_PHILOSOPHY_AND_WORLDVIEWS',
         '_first_principles_to_god', '00_CANONICAL', '00_CORE_ARGUMENTS', '01_Proofs-and-Arguments']
OUT = r'D:\FIS_REPORTS\argument-match-dryrun-2026-10-23'

TEXT_EXT = {'.md', '.txt'}
SKIP_DIRS = {'.git', '.obsidian', '.smart-env', '.stversions', '.trash', '.stfolder', '.lokus',
             '.olw', '.claude', '.lake', 'node_modules', '__pycache__'}
MAX_BYTES = 3_000_000
READ_CHARS = 30_000

STOP = set('''the and for are but not you all any can had her was one our out has have his how its may new now
old see two way who did get him let say she too use that this with from they will what when which would
about after again also been before being between both could does doing down each even ever every first
into just like made make many more most much must only other over said same should some still such than
their them then there these those through under very were where while your why does did god's gods does
people'''.split())
GENERIC_NAME = set('clipboard text untitled index readme overview prompt note notes draft copy new'.split())


def stem(w):
    for suf in ('ing', 'ed', 'ly', 'es', 's'):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def toks(text):
    return [stem(w) for w in re.findall(r'[a-z]{3,}', text.lower()) if w not in STOP]


def load_questions():
    qs = {}
    cur = ''
    pat = re.compile(r'^- `(Q-[A-Z0-9\-]+)`\s*(.*)$')
    sec = re.compile(r'^## (S-[A-Z]+)')
    for line in open(os.path.join(CANON, 'DEBATE_MAP.md'), encoding='utf8', errors='ignore'):
        line = line.rstrip('\n')
        m = sec.match(line)
        if m:
            cur = m.group(1)
        m = pat.match(line)
        if m:
            qid, text = m.group(1), m.group(2)
            qs[qid] = {'id': qid, 'text': text, 'section': cur}
    # folders
    for d in os.listdir(CANON):
        if re.match(r'P\d\d_', d):
            for q in os.listdir(os.path.join(CANON, d)):
                m = re.match(r'\d+_(Q-[A-Z0-9\-]+)$', q)
                if m:
                    qs.setdefault(m.group(1), {'id': m.group(1), 'text': '', 'section': ''})
                    qs[m.group(1)]['folder'] = os.path.join(d, q)
    for qid, q in qs.items():
        idpart = [p for p in qid.split('-')[1:] if p not in ('REAL',)]
        q['tokens'] = set(toks(' '.join(idpart) + ' ' + q['text']))
    return qs


def build_idf(qs):
    df = collections.Counter()
    for q in qs.values():
        for t in q['tokens']:
            df[t] += 1
    n = len(qs)
    return {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}


def read_text(p):
    try:
        if os.path.getsize(p) > MAX_BYTES:
            return None
        return open(p, encoding='utf8', errors='ignore').read(READ_CHARS)
    except OSError:
        return None


def score_doc(text, name, qs, idf):
    body = collections.Counter(toks(text))
    first_head = ''
    for ln in text.splitlines()[:12]:
        if ln.strip():
            first_head += ' ' + ln.strip('# ').strip()
    head = set(t for t in toks(os.path.splitext(name)[0] + ' ' + first_head) if t not in GENERIC_NAME)
    scored = []
    for q in qs.values():
        tot = 0.0
        got = 0.0
        hits = []
        distinct = 0
        for t in q['tokens']:
            w = idf.get(t, 0.0)
            tot += w
            if t in head:
                got += w; hits.append((w, t)); distinct += 1
            elif body.get(t):
                got += w * min(1.0, body[t] / 3.0); hits.append((w * 0.5, t)); distinct += 1
        if tot > 0 and got > 0:
            hits.sort(reverse=True)
            # one-token coincidences must not reach 1.0: scale by how many distinct question terms matched
            conf = (got / tot) * (0.5 + 0.5 * min(1.0, distinct / 3.0))
            scored.append((conf, q['id'], [t for _, t in hits[:5]]))
    scored.sort(reverse=True)
    return scored[:3]


def main():
    global ROOTS, OUT
    if len(sys.argv) > 1:               # optional: pass roots (folders or single files) on the command line
        ROOTS = sys.argv[1:]
        OUT = OUT + '-run2'
    os.makedirs(OUT, exist_ok=True)
    qs = load_questions()
    idf = build_idf(qs)
    print('questions parsed:', len(qs), '| with folder:', sum(1 for q in qs.values() if 'folder' in q),
          '| with text:', sum(1 for q in qs.values() if q['text']))

    skipped = collections.Counter()
    rows = []
    for root in ROOTS:
        rp = os.path.join(VAULT, root)
        if os.path.isfile(rp):
            walker = [(os.path.dirname(rp), [], [os.path.basename(rp)])]
        elif os.path.isdir(rp):
            walker = os.walk(rp)
        else:
            print('MISSING root', root); continue
        for d, dirs, files in walker:
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                fp = os.path.join(d, f)
                if ext not in TEXT_EXT:
                    skipped['not text (' + (ext or 'none') + ')'] += 1
                    continue
                text = read_text(fp)
                if text is None:
                    skipped['too big/unreadable'] += 1; continue
                if len(text.strip()) < 80:
                    skipped['near-empty'] += 1; continue
                top = score_doc(text, f, qs, idf)
                rel = os.path.relpath(fp, VAULT)
                row = {'root': root, 'file': rel, 'chars': len(text)}
                for i in range(3):
                    if i < len(top):
                        row['q%d' % (i + 1)] = top[i][1]; row['s%d' % (i + 1)] = round(top[i][0], 3)
                    else:
                        row['q%d' % (i + 1)] = ''; row['s%d' % (i + 1)] = 0
                row['terms'] = ','.join(top[0][2]) if top else ''
                rows.append(row)

    with open(os.path.join(OUT, 'matches.csv'), 'w', newline='', encoding='utf8') as fh:
        w = csv.DictWriter(fh, fieldnames=['root', 'file', 'chars', 'q1', 's1', 'q2', 's2', 'q3', 's3', 'terms'])
        w.writeheader(); w.writerows(rows)

    print('scored files:', len(rows))
    print('skipped:', dict(skipped.most_common(8)))
    s1 = sorted(r['s1'] for r in rows)
    if s1:
        pct = lambda p: s1[min(len(s1) - 1, int(len(s1) * p))]
        print('best-score percentiles  p10 %.2f  p25 %.2f  p50 %.2f  p75 %.2f  p90 %.2f  max %.2f' %
              (pct(.1), pct(.25), pct(.5), pct(.75), pct(.9), s1[-1]))
    byroot = collections.defaultdict(list)
    for r in rows:
        byroot[r['root']].append(r['s1'])
    for k, v in byroot.items():
        print('  %-30s files %4d  >=0.35: %3d  >=0.50: %3d' % (k, len(v), sum(x >= .35 for x in v), sum(x >= .5 for x in v)))
    tally = collections.Counter(r['q1'] for r in rows if r['s1'] >= 0.35)
    print('top questions by files (best score >= 0.35):', tally.most_common(12))
    print('questions never the top match:', len(qs) - len(set(r['q1'] for r in rows)))

    ranked = sorted(rows, key=lambda r: -r['s1'])
    def show(title, sel):
        print('\n--', title)
        for r in sel:
            print('  %.2f %-28s %s  <-  %s' % (r['s1'], r['q1'], r['terms'][:40], r['file'][-70:]))
    n = len(ranked)
    if n:
        show('TOP 8', ranked[:8])
        show('MIDDLE 8', ranked[n // 2 - 4: n // 2 + 4])
        show('LOW 6 (just above zero)', [r for r in ranked if r['s1'] > 0][-6:])

    print('\n-- CROSSWALK: _first_principles_to_god Q-series -> debate-map questions (top 3)')
    cw = [r for r in rows if r['root'] == '_first_principles_to_god' and re.search(r'[\\/]Q\d\d', r['file'])]
    cw.sort(key=lambda r: r['file'])
    for r in cw:
        base = os.path.basename(r['file'])[:34]
        print('  %-34s %s %.2f | %s %.2f | %s %.2f' % (base, r['q1'], r['s1'], r['q2'], r['s2'], r['q3'], r['s3']))

    with open(os.path.join(OUT, 'REPORT.md'), 'w', encoding='utf8') as fh:
        fh.write('# Argument match dry run (read-only)\n\n')
        fh.write('Generated %s. Nothing was written inside the vault or DEBATE_MAP.\n\n' % datetime.datetime.now().isoformat(timespec='seconds'))
        fh.write('Scored files: %d. Skipped: %s\n' % (len(rows), dict(skipped)))
    print('\nreports in', OUT)


if __name__ == '__main__':
    main()
