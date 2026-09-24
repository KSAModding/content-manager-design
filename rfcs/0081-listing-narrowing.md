---
rfc: "0081"
title: Listing edits reach the newest release
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-23
discussion: https://github.com/KSAModding/content-manager-design/pull/81
supersedes: []
superseded-by: []
---

# RFC 0081: Listing edits reach the newest release

## Summary

A merged listing edit to the compatibility, the loader or the dependencies now reaches the newest release, in both directions.
The watcher applies it as an amendment of the verified owner ([RFC 0079](https://github.com/KSAModding/content-manager-design/pull/79)), once the edit has stood for 24 hours and no newer release came in the meantime.
Older releases keep their stamp, and the comment on the listing pull request says which release an edit reaches.

## Motivation

[RFC 0031](0031-content-metadata-format.md) freezes the authored facts current at release time into each release file, and "editing the authored file affects future releases only".
content-index #114 added a `recommends` dependency on ModMenu to the listing of KSATelemetryOverlay after its newest release, 1.1.1, was stamped, so no player would have got the entry before the next release.
A steward carried it over by hand with the amendment pull request content-index-releases #64.
That is the only way today, and an author who edits the listing does not learn that it is needed.

The listing edit has already passed the ownership check of [RFC 0048](0048-ownership-of-an-edit.md), so it carries the same authority as an amendment by the owner.
With RFC 0079 such an amendment may widen as well as narrow, so the listing edit can simply reach the release it was meant for.

## Guide-level explanation

Edit your listing as before.
At least a day after your last edit, your newest release gets the same change, and older releases keep their stamp.

| You change in the listing | Newest release | Older releases |
|---|---|---|
| Add `recommends` ModMenu | Gets the entry. | Unchanged. |
| Raise or lower `game_min` | Gets the new bound. | Unchanged. |
| Remove a dependency you added by mistake | Loses it. | Unchanged. |

If you edit the listing for a release that is not out yet, tag it within the day or open its release pull request first.
Otherwise the edit reaches the release before it too, and you change it back with another edit or an amendment pull request.
An older release gets a change through an amendment pull request, for example with `tools/amend.py`.

## Reference-level explanation

### Which release

The watcher amends one release per listing, the target: the newest release file by SemVer precedence that is neither yanked nor `dev`.
A `dev` release is left out because RFC 0031 derives that status so that a nightly does not look like a release, and the next nightly replaces it anyway.
An edit is knowledge about the current build, so older releases keep their stamp.

### What is applied

The watcher compares the listing document as it stood when the most recent release of the listing was stamped, yanked and `dev` releases included, with the live document.
Only a change between the two is applied, so an edit that a release was already stamped with never moves on to the release below it, for example after a yank, and an edit made before this RFC takes effect changes nothing.
The watcher applies the change as a stamp would, with the dependency merge of RFC 0031, so a derived entry read from the archive's `mod.toml` stays, as RFC 0079 requires.

Applied are the fields an owner may amend under RFC 0079 that the listing carries: `[compatibility]` with `game_min`, `game_max` and `os`, the bounds of `[loader]` with the same `id`, and `[[dependencies]]`.
A month in `game_min` or `game_max` resolves as in a stamp, and a month that is not over yet waits until it is.
A changed loader `id` is not applied, because RFC 0079 keeps the loader `id` fixed.
The `listing` block stays as RFC 0031 made it, display history of the stamp.

The result goes through the amendment check of an owner's amendment pull request, with the file on the default branch as the base.
A change the check refuses, for example a `game_max` below the release's own `game_min`, is left out and named in the listing's issue, as `Watcher.month_pass` does.

### When

The watcher runs the pass on every tick for every listing that is neither delisted nor `disputed`, with or without `[releases]`, because the authority is the listing edit and not the host.
A dispute contests the ownership this rests on.
A merge to the authored repository already dispatches a tick, so no new trigger is needed, and the pass writes only when the file differs from its result.

An edit waits while one of these holds:

- The last commit that changed the listing document on the default branch is less than 24 hours old. Every further edit starts the time again.
- The generated repository has an open pull request that adds a release file of the listing.

So an edit made for the next release lands in that release, and from then on it is older than the most recent stamp.
The 24 hours are a tuning parameter.

### Authority

The watcher commits the amendment directly, like `download.mirrors` in [RFC 0033](0033-content-index.md) and the changelog fill of [RFC 0064](0064-changelog-text.md).
This adds no new permission:

- A listing edit merges itself only when its ownership verifies against the authority the base branch names (RFC 0048). Every other change to the authored document is merged or pushed by a steward.
- The owner could open the same amendment as a pull request under RFC 0079.
- The watcher writes only under `releases/<id>/` of the listing it read, and only what the amendment check accepts.

### How it is recorded

One commit per release file, like every other watcher write, whose message names the release, the listing commit it read, and each applied change:

```text
Apply the listing of KSATelemetryOverlay to 1.1.1

Listing: KSAModding/content-index@9fe1c0f
- adds the recommends dependency ModMenu
```

The release file gets no new field, and its history is the record, as for `download.mirrors` and `changelog_text`.

### The comment on the listing pull request

When an edit changes `[compatibility]`, `[loader]` or `[[dependencies]]`, the listing check adds one note: which release the change will reach and when, that older releases keep their stamp, and that an amendment pull request can change them.
A changed loader `id` gets its own note, because it reaches only releases stamped after the merge.
Like the other notes of the listing check, it never rejects.

### Relationship to other RFCs

This amends one sentence of RFC 0031: editing the authored file affects future releases and the target release.
It builds on RFC 0079 for the fields and both directions, and it gives the watcher one more write after publish in RFC 0033.
No field is added or changes its meaning, so `spec_version` and `snapshot_version` stay at `1`.

## Drawbacks

- An edit made for a release that is neither tagged within 24 hours nor opened as a release pull request reaches the release before it too, and the author changes it back.
- A listing that stamps a release, `dev` included, soon after most edits seldom gets an edit onto its target, and the owner amends by pull request.
- A release file changes after publish without a pull request of its own, and its audit trail is the watcher's commit plus the listing pull request.

## Alternatives

**Apply the edit to every stamped release.**
Rejected because an edit is knowledge about the current build, and nobody checked it against the older ones.

**Compare the live listing with the target release file.**
Rejected because a release that becomes the target through a yank would get the edits made for the yanked release, and every listing would get all of its older edits on the first tick.

**Apply it on the first tick after the merge.**
Rejected because an author who edits the listing before tagging a release would change the release before it.

**The watcher opens an amendment pull request.**
Rejected because the indexer bot owns no listing, so its pull request could never verify ownership and would always wait for a steward.

## Unresolved questions

- None.
