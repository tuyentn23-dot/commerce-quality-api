"""Local COD preview: python cli.py sample.json. No network or credentials."""
import argparse
import json
import sys
from pathlib import Path
from core import MAX_BYTES, reconcile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Input exceeds 1 MB')
        result = reconcile(json.loads(raw.decode('utf-8-sig')))
    except (ValueError, OSError):
        print('Input rejected. Check the contract, decimal strings and 1 MB limit.', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
