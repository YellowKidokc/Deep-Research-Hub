import pandas as pd
import os
import random

# Read the Excel file from the "Full HUD Arsenal" sheet
excel_path = r"C:\Users\lowes\Downloads\UNIFIED_HUD_MASTER_FINAL.xlsx"
df = pd.read_excel(excel_path, sheet_name="Full HUD Arsenal")

print(f"Excel Quality Verification Report")
print(f"File: {excel_path}")
print(f"Dataset: {len(df)} rows x {len(df.columns)} columns")

# ============================================================================
# 1. Check CBC Rebuttal Text Quality
# ============================================================================
print("\n" + "="*80)
print("CHECK 1: CBC Rebuttal Text Quality (3 random samples)")
print("="*80)

rows_with_rebuttal = df[df['CBC Rebuttal Text'].notna() & (df['CBC Rebuttal Text'] != '')]
print(f"\nTotal rows with CBC Rebuttal Text: {len(rows_with_rebuttal)} / {len(df)} ({len(rows_with_rebuttal)/len(df)*100:.1f}%)")

if len(rows_with_rebuttal) >= 3:
    sample_rows = rows_with_rebuttal.sample(n=3, random_state=42)
    for idx, (i, row) in enumerate(sample_rows.iterrows(), 1):
        print(f"\n--- CBC Rebuttal Sample {idx} ---")
        question = str(row['Question'])[:80]
        print(f"Question: {question}")
        
        rebuttal = str(row['CBC Rebuttal Text'])
        print(f"Rebuttal (first 200 chars):\n  {rebuttal[:200]}")
        
        # Relevance check
        q_words = set(w.lower() for w in question.split() if len(w) > 4)
        r_words = set(w.lower().rstrip('.,;:') for w in rebuttal.split() if len(w) > 4)
        overlap = len(q_words & r_words)
        
        print(f"Word overlap (long words >4 chars): {overlap}")
        print(f"Relevance: {'RELEVANT' if overlap >= 1 else 'MAY BE RELEVANT'}")

# ============================================================================
# 2. Verify Local Files Exist (check actual directory)
# ============================================================================
print("\n" + "="*80)
print("CHECK 2: Local File Existence Verification")
print("="*80)

base_path = r"D:\GitHub\crawl4ai\bible_contradictions_HUD"
if os.path.exists(base_path):
    actual_files = set(os.listdir(base_path))
    print(f"\nActual files in directory: {len(actual_files)}")
else:
    print(f"\nERROR: Base path does not exist: {base_path}")
    actual_files = set()

rows_with_localfile = df[df['Local File'].notna() & (df['Local File'] != '')]
print(f"Rows with Local File reference: {len(rows_with_localfile)} / {len(df)}")

# Sample 3 files that should exist
if len(rows_with_localfile) >= 3:
    sample_files = rows_with_localfile.sample(n=3, random_state=42)
    found_count = 0
    
    for idx, (i, row) in enumerate(sample_files.iterrows(), 1):
        filename = row['Local File']
        exists = filename in actual_files
        status = "EXISTS" if exists else "NOT FOUND"
        
        if exists:
            found_count += 1
        
        print(f"\n--- File Sample {idx} ---")
        print(f"Question: {str(row['Question'])[:60]}")
        print(f"Filename: {filename[:60]}")
        print(f"Status: {status}")
        
        # Check size if exists
        if exists:
            filepath = os.path.join(base_path, filename)
            size = os.path.getsize(filepath)
            print(f"File size: {size} bytes")
    
    print(f"\nFound: {found_count}/3 files exist in directory")

# ============================================================================
# 3. Column Fill Summary
# ============================================================================
print("\n" + "="*80)
print("CHECK 3: Data Completeness Summary")
print("="*80)

print("\nMost Complete Columns (>90% filled):")
for col in df.columns:
    fill_pct = (df[col].notna().sum() / len(df)) * 100
    if fill_pct > 90:
        filled = df[col].notna().sum()
        print(f"  {col:.<40} {filled:>4} / {len(df)} ({fill_pct:>5.1f}%)")

print("\nPartial Columns (30-90% filled):")
for col in df.columns:
    fill_pct = (df[col].notna().sum() / len(df)) * 100
    if 30 <= fill_pct <= 90:
        filled = df[col].notna().sum()
        print(f"  {col:.<40} {filled:>4} / {len(df)} ({fill_pct:>5.1f}%)")

print("\nSparse Columns (<30% filled):")
for col in df.columns:
    fill_pct = (df[col].notna().sum() / len(df)) * 100
    if fill_pct < 30:
        filled = df[col].notna().sum()
        print(f"  {col:.<40} {filled:>4} / {len(df)} ({fill_pct:>5.1f}%)")

# ============================================================================
# 4. Check SAB URL Coverage
# ============================================================================
print("\n" + "="*80)
print("CHECK 4: SAB URL Coverage and Source Alignment")
print("="*80)

sab_urls = df[df['SAB URL'].notna() & (df['SAB URL'] != '')]
print(f"\nRows with SAB URL: {len(sab_urls)} / {len(df)} ({len(sab_urls)/len(df)*100:.1f}%)")

# Show example
if len(sab_urls) > 0:
    example = sab_urls.iloc[0]
    print(f"\n--- Example SAB URL Match ---")
    print(f"Question: {str(example['Question'])[:70]}")
    print(f"Source: {example['Source']}")
    print(f"SAB URL: {str(example['SAB URL'])[:80]}")
    print(f"HUD Code: {example['HUD Code']}")
    print(f"Essay Title: {example['Essay Title'][:50]}")

# Source breakdown with URL coverage
print(f"\nURL coverage by source:")
for source in df['Source'].unique():
    source_df = df[df['Source'] == source]
    urls = source_df[source_df['SAB URL'].notna() & (source_df['SAB URL'] != '')]
    coverage = len(urls) / len(source_df) * 100
    print(f"  {source:.<20} {len(urls):>3} / {len(source_df):>3} ({coverage:>5.1f}%)")

print("\n" + "="*80)
print("Verification Report Complete")
print("="*80)
