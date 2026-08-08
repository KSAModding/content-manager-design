# Decisions

Newest first, one row per accepted RFC. This table answers "what did we decide". The RFC itself answers "why".

| Date | RFC | Decision |
|---|---|---|
| 2026-08-08 | [0031](rfcs/0031-content-metadata-format.md) | One metadata format for every content type, a shared authored core plus per-type extensions; a mod or mod loader is one authored TOML file plus one tooling-stamped JSON file per release, a pack is one authored document per version with exact pins, ids share one global case-insensitive namespace, and a published release accepts only narrowing amendments. The vehicle and save types themselves stay a future RFC. |
| 2026-08-04 | [0025](rfcs/0025-scope.md) | The project is a content manager covering mods, mod packs, vehicles, and saves, with the content type a required metadata field from day one; the index is our own on free infrastructure, StarMap stays an external dependency, Borea is the implementation, and the repository is renamed to match. |
| 2026-08-03 | [0017](rfcs/0017-game-version-ordering-and-compatibility.md) | KSA releases are ordered by their revision alone; a mod's compatibility is a revision range with a required lower bound and an optional open upper bound. |
