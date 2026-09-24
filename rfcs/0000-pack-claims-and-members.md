---
rfc: "0000"
title: Pack claims, members, and outdated packs
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-23
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: Pack claims, members, and outdated packs

## Summary

This RFC amends [RFC 0031](0031-content-metadata-format.md) and [RFC 0033](0033-content-index.md) for mod packs:

- A first pack claim merges itself, first come, first served, as a listing does. A steward no longer accepts it.
- Every pinned mod must be a listed mod, at a stamped release that is not yanked. An unlisted member no longer passes with a warning.
- The pinned set must be complete: every required dependency of a member is pinned too, and no two members conflict.
- A client shows how many members of a pack version have newer releases than the version pins.
- A mod author who asks to leave a pack gets a new pack version without the mod, and a steward retracts the older versions.

## Motivation

RFC 0033 gives a pack id to the first account whose pull request creates `packs/<id>/`, "applied by a steward".
A pack has no release host, so the only fact is who opened the pull request, and `pack_ownership.verify` in content-index already checks that the submitted `owner.json` names that account.
So the steward step is a queue item with nothing to decide.

RFC 0031 lets a pack pin an id that is not listed, and a client only warns.
A client cannot install such a member, so the pack is broken for every player from its first day.

On 2026-09-23 the Ahwoo forums added section 4 "Modpacks" to the Mod Release Rules, and the table below maps it to the format.

## Guide-level explanation

### For a pack author

Open one pull request that adds `packs/<id>/<version>.toml` and `packs/<id>/owner.json` with your GitHub login and account id.
When the checks pass, it merges itself and the id is yours.
Open the pull requests for later versions from the same account.

Pin listed mods at releases that the index has stamped.
When a member has newer releases, test them and publish a new pack version.
When a mod author asks to leave your pack, publish a version without that mod.

### For a mod author

Your mod can be in a pack only when it is listed.
To leave a pack, use the takedown form of the index and name the pack.

## Reference-level explanation

### The forum rules

| Rule | In the index |
|---|---|
| 4.1 Tag the pack as Modpack. | `links.forums` is required as for every listing and names the pack's own thread. Nothing reads the tag automatically. |
| 4.2 Link only, never re-host. | Already true: a pack carries no files, and each member downloads from its own host (RFC 0031). |
| 4.3 List name, version, author, license, download and thread of every mod. | The pin gives id and version. The member's listing gives `name`, `authors`, `license` and `links.forums`, and its release gives `download`. A client can show the list from the snapshot. |
| 4.4 Only mods with their own release thread. | Close: every member must be a listed mod, and every listing has a forums thread. The index does not check that the thread is on the Mod Releases board or that no other listing uses it. |
| 4.5 Publish the source of your own code. | Nothing to check: a pack in `spec_version = 1` carries no files of its own. |
| 4.6 Update or mark outdated, remove on request. | The newer-release count below, and the removal path below. |

### First claims

A pull request is a first pack claim when the base branch has no `packs/<id>/`.
It merges itself when:

- the id is free, by the collision check of RFC 0033,
- it adds `packs/<id>/owner.json` together with at least one version document of that pack,
- `owner.json` names the pull request author by login and numeric account id,
- every other check passes.

For the scope rule of RFC 0033, an added `packs/<id>/owner.json` is part of its pack document when the base branch has no `packs/<id>/`.
Every other change to an owner record is out of scope.

`packs/*/owner.json` leaves CODEOWNERS, because a required code-owner review makes auto-merge unreachable.
A check carries the rule instead: a pull request can add an owner record only with the first version of its pack.
A pull request that changes or deletes an owner record, a handover for example, never merges itself, and a steward merges it.

Later versions verify as content-index does today: against the `owner.json` on the base branch, by numeric account id.
This settles the pack question that [RFC 0048](0048-ownership-of-an-edit.md) left open.

Two first claims of the same id both add `packs/<id>/owner.json`, so after one merges, the other has a conflict and cannot merge.
Two claims whose ids differ only in case can both merge, as two such listings can today.
The checks on `main` then fail and tell the stewards, and the dispute path keeps the claim that merged first.
A contested pack id uses the dispute path of RFC 0033, with the forums thread as the tiebreaker, as for a mod.
Squatting a generic id such as `StarterPack` is an id dispute like any other.

### Members

When a pack version is submitted, every entry in `[[mods]]` must name:

- a listing of type `mod`, in its canonical spelling, that `index-status.toml` does not delist,
- a version of it that has a release file in the generated repository and is not yanked.

The check rejects every other entry and names it.
A member that is `disputed` passes, and a client warns about it.
`[[vehicles]]` and `[[saves]]` follow the same rule with their own types, so a pin there is refused until an RFC defines those types.

The pinned set must also be complete, because a pack is a curated, tested set, and a dependency that a client adds by itself is a release the pack author never tested with it ([content-index#118](https://github.com/KSAModding/content-index/issues/118)):

- Every `required` dependency of a pinned release names another member of the same pack version whose pinned version is inside the dependency's bounds. For an `any_of` entry, one of its members is enough.
- No pinned release has a `conflict` entry that matches another member.
- `optional`, `recommends` and `suggests` entries are not required. A pack author who wants one pins it.

The check reads the dependencies from the stamped release files, so a derived entry counts like an authored one, and it names each missing or conflicting member with the release that needs it.

An accepted pack version never changes.
When a member is later yanked or delisted, the version stays, and a client warns and lets the user proceed, as for a pack that pins a yanked release (RFC 0031).
A delisted member is only a tombstone in the snapshot, so a client installs the other members and names the one it cannot install.

### Newer releases

Next to a pack version, a client shows how many of its mods have newer releases, for example "3 of 12 mods have newer releases".
It counts a pinned mod when its listing in the snapshot has a release that:

- has higher SemVer precedence than the pinned version,
- is not yanked,
- has a `release_status` at least as stable as the pinned release, in the order `stable`, `testing`, `dev`.

The count uses the snapshot only, and it does not depend on the player's game version or instance, so every player sees the same count.
The pins stay: a pack is a tested set, and a client never replaces a pin by itself.

### Removal on a mod author's request

1. The mod author files a takedown that names the pack. A steward checks that the request comes from the owner of the member's listing, by the ownership proof of RFC 0033 or by its forums account.
2. The pack author publishes a version without the mod, through the ordinary pull request.
3. A steward retracts every accepted version of the pack that pins the mod, with one `retracted` entry per version and a reason that names the request.

The steward does step 3 also when the pack author does not answer.
A pack whose versions are all retracted stays listed, and its next version brings it back.
A retracted version stays installed where it is, and a client stops offering it, as for a yanked release.

### Relationship to other RFCs

In RFC 0033 this replaces the steward step for first pack claims, in the pack section and in the list of the residual steward queue, and it widens the scope rule by the owner record of a first claim.
In RFC 0031 the rule that an unlisted pack member warns stays as client behavior, for members delisted later and for other sources, but the index no longer accepts one.
The rules are checks on new submissions, and every document they accept was valid before, so `spec_version` stays at `1`.
The count comes from data the snapshot already carries, so `snapshot_version` stays at `1`, and [the snapshot specification](../spec/snapshot.md) does not change.

## Drawbacks

- A squatter can take a pack id without a human, and the dispute path acts only afterwards. That is the same trade as for mods.
- A pack cannot pin a mod that has a forums thread but no listing, until its author lists it.
- A pack author has to pin the required dependencies of every member, including libraries a player never looks at.
- The owner record is protected by a check that the stewards own, not by a GitHub review rule.

## Alternatives

**Keep the steward step for first claims.**
Rejected because the steward checks the same fact that the check already checks.

**Keep the warning for unlisted members.**
Rejected because such a pack cannot be installed complete by any client.

**An `outdated` flag that the pack author or a steward sets.**
Rejected because it needs work on every member release and goes stale, while the count is exact and costs nothing.

**Delist the whole pack on a removal request.**
Rejected because it takes the other members and the pack's history away from every player.

## Unresolved questions

- Should the index refuse a new pack version that pins a mod whose author asked to leave that pack, instead of a steward retracting it again?
