---
rfc: "0110"
title: A forums thread that is gone
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-10-29
discussion: https://github.com/KSAModding/content-manager-design/pull/110
supersedes: []
superseded-by: []
---

# RFC 0110: A forums thread that is gone

Amends [RFC 0033](0033-content-index.md) and answers [#101](https://github.com/KSAModding/content-manager-design/issues/101).
`spec_version` and `snapshot_version` stay at `1`.

## Why

RFC 0033 makes the forums link a tripwire, but nothing reads the thread, so a mod whose thread the moderators removed stays on offer until someone notices.
Ahwoo allowed a daily read of the sitemap and one read of a thread that left it ([#86](https://github.com/KSAModding/content-manager-design/issues/86)).

## Rules

1. Once a day the watcher reads the forum sitemap. A run counts only when the sitemap answers 200, parses, and lacks at most 10 percent of the listed thread ids that the last counted run saw.
2. For a listed thread that the sitemap lacks, it reads the thread once. 200, or a 301 that ends in 200, keeps the listing. A 404 with Ahwoo's page "The requested thread could not be found." is gone. Every other answer is unknown and changes nothing.
3. After three counted runs in a row, at least 20 hours apart, that all found the thread gone, the watcher marks the listing and pings the owner and the stewards in its watcher issue.
4. The first counted run that finds the thread, or a thread that a new `links.forums` names, removes the mark.
5. The mark lives in a generated file `forums-status.json` of the generated index repository, next to `download-counts.json` ([RFC 0052](0052-static-download-counts.md)), as the time of the third run per listing id. The snapshot carries it in each listing as `forums.unavailable_since`. The authored listing never holds it.
6. A client shows a warning, offers neither the listing nor a pack that pins it for a new install, and leaves installed copies alone. A client that does not know the field ignores it.
7. Delisting stays a steward's entry in `index-status.toml`. A banned author, a locked thread, and an unknown answer three runs in a row go to a steward and mark nothing.
