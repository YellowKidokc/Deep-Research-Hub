# Research Acquisition: working-tool map

## Quick Start Launchers (Repository Root)

### 1. Interactive Deep Research (Choose Folder + Web UI)
- **Launcher**: `D:\GitHub\Research-Acquisition\START_LOCAL_DEEP_RESEARCH.bat`
- **Port**: <http://127.0.0.1:8002>
- **How it works**:
  - Prompts you to pick any folder (Windows Explorer browse dialog, paste path, or hit Enter for `Z:\Theophysics_Vault`).
  - Automatically verifies documents and starts Ollama if needed.
  - Recycles port 8002 cleanly so you can switch folders 24/7 without task-manager friction.
  - Opens browser directly with your chosen folder pre-selected as the source.
  - Runs deep iterative research against your documents without requiring MCP.

### 2. Continuous All-Day Deep Research (24/7 Autonomous Runner)
- **Launcher**: `D:\GitHub\Research-Acquisition\START_CONTINUOUS_ALL_DAY_RESEARCH.bat`
- **Queue file**: `D:\GitHub\Research-Acquisition\gpt-researcher\research_queue.txt`
- **Output reports**: `D:\GitHub\Research-Acquisition\gpt-researcher\outputs\local_research\`
- **How it works**:
  - Prompts for target folder (default: `Z:\Theophysics_Vault`).
  - Reads research topics from `research_queue.txt`.
  - Runs unattended all day long, writing comprehensive research reports with citations directly to disk.
  - You can paste new topics into `research_queue.txt` anytime throughout the day; the runner picks them up automatically.

---

## Canonical Engines & Checkouts

### GPT Researcher (Local Document & Web Engine)
- **Canonical checkout**: `D:\GitHub\Research-Acquisition\gpt-researcher`
- **Primary Vault**: `Z:\Theophysics_Vault`
- **Fixes Applied**:
  - `main.py` configured with `load_dotenv(override=False)` so chosen folder is never overwritten by `.env`.
  - `document.py` upgraded to use `TextLoader` for markdown (avoids `unstructured` crashes), with limits expanded to 5,000 files / 50MB.
  - `app.py` dynamically injects the active chosen folder path into the frontend HTML dropdown.

### Local Deep Research (LDR)
- **Project**: `D:\GitHub\Research-Acquisition\local-deep-research`
- **Launcher**: `START.bat`
- **GUI**: <http://127.0.0.1:5000>
- **Purpose**: Authenticated iterative research, local collections, semantic search with SearXNG.

### Removed Web-Only Checkouts
- `open_deep_research` (LangChain web-only evaluation benchmark; removed).
- `local-deep-researcher` (LangChain web-only scraper; removed).
