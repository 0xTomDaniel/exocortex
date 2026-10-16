"""Select from caller-discovered eligible note paths; no GNU shuf dependency."""

import argparse
import json
import random
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("paths", type=Path, help="UTF-8 file, one eligible note path per line")
parser.add_argument("--count", type=int, default=1)
args = parser.parse_args()
if args.count < 1:
    parser.error("count must be positive")
paths = sorted({line.strip() for line in args.paths.read_text().splitlines() if line.strip()})
print(
    json.dumps(
        {"eligible": len(paths), "selected": random.sample(paths, min(args.count, len(paths)))}
    )
)
raise SystemExit(0 if paths else 1)
