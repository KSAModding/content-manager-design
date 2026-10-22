---
rfc: "0104"
title: A conformance specification for share hosts
status: Draft
authors: ["@SafeShows"]
created: 2026-10-21
discussion: https://github.com/KSAModding/content-manager-design/pull/104
supersedes: []
superseded-by: []
---

# RFC 0104: A conformance specification for share hosts

## Summary

This RFC adds [spec/share-host.md](../spec/share-host.md), a living checklist that every share host of [RFC 0094](0094-share-host.md) follows and that a steward checks at registration.
It puts hosts without GitHub storage on equal footing with those that have it, and the snapshot embeds `hosts.toml` so that clients learn the registered hosts.

## Motivation

RFC 0094 expects more than one host and a client that shares to any of them, but what an operator has to build is spread through its design.
It does not say what a steward checks before registration, in which order a host writes, or which errors a client handles.
An accepted RFC never changes, and host requirements will change as hosts appear, so the checklist belongs under `spec/`, as `spec/snapshot.md` and `spec/tags.md` do.

## The page

The page holds rules and no reasons.
A rule that RFC 0094 already states is one line with a link to its section, and where the two differ, the page applies.
Rules are numbered once, so a check or a review can cite one, and a removed rule keeps its number.

What it adds to RFC 0094:

- **Registration:** `bot` serves one host only (rule 4), and a steward's checklist with a test upload, and removal from `hosts.toml` for repeated breaks.
- **Publishing:** the order of writes (rule 9), because the watcher rejects a release list entry whose GitHub release does not exist yet. The release list only grows (rule 10), a takedown also removes the entry (rule 18), and every push gets a new attestation (rule 13).
- **The upload API:** the paths, answers and error codes (rules 15 and 16), so a client handles every host the same. A host accepts any `client_id` as a public client, because a registry of clients per host would undo a shared API. The names follow what Borea already implements ([KSAModding/Borea#821](https://github.com/KSAModding/Borea/issues/821)).
- **Hosts without GitHub storage:** signed data files, download rules and succession terms (rules 20 to 35), which stand in for what GitHub storage gives. A key in `hosts.toml` replaces "only a writer of `storage` can place the file", a `410` and a never-reused `url` replace the stable asset URL, and a hand-over of files and domains replaces the transfer of `storage`. Download counts are not replaced, because RFC 0052 never reads a host's own counter.

## How the page changes

A change that binds a registered host, such as a new or stricter rule or a breaking API change, needs an RFC, which states how long registered hosts have to comply.
Any other change is a pull request.

## Changes elsewhere

RFC 0094 is amended:

- It no longer calls GitHub storage the recommended form. A host that does not use GitHub storage is registered on the same terms, by the page.
- `hosts.toml` gains the keys `downloads`, `key` and `retired_keys` for such a host.
- The ownership check verifies the signature of an attestation from `data`, and records the attestation and its signature in its check run output.

The snapshot embeds `hosts.toml` of the authored repository verbatim as `hosts`, as it embeds `tags.toml` as `tags`, because a client never reads the index repositories directly ([RFC 0033](0033-content-index.md)).
[spec/snapshot.md](../spec/snapshot.md) gains the field, and `snapshot_version` stays at `1`, because it is an optional key an older client ignores.

## Drawbacks

- **Two places to read.** RFC 0094 explains, the page binds, and a reader needs both.
- **Key management is new work.** A lost key stops every proof on that host until a steward registers a new one, and a leaked key lets anyone attest changes to its listings until it is retired.
- **A host without GitHub storage is harder to audit.** Signatures prove what the host said, but not that it said the same to every reader, and it shows no download counts.
- **Any `client_id` is accepted.** A host cannot block a client by its id, only accounts.

## Alternatives

- **Leave the rules in RFC 0094.** Every new host requirement would need an RFC that amends it.
- **A conformance test suite instead of a page.** It cannot check a policy or a succession agreement, and needs the page as its source anyway.

## Unresolved questions

- Whether hosts with GitHub storage should sign their data files too, so one ownership check fits both kinds.
- Whether one year of redirects at succession is enough, and what the stewards do when an operator disappears without handing anything over.
- Whether GitHub keeps check run output long enough to serve as the record of rule 30.

## Future possibilities

- A conformance test suite that a steward points at a host and that a host runs in its own CI.
- A request in the API for the listings an account owns, so a client can offer a new version without the player picking the id.
