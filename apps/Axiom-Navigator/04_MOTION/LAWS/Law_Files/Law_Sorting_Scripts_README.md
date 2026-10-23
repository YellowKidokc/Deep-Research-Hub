---
id: MO-1345
phase: motion
role: map
depends_on: []
authority: human
status: draft
---

# Law Document Sorting Scripts

This collection of PowerShell scripts helps organize your law-related documents into appropriate folders based on explicit law number mentions. Each script offers different levels of functionality to suit your needs.

## Available Scripts

### 1. Sort_Laws_By_Pattern.ps1

**Basic sorting script** that organizes documents based on explicit law number mentions in filenames or content.

- Looks for patterns like "Law 1", "Law 2", etc.
- Handles special case of "Law 7B"
- Adds metadata headers to sorted files
- Places files with no law mentions in the Undecided folder

**Use this script when:** You want a simple, straightforward sorting approach that focuses only on explicit law mentions.

### 2. Sort_All_Laws.ps1

**Comprehensive sorting script** that uses multiple methods to determine which law a document belongs to.

- Checks if files are already in law-specific folders
- Looks for law mentions in filenames
- Looks for law mentions in content
- Tracks how each file was categorized
- Adds detailed metadata headers to sorted files

**Use this script when:** You want a more thorough approach that considers file location in addition to content.

### 3. Sort_And_Analyze_Laws.ps1

**Advanced sorting and analysis script** that not only sorts documents but also provides detailed analysis to help with manual organization.

- Performs all the sorting functionality of Sort_All_Laws.ps1
- Generates a sorting summary report
- Analyzes undecided documents and suggests potential categorizations
- Creates content snippets for quick review
- Helps identify which undecided documents might belong to which laws

**Use this script when:** You want the most comprehensive solution that includes analysis and reporting to help with manual organization of remaining documents.

## How to Use

1. Open PowerShell
2. Navigate to the directory containing these scripts
3. Run the desired script:

```powershell
.\Sort_Laws_By_Pattern.ps1
# or
.\Sort_All_Laws.ps1
# or
.\Sort_And_Analyze_Laws.ps1
```

## Directory Structure

These scripts use the following directory structure:

- `.\10 Laws` - Source directory containing unsorted documents
- `.\Raw_Collection\Law_X` - Destination directories for sorted documents
- `.\Undecided` - Directory for documents that couldn't be categorized
- `.\Reports` - Directory for analysis reports (only used by Sort_And_Analyze_Laws.ps1)

## Customization

If you need to modify the scripts for your specific needs, here are some common customizations:

- **Change source or destination directories**: Edit the `$sourceDir`, `$rawCollectionDir`, and `$undecidedDir` variables at the top of each script.
- **Adjust law titles**: Modify the `$lawTitles` hashtable in the `Create-MetadataHeader` function.
- **Change the metadata format**: Edit the `Create-MetadataHeader` function to adjust the format of the metadata headers added to each file.

## Troubleshooting

- **Files not being sorted correctly**: Check if your documents use different formatting for law mentions (e.g., "Law No. 1" instead of "Law 1"). You may need to adjust the regular expressions in the `Get-LawNumber` function.
- **Error accessing files**: Ensure you have read/write permissions for all directories involved.
- **Script runs slowly**: For large document collections, the scripts may take some time to process. The Sort_And_Analyze_Laws.ps1 script will be the slowest due to its additional analysis.

## Notes

- These scripts only process Markdown (.md) files. To include other file types, modify the file filter in the `Get-ChildItem` command.
- The scripts add metadata headers to the sorted files, which includes information about how they were categorized.
- Files are copied to their destination folders, not moved. The original files remain in the source directory.