# HTML to Markdown Converter for Philosophy Sites
# Converts downloaded HTML files to clean markdown format

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   HTML to Markdown Converter" -ForegroundColor Cyan
Write-Host "   For Stanford Encyclopedia Philosophy Sites" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Target directory
$targetDir = "O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views"

if (-not (Test-Path $targetDir)) {
    Write-Host "Error: Directory not found: $targetDir" -ForegroundColor Red
    exit 1
}

# Get all HTML files
$htmlFiles = Get-ChildItem $targetDir -Filter "*.html" | Where-Object { $_.Name -notmatch "_links\.html$" }

Write-Host "Found $($htmlFiles.Count) HTML files to convert:" -ForegroundColor Green
foreach ($file in $htmlFiles) {
    Write-Host "  - $($file.Name)" -ForegroundColor Gray
}

Write-Host ""
$confirm = Read-Host "Convert these HTML files to Markdown? (y/n, default: y)"
if ($confirm -eq 'n') {
    Write-Host "Conversion cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Converting HTML files to Markdown..." -ForegroundColor Green

# Create Python conversion script
$convertScript = @"
import os
from pathlib import Path
from bs4 import BeautifulSoup
import re

def html_to_markdown(html_content, title=""):
    """Convert Stanford Encyclopedia HTML to clean markdown"""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract title if not provided
    if not title:
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()

    # Find main content (Stanford Encyclopedia specific)
    main_content = soup.find('div', {'id': 'main-content'}) or \
                   soup.find('div', {'class': 'main-content'}) or \
                   soup.find('div', {'id': 'content'}) or \
                   soup.find('body')

    if not main_content:
        main_content = soup

    # Convert common HTML elements to markdown
    markdown_lines = []

    # Add title
    if title:
        markdown_lines.append(f"# {title}")
        markdown_lines.append("")

    def process_element(element, level=0):
        """Recursively process HTML elements"""
        if element.name is None:  # Text node
            text = element.string
            if text and text.strip():
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text.strip())
                if text:
                    markdown_lines.append(text)
        elif element.name in ['p', 'div']:
            # Paragraphs and divs
            if element.name == 'p' or (element.name == 'div' and element.get('class') and 'paragraph' in ' '.join(element.get('class', []))):
                content = []
                for child in element.children:
                    if child.name is None:
                        content.append(child.string or "")
                    elif child.name in ['em', 'i']:
                        content.append(f"*{child.get_text()}*")
                    elif child.name in ['strong', 'b']:
                        content.append(f"**{child.get_text()}**")
                    elif child.name == 'a' and child.get('href'):
                        content.append(f"[{child.get_text()}]({child.get('href')})")
                    else:
                        content.append(child.get_text())

                paragraph_text = ''.join(content).strip()
                if paragraph_text:
                    markdown_lines.append(paragraph_text)
                    markdown_lines.append("")
        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Headings
            level = int(element.name[1])
            text = element.get_text().strip()
            if text:
                markdown_lines.append(f"{'#' * level} {text}")
                markdown_lines.append("")
        elif element.name == 'ul':
            # Unordered lists
            for li in element.find_all('li', recursive=False):
                text = li.get_text().strip()
                if text:
                    markdown_lines.append(f"- {text}")
            markdown_lines.append("")
        elif element.name == 'ol':
            # Ordered lists
            for i, li in enumerate(element.find_all('li', recursive=False), 1):
                text = li.get_text().strip()
                if text:
                    markdown_lines.append(f"{i}. {text}")
            markdown_lines.append("")
        elif element.name == 'blockquote':
            # Blockquotes
            text = element.get_text().strip()
            if text:
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        markdown_lines.append(f"> {line.strip()}")
                markdown_lines.append("")
        else:
            # Process children
            for child in element.children:
                process_element(child, level)

    # Process the main content
    process_element(main_content)

    # Join lines and clean up
    markdown = '\n'.join(markdown_lines)

    # Clean up excessive newlines
    markdown = re.sub(r'\n\n\n+', '\n\n', markdown)

    return markdown.strip()

def convert_html_files(directory):
    """Convert all HTML files in directory to markdown"""

    html_files = [f for f in os.listdir(directory) if f.endswith('.html') and not f.endswith('_links.html')]

    converted = 0
    failed = 0

    for html_file in html_files:
        html_path = os.path.join(directory, html_file)
        md_file = html_file.replace('.html', '.md')
        md_path = os.path.join(directory, md_file)

        print(f"Converting {html_file}...")

        try:
            # Read HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Convert to markdown
            title = html_file.replace('.html', '').replace('_', ' ')
            markdown_content = html_to_markdown(html_content, title)

            # Save markdown
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"  ✓ Saved {md_file}")
            converted += 1

        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
            failed += 1

    print(f"\nConversion complete!")
    print(f"Converted: {converted}")
    print(f"Failed: {failed}")
    print(f"Files saved to: {directory}")

if __name__ == "__main__":
    target_directory = r"O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views"
    convert_html_files(target_directory)
"@

$convertScript | Out-File -FilePath "temp_convert.py" -Encoding UTF8

# Check if html2text is available, if not install it
Write-Host "Checking for required Python packages..." -ForegroundColor Yellow
try {
    python -c "import html2text" 2>$null
    Write-Host "html2text package found" -ForegroundColor Green
} catch {
    Write-Host "Installing html2text package..." -ForegroundColor Yellow
    python -m pip install html2text
}

# Run the conversion
Write-Host ""
Write-Host "Starting HTML to Markdown conversion..." -ForegroundColor Green
python temp_convert.py

# Cleanup
Remove-Item "temp_convert.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Conversion Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your philosophy files are now available in both formats:" -ForegroundColor White
Write-Host "  📄 HTML files: Original formatted content" -ForegroundColor White
Write-Host "  📝 Markdown files: Clean, readable text" -ForegroundColor White
Write-Host ""
Write-Host "Location: $targetDir" -ForegroundColor Cyan