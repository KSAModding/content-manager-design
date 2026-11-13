---
rfc: "0000"
title: Conflict severity, reasons and index-recorded conflicts
status: Draft
authors: ["@SafeShows"]
created: 2026-11-13
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: Conflict severity, reasons and index-recorded conflicts

## Summary

[RFC 0031](0031-content-metadata-format.md) has a dependency kind `conflict`, "must not be installed together", but never says what a client does with one.
This RFC gives a `conflict` entry a `severity`, `breaks` or `degrades`, and a `reason` for the player.
`breaks` blocks the pair until the player overrides it, and `degrades` warns.
A conflict applies from both sides, whichever listing declares it, may name a mod loader, and may use `any_of`.
Stewards record conflicts that no owner declared in `index-status.toml`, and anyone can propose one there by pull request, with both owners asked first.

`spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0031 says only incompatible blocks, and lists `conflict` among the resolver kinds without saying whether it is an exception.
So one client may refuse a pair that another installs silently, and an author cannot say whether their conflict means "the game does not start" or "both add the same button".

Today one listing of 48 in the snapshot uses the kind: KsaBabel declares a conflict with KsaChinese, without bounds and without a reason.
A player who has KsaChinese and opens KsaBabel learns nothing about why, and a player who opens KsaChinese sees nothing at all, because only KsaBabel's release carries the entry.

Only the owner of the declaring listing can record a conflict.
When two mods break each other and neither author is around, a steward can narrow a release by amendment ([RFC 0079](0079-author-freedom.md)), but has no way to say "these two together" without editing someone's release on their behalf.
StarMap has no notion of incompatibility ([research/starmap.md](../research/starmap.md)), so nothing in `mod.toml` can be derived either.

## Guide-level explanation

**As an author.**
When your mod breaks another, say how badly and why:

```toml
[[dependencies]]
id = "OtherFlightComputer"
kind = "conflict"
severity = "breaks"
max = "2.0.0"
reason = "Both patch FlightComputer.Update, and the game stops at load."
```

Use `breaks` when the pair crashes the game, corrupts a save or stops a mod from loading.
Use `degrades`, or leave `severity` out, when both still run but something is wrong or doubled, such as two translations of the same language.
You can name a mod loader in `id`, or several mods that do the same job in `any_of`.
You change an entry later with a listing edit or an amendment, as any dependency.

**As a player.**
When you install a mod that breaks one you have, the client says so, names who said it and why, and does not install it unless you confirm that you want both anyway.
When the conflict only degrades, the client tells you and asks once.
When installing a mod would pull in a dependency that conflicts with something you have, the client asks you which to keep.
It does not matter which of the two mods declared the conflict: you see it on both.

**As anyone else.**
When you find two mods that break each other and neither listing says so, open a pull request that adds the pair to `index-status.toml`.
The owners of both mods are asked, and a steward decides after a week, or sooner when an owner agrees.

## Reference-level explanation

### The entry

A `[[dependencies]]` entry of kind `conflict` gains two optional keys:

| Key | Meaning |
|---|---|
| `severity` | `breaks` or `degrades`. Absent means `degrades`. |
| `reason` | One sentence, written for the player the client shows it to, at most 200 characters. |

Both are invalid on every other kind.

On a `conflict` entry only:

- `id` may reference content of type `mod` or `mod-loader`. Every other kind keeps `mod` only.
- `any_of` is valid. Each member keeps its own bounds, and the entry matches when any member matches. `severity` and `reason` hold for every member.

`vehicle` and `save` listings already take `conflict` entries by [RFC 0085](0085-vehicles-and-saves.md), and gain the same keys and the same loader rule.

A release R declares a conflict with a release S when one of R's `conflict` entries names S's id, directly or in `any_of`, and S's version is inside that entry's bounds.

Conflict entries are always authored, because `mod.toml` has none to derive.
An owner adds, removes or changes one by amendment in both directions under RFC 0079, and a listing edit reaches the newest release under [RFC 0081](0081-listing-narrowing.md).
A steward's amendment may add an entry or raise `degrades` to `breaks`, which narrows, and nothing else.

### Index-recorded conflicts

`index-status.toml` gains an array of tables, `conflicts`, beside the per-id states of [RFC 0033](0033-content-index.md):

```toml
[[conflicts]]
between = [ { id = "ModA", max = "1.2.0" }, { id = "ModB" } ]
severity = "breaks"
reason = "Both replace the same part template, and the game stops at load."
since = "2026-11-13T00:00:00Z"
```

| Key | Required | Meaning |
|---|---|---|
| `between` | yes | Exactly two tables, each an `id` of a listed `mod`, `mod-loader`, `vehicle` or `save` with optional `min` and `max`. The two ids differ. |
| `severity` | yes | `breaks` or `degrades`. |
| `reason` | yes | As on the entry. An index-recorded conflict always says why. |
| `since` | no | ISO 8601 UTC. |

Releases A and B conflict by the index when one table of `between` matches A and the other matches B.

The snapshot embeds the array verbatim as the optional top-level `conflicts`, as it embeds `tags.toml` as `tags`, so a client reads every index-recorded conflict from one place.

### Proposing one

Anyone may open a pull request that adds a `conflicts` entry.
The path stays owned by the stewards through CODEOWNERS, so nothing merges without one.

- A check comments on the pull request and mentions the owners of both listings by the GitHub account their ownership proof names. An owner on a share host without a linked GitHub account is not mentioned, and the comment says so.
- A steward merges after seven days, or sooner when an owner of either listing approves, or when the pull request shows the failure, such as a game log.
- When an owner records the same conflict in their own listing, a steward removes the index entry, because the author's voice says the same with less indirection.
- An owner who disagrees with an index entry asks for its removal with a pull request or the dispute issue form, and a steward decides.

### What a client does

A client evaluates every conflict among the releases it is about to have in one instance: those installed, and those the player or the resolver has selected.
Two releases conflict when either declares a conflict with the other, or when the index records one between them.
When more than one source says so, the highest severity applies, and the client shows every reason with who said it: the author of which listing, or the index.

| Severity | On install or update |
|---|---|
| `breaks` | Blocked. The client names both releases, the reasons and their sources, and installs only after the player confirms that they want both anyway. |
| `degrades` | A warning with the same information, and one confirmation. |

When resolving would add a release that conflicts with one installed or selected, the resolver does not look for another version by itself.
It stops and asks the player: keep what they have and drop this part of the install, remove the other content, or install both under the rule above.
An update that would create a conflict asks in the same way, and an automatic update never creates one.

A client records an override per instance and per pair of releases, and asks again when either release changes.
A conflict that appears after both are installed, through an amendment or the index, is shown on both in the instance, and nothing is removed or disabled.

A listing's page shows its conflicts from both sides: the entries of its own releases, the entries of other listings that name it, and the index's.
A client finds the other listings' entries in the snapshot, so nothing new is published for them.

This amends the client behavior of RFC 0031: incompatible blocks, and so does a `breaks` conflict, with an override.
A `severity` or a type a client does not know is treated as `breaks`, because guessing low hides a crash.

### Packs

[RFC 0080](0080-pack-claims-and-members.md)'s member check rejects a pack version in which two pinned releases conflict with `breaks`, from either side or by the index, and notes a `degrades` conflict on the pull request without rejecting.
A conflict recorded after a pack version is accepted does not change that version, and a client warns on install.

### What changes elsewhere

- RFC 0031: the keys `severity` and `reason` on a `conflict` entry, a loader as its `id`, `any_of` on it, and the client behavior above.
- RFC 0033: `conflicts` in `index-status.toml`, and the proposal path.
- RFC 0079: a steward's amendment may raise a conflict's severity.
- RFC 0080: the member check uses severity and index-recorded conflicts.
- RFC 0085: the same keys and loader rule on `vehicle` and `save`.
- [spec/snapshot.md](../spec/snapshot.md): the optional top-level `conflicts`.

`spec_version` stays at `1`.
`severity` and `reason` are optional fields an older client ignores, and RFC 0031 never stated whether a conflict blocks, so giving an absent `severity` a meaning settles behavior that was open rather than changing a field.
`snapshot_version` stays at `1`, because `conflicts` is an optional key an older client ignores.

## Drawbacks

- **Existing entries become soft.** KsaBabel's conflict with KsaChinese reads as "must not be installed together" in RFC 0031 and as `degrades` here, until its owner adds `breaks`.
- **An unknown severity blocks.** A future third level would block on every older client, which is the safe side but still a block.
- **The index takes a view on two people's mods.** An index-recorded conflict is a steward's judgment about content neither of them wrote, and a wrong `breaks` takes a working pair away from players until it is removed. The waiting time and the owners' mention are what keep that rare.
- **Steward work grows.** Every proposed conflict is a pull request a steward reads and decides.
- **Owners without GitHub are not asked.** An owner on a share host without a linked GitHub account learns of a proposed conflict only from the host.
- **The resolver asks rather than solves.** A player may be asked a question a resolver could have answered by picking another version.

## Alternatives

- **A second kind, such as `discourages`, beside `conflict`.** Two kinds for one relation, and an author has to know which name means which level.
- **Absent `severity` means `breaks`.** Keeps RFC 0031's wording, but every existing entry would start to block on clients that did not block before, without its author having said how bad the conflict is.
- **Block without override.** Treats an author's or a steward's statement as certain, while RFC 0017 and RFC 0031 both judge a false block worse than a false pass.
- **A new `conflicts.toml` for index-recorded conflicts.** A separate file with its own owners, while `index-status.toml` already holds the index's voice about listings and is already steward-owned.
- **A reverse index in the snapshot.** The builder could attach, to each listing, the entries of others that name it. A client can compute that from the snapshot it already has.
- **Searching for a non-conflicting version.** Hides a choice from the player that may matter to them, such as staying on an older release of a mod they rely on.

## Unresolved questions

- Whether seven days is the right waiting time, and whether a `degrades` proposal should wait longer than a `breaks` one.
- Whether a check should notify an owner on a share host through the host, for example through an API request of [spec/share-host.md](../spec/share-host.md).
- Whether `reason` needs translations once the index has a localization story.
- Whether 200 characters is the right limit for `reason`.

## Future possibilities

- A crash-report path that proposes a conflict when two mods appear together in many reports ([research/mod-crash-report.md](../research/mod-crash-report.md)).
- A client setting that treats `degrades` as `breaks` for players who want a strict instance.
- Conflicts between a mod and a game build range, if a case appears that `game_max` cannot express.
