---
rfc: "0091"
title: A stated upper game bound blocks
status: Draft
authors: ["@Maximilian-Nesslauer"]
created: 2026-10-04
discussion: https://github.com/KSAModding/content-manager-design/pull/91
supersedes: []
superseded-by: []
---

# RFC 0091: A stated upper game bound blocks

## Summary

When content states a `game_max` and the installed game is newer than it, the content is Incompatible, and a client blocks it as it blocks a game older than `game_min`.
Content without `game_max` stays Compatible on every newer game, as before.
This amends [RFC 0017](0017-game-version-ordering-and-compatibility.md) and the meaning of `game_max` in [RFC 0031](0031-content-metadata-format.md).
No field is added, and `spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0017 rates a game above a stated `game_max` as Untested, which warns and lets the user install.
But the index uses `game_max` to say that a release should not be used above a build: [RFC 0033](0033-content-index.md) names "a mod found to break at a given game build" as the common case of an amendment, and RFC 0031 lists adding or lowering `game_max` as an amendment that tightens compatibility.
On 2026-10-04, 20 of the 94 release files in content-index-releases carry a `game_max`.
17 of them come from amendments of their owner, who bounded an old release at the last build it was validated on once a newer release took over.

Under RFC 0017 such a bound only warns, so a pack that pins the old release, or a player who picks it on a versions list, still gets it on a game where it may not load.
The one tool the index has to retire a release for newer games does not retire it.
A false Incompatible was judged worse than a false Compatible in RFC 0017, and that stays true for content without an upper bound, which is why an open bound keeps its meaning.
A stated `game_max` is different: someone chose it on purpose, and in practice they chose it because the content breaks above it.

## Guide-level explanation

### For an author

Leave `game_max` out unless your content breaks on newer games, which stays the recommended default.
If you set it, players on a newer game cannot install that release, so do not set it to the newest build you happened to test with.
When a newer game breaks your mod, a `game_max` on the old releases, through an amendment or the listing edit of [RFC 0081](0081-listing-narrowing.md), stops players from installing them, and your fix release with a new `game_min` takes over.

### For a player

A mod whose author or a steward stated that it breaks above your game version shows Incompatible and cannot be installed, with the last game version it supports.

## Reference-level explanation

### Evaluating compatibility

This replaces the evaluation table of RFC 0017.
For an installed revision `r`, a lower bound `min` and an optional upper bound `max`:

| Condition | State |
|---|---|
| no usable `min` | Unknown |
| `r < min` | Incompatible |
| `max` present and `r > max` | Incompatible |
| otherwise | Compatible |

Bounds do not produce Untested anymore.
Incompatible blocks, and Unknown warns and lets the user proceed, as in RFC 0017.
A pack that pins a release follows the state of that release, so a pinned release above its `game_max` makes the pack Incompatible.

### The meaning of `game_max`

The `game_max` row of the `[compatibility]` table of RFC 0031 reads: "Newest game version the content works with. Above it, clients block the content. Absent means no known upper limit, which is the recommended default."
The comment in the example of RFC 0031 that says a client warns above `game_max` no longer applies.

### Checks

The checks of the index add a note, which warns and never rejects, when an authored `game_max` equals the newest game build the index knows, because that usually means "tested with" and blocks the content on the next game update.

## Drawbacks

- A `game_max` that an author meant as "tested with" now blocks players on the next game update, until the author widens it. One listing does this today (`game_min` and `game_max` both at 2026.10.7.5541); its author has to be told before clients follow this RFC.
- A `game_max` that is too low now blocks working content until the owner widens it under [RFC 0079](0079-author-freedom.md), or a steward does on the owner's behalf.
- A pack that pins a release with a `game_max` becomes Incompatible on newer games, so the pack needs a new version that pins newer releases.

## Alternatives

**Keep Untested above `game_max`.**
Rejected, because the index then has no way to stop installs of a release that is known to break.

**Rate a release without `game_max` as Untested on any game newer than its `game_min`.**
Rejected, because at about thirteen game releases a month almost every mod would ask for a confirmation within days, which is the warning fatigue RFC 0017 avoids.
A client can still say, for the game as a whole, that the installed build is newer than the builds it has verified.

**A separate key, such as `game_breaks_at`, next to `game_max`.**
Rejected, because the amendments of the index already write `game_max` with this meaning, and a second key would leave the 20 existing bounds as warnings.
