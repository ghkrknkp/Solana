#!/usr/bin/env python3
"""
Convert Substreams CLI output into line-delimited JSON (JSONL) matching:
{"from": "...", "to": "...", "amount": 12345}
"""
import sys
import json
import re

def process_stream(input_file, output_file):
    count = 0
    records = []

    try:
        with open(input_file, "r", encoding="utf-8") as f_in:
            content = f_in.read()

        # Strategy 1: Attempt structured JSON parsing
        # Substreams JSON output often consists of lines of JSON objects or an array
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Check if it has a @data or data or transfers field
                transfers = None
                if isinstance(data, dict):
                    if "@data" in data and isinstance(data["@data"], dict):
                        transfers = data["@data"].get("transfers")
                    elif "data" in data and isinstance(data["data"], dict):
                        transfers = data["data"].get("transfers")
                    elif "transfers" in data:
                        transfers = data.get("transfers")

                if transfers and isinstance(transfers, list):
                    for t in transfers:
                        if "from" in t and "to" in t and "amount" in t:
                            records.append({
                                "from": str(t["from"]),
                                "to": str(t["to"]),
                                "amount": int(t["amount"])
                            })
            except Exception:
                pass

        # Strategy 2: Robust regex fallback across the whole file
        if not records:
            matches = re.finditer(
                r'\{[^{}]*?"from"\s*:\s*"([^"]+)"[^{}]*?"to"\s*:\s*"([^"]+)"[^{}]*?"amount"\s*:\s*"?(\d+)"?[^{}]*?\}',
                content
            )
            for m in matches:
                records.append({
                    "from": m.group(1),
                    "to": m.group(2),
                    "amount": int(m.group(3))
                })

        with open(output_file, "w", encoding="utf-8") as f_out:
            for r in records:
                f_out.write(json.dumps(r) + "\n")
                count += 1

        print(f"Successfully exported {count} transfers to {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)

if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "output/raw_output.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "output/transfers.jsonl"
    process_stream(in_path, out_path)
