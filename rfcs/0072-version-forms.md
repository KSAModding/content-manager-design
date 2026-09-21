---
rfc: "0072"
title: Shorter version forms on a release tag
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-21
discussion: https://github.com/KSAModding/content-manager-design/pull/72
supersedes: []
superseded-by: []
---

# RFC 0072: Shorter version forms on a release tag

## Summary

A release tag may name one or two components instead of three.
The index fills the missing components with zero, so `0.5` is stored as `0.5.0` and `1` as `1.0.0`, and the stored `version` stays a full [SemVer 2.0.0](https://semver.org/) version exactly as [RFC 0031](0031-content-metadata-format.md) defines it.
Nothing downstream changes, because every value a client reads is still a normalized triple.
`spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0031 requires the tag itself to parse as SemVer 2.0.0, so a tag with fewer than three components is refused and the release can never be stamped.

That is stricter than what the index needs, and it is refusing real content today.
The Compendium listing carries the tags `0.5`, `0.6`, `0.7`, `0.8` and `0.9`, and the watcher reports each of them as a version that does not parse.
A second mod offered nineteen releases and not one of them could be stamped for the same reason.
Both authors write a version that every reader understands and that orders without any ambiguity.

What the index needs from a version is a total order.
A client asks whether there is a newer release, a dependency bound asks whether a version is inside `min` and `max`, and the snapshot orders the releases of a listing.
`0.5` answers all three the moment it is read as `0.5.0`, so the refusal buys nothing.

This project already resolves a shorter form elsewhere rather than refusing it.
[RFC 0017](0017-game-version-ordering-and-compatibility.md) accepts a game version written as a month, `2026.7`, and resolves it to a revision, because an author writes what the game shows them.
A release tag deserves the same treatment.

The wider argument against SemVer, that its promises about compatibility do not hold and that resolvers built on them fail, does not apply here and is not reopened by this RFC.
This index never derives compatibility from a version number.
RFC 0031 rejected range expressions, its authored dependency bounds are plain inclusive `min` and `max` written by a person, and a dependency derived from a loader section carries no bounds at all.
SemVer is used here as an ordering and never as a promise.

## Guide-level explanation

### For an author

Tag your release the way you already do.
`0.5`, `v0.5`, `1`, `2.3.4` and `1.0.0-rc.1` are all accepted.
The index stores `0.5` as `0.5.0` and `1` as `1.0.0`, and that is the version a player sees in a client and the version a dependency bound is compared against.

Two things follow from that, and both are worth knowing before you pick a tag.

A shorter tag and its filled form are the same version.
If you have already released `0.5`, a later tag `0.5.0` is that same version, and the index refuses it rather than stamping the same version twice.

A tag is still a version and not a name.
A date or a word is not a version, and it is still refused, because nothing can order it against the rest of your releases.

### For a client

Nothing changes.
Every `version` in the index is a normalized SemVer 2.0.0 version, as it was before.

## Reference-level explanation

### What a tag may look like

This replaces the parsing half of the `version` row of RFC 0031, and nothing else in that row.

A tag is read as an optional leading `v`, then one, two or three numeric components separated by `.`, then the optional pre-release and build parts of SemVer 2.0.0.
A numeric component is `0` or a number without a leading zero, as SemVer requires.

| Tag | Stored `version` |
|---|---|
| `2.3.4` | `2.3.4` |
| `v2.3.4` | `2.3.4` |
| `0.5` | `0.5.0` |
| `v1` | `1.0.0` |
| `1.2-rc.1` | `1.2.0-rc.1` |
| `1.2+build.7` | `1.2.0+build.7` |
| `2026.9` | `2026.9.0` |
| `0.5.0.1` | refused, four components |
| `01.2.3` | refused, a leading zero |
| `latest` | refused, not a version |

A missing component is filled with `0` before anything else reads the value.
The pre-release and build parts keep the meaning and the precedence SemVer 2.0.0 gives them, so a filled version orders against every other version by the same rule as before.

`2026.9` is in the table because it is accepted as a version, and it is worth saying plainly that it is not a date to the index.
It is stored as `2026.9.0` and ordered against the other releases of that listing, and it has no relation to a game version, which RFC 0017 governs separately.

### One version, one stamp

RFC 0031 stamps a version exactly once, and that rule now carries the filled form.
Two tags that fill to the same version are the same version, so the second one is refused with the error in front of the author, the way a re-tag with different bytes already is.
The error names both tags, because an author who tagged `0.5` and later `0.5.0` cannot otherwise see why the second one was refused.

### What does not change

- The stored `version` is a full SemVer 2.0.0 version, so `version_scheme` stays `semver` and ordering is unchanged.
- A version that cannot be read as a version at all is still refused at publish time, with the error in front of the author.
- `release_status` is still derived from the host flag and the pre-release part.
- The authored dependency bounds of RFC 0031 are written as versions and compared against the stored value, so an author who writes `min = "0.5"` means `0.5.0`, by the same filling rule.

### The releases that were refused before

An author whose tags were refused has releases the index never stamped.
The watcher moves forward and stamps what appears after the newest release it already stamped, so it does not reach back by itself.
Those releases reach the index through the backfill the index already has, which a steward starts, and this RFC adds no new mechanism for it.

## Drawbacks

- There is more than one way to write the same version, so two authors can tag the same release differently. The stored value is the same, and a client never sees the tag, so the cost is a reader comparing a tag against a version and finding them different.
- An author who wants four components, such as a build counter, is still refused, and this RFC does not help them. That is deliberate, because a fourth component has no defined precedence in SemVer.
- Filling with zero is a decision made for the author. An author who meant `0.5` to name the whole `0.5` line, rather than one release in it, gets a release named `0.5.0`.

## Alternatives

**Keep the rule as it is and ask authors to re-tag.**
It keeps one way to write a version and needs no change at all.
Rejected because it costs every affected author a re-tag of their whole history for a rule that buys the index nothing, and because it turns the first contact a mod author has with the index into a refusal of content that is not wrong.

**Accept any tag and order by the date the host published it.**
It refuses nothing.
Rejected because a version then has no meaning of its own, a dependency bound cannot be evaluated at all, and a release published out of order, which RFC 0033 explicitly allows, would sort wrongly.

**Store the tag as the author wrote it and fill only when comparing.**
The index would then keep what the author typed.
Rejected because every consumer would have to repeat the filling rule, and any consumer that forgot it would order the releases differently from the index.

**Admit a second version scheme through `version_scheme`.**
RFC 0031 leaves that door open for a future RFC.
Rejected for this problem, because these tags are SemVer in every respect except the number of components, and a second scheme would mean two orderings to define and two to implement, for versions that already order.

## Unresolved questions

- Whether the checks should note a shorter tag on a listing, so an author learns the stored form without reading this document. A note costs an author nothing and might prevent the collision between `0.5` and `0.5.0`, and it also adds noise for an author who tags this way on purpose.

## Future possibilities

- A fourth component, if a loader or a mod ever needs one, which would need a precedence rule of its own and therefore its own RFC.
