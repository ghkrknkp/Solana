#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "Solana Substreams Transfer Extractor - One-Click Execution"
echo "=========================================================="

# 1. Check Rust & WebAssembly Target
echo "[1/5] Checking Rust and WebAssembly target..."
if ! command -v cargo &> /dev/null; then
    echo "ERROR: Cargo is not installed. Please install Rust via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

rustup target add wasm32-unknown-unknown || true

# 2. Check Substreams CLI
echo "[2/5] Checking Substreams CLI..."
if ! command -v substreams &> /dev/null; then
    echo "ERROR: Substreams CLI not found in PATH."
    echo "Install it with: wget https://github.com/streamingfast/substreams/releases/latest/download/substreams_linux_x86_64.tar.gz && tar -xzf substreams_linux_x86_64.tar.gz && sudo mv substreams /usr/local/bin/"
    exit 1
fi

# 3. Build WebAssembly Module & Package SPKG
echo "[3/5] Building WebAssembly binary and SPKG package..."
cargo build --target wasm32-unknown-unknown --release
substreams pack substreams.yaml

echo "Build successful! Generated solana_transfer_extractor-v0.1.0.spkg"

# 4. Check API Key
if [ -z "$SUBSTREAMS_API_KEY" ] && [ -z "$SUBSTREAMS_API_TOKEN" ]; then
    echo "WARNING: Neither SUBSTREAMS_API_KEY nor SUBSTREAMS_API_TOKEN is set!"
    echo "Please export your key, e.g.: export SUBSTREAMS_API_KEY='your_pinax_key'"
    read -p "Enter your Pinax Substreams API Key now: " user_key
    export SUBSTREAMS_API_KEY="$user_key"
fi

# 5. Execute Substreams against Solana blocks 385870151-385870156
echo "[4/5] Streaming transfers for blocks 385870151 to 385870156..."
mkdir -p output
substreams run -e solana.substreams.pinax.network:443 substreams.yaml map_transfers -s 385870151 -t 385870157 -o json > output/raw_output.json

# 6. Format Output to strict JSONL
echo "[5/5] Formatting extracted transfers to output/transfers.jsonl..."
python3 export_transfers.py output/raw_output.json output/transfers.jsonl || python export_transfers.py output/raw_output.json output/transfers.jsonl

echo ""
echo "=========================================================="
echo "EXTRACTION COMPLETE!"
echo "Total transfers extracted:"
wc -l output/transfers.jsonl || true
echo ""
echo "First 5 transfers:"
head -n 5 output/transfers.jsonl || true
echo "=========================================================="
echo "Output saved to output/transfers.jsonl"

