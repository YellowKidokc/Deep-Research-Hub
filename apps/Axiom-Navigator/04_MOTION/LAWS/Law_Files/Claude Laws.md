---
id: MO-0181
phase: motion
role: node
depends_on: []
authority: human
status: draft
---

# Claude Laws - Quantum-Theological Framework Tools   
   
A suite of non-destructive Python tools for analyzing and organizing your Quantum-Theological Framework in Obsidian.   
   
## Overview   
   
These tools help you analyze, organize, and visualize the connections between your 10 Universal Laws without modifying your original content. All outputs are stored in a dedicated "Claude Laws" folder.   
   
## Features   
   
   
- **Law Indexing**: Create searchable indexes of all your law content   
- **Concept Analysis**: Analyze theological and physics concepts across your framework   
- **Connection Mapping**: Visualize connections between different laws   
- **Master Document Generation**: Combine all laws into comprehensive documents   
- **Obsidian Integration**: Run directly from within Obsidian using Shell Commands   
   
## Installation   
   
1. Download all files to a temporary location   
2. Run `install.py` from within your Obsidian vault:   
       
```bash
    python install.py
```
   
       
3. The installer will:   
   
    - Create a "Claude Laws" folder in your vault   
    - Set up the necessary folder structure   
    - Copy all script files to the right locations   
    - Create configuration files   
    - Check for required Python packages   
   
## Requirements   
   
   
- Python 3.6+   
- Obsidian   
- The following Python packages:   
    - matplotlib   
    - networkx   
    - nltk   
   
## Obsidian Integration   
   
These tools can be run directly from within Obsidian using the "Shell commands" community plugin:   
   
1. Install the "Shell commands" community plugin in Obsidian   
2. Go to Settings > Shell Commands   
3. Add commands following the guide in `Claude Laws/Scripts/obsidian_commands.md`   
   
## Available Tools   
   
### index_laws.py   
   
Creates an index of all content in your 10 Laws folders.   
   
   
- Lists all files, their paths, and metadata   
- Generates both JSON and markdown outputs   
- Useful for navigating and finding content   
   
### analyze_concepts.py   
   
Analyzes theological and physics concepts across your framework.   
   
   
- Identifies key theological concepts (trinity, sin, grace, etc.)   
- Maps physics concepts (quantum mechanics, relativity, etc.)   
- Finds connections between theological and physics concepts   
- Generates visualizations of concept relationships   
   
### generate_master.py   
   
Creates master documents combining all laws.   
   
   
- Generates a comprehensive document with all laws   
- Creates an executive summary of the framework   
- Maintains proper structure with table of contents   
- Removes frontmatter for clean presentation   
   
### find_connections.py   
   
Maps connections between different laws in your framework.   
   
   
- Identifies explicit links between laws   
- Detects implicit mentions of other laws   
- Visualizes the connection network   
- Generates detailed reports of connections   
   
## Folder Structure   
   
After installation, you'll have the following structure:   
   
```
Claude Laws/
├── Scripts/                     # Python scripts
│   ├── index_laws.py
│   ├── analyze_concepts.py
│   ├── generate_master.py
│   ├── find_connections.py
│   ├── config.json
│   └── obsidian_commands.md     # Obsidian setup guide
├── Outputs/                     # All outputs stored here
│   ├── Analyses/                # Concept analysis reports
│   ├── Indexes/                 # Law indexes
│   ├── Visualizations/          # Charts and visualizations
│   └── Master Documents/        # Combined law documents
└── README.md                    # Documentation
```
   
   
## Safety   
   
All tools are designed to be non-destructive:   
   
   
- They only read from your existing vault   
- They never modify your original content   
- All outputs are stored in the Claude Laws folder   
- You can delete the Claude Laws folder at any time without affecting your vault   
   
## Mem0 Integration (Optional)   
   
The tools include optional integration with mem0ai for advanced memory and search capabilities:   
   
1. Install the mem0ai package:   
       
```bash
    pip install mem0ai
```
   
       
2. Set your API key in the config.json file:   
       
```json
    {
        "mem0_enabled": true,
        "mem0_api_key": "your-api-key"
    }
```
   
       
3. Run the tools as normal - they'll automatically detect and use mem0ai when enabled   
       
   
## Troubleshooting   
   
**Missing Packages** If you see errors about missing packages, install them manually:   
   
```bash
pip install matplotlib networkx nltk
```
   
   
**Permission Errors** If you get permission errors running scripts in Obsidian:   
   
1. Make sure Python is in your system PATH   
2. Try running the scripts from a terminal first   
3. Check that the Shell Commands plugin has necessary permissions   
   
**Visualization Errors** If visualizations don't generate:   
   
1. Install matplotlib: `pip install matplotlib`   
2. Install networkx: `pip install networkx`   
3. Try running the script from a terminal to see detailed error messages   
   
## Contact & Support   
   
For questions or issues with the tools, please contact the developer.   
   
   
---   
   
Created by Claude for David Lowe's Quantum-Theological Framework.