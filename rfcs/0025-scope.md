---
rfc: 0025
title: "Scope: a content manager for KSA"
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-08-03
discussion: https://github.com/KSAModding/mod-manager-design/pull/25
supersedes: []
superseded-by: []
---

# RFC 0025: Scope: a content manager for KSA

## Summary

This project designs a content manager, not only a mod manager.
One metadata format, one index, and one client covering mods, mod packs, vehicles, and saves.

The content type is a required, first-class field of the metadata format from day one.
The implementation order is mods and mod packs first, vehicles and saves after.

The catalogue is an index of our own definition; SpaceDock and other hosts stay download locations, not the metadata authority.

StarMap stays an external dependency that the manager installs and depends on, not something this project absorbs.
[Borea](https://github.com/KSAModding/Borea) in the KSAModding org is the implementation.
The repository is renamed to match the widened scope.

## Motivation

The metadata format cannot be designed without knowing which content types it must carry, and the index cannot be designed without knowing what it lists.

The pre-RFC discussion ([#13](https://github.com/KSAModding/mod-manager-design/discussions/13)) has converged on answers.
This RFC records them so the format RFC ([#15](https://github.com/KSAModding/mod-manager-design/discussions/15), [#16](https://github.com/KSAModding/mod-manager-design/discussions/16)) and the loader boundary RFC ([#20](https://github.com/KSAModding/mod-manager-design/discussions/20)) can build on settled ground.

## Guide-level explanation

For a user, this should be one application: install mods, assemble and install mod packs, and later fetch vehicles and saves, with dependencies resolving across types, so a vehicle built with modded parts brings the mods it needs.

For a content author, this is one publishing workflow: you declare what type your content is, and identity, versioning, and game compatibility work the same way for every type.

## Reference-level explanation

### Content types

In scope as published content: mods, mod packs, vehicles, saves.
The metadata format carries a required content type field from day one, so widening to a new type later is a format extension, not a format break.

New content types are added by RFC.

The mechanics are shared, which is the argument for handling these together: every type lives under the same user-global root the game derives from `Constants.DocumentsFolderPath` (see [research/ksa-mod-loading.md](../research/ksa-mod-loading.md)), every type needs install, uninstall, and tracking of what came from where, and every type can depend on mods.

### Implementation order

1. Mods and mod packs first.
2. Vehicles and saves second.

Nothing in the first phase may make the second phase a format break, which the required content type field ensures.

### The catalogue

We define our own index format, with the authored/generated split as the main reference (see [research/prior-art-ckan.md](../research/prior-art-ckan.md)).

SpaceDock remains a place content is hosted and downloaded from, but it cannot be the metadata authority: it has no notion of the folder-name identity the game enforces (`Mod.MakeUsing` overwrites any declared id with the folder name), no dependency data, and no loader field.

The index and its automation run on free infrastructure such as GitHub repositories and actions, following the pattern proven by the self-updating `builds.json` in [KSA-CKAN-meta](https://github.com/KSAModding/KSA-CKAN-meta).

### The loader

StarMap is an external dependency.
The manager installs it, expresses dependencies on it, and stays capable of describing other loaders in metadata, including an official one if RocketWerkz ever ships it.
This project does not build, fork, or absorb a loader; rebuilding the only working loader would split the ecosystem.
Where exactly the manager ends and the loader begins is its own decision and stays with the [#20](https://github.com/KSAModding/mod-manager-design/discussions/20) RFC.

### The implementation

[Borea](https://github.com/KSAModding/Borea), transferred into the KSAModding org, is the implementation this repository designs for.
The specification stays implementation-neutral, so other clients can consume the same metadata and index.

### Naming

The repository is renamed from `mod-manager-design` to `content-manager-design`, and the org project is renamed to match.
GitHub redirects the old repository URLs.
In-repo references (README, charter) are updated in a follow-up pull request after acceptance, together with resolving the charter's now-answered open questions.

### Non-goals

- Hosting content files ourselves; downloads come from each release's own host.
- Anything that needs a service somebody has to keep running and paying for.
- Building or absorbing a loader.

## Drawbacks

- Every content type adds surface to the format, the index, the publishing workflow, and the UI. The implementation order and the required type field are the mitigation, not a solution.
- Vehicles and saves may not carry machine-readable dependency data, which would put the burden of declaring dependencies on the publisher (see unresolved questions).

## Unresolved questions

- Whether a vehicle or save file records which mods it needs, or whether the publisher declares that by hand.
- The metadata format itself, including the shared core, the per-type extensions, and where authored metadata lives, inside `mod.toml` or in a file next to it. The StarMap author @KlaasWhite prefers the loader not to carry manager metadata until that is settled. That is the format RFC, folding in #15 and #16.
- The manager/loader boundary in detail (#20).
- Index storage layout and the stable URL clients fetch it from. That belongs to the index RFC.

## Future possibilities

- Multiplayer server content, once the game has it.
- Integration with an official loader or an official mod API, if one appears.
- Further content types by RFC, which the required type field makes cheap.
