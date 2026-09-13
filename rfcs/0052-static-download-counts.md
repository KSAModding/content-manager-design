---
rfc: "0052"
title: Static download counts
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-10
discussion: https://github.com/KSAModding/content-manager-design/pull/52
supersedes: []
superseded-by: []
---

# RFC 0052: Static download counts

## Summary

The generated half of the content index gets one static document with the download counts that release hosts report.
It carries combined and per-host totals for each listing and release version.
The indexer refreshes it on a schedule and keeps the last known value when a source becomes unavailable.

The snapshot attaches the data to each listing, so clients can display it and can sort by it.

Counts never affect resolution, compatibility, installation, moderation, or ownership.

Nothing is added to authored documents or stamped release files, and no new repository or service is required.

## Motivation

[RFC 0033](0033-content-index.md) names GitHub and SpaceDock download counts as a possible future static aggregation, while [the snapshot specification](../spec/snapshot.md) excludes them until that aggregation exists.

Both hosts already expose the required values:
GitHub reports `download_count` for each release asset through its [release asset API](https://docs.github.com/en/rest/releases/assets).
SpaceDock reports `downloads` for the mod and each version through `/api/mod/{id}`.

The counts cannot go into stamped release files because [RFC 0031](0031-content-metadata-format.md) makes those files immutable apart from narrow amendments and the mirror exception from RFC 0033.
A separate generated document keeps the changing signal outside the release record and preserves the snapshot's one-fetch contract.

## Guide-level explanation

A client can show one total for a listing, one total for each version, and the contribution from each host.
A missing count means unknown and not zero.

The values count downloads as each host defines them.
They do not identify unique people, installations, active users, or successful launches.

Clients can use the listing total for a popularity sort, but the index defines no ranking formula or featured list.

## Reference-level explanation

### Sources and totals

Counts are collected for `mod` and `mod-loader` listings that declare a host under `[releases]`.
Packs and listings without `[releases]` have no count in this RFC.

Every named host contributes, whether it is the authority or a mirror.

For GitHub, the indexer uses the `download_count` of the archive asset selected by the same rules that select an asset for stamping.
Draft releases are excluded, and the GitHub listing total is the sum of the selected assets from its published releases.

For SpaceDock, the indexer uses the top-level `downloads` value as the host total and each version's `downloads` value as its release count.

A host release contributes to a version after its tag is normalized as SemVer 2.0.0 by the RFC 0031 rule.
A tag that does not parse can contribute to the listing total but has no version entry, so a listing total does not have to equal the sum of its release totals.

Each value is a non-negative integer reported by its host.
The indexer does not estimate missing values or try to identify unique users.

### Generated document

The generated repository carries `download-counts.json` as CC0 metadata.

```json
{
  "spec_version": 1,
  "listings": [
    {
      "id": "AdvancedFlightComputer",
      "total": 1200,
      "hosts": {
        "github": 479,
        "spacedock": 721
      },
      "releases": [
        {
          "version": "0.7.5",
          "total": 40,
          "hosts": {
            "github": 17,
            "spacedock": 23
          }
        }
      ]
    }
  ]
}
```

`spec_version` starts at `1` and versions this generated document.
`listings` is ordered by lowercased id and keeps the authored casing.
`releases` is ordered by descending SemVer precedence, with version text as the stable tie breaker.

Each `total` is the sum of its `hosts` values.
The host keys defined here are `github` and `spacedock`.
An absent listing, host, or version count means unknown.

The aggregate copies no download URLs or other release facts.
The listing id and normalized version are the joins.

### Refresh and retention

The org indexer bot refreshes the document on a schedule and commits only when its bytes change.
The format promises no refresh interval.

A successful observation replaces the stored value, including when the host reports a lower value.
When a host request fails or a later response no longer contains a stored release, asset, or mirror, the last known value remains.
When a listing stops naming a host, its last known contribution remains as a historical count and the indexer stops polling it.

The indexer omits a value until its first successful observation and never substitutes zero for an unavailable value.
An invalid current aggregate makes the refresh fail without replacing it.

The document carries no collection timestamp because changing one without a count change would invalidate snapshot caches for no change in content.

### Snapshot and client behavior

The snapshot builder attaches the matching aggregate entry to each non-delisted listing as an optional `downloads` field and removes the repeated `id`.

```json
"downloads": {
  "total": 1200,
  "hosts": {
    "github": 479,
    "spacedock": 721
  },
  "releases": [
    {
      "version": "0.7.5",
      "total": 40,
      "hosts": {
        "github": 17,
        "spacedock": 23
      }
    }
  ]
}
```

An aggregate entry for an unknown id is an error because it cannot be joined safely.
A delisted listing remains a tombstone without counts.
Disputed and deprecated listings keep their counts, and a yanked release keeps its historical count.

The optional field does not change `snapshot_version`.
The authored and release `spec_version` also stay unchanged because those documents do not change.

A client can display the totals and host values and can sort listings by `downloads.total`.
It must keep listings without a count available and must not use counts for dependency resolution, version selection, compatibility, installation, ownership, or moderation.

## Drawbacks

- The hosts do not measure unique users, and the combined total can count one person several times.
- A total can combine values observed at different times when one host is unavailable.
- Retained values preserve history but do not show their age.
- A host correction can make a total decrease.
- Popularity sorting can make new content harder to discover.

## Alternatives

**Write counts into stamped release files.**
Rejected because the count changes independently of the immutable release record.

**Create another repository.**
Rejected because the generated repository already holds tool-owned index data.

**Let each client fetch the hosts.**
Rejected because every client would repeat the integrations, use its own rate limit, and lose the one-fetch offline contract.

**Run a live statistics service.**
Rejected because RFC 0025 rules out operated infrastructure and static data is sufficient for display and sorting.
