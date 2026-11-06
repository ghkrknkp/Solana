#!/usr/bin/env python3
"""
Independent Verification & Quality Assurance Suite
Validates the extracted transfers in output/transfers.jsonl:
1. Schema conformance (exact keys: 'from', 'to', 'amount')
2. Solana Base58 address validation (32-44 characters, valid Base58 alphabet)
3. Non-negative integer transfer amounts
4. Statistical summary of active senders, recipients, and transfer types
"""
import json
import re
import sys

BASE58_ALPHABET = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
OUTPUT_PATH = "output/transfers.jsonl"

def validate_base58_address(address):
    if not isinstance(address, str):
        return False
    if not (32 <= len(address) <= 44):
        return False
    return set(address).issubset(BASE58_ALPHABET)

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION SUITE ON output/transfers.jsonl")
    print("=" * 60)

    total_records = 0
    unique_senders = set()
    unique_recipients = set()
    total_amount_units = 0
    errors = []

    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            # 1. Parse JSON
            try:
                record = json.loads(line)
            except Exception as e:
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue

            # 2. Check exact keys
            keys = set(record.keys())
            expected_keys = {"from", "to", "amount"}
            if keys != expected_keys:
                errors.append(f"Line {line_num}: Unexpected keys {keys}, expected {expected_keys}")
                continue

            src = record["from"]
            dst = record["to"]
            amt = record["amount"]

            # 3. Validate address format
            if not validate_base58_address(src):
                errors.append(f"Line {line_num}: Invalid sender Base58 address: {src}")
            if not validate_base58_address(dst):
                errors.append(f"Line {line_num}: Invalid recipient Base58 address: {dst}")

            # 4. Validate amount
            if not isinstance(amt, int) or amt < 0:
                errors.append(f"Line {line_num}: Invalid amount (must be non-negative integer): {amt}")

            total_records += 1
            unique_senders.add(src)
            unique_recipients.add(dst)
            total_amount_units += amt

    print(f"Total Validated Transfer Records : {total_records:,}")
    print(f"Unique Sender Addresses         : {len(unique_senders):,}")
    print(f"Unique Recipient Addresses      : {len(unique_recipients):,}")
    print(f"Aggregated Transfer Volume Units: {total_amount_units:,}")

    if errors:
        print("\nERRORS DETECTED:")
        for err in errors[:10]:
            print(" -", err)
        if len(errors) > 10:
            print(f" ... and {len(errors) - 10} more errors.")
        sys.exit(1)
    else:
        print("\nVERIFICATION STATUS: 100% PASSED (Zero Schema or Data Violations)")
        print("=" * 60)

if __name__ == "__main__":
    run_verification()
