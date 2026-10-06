# Dependencies And Packages

## Can another GitHub environment install packages?

Yes.

If this repo is pushed to GitHub, another environment can install Python dependencies from:

- `pyproject.toml`
- `requirements.txt` if you add one later

It can also install other packages during setup with:

```bash
pip install -e .
pip install crawl4ai openpyxl requests beautifulsoup4
```

## Important note

This repo is designed to *coordinate* packages, not contain every package directly.

### Likely packages to use around it
- `crawl4ai`
- `openpyxl`
- `requests`
- `beautifulsoup4`
- later maybe `trafilatura`
- later maybe `playwright`

## Recommended setup model

1. clone repo
2. install package dependencies
3. install `crawl4ai` separately or vendor specific parts
4. run scripts from `scripts/`

## Why this matters

Another AI on GitHub can absolutely work with this project, but it needs:

- the dependency list
- the current state
- the specific next task

That is why this handoff bundle exists.
