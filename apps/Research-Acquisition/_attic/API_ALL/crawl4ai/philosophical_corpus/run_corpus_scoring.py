#!/usr/bin/env python3
"""
PHILOSOPHICAL CORPUS SCORER
============================
Processes all texts in philosophical_corpus through Fruits of the Spirit metrics.
Generates comparison report with category breakdowns.
"""

import sys
import os
sys.path.insert(0, r'O:\Theophysics_Backend\In_House_Programs\Plugins\Theophysics theory downloader\Data_Analytics\Scripts')

from fruits_scorer import (
    analyze_theory_fruits, 
    FruitsAnalysis,
    score_to_grade
)
from pathlib import Path
from datetime import datetime
import json
import re

CORPUS_DIR = Path(r"D:\GitHub\crawl4ai\philosophical_corpus")
OUTPUT_DIR = CORPUS_DIR / "scoring_output"

def extract_category(filename: str) -> str:
    """Extract category from filename prefix."""
    prefixes = [
        "Calibration", "Classical_Philosophy", "Consciousness_Science",
        "Cosmology", "Eastern_Religion", "Gnostic_Esoteric",
        "Information_Theory", "Islamic_Philosophy", "Moral_Ethical",
        "Negative_Control", "Quantum_Mechanics", "Scientific_Classics",
        "Structural", "Theology"
    ]
    for prefix in prefixes:
        if filename.startswith(prefix):
            return prefix.replace("_", " ")
    return "Other"

def process_corpus():
    """Process all markdown files in corpus."""
    results = []
    md_files = list(CORPUS_DIR.glob("*.md"))
    
    # Skip non-content files
    skip_files = ["download_report", "README"]
    md_files = [f for f in md_files if not any(s in f.stem for s in skip_files)]
    
    print(f"Processing {len(md_files)} texts...")
    print("-" * 60)
    
    for i, fpath in enumerate(sorted(md_files)):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip header metadata (everything before first ---)
            if content.startswith('#'):
                # Find content after metadata
                lines = content.split('\n')
                content_start = 0
                in_header = True
                for j, line in enumerate(lines):
                    if line.strip() == '---':
                        content_start = j + 1
                        break
                content = '\n'.join(lines[content_start:])
            
            if len(content.split()) < 30:
                print(f"  [{i+1}] SKIP (too short): {fpath.stem[:50]}")
                continue
            
            analysis = analyze_theory_fruits(content, fpath.stem)
            category = extract_category(fpath.stem)
            
            results.append({
                'filename': fpath.stem,
                'category': category,
                'analysis': analysis
            })
            
            print(f"  [{i+1}] {analysis.grade:>2} | {analysis.total_score:>6.2f} | {category:>20} | {fpath.stem[:35]}")
            
        except Exception as e:
            print(f"  [{i+1}] ERROR: {fpath.stem}: {e}")
    
    return results

def generate_report(results):
    """Generate comprehensive scoring report."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    report = []
    report.append("=" * 80)
    report.append("PHILOSOPHICAL CORPUS - FRUITS OF THE SPIRIT SCORING")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total texts scored: {len(results)}")
    report.append("")
    
    # Category breakdown
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    report.append("-" * 80)
    report.append("CATEGORY AVERAGES")
    report.append("-" * 80)
    report.append(f"{'Category':<25} {'Count':>6} {'Avg Score':>10} {'Avg Grade':>10}")
    report.append("-" * 80)
    
    cat_averages = []
    for cat, items in sorted(categories.items()):
        avg_score = sum(i['analysis'].total_score for i in items) / len(items)
        avg_norm = sum(i['analysis'].normalized_score for i in items) / len(items)
        cat_averages.append((cat, len(items), avg_score, avg_norm))
        report.append(f"{cat:<25} {len(items):>6} {avg_score:>10.2f} {score_to_grade(avg_norm):>10}")
    
    report.append("")
    
    # Top 20 overall
    report.append("-" * 80)
    report.append("TOP 20 HIGHEST SCORING TEXTS")
    report.append("-" * 80)
    
    sorted_results = sorted(results, key=lambda x: x['analysis'].total_score, reverse=True)
    for i, r in enumerate(sorted_results[:20]):
        a = r['analysis']
        report.append(f"  {i+1:2}. {a.grade:>2} | {a.total_score:>6.2f} | {r['category']:>20} | {r['filename'][:40]}")
    
    report.append("")
    
    # Bottom 10 (negative controls should appear here)
    report.append("-" * 80)
    report.append("BOTTOM 10 LOWEST SCORING TEXTS")
    report.append("-" * 80)
    
    for i, r in enumerate(sorted_results[-10:]):
        a = r['analysis']
        report.append(f"  {i+1:2}. {a.grade:>2} | {a.total_score:>6.2f} | {r['category']:>20} | {r['filename'][:40]}")
    
    report.append("")
    
    # Per-category top 3
    report.append("-" * 80)
    report.append("TOP 3 PER CATEGORY")
    report.append("-" * 80)
    
    for cat, items in sorted(categories.items()):
        sorted_cat = sorted(items, key=lambda x: x['analysis'].total_score, reverse=True)
        report.append(f"\n{cat}:")
        for i, r in enumerate(sorted_cat[:3]):
            a = r['analysis']
            report.append(f"  {i+1}. {a.grade:>2} | {a.total_score:>6.2f} | {r['filename'][:50]}")
    
    report.append("")
    
    # Fruit-by-fruit averages across all
    report.append("-" * 80)
    report.append("AVERAGE FRUIT SCORES ACROSS ENTIRE CORPUS")
    report.append("-" * 80)
    
    fruits = [
        ('F1 Grace', 'f1_grace'),
        ('F2 Hope', 'f2_hope'),
        ('F3 Patience', 'f3_patience'),
        ('F4 Faithfulness', 'f4_faithfulness'),
        ('F5 Self-Control', 'f5_self_control'),
        ('F6 Love', 'f6_love'),
        ('F7 Peace', 'f7_peace'),
        ('F8 Truth', 'f8_truth'),
        ('F9 Humility', 'f9_humility'),
        ('F10 Goodness', 'f10_goodness'),
        ('F11 Unity', 'f11_unity'),
        ('F12 Joy', 'f12_joy'),
    ]
    
    for label, attr in fruits:
        avg = sum(getattr(r['analysis'], attr).score for r in results) / len(results)
        bar = "+" * int(max(0, avg * 20)) if avg > 0 else "-" * int(abs(avg * 20))
        report.append(f"  {label:<20} {avg:>7.3f}  {bar}")
    
    report.append("")
    report.append("=" * 80)
    
    # Write report
    report_text = "\n".join(report)
    
    with open(OUTPUT_DIR / "corpus_fruits_report.txt", 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # JSON output
    json_data = {
        "generated_at": datetime.now().isoformat(),
        "total_texts": len(results),
        "category_averages": [
            {"category": c, "count": n, "avg_score": s, "avg_norm": norm}
            for c, n, s, norm in cat_averages
        ],
        "texts": [
            {
                "filename": r['filename'],
                "category": r['category'],
                "total_score": r['analysis'].total_score,
                "normalized": r['analysis'].normalized_score,
                "grade": r['analysis'].grade,
                "fruits": {
                    "grace": r['analysis'].f1_grace.score,
                    "hope": r['analysis'].f2_hope.score,
                    "patience": r['analysis'].f3_patience.score,
                    "faithfulness": r['analysis'].f4_faithfulness.score,
                    "self_control": r['analysis'].f5_self_control.score,
                    "love": r['analysis'].f6_love.score,
                    "peace": r['analysis'].f7_peace.score,
                    "truth": r['analysis'].f8_truth.score,
                    "humility": r['analysis'].f9_humility.score,
                    "goodness": r['analysis'].f10_goodness.score,
                    "unity": r['analysis'].f11_unity.score,
                    "joy": r['analysis'].f12_joy.score
                }
            }
            for r in sorted_results
        ]
    }
    
    with open(OUTPUT_DIR / "corpus_fruits_data.json", 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    print("\n" + report_text)
    print(f"\nReport saved to: {OUTPUT_DIR / 'corpus_fruits_report.txt'}")
    print(f"JSON saved to: {OUTPUT_DIR / 'corpus_fruits_data.json'}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHILOSOPHICAL CORPUS SCORING ENGINE")
    print("=" * 60)
    print()
    
    results = process_corpus()
    print()
    print(f"Successfully scored {len(results)} texts")
    print()
    
    generate_report(results)
