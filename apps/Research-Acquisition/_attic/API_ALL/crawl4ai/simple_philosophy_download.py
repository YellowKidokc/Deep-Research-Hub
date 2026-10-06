#!/usr/bin/env python3
"""
Simple philosophy sites downloader using requests instead of Crawl4AI
to avoid Windows console encoding issues.
"""

import requests
from pathlib import Path
import time

def download_philosophy_sites():
    sites = [
        ("Physicalism_Materialism", "https://plato.stanford.edu/entries/physicalism/"),
        ("Idealism", "https://plato.stanford.edu/entries/idealism/"),
        ("Dualism_Cartesian", "https://plato.stanford.edu/entries/dualism/"),
        ("Neutral_Monism", "https://plato.stanford.edu/entries/neutral-monism/"),
        ("Panpsychism", "https://plato.stanford.edu/entries/panpsychism/"),
        ("Emergentism", "https://plato.stanford.edu/entries/properties-emergent/"),
        ("Process_Philosophy", "https://plato.stanford.edu/entries/process-philosophy/"),
        ("Classical_Theism", "https://plato.stanford.edu/entries/classical-theism/"),
        ("Deism", "https://plato.stanford.edu/entries/deism/"),
        ("Pantheism", "https://plato.stanford.edu/entries/pantheism/"),
        ("Panentheism", "https://plato.stanford.edu/entries/panentheism/"),
        ("Atheistic_Naturalism", "https://plato.stanford.edu/entries/naturalism/"),
        ("Nihilism", "https://plato.stanford.edu/entries/nihilism/"),
        ("Existentialism", "https://plato.stanford.edu/entries/existentialism/"),
        ("Determinism_Hard", "https://plato.stanford.edu/entries/determinism-causal/"),
        ("Eliminative_Materialism", "https://plato.stanford.edu/entries/materialism-eliminative/"),
        ("Functionalism", "https://plato.stanford.edu/entries/functionalism/"),
        ("Epiphenomenalism", "https://plato.stanford.edu/entries/epiphenomenalism/"),
        ("Buddhist_Metaphysics", "https://plato.stanford.edu/entries/buddha/"),
        ("Advaita_Vedanta", "https://plato.stanford.edu/entries/advaita-vedanta/")
    ]

    output_dir = r"O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(sites)} philosophy sites to: {output_dir}")
    print("=" * 60)

    successful = 0
    failed = 0

    for i, (name, url) in enumerate(sites, 1):
        print(f"[{i}/{len(sites)}] Downloading {name}...")
        print(f"  URL: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Save HTML
            html_file = output_path / f"{name}.html"
            html_file.write_text(response.text, encoding='utf-8')
            print(f"  ✓ Saved HTML: {html_file.name}")

            successful += 1
            print("  SUCCESS")
            print(f"    Content size: {len(response.text):,} characters")

        except Exception as e:
            print(f"  ✗ FAILED: {str(e)}")
            failed += 1

        # Delay between downloads to be respectful
        if i < len(sites):
            print("  Waiting 2 seconds...")
            time.sleep(2)

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE!")
    print("=" * 60)
    print(f"Total sites: {len(sites)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(sites)*100):.1f}%")
    print(f"Files saved to: {output_dir}")

if __name__ == "__main__":
    download_philosophy_sites()