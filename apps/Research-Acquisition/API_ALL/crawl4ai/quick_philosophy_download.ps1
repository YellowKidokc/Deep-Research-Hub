# Quick Philosophy Sites Downloader
# Simple, pre-configured download to your specified folder

Write-Host "Downloading philosophy sites to: O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views" -ForegroundColor Green
Write-Host ""

# Hard-coded philosophy sites
$philosophySites = @"
Physicalism/Materialism - https://plato.stanford.edu/entries/physicalism/
Idealism - https://plato.stanford.edu/entries/idealism/
Dualism (Cartesian) - https://plato.stanford.edu/entries/dualism/
Neutral Monism - https://plato.stanford.edu/entries/neutral-monism/
Panpsychism - https://plato.stanford.edu/entries/panpsychism/
Emergentism - https://plato.stanford.edu/entries/properties-emergent/
Process Philosophy - https://plato.stanford.edu/entries/process-philosophy/
Classical Theism - https://plato.stanford.edu/entries/classical-theism/
Deism - https://plato.stanford.edu/entries/deism/
Pantheism - https://plato.stanford.edu/entries/pantheism/
Panentheism - https://plato.stanford.edu/entries/panentheism/
Atheistic Naturalism - https://plato.stanford.edu/entries/naturalism/
Nihilism - https://plato.stanford.edu/entries/nihilism/
Existentialism - https://plato.stanford.edu/entries/existentialism/
Determinism (Hard) - https://plato.stanford.edu/entries/determinism-causal/
Eliminative Materialism - https://plato.stanford.edu/entries/materialism-eliminative/
Functionalism - https://plato.stanford.edu/entries/functionalism/
Epiphenomenalism - https://plato.stanford.edu/entries/epiphenomenalism/
Buddhist Metaphysics - https://plato.stanford.edu/entries/buddha/
Advaita Vedanta - https://plato.stanford.edu/entries/advaita-vedanta/
"@

# Save to temp file and read back
$philosophySites | Out-File -FilePath "temp_sites.txt" -Encoding UTF8
$urls = Get-Content "temp_sites.txt" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

Write-Host "Found $($urls.Count) philosophy sites to download" -ForegroundColor Cyan
Write-Host ""

# Create simple Python script
$downloadScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import json

async def download_sites():
    urls = [
        "https://plato.stanford.edu/entries/physicalism/",
        "https://plato.stanford.edu/entries/idealism/",
        "https://plato.stanford.edu/entries/dualism/",
        "https://plato.stanford.edu/entries/neutral-monism/",
        "https://plato.stanford.edu/entries/panpsychism/",
        "https://plato.stanford.edu/entries/properties-emergent/",
        "https://plato.stanford.edu/entries/process-philosophy/",
        "https://plato.stanford.edu/entries/classical-theism/",
        "https://plato.stanford.edu/entries/deism/",
        "https://plato.stanford.edu/entries/pantheism/",
        "https://plato.stanford.edu/entries/panentheism/",
        "https://plato.stanford.edu/entries/naturalism/",
        "https://plato.stanford.edu/entries/nihilism/",
        "https://plato.stanford.edu/entries/existentialism/",
        "https://plato.stanford.edu/entries/determinism-causal/",
        "https://plato.stanford.edu/entries/materialism-eliminative/",
        "https://plato.stanford.edu/entries/functionalism/",
        "https://plato.stanford.edu/entries/epiphenomenalism/",
        "https://plato.stanford.edu/entries/buddha/",
        "https://plato.stanford.edu/entries/advaita-vedanta/"
    ]

    labels = [
        "Physicalism_Materialism",
        "Idealism",
        "Dualism_Cartesian",
        "Neutral_Monism",
        "Panpsychism",
        "Emergentism",
        "Process_Philosophy",
        "Classical_Theism",
        "Deism",
        "Pantheism",
        "Panentheism",
        "Atheistic_Naturalism",
        "Nihilism",
        "Existentialism",
        "Determinism_Hard",
        "Eliminative_Materialism",
        "Functionalism",
        "Epiphenomenalism",
        "Buddhist_Metaphysics",
        "Advaita_Vedanta"
    ]

    output_dir = r"O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(urls)} philosophy sites...")
    print(f"Output directory: {output_dir}")

    async with AsyncWebCrawler(verbose=False) as crawler:
        for i, (url, label) in enumerate(zip(urls, labels), 1):
            print(f"[{i}/{len(urls)}] Downloading {label}...")

            try:
                result = await crawler.arun(url=url)

                if result.success:
                    # Save markdown
                    md_file = output_path / f"{label}.md"
                    md_file.write_text(result.markdown, encoding='utf-8')
                    print(f"  Saved markdown: {md_file.name}")

                    # Save HTML
                    html_file = output_path / f"{label}.html"
                    html_file.write_text(result.html, encoding='utf-8')
                    print(f"  Saved HTML: {html_file.name}")
                    print("  SUCCESS")
                else:
                    print(f"  FAILED: {result.error_message}")

            except Exception as e:
                print(f"  ERROR: {str(e)}")

            # Small delay between downloads
            await asyncio.sleep(2)

    print(f"\nComplete! Files saved to {output_dir}")

asyncio.run(download_sites())
"@

$downloadScript | Out-File -FilePath "temp_quick_download.py" -Encoding UTF8

# Run the download
Write-Host "Starting download..." -ForegroundColor Green
python temp_quick_download.py

# Cleanup
Remove-Item "temp_quick_download.py" -ErrorAction SilentlyContinue
Remove-Item "temp_sites.txt" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Download complete!" -ForegroundColor Green
Write-Host "Check your folder: O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views"