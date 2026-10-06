# API Key Setup Helper for Crawl4AI
# Interactive script to configure API keys for LLM features

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Crawl4AI - API Key Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Crawl4AI can work WITHOUT API keys for basic crawling!" -ForegroundColor Green
Write-Host "API keys are only needed for advanced LLM extraction features." -ForegroundColor Yellow
Write-Host ""

$setupKeys = Read-Host "Do you want to set up API keys now? (y/n)"

if ($setupKeys -ne 'y') {
    Write-Host ""
    Write-Host "No problem! You can run basic crawling without API keys." -ForegroundColor Green
    Write-Host "Run this script again when you need LLM features." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Supported LLM Providers:" -ForegroundColor Cyan
Write-Host "  1. OpenAI (GPT-4, GPT-3.5)" -ForegroundColor White
Write-Host "  2. Anthropic (Claude)" -ForegroundColor White
Write-Host "  3. Groq (Fast, free tier available)" -ForegroundColor White
Write-Host "  4. Other (via LiteLLM)" -ForegroundColor White
Write-Host ""

# Check if .env exists
$envFile = ".env"
$envExists = Test-Path $envFile

if ($envExists) {
    Write-Host "Found existing .env file" -ForegroundColor Yellow
    $overwrite = Read-Host "Update existing keys? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Keeping existing configuration" -ForegroundColor Green
        exit 0
    }
}

# Create or update .env file
$envContent = @"
# Crawl4AI API Keys Configuration
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

"@

Write-Host ""
Write-Host "Enter API keys (press Enter to skip):" -ForegroundColor Green
Write-Host ""

# OpenAI
$openaiKey = Read-Host "OpenAI API Key"
if (-not [string]::IsNullOrWhiteSpace($openaiKey)) {
    $envContent += "OPENAI_API_KEY=$openaiKey`n"
}

# Anthropic
$anthropicKey = Read-Host "Anthropic API Key"
if (-not [string]::IsNullOrWhiteSpace($anthropicKey)) {
    $envContent += "ANTHROPIC_API_KEY=$anthropicKey`n"
}

# Groq
$groqKey = Read-Host "Groq API Key"
if (-not [string]::IsNullOrWhiteSpace($groqKey)) {
    $envContent += "GROQ_API_KEY=$groqKey`n"
}

# Other providers
Write-Host ""
$addOther = Read-Host "Add other provider keys? (y/n)"
if ($addOther -eq 'y') {
    while ($true) {
        $providerName = Read-Host "Provider name (or press Enter to finish)"
        if ([string]::IsNullOrWhiteSpace($providerName)) {
            break
        }
        $providerKey = Read-Host "$providerName API Key"
        if (-not [string]::IsNullOrWhiteSpace($providerKey)) {
            $envContent += "${providerName}_API_KEY=$providerKey`n"
        }
    }
}

# Save .env file
$envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "✓ API keys saved to .env file" -ForegroundColor Green
Write-Host ""
Write-Host "Note: The .env file is gitignored for security" -ForegroundColor Yellow
Write-Host ""

# Test the configuration
Write-Host "Would you like to test the API connection? (y/n)" -ForegroundColor Cyan
$testApi = Read-Host

if ($testApi -eq 'y') {
    Write-Host ""
    Write-Host "Testing API connection..." -ForegroundColor Yellow
    
    $testScript = @"
import os
from dotenv import load_dotenv

load_dotenv()

print("\nConfigured API Keys:")
print("-" * 40)

providers = {
    'OpenAI': os.getenv('OPENAI_API_KEY'),
    'Anthropic': os.getenv('ANTHROPIC_API_KEY'),
    'Groq': os.getenv('GROQ_API_KEY')
}

for provider, key in providers.items():
    if key:
        masked_key = key[:8] + '...' + key[-4:] if len(key) > 12 else '***'
        print(f"✓ {provider}: {masked_key}")
    else:
        print(f"✗ {provider}: Not configured")

print("-" * 40)
print("\nAPI keys are ready to use!")
"@

    $testScript | Out-File -FilePath "temp_test_keys.py" -Encoding UTF8
    python temp_test_keys.py
    Remove-Item "temp_test_keys.py" -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
