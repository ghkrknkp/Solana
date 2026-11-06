# One-Click Execution Script for PowerShell
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Solana Substreams Transfer Extractor - One-Click Execution" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Target check
Write-Host "[1/5] Checking WebAssembly target..." -ForegroundColor Yellow
rustup target add wasm32-unknown-unknown

# 2. Build Wasm
Write-Host "[2/5] Compiling Rust to WebAssembly..." -ForegroundColor Yellow
cargo build --target wasm32-unknown-unknown --release

# 3. Pack SPKG
Write-Host "[3/5] Packaging SPKG..." -ForegroundColor Yellow
substreams pack substreams.yaml

# 4. Check API Key
if (-not $env:SUBSTREAMS_API_KEY -and -not $env:SUBSTREAMS_API_TOKEN) {
    Write-Host "Please enter your Pinax API Key:" -ForegroundColor Yellow
    $key = Read-Host
    $env:SUBSTREAMS_API_KEY = $key
}

# 5. Run Substreams
Write-Host "[4/5] Running Substreams for blocks 385870151 - 385870156..." -ForegroundColor Yellow
if (-not (Test-Path "output")) { New-Item -ItemType Directory -Path "output" }
substreams run -e solana.substreams.pinax.network:443 substreams.yaml map_transfers -s 385870151 -t 385870157 -o json | Out-File -Encoding utf8 "output/raw_output.json"

# 6. Format JSONL
Write-Host "[5/5] Formatting output into transfers.jsonl..." -ForegroundColor Yellow
python export_transfers.py output/raw_output.json output/transfers.jsonl

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "EXTRACTION COMPLETE!" -ForegroundColor Green
Write-Host "Output written to output/transfers.jsonl" -ForegroundColor Green
Get-Content output/transfers.jsonl -Head 5
Write-Host "==========================================================" -ForegroundColor Green

