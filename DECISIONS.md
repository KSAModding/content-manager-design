# Decisions

Newest first, one row per accepted RFC. This table answers "what did we decide". The RFC itself answers "why".

| Date | RFC | Decision |
|---|---|---|
| 2026-08-07 | [0031](rfcs/0031-content-metadata-format.md) | The standard metadata specifications for content. Mainly focuses on Mods and Mod Packs with small mentions of Game Saves, Vehicles, and Mod Loaders. The metadata specifications for Mods are one authored file, many versioned files. The metadata specifications for Mod Packs are every version is on file. Game Saves, Vehicles, and Mod Loaders are still undecided. |
| 2026-08-04 | [0025](rfcs/0025-scope.md) | The project is a content manager covering mods, mod packs, vehicles, and saves, with the content type a required metadata field from day one; the index is our own on free infrastructure, StarMap stays an external dependency, Borea is the implementation, and the repository is renamed to match. |
| 2026-08-03 | [0017](rfcs/0017-game-version-ordering-and-compatibility.md) | KSA releases are ordered by their revision alone; a mod's compatibility is a revision range with a required lower bound and an optional open upper bound. |
