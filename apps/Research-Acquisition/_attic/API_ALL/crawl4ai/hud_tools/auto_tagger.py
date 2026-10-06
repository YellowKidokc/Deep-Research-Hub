#!/usr/bin/env python3
"""
AUTO-TAGGER: Feed raw rebuttal text → get HUD code assignment
Works with CSV, JSON, or plain text input.

Usage:
  python auto_tagger.py input.csv          # CSV with 'text' column
  python auto_tagger.py input.json         # JSON array with 'text' field
  python auto_tagger.py --text "The copyist error in the Hebrew numeral..."

Output: Tagged version with HUD codes assigned
"""

import re
import sys
import json
import csv
from collections import Counter

# ===== KEYWORD RULES =====
# Priority keywords = strong signal (2 points each)
# Secondary keywords = weaker signal (1 point each)
# Negative keywords = disqualifier (-3 points)

RULES = {
    'META': {
        'priority': ['false dilemma', 'argument from silence', 'logical fallacy', 'non-sequitur',
                     'straw man', 'begging the question', 'both true', 'not mutually exclusive',
                     'different senses', 'compatible', 'complementary', 'does not follow',
                     'category error', 'no actual contradiction', 'both can be true',
                     'not a real contradiction', 'misunderstands the text'],
        'secondary': ['fallacious', 'faulty reasoning', 'misreading', 'misunderstanding',
                      'harmonize', 'reconcile', 'both accounts', 'no conflict'],
        'negative': ['manuscript', 'copy error', 'scribe', 'hebrew letter', 'numeral variant'],
    },
    'SCRIBE': {
        'priority': ['copyist error', 'scribal variant', 'numeral corruption', 'manuscript tradition',
                     'textual criticism', 'dalet', 'resh', 'yod', 'vav', 'hebrew letter',
                     'transmission error', 'textual variant', 'copying mistake', 'scribal error'],
        'secondary': ['copy error', 'number discrepancy', 'ancient manuscripts', 'name variant',
                      'minor numerical', 'text critical', 'original reading'],
        'negative': ['context', 'old testament law', 'covenant change', 'audience'],
    },
    'STRIPPING': {
        'priority': ['out of context', 'read the full passage', 'surrounding verses',
                     'incomplete quotation', 'cherry-picking', 'partial quote', 'context shows',
                     'broader passage', 'read in context', 'taken out of context'],
        'secondary': ['missing context', 'when read together', 'in light of', 'full picture',
                      'rest of the chapter', 'preceding verses', 'following verses'],
        'negative': ['manuscript', 'numeral', 'copyist', 'scribal'],
    },
    'VANTAGE': {
        'priority': ['different perspective', 'different witness', 'vantage point',
                     'complementary accounts', 'independent testimony', 'multiple angles',
                     'eyewitness variation', 'different author', 'different gospel writer'],
        'secondary': ['eyewitness', 'angle', 'perspective', 'viewpoint', 'remembered differently',
                      'additional detail', 'saw from', 'reported from'],
        'negative': ['translation', 'hebrew word', 'covenant change', 'copyist'],
    },
    'COVENANT': {
        'priority': ['old covenant', 'new covenant', 'old testament law', 'ceremonial law',
                     'civil law', 'moral law', 'fulfilled in christ', 'hebrews', 'galatians',
                     'law of moses', 'dispensation', 'mosaic law'],
        'secondary': ['old vs new', 'law and grace', 'no longer required', 'fulfilled',
                      'superseded', 'abrogated', 'temporary regulation'],
        'negative': ['manuscript', 'copyist', 'witness perspective', 'translation artifact'],
    },
    'SEMANTIC': {
        'priority': ['hebrew word', 'greek word', 'translation', 'original language',
                     'word range', 'multiple meanings', 'idiom', 'semantic range',
                     'in the original', 'hebrew term', 'greek term'],
        'secondary': ['ben means', 'agape', 'phileo', 'english equivalent', 'linguistic',
                      'literal translation', 'figure of speech', 'hebrew idiom'],
        'negative': ['scribal error', 'manuscript', 'covenant', 'audience adaptation'],
    },
    'DISTINCT': {
        'priority': ['separate event', 'two events', 'happened twice', 'different occasion',
                     'distinct incident', 'not the same event', 'two different', 'occurred twice'],
        'secondary': ['earlier and later', 'first and second time', 'repeated', 'another instance',
                      'similar but distinct', 'two occasions'],
        'negative': ['translation', 'copyist', 'logical fallacy', 'context removal'],
    },
    'ROUNDING': {
        'priority': ['round number', 'approximation', 'approximate', 'rounded', 'precision',
                     'about', 'roughly', 'ancient rounding', 'general figure'],
        'secondary': ['exact vs round', 'estimate', 'numerical convention', 'rough number'],
        'negative': ['context', 'translation', 'witness', 'audience'],
    },
    'AUDIENCE': {
        'priority': ['jewish audience', 'roman audience', 'greek audience', 'target audience',
                     'narrative purpose', 'emphasis for readers', 'adapted for', 'writing to'],
        'secondary': ['matthew for jews', 'mark for romans', 'luke for greeks', 'reader oriented',
                      'different emphasis', 'pastoral purpose'],
        'negative': ['copyist', 'manuscript', 'translation artifact', 'scribal'],
    },
    'PHENOM': {
        'priority': ['observational language', 'phenomenological', 'poetic language', 'metaphor',
                     'anthropomorphic', 'literary device', 'figurative', 'poetic expression'],
        'secondary': ['appears to', 'from human perspective', 'manner of speaking', 'poetic',
                      'not literal science', 'figures of speech'],
        'negative': ['copyist', 'manuscript', 'audience adaptation', 'covenant transition'],
    },
}

def tag_text(text):
    """Score text against all HUD categories. Returns (best_code, confidence, scores)."""
    text_lower = text.lower()
    scores = {}
    
    for code, rules in RULES.items():
        score = 0
        hits = []
        
        for kw in rules['priority']:
            if kw in text_lower:
                score += 2
                hits.append(f"+2:{kw}")
        
        for kw in rules['secondary']:
            if kw in text_lower:
                score += 1
                hits.append(f"+1:{kw}")
        
        for kw in rules['negative']:
            if kw in text_lower:
                score -= 3
                hits.append(f"-3:{kw}")
        
        scores[code] = {'score': score, 'hits': hits}
    
    # Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    best_code = ranked[0][0]
    best_score = ranked[0][1]['score']
    second_score = ranked[1][1]['score'] if len(ranked) > 1 else 0
    
    # Confidence
    if best_score >= 4 and best_score > second_score + 2:
        confidence = 'HIGH'
    elif best_score >= 2:
        confidence = 'MEDIUM'
    elif best_score >= 1:
        confidence = 'LOW'
    else:
        confidence = 'NONE'
        best_code = 'UNKNOWN'
    
    return best_code, confidence, scores

def process_csv(filepath):
    """Process CSV with columns: id, question, text"""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get('text', '') or row.get('rebuttal', '') or row.get('content', '')
            code, conf, scores = tag_text(text)
            row['hud_code'] = code
            row['confidence'] = conf
            row['top_score'] = scores[code]['score'] if code != 'UNKNOWN' else 0
            row['hits'] = '; '.join(scores[code]['hits']) if code != 'UNKNOWN' else ''
            results.append(row)
    
    # Write output
    out_path = filepath.replace('.csv', '_tagged.csv')
    if results:
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
    
    return results, out_path

def process_json(filepath):
    """Process JSON array with 'text' field"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'contradictions' in data:
        items = data['contradictions']
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    
    for item in items:
        text = item.get('text', '') or item.get('rebuttal', '') or item.get('content', '')
        code, conf, scores = tag_text(text)
        item['auto_hud_code'] = code
        item['auto_confidence'] = conf
    
    out_path = filepath.replace('.json', '_tagged.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data if not isinstance(data, list) else items, f, indent=2)
    
    return items, out_path

def tag_single(text):
    """Tag a single text string"""
    code, conf, scores = tag_text(text)
    print(f"\n{'='*60}")
    print(f"INPUT: {text[:200]}...")
    print(f"\nRESULT: [{code}] (Confidence: {conf})")
    print(f"\nSCORES:")
    for c, s in sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True):
        if s['score'] > 0:
            print(f"  [{c}]: {s['score']} pts — {', '.join(s['hits'])}")
    return code, conf

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python auto_tagger.py input.csv")
        print("  python auto_tagger.py input.json")
        print('  python auto_tagger.py --text "The copyist error in Hebrew..."')
        sys.exit(1)
    
    if sys.argv[1] == '--text':
        text = ' '.join(sys.argv[2:])
        tag_single(text)
    elif sys.argv[1].endswith('.csv'):
        results, out = process_csv(sys.argv[1])
        codes = Counter(r['hud_code'] for r in results)
        print(f"Tagged {len(results)} entries → {out}")
        print(f"Distribution: {dict(codes)}")
    elif sys.argv[1].endswith('.json'):
        results, out = process_json(sys.argv[1])
        codes = Counter(r.get('auto_hud_code', 'UNKNOWN') for r in results)
        print(f"Tagged {len(results)} entries → {out}")
        print(f"Distribution: {dict(codes)}")
    else:
        print(f"Unknown format: {sys.argv[1]}")
        sys.exit(1)
