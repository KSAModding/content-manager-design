#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check RFC front matter, and that accepted RFCs are recorded in DECISIONS.md.
"""

import re
import sys
from pathlib import Path

RFC_DIR = Path("rfcs")
DECISIONS = Path("DECISIONS.md")
TEMPLATE = "0000-template.md"

REQUIRED = ("rfc", "title", "status", "authors", "created")
STATUSES = ("Draft", "Proposed", "FCP", "Accepted", "Rejected", "Postponed", "Superseded")
FILENAME = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def front_matter(text):
    """Parse the leading --- block. Returns a dict, or None if it is missing."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            return None
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def main():
    errors = []
    seen = {}
    decisions = DECISIONS.read_text(encoding="utf-8") if DECISIONS.exists() else ""

    for path in sorted(RFC_DIR.glob("*.md")) if RFC_DIR.is_dir() else []:
        if path.name == TEMPLATE:
            continue

        match = FILENAME.match(path.name)
        if not match:
            errors.append(f"{path}: name must look like NNNN-short-title.md")
            continue

        fields = front_matter(path.read_text(encoding="utf-8"))
        if fields is None:
            errors.append(f"{path}: front matter is missing or not closed by ---")
            continue

        for key in REQUIRED:
            if not fields.get(key) or fields[key] == "[]":
                errors.append(f"{path}: front matter is missing '{key}'")

        number = fields.get("rfc", "")
        if not number.isdigit():
            errors.append(f"{path}: 'rfc' must be a number, got '{number}'")
        elif int(number) != int(match.group(1)):
            errors.append(f"{path}: front matter says rfc {int(number)}, the filename says {int(match.group(1))}")
        elif int(number) in seen:
            errors.append(f"{path}: rfc {int(number)} is already used by {seen[int(number)]}")
        else:
            seen[int(number)] = path.name

        status = fields.get("status", "")
        if status not in STATUSES:
            errors.append(f"{path}: status '{status}' is not one of {', '.join(STATUSES)}")
        elif status == "Accepted" and match.group(1) not in decisions:
            errors.append(f"{path}: accepted, but has no row in DECISIONS.md")

        created = fields.get("created", "")
        if created and not ISO_DATE.match(created):
            errors.append(f"{path}: 'created' must be YYYY-MM-DD, got '{created}'")

    if errors:
        print("\n".join(errors))
        return 1

    print(f"checked {len(seen)} RFC(s), all good")
    return 0


if __name__ == "__main__":
    sys.exit(main())
