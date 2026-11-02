---
rfc: "0000"
title: Download counts of a share host
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-11-02
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: Download counts of a share host

## Summary

The signed release list `releases/<type>/<id>.json` of a share host without GitHub storage may carry an optional `downloads` object, and the index reads it once a day into `download-counts.json` as that host's count of the listing and of each version.
It amends the counts of [RFC 0052](0052-static-download-counts.md), [Download counts](0094-share-host.md#download-counts) of [RFC 0094](0094-share-host.md) and the hosts without GitHub storage of [RFC 0104](0104-share-host-conformance.md), and `spec_version` stays at `1`.

## Motivation

ksamods.gg keeps its archives outside GitHub, so its vehicles and saves have no release asset to count, and a client shows no download count for them while it shows one for every mod.
RFC 0094 and RFC 0104 keep it so on purpose: "The host's own counter is never read, so a host cannot inflate a count."
The host already counts each player once a day through rule 36 of [spec/share-host.md](../spec/share-host.md), so the number exists and only the index does not read it.

## Reference-level explanation

```json
"downloads": { "total": 412, "versions": { "1.0.0": 300, "1.1.0": 112 }, "updated": "2026-11-02T04:00:00Z" }
```

`downloads` comes after `releases` and is absent until the host has counted a report.
`total` is the count of the listing, each key of `versions` is a version of the list with its count, every count is a non-negative integer, and `updated` is the time of the count in ISO 8601 UTC.
The host computes the counts only from the reports of rule 36, so it counts each player once a day and never a file fetch, and it never lowers a count.
The object is part of the bytes that rule 22 signs, so a changed count is a changed file that the host signs again.

Once a day the indexer reads the release list of each listing on such a host, only when its signature is valid, and takes `total` as the listing's count and each `versions` entry whose key normalizes to a stamped version of the listing as that version's count, under the host key from `hosts.toml`.
It keeps the highest value it saw for each count, so a count never goes down, which replaces for a share host the RFC 0052 rule that a lower observation replaces the stored value.
A file without a valid signature, or an object or value of the wrong shape, changes no count and the last known values remain, while the releases of the file are read as today.
A version key that is not a stamped release of the listing is ignored, and `updated` is not copied, because RFC 0052 keeps timestamps out of the document.
The snapshot and a client treat the count as a GitHub count: it is a value in `hosts`, part of every `total`, shown and sortable.
A host with GitHub storage keeps the asset counts of RFC 0094, and the index ignores a `downloads` object in its file.

The old rule falls for four reasons.
The host is registered, and its key in `hosts.toml` signs the file, so every count is a statement that the host made and cannot deny.
It counts each player once a day by rule 36, so a player who installs again on the same day adds nothing.
It never counts a file fetch, so a retry, a mirror check or the watcher's own download adds nothing.
A host that inflates a count breaks its registration, so a steward removes it from `hosts.toml` as [What a steward checks](../spec/share-host.md#what-a-steward-checks) says, and its counts leave `download-counts.json` with it.

At acceptance, rule 36 drops its last sentence, a new rule states the `downloads` object, and the drawback of RFC 0104 that such a host shows no download counts no longer holds.

## Drawbacks

- The index cannot check a count, only that the host signed it, so a count is as good as the host's word until a steward sees a break.
- Keeping the highest value hides a host's own correction downward.
- A share host count and a GitHub count measure different things, players a day against file fetches, and one `total` adds them.

## Alternatives

- **Keep the old rule:** rejected, because the vehicles and saves of a host without GitHub storage then never show a count, and a client cannot tell them from content that nobody installed.
- **A counts file of its own next to the release list:** rejected, because it needs its own path, signature and rule, while the release list is already signed, kept per listing and read by the watcher.
- **Clients report installs to the index:** rejected, because [RFC 0025](0025-scope.md) rules out an operated service.
