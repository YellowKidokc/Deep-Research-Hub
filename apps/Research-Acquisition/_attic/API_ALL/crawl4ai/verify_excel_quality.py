import pandas as pd
import os
import random
from pathlib import Path

# Read the Excel file from the "Full HUD Arsenal" sheet
excel_path = r"C:\Users\lowes\Downloads\UNIFIED_HUD_MASTER_FINAL.xlsx"
print(f"Reading Excel file: {excel_path}")
df = pd.read_excel(excel_path, sheet_name="Full HUD Arsenal")

print(f"\nDataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# ============================================================================
# 1. Find rows with "Kill Method" text (similar to Rebuttal)
# ============================================================================
print("\n" + "="*80)
print("CHECK 1: 3 random rows with Kill Method text")
print("="*80)

rows_with_method = df[df['Kill Method'].notna() & (df['Kill Method'] != '')]
print(f"\nTotal rows with Kill Method: {len(rows_with_method)}")

if len(rows_with_method) >= 3:
    sample_rows = rows_with_method.sample(n=3, random_state=42)
    for idx, (i, row) in enumerate(sample_rows.iterrows(), 1):
        print(f"\n--- Sample {idx} ---")
        question = str(row.get('Question', 'N/A'))
        print(f"Question: {question[:150]}")
        
        method_text = str(row.get('Kill Method', 'N/A'))
        print(f"Kill Method (first 200 chars):\n{method_text[:200]}")
        
        # Quick relevance check
        question_words = question.lower().split()[:5]
        method_lower = method_text.lower()
        matching_words = [w for w in question_words if len(w) > 3 and w in method_lower]
        relevance = "YES - appears relevant" if matching_words else "UNCLEAR - limited word overlap"
        print(f"Relevance check: {relevance}")
else:
    print(f"WARNING: Only {len(rows_with_method)} rows with method text found")

# ============================================================================
# 2. Find rows with local file references (looking for .md file patterns)
# ============================================================================
print("\n" + "="*80)
print("CHECK 2: Rows with potential Local File references")
print("="*80)

base_path = r"D:\GitHub\crawl4ai\bible_contradictions_HUD"
print(f"\nBase path: {base_path}")
print(f"Checking if base path exists: {os.path.exists(base_path)}")

# Look for columns that might contain file references
print(f"\nSearching for .md file references in dataframe...")
found_files = 0
file_samples = []

for col_idx, col in enumerate(df.columns):
    for row_idx, val in enumerate(df[col]):
        if val and isinstance(val, str) and '.md' in val:
            found_files += 1
            if len(file_samples) < 3:
                file_samples.append((col, val, row_idx + 2))  # +2 for header and 0-indexing

if file_samples:
    print(f"\nFound {found_files} references to .md files")
    print("\nVerifying file existence:")
    for col_name, filename, row_num in file_samples:
        print(f"\n--- File {len(file_samples) - len(file_samples) + 1} ---")
        print(f"Column: {col_name}, Row: {row_num}")
        print(f"Filename from Excel: {filename}")
        
        full_path = os.path.join(base_path, filename)
        exists = os.path.exists(full_path)
        status = "EXISTS" if exists else "NOT FOUND"
        print(f"Full path: {full_path}")
        print(f"Status: {status}")
else:
    print("\nNo .md file references found in the dataset")

# ============================================================================
# 3. Count rows with each column filled
# ============================================================================
print("\n" + "="*80)
print("CHECK 3: Column fill status (non-empty cells per column)")
print("="*80)

print(f"\nTotal rows in dataset: {len(df)}")
print("\nColumn completion rates:")
print("-" * 70)

column_stats = {}
for col in df.columns:
    non_empty = df[col].notna().sum()
    non_empty = non_empty - (df[col] == '').sum()
    percentage = (non_empty / len(df)) * 100
    column_stats[col] = non_empty
    print(f"{col:.<45} {non_empty:>5} rows ({percentage:>6.1f}%)")

# ============================================================================
# 4. Check for multiple data sources (CBC vs SAB indication)
# ============================================================================
print("\n" + "="*80)
print("CHECK 4: Data source verification")
print("="*80)

if 'Source' in df.columns:
    source_counts = df['Source'].value_counts()
    print(f"\nSource distribution:")
    for source, count in source_counts.items():
        print(f"  {source}: {count} rows")
    
    print(f"\nSample rows from different sources:")
    for source in source_counts.index[:2]:
        sample = df[df['Source'] == source].iloc[0]
        print(f"\n--- Source: {source} ---")
        print(f"Question: {str(sample.get('Question', 'N/A'))[:100]}")
        print(f"Scripture: {sample.get('Scripture', 'N/A')}")
        print(f"HUD Code: {sample.get('HUD Code', 'N/A')}")

print("\n" + "="*80)
print("Verification complete!")
print("="*80)
