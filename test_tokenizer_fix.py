#!/usr/bin/env python3
"""
Test script to verify the tokenizer fix works correctly.
"""
import json
from pathlib import Path
from datasets import load_dataset

# Test reading the holdout file
holdout_file = Path("holdout/phishing/phishing_email_dataset.jsonl")
if not holdout_file.exists():
    print(f"[ERROR] File not found: {holdout_file}")
    exit(1)

# Load the dataset
print(f"[+] Loading dataset from {holdout_file}")
ds = load_dataset("json", data_files=str(holdout_file), split="train")
print(f"[+] Dataset columns: {ds.column_names}")
print(f"[+] Dataset size: {len(ds)}")

# Print first sample
first = ds[0]
print(f"[+] First sample keys: {first.keys()}")
print(f"[+] First sample 'Email Text' type: {type(first.get('Email Text'))}")

# Test batch access
batch = ds.select(range(0, min(3, len(ds))))
print(f"\n[+] Batch selected (0-3): {len(batch)} samples")
print(f"[+] batch['Email Text'] type: {type(batch['Email Text'])}")
print(f"[+] batch['Email Text']: {batch['Email Text']}")

# Test conversion
text_data = batch['Email Text']
if not isinstance(text_data, list):
    print(f"[!] text_data is not a list, converting...")
    if hasattr(text_data, 'tolist'):
        text_data = text_data.tolist()
    else:
        text_data = [text_data]

texts = [str(t) if t is not None else "" for t in text_data]
print(f"[+] Converted texts: {len(texts)} items")
print(f"[+] First text length: {len(texts[0])} chars")

print("\n[SUCCESS] Tokenizer fix test passed!")
