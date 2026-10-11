---
rfc: "0079"
title: More freedom for authors in the index
status: Accepted
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-24
discussion: https://github.com/KSAModding/content-manager-design/pull/79
supersedes: []
superseded-by: []
---

# RFC 0079: More freedom for authors in the index

## Summary

The index keeps strict only what protects players: the bytes of a release, the id rules, the ownership proof, the install descriptor, and the images a description may load.
Everything else becomes the author's decision, checked by the index and merged without a steward:

- The verified owner may amend a published release in both directions, not only narrow it.
- A fork can prove ownership through the owner id or the topic.
- A SpaceDock-only listing proves ownership through the GitHub repository its SpaceDock mod names.
- A listing chooses from which version the watcher stamps its older releases.
- The watcher follows edits of the release notes.

This amends [RFC 0031](0031-content-metadata-format.md), [RFC 0033](0033-content-index.md), [RFC 0038](0038-repository-topic-ownership-proof.md) and [RFC 0064](0064-changelog-text.md). No field changes its meaning, so `spec_version` and `snapshot_version` stay at `1`.

## Motivation

The accepted RFCs were written to be safe first.
Several of their rules do not protect a player and only cost an author a new release or a steward a queue item:

- An author whose release works on a newer game build than its `game_max` says cannot say so, because an amendment may only narrow. The only way is a new release with the same bytes under another version.
- KittenExtensionsContinued, a continuation of an abandoned mod, needed a steward because its repository is a fork, and RFC 0033 rejects every fork.
- A listing whose releases are only on SpaceDock always waits for a steward, because RFC 0033 has no proof for SpaceDock.
- The watcher stamps only the newest release when a listing is new, and the back catalogue of a mod stays out of the index unless a steward starts a backfill.
- An author who fixes a typo in the release notes never sees the fix in a client, because RFC 0064 freezes the text after the first fill.

The stewards are few, and every item in their queue delays an author who did nothing wrong.

## Guide-level explanation

| You want to | Today | With this RFC |
|---|---|---|
| Say that a release also works on a newer game build | Publish a new release. | Raise or remove `game_max` of that release with an amendment pull request. It merges itself. |
| Remove a dependency you declared by mistake | Publish a new release. | Remove it with an amendment pull request. |
| Take back a yank | Not possible. | Set `yanked` back with an amendment pull request. |
| List a continuation of an abandoned mod from your fork | A steward decides. | Own the fork, or set the topic, and the listing merges itself under a new id. |
| List a mod that is only on SpaceDock | A steward decides. | Name your GitHub repository as the source code of the SpaceDock mod and prove it as for a GitHub listing. |
| Get your older releases into the index | A steward starts a backfill. | Set `since` under `[releases]`, and the watcher stamps every release from that version on. |
| Fix your release notes | The first text stays. | Edit them on the host, and the watcher copies the new text. |

## Reference-level explanation

### What stays strict

These rules protect players or the game, and this RFC changes none of them:

1. The `version`, `download`, `install` and `release_date` of a stamped release never change, and a version is stamped once (RFC 0031, RFC 0033). A client that verifies `download.sha256` gets the bytes the checks saw.
2. The id rules and the one case-insensitive namespace (RFC 0031), because the id is the folder name the game uses.
3. The ownership proof against the release authority, and the rule that an edit verifies against the authority on the base branch ([RFC 0048](0048-ownership-of-an-edit.md)), because without it anybody can publish updates to another author's players.
4. Path containment and the closed vocabularies of the install descriptor ([RFC 0035](0035-content-install-descriptor.md)), because a manager writes files with the player's rights.
5. A description loads only its own image records, within the limits of [RFC 0058](0058-listing-images-and-dates.md) and [RFC 0065](0065-icon-center-crop.md), because every other image tells a host who reads it.
6. The required `links.forums`.

### Amendments in both directions

RFC 0031 lets a published release accept only amendments that narrow it.
This RFC keeps that class for a steward, and lets the verified owner of the listing also widen what a release claims:

| Field | The owner may |
|---|---|
| `game_min`, `game_min_revision` | Raise or lower. |
| `game_max`, `game_max_revision` | Add, raise, lower or remove. |
| `os` | Add, change or remove. |
| `loader` bounds | Tighten, loosen, add or remove a `min` or `max`. The loader `id` stays. |
| `dependencies` | Add, remove, or change the bounds and the kind of an entry. A derived entry, read from the archive's `mod.toml`, can be tightened and can change its kind, but it cannot be removed, because the loader acts on it. |
| `yanked`, `yanked_reason` | Set and take back. |

Every other field of a release file stays out of reach of an amendment, and the fields the watcher owns, `download.mirrors`, `changelog_text` and any field a later RFC gives to the watcher, stay the watcher's.
The amendment check verifies the result against the schema and the id and version rules as before, so an amendment can still not produce a release that no client can read.

A widening that a steward makes on behalf of an author follows the same table.
A steward's own amendment without the author stays narrowing only, as in RFC 0031, because a steward acts on reports and not on knowledge of the build.

### Forks

RFC 0033 rejects a fork outright, because a fork inherits files and so inherits a marker file.
Only the marker proof depends on files.
The owner id proof and the topic proof of RFC 0038 now accept a fork: the owner id of a fork is the account that forked it, and GitHub does not copy topics to a fork.
The marker proof still rejects a fork.

A fork proves only that its owner controls the fork.
It still needs its own id, because the original listing keeps its id, and moving an existing listing to a fork is a change of authority that RFC 0048 governs.

### SpaceDock listings

The SpaceDock API returns `source_code` for a mod (`/api/mod/<id>`), which only the owner of the SpaceDock mod can set.
A listing whose authority is SpaceDock verifies when that `source_code` is the URL of a GitHub repository, and the pull request author proves control of that repository by any GitHub proof of RFC 0033 and RFC 0038.
The chain is: the SpaceDock owner names the repository, and the pull request author controls the repository.

A SpaceDock mod without `source_code`, or with a URL that is not a GitHub repository, waits for a steward as before.

### Older releases

`[releases]` gets an optional key `since`, a version.
The watcher stamps every release of the authority whose version is at least `since` and has no release file yet, with the same checks as every stamp.
A release that fails its checks is reported in the listing's issue, as today, and does not stop the others.
Without `since`, the watcher stamps as it does today.

Older releases are stamped with the listing facts that stand when they are stamped, so a bound written for the newest release lands on them too.
The owner corrects that with an amendment in either direction.
Lowering `since` later stamps more releases, raising it removes nothing.

### Release notes

RFC 0064 fills `changelog_text` once and freezes it.
The watcher now replaces it when the authority's notes for that release changed, and removes it when they became empty, for every release that the release list it fetches on a tick already carries, so this costs no request.
The rules of RFC 0064 on length, trimming and line endings stay, and a text over the limit is left out as before.
A text that came with a release pull request is changed by the owner with an amendment pull request.

### Relationship to other RFCs

- RFC 0031: the amendment class gains the widening changes of the verified owner, and the sentence "a release file can never become more permissive after publish" holds for steward amendments only.
- RFC 0033: forks and SpaceDock listings gain a proof, and the watcher gains `since`.
- RFC 0038: the topic proof accepts a fork.
- RFC 0064: the text follows the host instead of freezing.

Every document that was valid stays valid and means the same thing.

## Drawbacks

- A release can become more permissive after a player's client read it, so the answer "compatible" can appear where "untested" stood yesterday. The owner states it, and above `game_max` a client only warns anyway.
- A SpaceDock owner who names another person's repository as the source code lets that person list the SpaceDock mod.
- A backfill stamps today's listing facts into old releases until the owner corrects them.
- Release notes can change after a player read them.

## Alternatives

**Keep the rules and let stewards handle the cases.**
Rejected because the stewards are few, and every case above is one where the author already proved who they are.

**Let the author widen through a new release only.**
Rejected because a new release with the same bytes costs the author a tag, costs every player a download, and makes the history longer for no change.

**Accept forks without any proof.**
Rejected because a fork proves nothing about its owner by its files.

## Unresolved questions

- Whether a change of kind on a dependency, such as `required` to `recommends`, needs its own note in the listing's issue so players can see it.
