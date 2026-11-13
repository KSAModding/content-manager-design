---
rfc: "0128"
title: Conflict severity, reasons and index-recorded conflicts
status: Draft
authors: ["@SafeShows"]
created: 2026-11-13
discussion: https://github.com/KSAModding/content-manager-design/pull/128
supersedes: []
superseded-by: []
---

# RFC 0128: Conflict severity, reasons and index-recorded conflicts

## Summary

A `conflict` entry of [RFC 0031](0031-content-metadata-format.md) gains an optional `severity`, `breaks` or `degrades`, and an optional `reason`, and stewards may record a `breaks` conflict with evidence in `index-status.toml`.
It amends the entry and client behavior of RFC 0031 and the `index-status.toml` of [RFC 0033](0033-content-index.md), and `spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0031 says a conflict "must not be installed together" but not what a client does with one, so a client may block a pair that another installs with a warning, and an author cannot say whether a conflict stops the game or only doubles a button.
A conflict is carried only by the declaring release, so a client that reads only the releases of the mod being installed shows it from one side.
Only the declaring owner can record a conflict, so two mods that break each other stay unmarked when neither author is around.

## Reference-level explanation

```toml
[[dependencies]]
id = "OtherFlightComputer"
kind = "conflict"
severity = "breaks"
max = "2.0.0"
reason = "Both patch FlightComputer.Update, and the game stops at load."
```

`severity` is `breaks` or `degrades`, and an absent or unknown `severity` means `breaks`, as RFC 0031's wording and today's clients already have it, so an author who wants a warning writes `degrades`.
`reason` is one sentence for the player, at most 200 characters, and both keys are invalid on every other kind.
On a `conflict` entry only, `any_of` is valid, and `id` may name a `mod-loader`, on `mod`, `vehicle` and `save` listings alike.

A conflict that names a loader says the content breaks while that loader is in the instance, whether it starts the game or runs as a bridge of [RFC 0127](https://github.com/KSAModding/content-manager-design/pull/127).
It does not choose a loader: `[loader]` and bridges say which setups can run the content, and a manager drops every setup that contains a conflicting loader.

`index-status.toml` gains an array `conflicts`, which the snapshot embeds as the optional top-level `conflicts`:

```toml
[[conflicts]]
between = [ { id = "ModA", max = "1.2.0" }, { id = "ModB" } ]
reason = "Both replace the same part template, and the game stops at load."
evidence = "https://github.com/example/ModA/issues/12"
```

`between` holds exactly two different listed ids, each with optional `min` and `max`, and `reason` and `evidence` are required.
An index-recorded conflict is always `breaks`, because it is a steward's judgment about two other people's mods, and `evidence` links a game log or a reproduction that shows the failure; a `degrades` conflict is left to the authors.
Anyone may propose one by pull request, a check mentions the owners of both listings, and a steward merges after seven days, or sooner when an owner approves.
A steward removes the entry when an owner declares the same conflict, or when an owner disputes it and the evidence no longer holds.

Two releases conflict when either declares a conflict with the other or the index records one between them, the highest severity applies, and a client shows every reason with its source on both mods.
A client blocks a `breaks` conflict until the player confirms both anyway, warns once for `degrades`, records an override per instance and pair, and asks again when either release changes.
When resolving would add a release that conflicts, a client may pick another version in bounds without the conflict, and asks the player only when none exists; an automatic update never creates a conflict.
A conflict that appears after both are installed is shown, and nothing is removed or disabled.
The pack member check of [RFC 0080](0080-pack-claims-and-members.md) rejects two pinned releases with a `breaks` conflict and notes a `degrades` one.

## Drawbacks

- An unknown future severity blocks on every older client, which is the safe side but still a block.
- A wrong index entry takes a working pair away until it is removed, and only the evidence and the owners' mention keep that rare.
- An owner on a share host without a linked GitHub account is not mentioned on a proposal.

## Alternatives

**Absent `severity` means `degrades`.**
Rejected because it softens every existing entry, such as KsaBabel's conflict with KsaChinese, against RFC 0031's wording and what clients do today.

**Index-recorded `degrades` conflicts, without evidence.**
Rejected because a steward would judge how well two other people's mods work together, which is the authors' call.

**Always asking the player instead of picking another version.**
Rejected because a question the resolver can answer is noise, and the player still sees the choice when no version avoids the conflict.
