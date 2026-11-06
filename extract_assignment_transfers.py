#!/usr/bin/env python3
"""
Official Solana Transfer Extractor for Blocks 385870151 - 385870156
Queries Solana Mainnet RPC for the exact requested blocks,
extracts Native SOL and SPL Token transfers (both top-level and inner CPIs),
filters out failed transactions, and writes to output/transfers.jsonl.
"""
import urllib.request
import json
import time
import os

RPC_URL = "https://api.mainnet-beta.solana.com"
START_BLOCK = 385870151
END_BLOCK = 385870156
OUTPUT_FILE = "output/transfers.jsonl"

def get_block_data(slot):
    payload = {
        "jsonrpc": "2.0",
        "id": slot,
        "method": "getBlock",
        "params": [
            slot,
            {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
                "rewards": False,
                "transactionDetails": "full"
            }
        ]
    }
    req = urllib.request.Request(
        RPC_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "SolanaSubstreamsExtractor/1.0"}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                response = json.loads(res.read().decode("utf-8"))
                if "result" in response and response["result"]:
                    return response["result"]
                elif "error" in response:
                    print(f"Slot {slot} RPC returned error: {response['error']}")
                    if "Slot was skipped" in str(response['error']):
                        return None
        except Exception as e:
            print(f"Attempt {attempt+1} for slot {slot} failed: {e}. Retrying in 2s...")
            time.sleep(2)
    return None

def extract_from_instruction(ix, transfers):
    if not isinstance(ix, dict):
        return
    parsed = ix.get("parsed")
    if not isinstance(parsed, dict):
        return

    ix_type = parsed.get("type")
    # Native SOL transfer, transferWithSeed, or SPL Token transfer / transferChecked
    if ix_type in ("transfer", "transferChecked", "transferWithSeed"):
        info = parsed.get("info", {})
        src = info.get("source")
        dst = info.get("destination")
        # In System Program lamports is used; in SPL Token amount is used
        raw_amt = info.get("lamports", info.get("amount"))

        if src and dst and raw_amt is not None:
            try:
                amt = int(raw_amt)
                transfers.append({
                    "from": str(src),
                    "to": str(dst),
                    "amount": amt
                })
            except (ValueError, TypeError):
                pass

def process_block(block, slot):
    transfers = []
    transactions = block.get("transactions", [])
    print(f"Processing slot {slot}: {len(transactions)} total transactions...")

    for tx in transactions:
        # 1. Skip failed transactions
        meta = tx.get("meta") or {}
        if meta.get("err") is not None:
            continue

        trx = tx.get("transaction") or {}
        message = trx.get("message") or {}

        # 2. Extract top-level instructions
        instructions = message.get("instructions") or []
        for ix in instructions:
            extract_from_instruction(ix, transfers)

        # 3. Extract inner instructions (Cross-Program Invocations / CPIs)
        inner_instructions = meta.get("innerInstructions") or []
        for inner in inner_instructions:
            for ix in inner.get("instructions", []):
                extract_from_instruction(ix, transfers)

    print(f"Slot {slot} completed: extracted {len(transfers)} qualifying transfers.")
    return transfers

def main():
    os.makedirs("output", exist_ok=True)
    all_transfers = []

    print(f"Starting extraction for Solana blocks {START_BLOCK} to {END_BLOCK} (inclusive)...")
    for slot in range(START_BLOCK, END_BLOCK + 1):
        block = get_block_data(slot)
        if block is None:
            print(f"Slot {slot} was skipped or empty on-chain.")
            continue
        transfers = process_block(block, slot)
        all_transfers.extend(transfers)
        time.sleep(0.5)

    print(f"\nTotal extracted transfers across all 6 blocks: {len(all_transfers)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for t in all_transfers:
            # Write exact required JSON format per line
            f.write(json.dumps(t) + "\n")

    print(f"Successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
