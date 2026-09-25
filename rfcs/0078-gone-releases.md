---
rfc: "0078"
title: Releases that disappear from their host
status: Accepted
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-22
discussion: https://github.com/KSAModding/content-manager-design/pull/78
supersedes: []
superseded-by: []
---

# RFC 0078: Releases that disappear from their host

## Summary

The watcher notices when a stamped release is no longer on its host, and writes that into the release file itself, as `download.unavailable_since`.
A client stops offering that release for a new install, shows it in the history as no longer downloadable, and never touches an installed copy.
When the same archive appears again, the watcher removes the field.
This answers [content-index-releases#58](https://github.com/KSAModding/content-index-releases/issues/58), and `spec_version` and `snapshot_version` stay at `1`.

## Motivation

The unscience mod builds a release on every commit and keeps only the last five builds on GitHub.
Each build the watcher stamps stays in the index, and after five more commits its `download.url` answers 404.

The watcher does not notice.
`Watcher.check_for_a_swap` compares the size and the URL from the host's release list with the stamped file, and its docstring names the limit: "a deleted asset reads as unchanged".
A release that is gone from the list entirely is never compared at all.

A client verifies `download.sha256`, so no other file is acceptable, and it learns that the file is gone only when the download fails.
By then its resolver has already picked that version, for example for a dependency with a `max` bound, instead of the newest version that still downloads.
A pack that pins that version fails the same way.

## Guide-level explanation

An author may delete old builds whenever they like.
About a day later, clients stop offering a deleted build for new installs and show it as no longer downloadable, players who have it installed keep it, and the watcher names it in the listing's issue.
An author who deleted a build by accident uploads the same archive again, and the release comes back with the next tick.

An author who builds on every commit can keep those builds out of the way from the start.
A GitHub draft release is never indexed, and a version whose pre-release part is `dev` or `nightly`, such as `1.67.0-nightly.3`, is stamped with `release_status` `dev`, so a client does not offer it on the stable channel.
This RFC is for the builds that were published as ordinary releases and deleted later.

## Reference-level explanation

### When the watcher marks a release

A stamped release is **missing** when an answer from the listing's authority host lists no archive at any stamped URL of the release, `download.url` or an entry of `download.mirrors`.
That covers a deleted release, a release turned back into a draft, and a release whose archive asset was deleted.
The asset URLs are part of the release list the watcher already fetches, so this costs no request.

Only a complete answer counts as an observation:

- A host that does not answer, a rate limit, a server error or an answer that does not parse is could-not-evaluate, per [RFC 0033](0033-content-index.md). It neither starts nor ends a wait.
- A repository or mod that the host does not serve at all is the listing-level problem of RFC 0033. It marks no release, so a repository that is briefly private or renamed keeps its releases.
- When the answer is truncated, a stamped release that is not in it is no observation.
- A 304 on the conditional request repeats the previous answer.

The watcher marks a missing release when both are true:

1. Every observation for at least 24 hours found it missing, counted from the first one that did.
2. A GET to each stamped URL, which follows redirects and stops reading after the status, answers 404, 410 or 451, the codes `hosts.download` already treats as a gone archive.

Any other answer to step 2 marks nothing, and the watcher asks again a day later while the release stays missing.
That is the answer for a mirror: a release that the authority dropped while a mirror in `download.mirrors` still serves it is not marked, because a client may use any source whose bytes match `download.sha256` ([RFC 0031](0031-content-metadata-format.md)).

The start of a wait and the time of each confirmation are derived cache, like the ETags of RFC 0033, so losing them only restarts the wait.

### Listings without `[releases]`

The watcher polls no host for them, so once a day it sends the same GET to each stamped URL of their releases.
Such a release is marked when every URL answered 404, 410 or 451 in every request over at least 24 hours.

### The field

`download.unavailable_since` is the ISO 8601 UTC time the watcher marked the release.
It sits in the `download` object next to `mirrors`, because it says something about the download and not about the release: the version, its compatibility and its dependencies stay true.

```json
"download": {
  "url": "https://github.com/meow-sci/unscience/releases/download/v1.66.0/unscience-1.66.0.zip",
  "sha256": "AFB5A4BFA80C5062BC5E08E9A8D54478E995B280E57D494B95F94242FF8D05A8",
  "size": 1348099,
  "content_type": "application/zip",
  "unavailable_since": "2026-09-23T10:24:00Z"
}
```

The watcher writes it with its own commit, like `download.mirrors` and the changelog fill of [RFC 0064](0064-changelog-text.md), and the value does not change while the mark stands.
The release file and its history stay, so the index never forgets that the release existed.

### When the mark goes away

The watcher removes the field when the authority lists an archive at a stamped URL again, when a stamped URL of a listing without `[releases]` answers with a success, or when `Watcher.check_for_a_swap` finds the stamped digest at a new URL and appends it to `download.mirrors`.
Before it removes the field, the watcher downloads the archive once and compares it with `download.sha256`.
Other bytes are a swap, reported as today, and the mark stays.
Any other answer neither adds nor removes the field.

This is the first field that the watcher may remove again after publish.
That does not break the invariant of RFC 0031 that a release file never becomes more permissive, because availability is a fact about a host and not a claim of the release.
For the same reason the field is outside the amendment class: the amendment check rejects every pull request that adds, changes or removes `download.unavailable_since`, so only the watcher writes it.
The checks that re-derive a stamped release file skip the field, as they skip `download.mirrors` and `changelog_text`.

### Telling the author

On the tick the watcher marks a release or removes a mark, and on the first tick a missing release stays unmarked only because a mirror still serves it, it adds one comment that names the versions to the listing's issue.
A mark is a fact, not an error, so it does not keep that issue open.
When no issue is open, the comment goes to the listing's last watcher issue, found by the listing marker, which stays closed.
Only a listing that never had a watcher issue gets a new one, closed in the same tick.

### Snapshot

The snapshot builder copies release files verbatim, so the field reaches clients with no change to the builder or to the [snapshot specification](../spec/snapshot.md).

### Client behavior

- A client does not offer a release with `download.unavailable_since` for a new install or an update, and a resolver does not pick it, as for a yanked release (RFC 0031).
- When that exact version is asked for, by a pack pin or a reinstall, the client warns and names it. It installs the release only from an archive it already holds whose bytes match `download.sha256`.
- The release stays in the version history, shown as no longer downloadable since that date, with `yanked_reason` as well when the author also yanked it.
- A client never changes, removes or disables an installed copy because of the mark.
- The mark never affects compatibility, ownership, moderation, the download counts of [RFC 0052](0052-static-download-counts.md) or the dates of [RFC 0058](0058-listing-images-and-dates.md).

A client that does not know the field offers the release as today, and its download fails as today.

### Relationship to other RFCs

This adds an optional field to the release file of RFC 0031, so `spec_version` stays at `1`, and the snapshot carries it verbatim, so `snapshot_version` stays at `1`.
It adds one field to the watcher's writes after publish in RFC 0033, and it is the first of them that can be removed again.

## Drawbacks

- For at least a day after a deletion, plus a snapshot build, a client still offers the release, and its download fails.
- A release beyond what one scan of the host covers is never marked.
- Every listing without `[releases]` costs one request per stamped URL per day.
- An author who deletes builds on purpose gets one comment per tick that marks one.
- A release file can change back and forth, so its history is less simple to read than before.
- A mirror URL that died stays in `download.mirrors`, which only grows, so a client may try it before it moves on.

## Alternatives

**A generated document next to the release files, as for the download counts of RFC 0052.**
Rejected because availability belongs to the one release it describes and changes rarely, while a separate document needs a join in the snapshot builder, in the specification and in every tool that reads release files.
RFC 0052 chose a separate document because counts change on every refresh, which does not hold here.

**A new `index_status` state.**
Rejected for the reason RFC 0058 gave for dead images: `index_status` is the stewards' moderation voice with a closed set of states, and it names a listing or a pack version, not a release.

**The watcher asks the author to yank.**
Rejected because a yank is the author's permanent statement, a restored archive could never be offered again, and a listing that deletes old builds on purpose would need an amendment pull request for every build.

**Report it in the issue only, like a dead image in RFC 0058.**
Rejected because a gone archive changes which version a resolver may pick, and that is decided before any download starts.

**Check every archive on every tick.**
Rejected because it costs one request per release per tick, while the release list the watcher already fetches carries the answer.

## Unresolved questions

- None.
