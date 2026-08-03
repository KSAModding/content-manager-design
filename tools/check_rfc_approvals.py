#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check that a pull request touching rfcs/ is approved by at least two stewards.

The steward list is read from the "Who decides" section of CHARTER.md.
The rfc workflow runs this on pull_request and pull_request_review events.
For a manual run: GITHUB_TOKEN=<token> PR_NUMBER=<n> python3 tools/check_rfc_approvals.py
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

CHARTER = Path("CHARTER.md")
TEMPLATE = "0000-template.md"
REQUIRED_APPROVALS = 2
STEWARD_LINE = re.compile(r"^- @([A-Za-z0-9-]+)", re.MULTILINE)


def api(path, token):
    request = urllib.request.Request(f"https://api.github.com{path}")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def paged(path, token):
    page = 1
    while True:
        batch = api(f"{path}?per_page=100&page={page}", token)
        yield from batch
        if len(batch) < 100:
            return
        page += 1


def stewards_from_charter():
    """Return the handles listed as '- @handle' under '## Who decides', lowercased."""
    text = CHARTER.read_text(encoding="utf-8")
    start = text.find("## Who decides")
    if start == -1:
        return []
    end = text.find("\n## ", start + 1)
    section = text[start:end] if end != -1 else text[start:]
    return [handle.lower() for handle in STEWARD_LINE.findall(section)]


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "KSAModding/mod-manager-design")
    number = os.environ.get("PR_NUMBER", "")
    if not token or not number:
        print("GITHUB_TOKEN and PR_NUMBER are required")
        return 2

    rfc_files = [
        f["filename"]
        for f in paged(f"/repos/{repo}/pulls/{number}/files", token)
        if f["filename"].startswith("rfcs/") and not f["filename"].endswith(TEMPLATE)
    ]
    if not rfc_files:
        print("no RFC files changed, the approval rule does not apply")
        return 0

    if os.environ.get("PR_IS_DRAFT", "") == "true":
        print("draft pull request, the approval rule is not enforced yet")
        return 0

    stewards = stewards_from_charter()
    if len(stewards) < REQUIRED_APPROVALS:
        print(f"{CHARTER} lists fewer than {REQUIRED_APPROVALS} stewards under 'Who decides', cannot enforce the rule")
        return 1

    author = api(f"/repos/{repo}/pulls/{number}", token)["user"]["login"].lower()

    # Reviews arrive in chronological order; the last APPROVED, CHANGES_REQUESTED,
    # or DISMISSED per reviewer wins. COMMENTED does not change an existing approval,
    # which matches how GitHub itself treats review state.
    state = {}
    for review in paged(f"/repos/{repo}/pulls/{number}/reviews", token):
        login = ((review.get("user") or {}).get("login") or "").lower()
        if login and review["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            state[login] = review["state"]

    approved = sorted(
        login for login, review_state in state.items()
        if review_state == "APPROVED" and login in stewards and login != author
    )

    print(f"RFC files changed: {', '.join(rfc_files)}")
    print(f"steward approvals: {len(approved)} of {REQUIRED_APPROVALS} ({', '.join(approved) or 'none'})")
    if len(approved) >= REQUIRED_APPROVALS:
        return 0

    missing = sorted(set(stewards) - set(approved) - {author})
    print(f"needs approval from {REQUIRED_APPROVALS - len(approved)} more of: {', '.join(missing)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
