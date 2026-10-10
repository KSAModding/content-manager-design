---
rfc: "0092"
title: When a listing was listed
status: Draft
authors: ["@Maximilian-Nesslauer"]
created: 2026-10-09
discussion: https://github.com/KSAModding/content-manager-design/pull/92
supersedes: []
superseded-by: []
---

# RFC 0092: When a listing was listed

## Summary

Every listing and pack entry of the snapshot gets an optional derived field `listed_at`: when it came into the index.
It amends the derived dates of [RFC 0058](0058-listing-images-and-dates.md), so `spec_version` and `snapshot_version` stay at `1`.

## Motivation

A client cannot sort by "recently listed" ([Borea#692](https://github.com/KSAModding/Borea/issues/692)).
`published_at` comes from the release dates, so an old mod that is listed today sorts as old content.

## Reference-level explanation

`listed_at` sits next to `published_at` and `updated_at`, as an ISO 8601 UTC timestamp to the second.

The snapshot builder derives it from the authored repository: the committer time of the oldest commit in the first-parent history of `main` whose tree holds the listing's document or a version of the pack.
It compares ids case-insensitively, so a rename that keeps the id, and a delisting followed by a new listing, keep the first time.
The builder therefore checks out the authored repository with its full history.
A tombstone has no `listed_at`.

A client may sort by `listed_at`, newest first, with a stable tie break such as the name.
An entry without `listed_at` sorts last, and a client does not use `published_at` in its place.

## Drawbacks

- The builder clones the whole history on every build, which is small today.
- A rewrite of the history of `main`, which RFC 0033 keeps for a legal requirement, can move the times it touches.

## Alternatives

- **A date the author writes:** rejected, because a listing could claim to be new forever.
- **The merge time from the GitHub API:** rejected, because it costs requests on every build and misses a direct commit of a steward.
- **The author time of the commit:** rejected, because a rebase merge keeps it, and it can be days before the merge.
