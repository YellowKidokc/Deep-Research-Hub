#!/usr/bin/env python3
"""
Foundational Papers Coherence Scorer

Score all Theophysics foundational papers against the 12 Fruits coherence metric.
Test the framework against its own structural invariants.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

# Add coherence scorer to path
sys.path.insert(0, str(Path(__file__).parent.parent / "theophysics_coherence_engine"))

from unified_coherence_scorer import UnifiedCoherenceScorer


# Configuration
FOUNDATIONAL_PAPERS_DIR = Path(r"O:\Theophysics_Master\TMSUB\GO FOLDER\Axiom\__AXIOM\Foundational papers")
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def score_all_papers():
    """Score all foundational papers and generate comprehensive report."""
    
    print("=" * 80)
    print("THEOPHYSICS FOUNDATIONAL PAPERS COHERENCE ANALYSIS")
    print("Testing the framework against its own metrics")
    print("=" * 80)
    print()
    
    # Initialize scorer
    scorer = UnifiedCoherenceScorer()
    
    # Get all markdown files
    papers = sorted(FOUNDATIONAL_PAPERS_DIR.glob("*.md"))
    
    if not papers:
        print(f"ERROR: No papers found in {FOUNDATIONAL_PAPERS_DIR}")
        return
    
    print(f"Found {len(papers)} foundational papers")
    print()
    
    # Score each paper
    results = []
    
    for i, paper_path in enumerate(papers, 1):
        print(f"[{i}/{len(papers)}] Scoring: {paper_path.name}")
        
        # Read paper
        try:
            text = paper_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"  ERROR reading file: {e}")
            continue
        
        # Score it
        try:
            score_result = scorer.score_text(text, doc_id=paper_path.stem)
        except Exception as e:
            print(f"  ERROR scoring: {e}")
            continue
        
        # Store results
        result_row = {
            "paper": paper_path.name,
            "paper_stem": paper_path.stem,
            "word_count": score_result["word_count"],
            "chi": score_result["chi"],
            "total_score": score_result["total_score"],
            "normalized_score": score_result["normalized_score"],
            "grade": score_result["grade"],
            "interpretation": score_result["interpretation"],
            
            # Individual fruits
            "f1_grace": score_result["f1_grace"],
            "f2_hope": score_result["f2_hope"],
            "f3_patience": score_result["f3_patience"],
            "f4_faithfulness": score_result["f4_faithfulness"],
            "f5_self_control": score_result["f5_self_control"],
            "f6_love": score_result["f6_love"],
            "f7_peace": score_result["f7_peace"],
            "f8_truth": score_result["f8_truth"],
            "f9_humility": score_result["f9_humility"],
            "f10_goodness": score_result["f10_goodness"],
            "f11_unity": score_result["f11_unity"],
            "f12_joy": score_result["f12_joy"],
        }
        
        results.append(result_row)
        
        print(f"  chi = {score_result['chi']:.4f} | Grade: {score_result['grade']} | {score_result['interpretation']}")
        print()
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by chi (descending)
    df = df.sort_values('chi', ascending=False)
    
    # Generate outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. CSV export
    csv_path = OUTPUT_DIR / f"foundational_papers_scores_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    print(f"[OK] Saved CSV: {csv_path}")
    
    # 2. Excel export with formatting
    excel_path = OUTPUT_DIR / f"foundational_papers_scores_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Scores', index=False)
    print(f"[OK] Saved Excel: {excel_path}")
    
    # 3. JSON export (detailed)
    json_path = OUTPUT_DIR / f"foundational_papers_scores_{timestamp}.json"
    df.to_json(json_path, orient='records', indent=2)
    print(f"[OK] Saved JSON: {json_path}")
    
    # 4. Generate markdown report
    report_path = OUTPUT_DIR / f"foundational_papers_report_{timestamp}.md"
    generate_markdown_report(df, report_path)
    print(f"[OK] Saved Report: {report_path}")
    
    print()
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Papers analyzed: {len(df)}")
    print(f"Mean chi: {df['chi'].mean():.4f}")
    print(f"Median chi: {df['chi'].median():.4f}")
    print(f"Std Dev: {df['chi'].std():.4f}")
    print(f"Min chi: {df['chi'].min():.4f} ({df.loc[df['chi'].idxmin(), 'paper']})")
    print(f"Max chi: {df['chi'].max():.4f} ({df.loc[df['chi'].idxmax(), 'paper']})")
    print()
    
    # Grade distribution
    print("Grade Distribution:")
    grade_counts = df['grade'].value_counts().sort_index(ascending=False)
    for grade, count in grade_counts.items():
        pct = (count / len(df)) * 100
        print(f"  {grade}: {count:2d} papers ({pct:5.1f}%)")
    print()
    
    # Top 3 papers
    print("TOP 3 PAPERS BY COHERENCE:")
    for i, row in df.head(3).iterrows():
        print(f"  {i+1}. {row['paper']:50s} chi={row['chi']:.4f} ({row['grade']})")
    print()
    
    # Top 3 fruits overall
    fruit_cols = [f"f{i}_{fruit}" for i, fruit in enumerate([
        "grace", "hope", "patience", "faithfulness", "self_control", "love",
        "peace", "truth", "humility", "goodness", "unity", "joy"
    ], 1)]
    
    fruit_means = df[fruit_cols].mean().sort_values(ascending=False)
    print("TOP 3 FRUITS ACROSS ALL PAPERS:")
    for i, (fruit, score) in enumerate(fruit_means.head(3).items(), 1):
        fruit_name = fruit.split('_', 1)[1].title()
        print(f"  {i}. {fruit_name:20s}: {score:+.4f}")
    print()
    
    print("=" * 80)
    print("SELF-CONSISTENCY CHECK")
    print("=" * 80)
    print()
    print("If Theophysics is coherent, its foundational papers should score HIGH")
    print("on the same structural invariants (12 Fruits) it claims are universal.")
    print()
    
    if df['chi'].mean() >= 0.7:
        print("PASS: Mean chi >= 0.7 -- Framework demonstrates internal coherence")
    elif df['chi'].mean() >= 0.6:
        print("MARGINAL: Mean chi in [0.6, 0.7) -- Room for improvement")
    else:
        print("FAIL: Mean chi < 0.6 -- Framework lacks internal coherence")
    print()
    
    return df


def generate_markdown_report(df, output_path):
    """Generate detailed markdown report."""
    
    report = f"""# THEOPHYSICS FOUNDATIONAL PAPERS COHERENCE REPORT
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Executive Summary

- **Papers Analyzed:** {len(df)}
- **Mean χ (Coherence):** {df['chi'].mean():.4f}
- **Median χ:** {df['chi'].median():.4f}
- **Range:** [{df['chi'].min():.4f}, {df['chi'].max():.4f}]

### Self-Consistency Result

"""
    
    if df['chi'].mean() >= 0.7:
        report += "**✓ PASS** — Framework demonstrates strong internal coherence\n\n"
    elif df['chi'].mean() >= 0.6:
        report += "**⚠ MARGINAL** — Framework shows adequate but improvable coherence\n\n"
    else:
        report += "**✗ FAIL** — Framework lacks sufficient internal coherence\n\n"
    
    report += """---

## Detailed Scores (Ranked by χ)

| Rank | Paper | χ | Grade | Interpretation |
|------|-------|---|-------|----------------|
"""
    
    for i, row in df.iterrows():
        rank = i + 1
        report += f"| {rank} | {row['paper']} | {row['chi']:.4f} | {row['grade']} | {row['interpretation']} |\n"
    
    report += """
---

## Grade Distribution

"""
    
    grade_counts = df['grade'].value_counts().sort_index(ascending=False)
    for grade, count in grade_counts.items():
        pct = (count / len(df)) * 100
        report += f"- **{grade}**: {count} papers ({pct:.1f}%)\n"
    
    report += """
---

## Fruit Analysis

### Mean Scores Across All Papers

"""
    
    fruit_cols = [f"f{i}_{fruit}" for i, fruit in enumerate([
        "grace", "hope", "patience", "faithfulness", "self_control", "love",
        "peace", "truth", "humility", "goodness", "unity", "joy"
    ], 1)]
    
    fruit_means = df[fruit_cols].mean().sort_values(ascending=False)
    
    for fruit_col, score in fruit_means.items():
        fruit_name = fruit_col.split('_', 1)[1].title()
        report += f"- **{fruit_name}**: {score:+.4f}\n"
    
    report += """
---

## Individual Paper Breakdowns

"""
    
    for i, row in df.iterrows():
        report += f"### {row['paper']}\n\n"
        report += f"- **χ**: {row['chi']:.4f}\n"
        report += f"- **Grade**: {row['grade']}\n"
        report += f"- **Word Count**: {row['word_count']:,}\n"
        report += f"- **Interpretation**: {row['interpretation']}\n\n"
        report += "**Fruit Scores:**\n\n"
        
        for fruit_col in fruit_cols:
            fruit_name = fruit_col.split('_', 1)[1].title()
            score = row[fruit_col]
            bar = "█" * int((score + 1) * 10)
            report += f"- {fruit_name:15s}: {score:+.3f} {bar}\n"
        
        report += "\n---\n\n"
    
    report += """
## Methodology

This analysis scores each foundational paper using the **12 Fruits of the Spirit**
structural invariants that Theophysics claims are universal coherence metrics:

1. **Grace** — Forgiveness, non-zero-sum
2. **Hope** — Future orientation, telos
3. **Patience** — Long-term thinking
4. **Faithfulness** — Reliability, consistency
5. **Self-Control** — Discipline, boundaries
6. **Love** — Other-orientation, unity
7. **Peace** — Conflict resolution
8. **Truth** — Alignment with reality
9. **Humility** — Teachability, error-correction
10. **Goodness** — Constructive action
11. **Unity** — Coherence, integration
12. **Joy** — Positive-sum outcomes

Each fruit scores [-1, +1]. Total scores range [-12, +12], normalized to χ ∈ [0, 1].

**Self-Consistency Test:** If Theophysics is correct that these are universal
structural invariants, then its own foundational papers should score HIGH on
these same metrics.

---

**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    output_path.write_text(report, encoding='utf-8')


if __name__ == "__main__":
    try:
        df = score_all_papers()
        print("[SUCCESS] Analysis complete!")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
