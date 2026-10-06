#!/usr/bin/env python3
"""
Universal Canonical Documents Coherence Scorer

Score EVERYTHING against the 12 Fruits framework:
1. Theophysics foundational papers
2. US Founding Documents  
3. Scientific Theories (118 papers)
4. World Religions texts

This is the ULTIMATE self-consistency test.
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
CANONICAL_BASE = Path(r"O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical")
THEOPHYSICS_PAPERS = Path(r"O:\Theophysics_Master\TMSUB\GO FOLDER\Axiom\__AXIOM\Foundational papers")
OUTPUT_DIR = Path(__file__).parent / "outputs" / "comprehensive"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def score_directory(directory, category_name, scorer):
    """Score all documents in a directory."""
    
    print(f"\n{'='*80}")
    print(f"SCORING: {category_name}")
    print(f"Directory: {directory}")
    print(f"{'='*80}\n")
    
    # Get all text/markdown files
    files = list(directory.glob("*.md")) + list(directory.glob("*.txt"))
    
    if not files:
        print(f"  WARNING: No files found in {directory}")
        return []
    
    print(f"Found {len(files)} documents\n")
    
    results = []
    
    for i, file_path in enumerate(sorted(files), 1):
        # ASCII-safe printing
        filename_safe = file_path.name.encode('ascii', 'replace').decode('ascii')
        print(f"[{i}/{len(files)}] {filename_safe}")
        
        try:
            text = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"  ERROR reading: {e}")
            continue
        
        try:
            score_result = scorer.score_text(text, doc_id=file_path.stem)
        except Exception as e:
            print(f"  ERROR scoring: {e}")
            continue
        
        result_row = {
            "category": category_name,
            "document": file_path.name,
            "stem": file_path.stem,
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
        print(f"  chi = {score_result['chi']:.4f} | {score_result['grade']}\n")
    
    return results


def main():
    print("="*80)
    print("COMPREHENSIVE CANONICAL DOCUMENTS COHERENCE ANALYSIS")
    print("Testing universal structural invariants across ALL domains")
    print("="*80)
    
    scorer = UnifiedCoherenceScorer()
    all_results = []
    
    # 1. Theophysics Foundational Papers
    if THEOPHYSICS_PAPERS.exists():
        results = score_directory(THEOPHYSICS_PAPERS, "Theophysics", scorer)
        all_results.extend(results)
    
    # 2. US Founding Documents
    founding_docs = CANONICAL_BASE / "01_US_Founding_Documents"
    if founding_docs.exists():
        results = score_directory(founding_docs, "US_Founding_Documents", scorer)
        all_results.extend(results)
    
    # 3. Scientific Theories
    theories = CANONICAL_BASE / "02_Scientific_Theories"
    if theories.exists():
        results = score_directory(theories, "Scientific_Theories", scorer)
        all_results.extend(results)
    
    # 4. World Religions
    religions = CANONICAL_BASE / "03_World_Religions"
    if religions.exists():
        results = score_directory(religions, "World_Religions", scorer)
        all_results.extend(results)
    
    # Create master DataFrame
    df = pd.DataFrame(all_results)
    
    if df.empty:
        print("\nERROR: No results to analyze!")
        return
    
    # Generate outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. CSV
    csv_path = OUTPUT_DIR / f"comprehensive_scores_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[OK] CSV: {csv_path}")
    
    # 2. Excel with multiple sheets
    excel_path = OUTPUT_DIR / f"comprehensive_scores_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Documents', index=False)
        
        # Category sheets
        for category in df['category'].unique():
            cat_df = df[df['category'] == category].sort_values('chi', ascending=False)
            cat_df.to_excel(writer, sheet_name=category[:31], index=False)
        
        # Summary statistics
        summary = df.groupby('category').agg({
            'chi': ['mean', 'median', 'std', 'min', 'max', 'count']
        }).round(4)
        summary.to_excel(writer, sheet_name='Summary')
    
    print(f"[OK] Excel: {excel_path}")
    
    # 3. JSON
    json_path = OUTPUT_DIR / f"comprehensive_scores_{timestamp}.json"
    df.to_json(json_path, orient='records', indent=2)
    print(f"[OK] JSON: {json_path}")
    
    # 4. Generate comprehensive report
    generate_report(df, OUTPUT_DIR / f"comprehensive_report_{timestamp}.md")
    
    # Print summary
    print("\n" + "="*80)
    print("COMPREHENSIVE SUMMARY")
    print("="*80 + "\n")
    
    print(f"Total Documents: {len(df)}\n")
    
    print("BY CATEGORY:")
    for category in df['category'].unique():
        cat_df = df[df['category'] == category]
        print(f"\n  {category}:")
        print(f"    Count: {len(cat_df)}")
        print(f"    Mean chi: {cat_df['chi'].mean():.4f}")
        print(f"    Median chi: {cat_df['chi'].median():.4f}")
        print(f"    Range: [{cat_df['chi'].min():.4f}, {cat_df['chi'].max():.4f}]")
    
    print("\n" + "="*80)
    print("TOP 10 DOCUMENTS (All Categories):")
    print("="*80)
    
    top_10 = df.nlargest(10, 'chi')
    for i, row in top_10.iterrows():
        print(f"  {i+1:2d}. [{row['category']:20s}] {row['document']:50s} chi={row['chi']:.4f}")
    
    print("\n[SUCCESS] Analysis complete!")
    return df


def generate_report(df, output_path):
    """Generate comprehensive markdown report."""
    
    report = f"""# COMPREHENSIVE CANONICAL DOCUMENTS COHERENCE REPORT
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Executive Summary

**Total Documents Analyzed:** {len(df)}

**Categories:**
"""
    
    for category in sorted(df['category'].unique()):
        cat_df = df[df['category'] == category]
        report += f"- **{category}**: {len(cat_df)} documents (mean χ = {cat_df['chi'].mean():.4f})\n"
    
    report += f"""
**Overall Statistics:**
- Mean χ: {df['chi'].mean():.4f}
- Median χ: {df['chi'].median():.4f}
- Std Dev: {df['chi'].std():.4f}
- Range: [{df['chi'].min():.4f}, {df['chi'].max():.4f}]

---

## Top 10 Documents (Cross-Category)

| Rank | Category | Document | χ | Grade |
|------|----------|----------|---|-------|
"""
    
    for i, row in df.nlargest(10, 'chi').iterrows():
        report += f"| {i+1} | {row['category']} | {row['document']} | {row['chi']:.4f} | {row['grade']} |\n"
    
    report += "\n---\n\n"
    
    # Category breakdowns
    for category in sorted(df['category'].unique()):
        cat_df = df[df['category'] == category].sort_values('chi', ascending=False)
        
        report += f"## {category}\n\n"
        report += f"**Count:** {len(cat_df)} | "
        report += f"**Mean χ:** {cat_df['chi'].mean():.4f} | "
        report += f"**Median χ:** {cat_df['chi'].median():.4f}\n\n"
        
        report += "| Rank | Document | χ | Grade | Interpretation |\n"
        report += "|------|----------|---|-------|----------------|\n"
        
        for i, row in cat_df.iterrows():
            report += f"| {i+1} | {row['document']} | {row['chi']:.4f} | {row['grade']} | {row['interpretation']} |\n"
        
        report += "\n---\n\n"
    
    output_path.write_text(report, encoding='utf-8')
    print(f"[OK] Report: {output_path}")


if __name__ == "__main__":
    try:
        df = main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
