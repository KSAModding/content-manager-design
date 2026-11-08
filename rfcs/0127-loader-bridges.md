---
rfc: "0127"
title: Loader bridges
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-11-08
discussion: "https://github.com/KSAModding/content-manager-design/pull/127"
supersedes: []
superseded-by: []
---

# RFC 0127: Loader bridges

## Summary

A mod may carry an optional `[bridge]` table that names a mod loader it runs inside its own `[loader]`, and a manager may then meet a mod's need for that loader through the bridge instead of starting that loader.
It amends the authored file, the release file and the client behavior of [RFC 0031](0031-content-metadata-format.md), and `spec_version` and `snapshot_version` stay at `1`.

## Motivation

Oxidizer runs its mods either as a loader that starts the game or as `Oxidizer.StarMap`, a StarMap mod that runs the same runtime inside StarMap, and both read the same mod folders.
RFC 0031 lets a mod name one `[loader]`, and that loader starts the game, so a mod for Oxidizer today names StarMap and depends on `Oxidizer.StarMap`.
That is false for a player on Oxidizer alone, and a manager cannot offer the mod there.
The mod should name the loader that runs its code, and the setup should say how that loader reaches the game.

## Reference-level explanation

```toml
# Oxidizer.StarMap
[loader]
id = "StarMap"
min = "0.5.0"

[bridge]
loader = "Oxidizer"
```

`[bridge]` is valid only for `type = "mod"` and has one required key, `loader`, the id of a `mod-loader` listing other than the mod's own `[loader]`.
A listing with `[bridge]` must have `[loader]`, and the listing of that loader must have `[provides].launch`, so a bridge always runs inside a loader that starts the game and bridges never chain.
The bridge and the loader it runs must name the same release authority under `[releases]`, and the `content-dir` of both loaders must be the same, so only the loader's author can claim a bridge and a mod lands where the bridge reads it.
The watcher stamps both from the same releases, so the version of a bridge release is the version of the loader it runs, and a mod's `[loader]` bounds apply to the bridge as they apply to that loader.
The watcher stamps `"bridge": { "loader": "<id>" }` into the release file, frozen at release time like `loader`, and a merged edit of `[bridge]` reaches the newest release as [RFC 0081](0081-listing-narrowing.md) says for `[loader]`.

A manager meets each `[loader]` need of an instance either with the loader that starts the instance or with a listed release of a bridge for that loader, in the need's bounds, whose own `[loader]` is the loader that starts the instance.
It installs such a bridge as a required dependency of the mods that need it, and removes it with the last of them.
When several setups meet every need, a manager should take the loader the player chose for the instance, then the setup with the fewest bridges.
When no setup meets every need, the instance needs different loaders, as before.

A manager that does not know `bridge` sees a mod that names its loader, and offers it on that loader alone.

## Drawbacks

- A bridge and its loader must come from one repository and one release.
- A manager chooses a setup instead of reading one, so two managers can start the same instance differently.

## Alternatives

**Loader stand-ins** (drafted by @SafeShows): the standalone loader says it does the work of StarMap with `Oxidizer.StarMap`, so a mod that names StarMap and depends on `Oxidizer.StarMap` installs on Oxidizer alone and mod listings stay as they are.
Rejected because the mod keeps naming a loader it does not need, so a manager must ignore its `[loader]` bounds on Oxidizer and starts StarMap where Oxidizer alone would do; the shared release authority and the `content-dir` check come from that draft.

**`any_of` across loaders in `[loader]`.**
Rejected because every mod would repeat each setup, and a new bridge would need an edit of every mod for it.
