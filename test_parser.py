"""
test_parser.py
--------------
Standalone sanity check — run this BEFORE launching Streamlit to confirm
your preprocessor.py can read your chat file. This bypasses Streamlit
entirely, so it tells you whether the problem is your code or your setup.

Usage:
    python test_parser.py path/to/your_chat.txt
"""

import sys

import preprocessor


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_parser.py path/to/your_chat.txt")
        sys.exit(1)

    path = sys.argv[1]

    print(f"Reading: {path}")
    with open(path, "rb") as f:
        raw = f.read()
    print(f"File size: {len(raw):,} bytes")
    print(f"First 4 bytes (checking for BOM): {raw[:4]}")

    text = raw.decode("utf-8", errors="ignore")
    print("\nFirst 300 characters of the file:")
    print("-" * 60)
    print(text[:300])
    print("-" * 60)

    print("\nChecking which date pattern matches...")
    for style, pattern in preprocessor._PATTERNS.items():
        import re
        count = len(re.findall(pattern, text))
        print(f"  {style:16s} -> {count} matches")

    print("\nRunning full preprocess()...")
    try:
        df = preprocessor.preprocess(text)
        print(f"\n✅ SUCCESS — parsed {df.shape[0]:,} messages from {df['user'].nunique()} users")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print("\nFirst 5 rows:")
        print(df[["date", "user", "message"]].head())
    except ValueError as exc:
        print(f"\n❌ FAILED: {exc}")


if __name__ == "__main__":
    main()