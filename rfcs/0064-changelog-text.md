---
rfc: "0064"
title: Changelog text in release files
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-15
discussion: https://github.com/KSAModding/content-manager-design/pull/64
supersedes: []
superseded-by: []
---

# RFC 0064: Changelog text in release files

## Summary

A release file gets an optional `changelog_text`: the release notes as CommonMark, copied by the watcher from the release host, or supplied on the release pull request of a listing that has no watched host.
`changelog` keeps its meaning, the URL of the changelog.
A client shows the text from the snapshot, offline, and shows the link when the text is absent.
`spec_version` and `snapshot_version` stay at `1`.

## Motivation

[RFC 0031](0031-content-metadata-format.md) defines `changelog` as a URL, and the watcher stamps the page of the release: the GitHub release page, or the SpaceDock mod page.
A client can therefore only offer a link, and a player who wants to know what an update changes opens a browser once per release.

A client cannot simply fetch that URL.
The page is HTML, and the release notes as text come only from host-specific API calls, with their rate limits: GitHub allows 60 unauthenticated requests an hour for each address.
Every request also tells the host the reader's address, and it breaks the one-fetch offline contract of [RFC 0033](0033-content-index.md).

The text is already in the data the watcher reads.
The GitHub release object carries `body` next to `tag_name`, `published_at` and `html_url`, and the SpaceDock version object carries `changelog`.
On 2026-09-15 the GitHub release notes of the listed mods were between 0 and 11,551 bytes long, and SpaceDock's `changelog` for AdvancedFlightComputer 0.7.5 held the same text as its GitHub release.

## Guide-level explanation

### For an author

Nothing changes.
Write your release notes on GitHub or SpaceDock, and the watcher copies them into the index when it stamps the release.
Notes you edit after that do not reach the index, and the link still leads to the current page.
If your listing has no `[releases]` section, put the notes into the release pull request instead.

### For a client

Show `changelog_text` as Markdown next to the release, for example on a version list or before an update.
When it is absent, show `changelog` as a link.

## Reference-level explanation

### The field

| Field | Meaning |
|---|---|
| `changelog_text` | The release notes as CommonMark, at most 16 KiB of UTF-8. Absent when there are no notes, when they are empty, or when they are longer than the limit. |

```json
"changelog": "https://github.com/Maximilian-Nesslauer/KSA-AdvancedFlightComputer/releases/tag/v0.7.5",
"changelog_text": "## Changes\n- Marks the mod as compatible with KSA 2026.9.7.5402."
```

### Where the text comes from

| Authority host | Source |
|---|---|
| GitHub | `body` of the release object. |
| SpaceDock | `changelog` of the version object. |

The watcher takes the text of the release authority only, removes whitespace at both ends, and writes line endings as LF.
A text longer than the limit is left out and not cut, because a cut can break the Markdown and drop what the author put last.
The release file still carries `changelog`, so a client shows the link for that release, as every client does today.

### Why 16 KiB

The limit trades complete notes in the snapshot against the size that every client downloads whole.
On 2026-09-15 the listed GitHub repositories had 165 releases.
Their notes had a median of 610 bytes, 90 percent were at most 1,413 bytes, two were longer than 4 KiB, one was longer than 8 KiB (11,551 bytes, a generated list of changes), and none was longer than 16 KiB.
So 16 KiB keeps the notes of every release seen today, and no single release can add more than 16 KiB to a snapshot that held 16 releases in 122 KB on the same day.
A limit of 8 KiB would drop one of these notes, and 4 KiB two, for a small saving.
A higher limit would in my opinion grow the download of every client too much.

### Text on a release pull request

A listing without `[releases]` gets its releases through release pull requests (RFC 0033), and no host can be read for its notes.

- **Who:** only the release pull request that creates the release file can carry `changelog_text`. That pull request passes the same ownership check as the rest of the release, so the text comes from the verified owner of the listing or from a steward.
- **Status:** authoritative. From the merge on, it is the release's `changelog_text` like a copied one, and the rules below apply to it.
- **The watcher:** it does not poll a listing without `[releases]`, so it never replaces this text. If the listing later names a host in `[releases]`, the watcher may fill the field only into release files of that listing that still have none.
- **The checks:** a string, not empty after whitespace at both ends is removed, at most 16 KiB of UTF-8, with LF line endings. They cannot compare it with a host.

A release that the watcher stamps never carries author-supplied text.

### When the field may change

A release file either has `changelog_text` or has not.

| Change | Rule |
|---|---|
| Present when the release file is created | Allowed: copied by the watcher from the authority, or supplied on a release pull request. |
| Absent, later present | Allowed once, only as a commit by the watcher, and only when the listing names that host as its authority in `[releases]`, the host still lists the release under the same normalized version, and its notes are not empty and within the limit. |
| Present, later a different text | Never. |
| Present, later absent | Never, through the watcher or a pull request. Text that has to go is handled by the moderation path of RFC 0033. |

The fill uses the release list the watcher already fetches on a tick, so it costs no extra request, and a release file that already has the field is not checked again.
Notes longer than the limit stay absent, and they can still be filled later if the author shortens them on the host.
The watcher commits the fill directly, like `download.mirrors` in RFC 0033.
The amendment check rejects every pull request that adds, changes or removes `changelog_text` in an existing release file.
So after the first present value, the text is frozen, like the `listing` block of RFC 0031: display history, not an amendable surface.

### Client behavior

- A client renders `changelog_text` with the rules of `description`. A changelog has no image records, so by rule 3 of [RFC 0058](0058-listing-images-and-dates.md) a client shows no image from it. Links stay links.
- A client shows `changelog` as a link when `changelog_text` is absent, and may show both.
- The text never affects resolution, installation, compatibility or ownership.

### Snapshot

The builder copies release files verbatim, so `changelog_text` reaches the snapshot with no change to the builder or to [the snapshot specification](../spec/snapshot.md).

### Relationship to other RFCs

This adds an optional field to the release file of RFC 0031 and changes no existing field, so `spec_version` stays at `1`.
It adds one field to the watcher's post-publish additions in RFC 0033.
The `changelog` of a pack version, which is already a URL or free text, does not change.

## Drawbacks

- The snapshot grows, because every release carries its notes. On 2026-09-15 the snapshot held 16 releases in 122 KB, served as 13 KB compressed, and the 165 releases of the listed GitHub repositories carried 122 KB of notes together, 755 bytes each on average. In the snapshot these notes would add about 32 KB after compression, which is more than twice the compressed size of the snapshot today.
- Notes edited after the first fill never reach the index, so the text and the host page can differ.
- The index republishes author text next to the release, which falls under the same moderation path as `description`.

## Alternatives

**Clients fetch the notes from the host APIs.**
Rejected because every client would repeat host-specific code under its own rate limit, send the reader's address to the host, and lose the offline contract.

**Widen `changelog` to a URL or text, as packs already allow.**
Rejected because it changes the meaning of an existing release field, and a release could no longer carry both the link and the text.

**A generated document refreshed on a schedule, like the download counts of RFC 0052.**
It would follow notes edited later.
Rejected for now because release notes rarely change, and a schedule costs requests for every release on every refresh.

**Cut a long text at the limit.**
Rejected because a cut can break the Markdown and hide the end of the notes.

## Unresolved questions

- None.

## Future possibilities

- A client can list the changelogs of every skipped release before an update with no request at all.
- A scheduled refresh of edited notes, if authors ask for it.
