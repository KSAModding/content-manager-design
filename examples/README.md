# Example metadata

Real listings in the [RFC 0031](../rfcs/0031-content-metadata-format.md) format, laid out the way the index of [RFC 0033](../rfcs/0033-content-index.md) stores them.
They serve as worked examples for the index tooling, and mock data for the UI work in [Borea#8](https://github.com/KSAModding/Borea/issues/8).

Everything here is a real mod with real release data.

`AdvancedFlightComputer`, `MeasureTools` and `StarMap` are listed in the index today, and their newest documents here are copies of it as examples.

The rest predates the index and was stamped by hand following the watcher procedure from RFC 0033: each archive was downloaded from its release host, the sha256 and sizes were computed from the actual bytes, the derived dependencies were read from the `mod.toml` inside that exact archive, and every `download.mirrors` entry was verified byte-identical against the authority host before being stamped.

## Layout

| Path | Contents |
|---|---|
| `listings/<id>.toml` | One authored document per listing, written by the content author. |
| `releases/<id>/<version>.json` | One generated document per release, stamped by tooling. |
| `packs/<id>/<version>.toml` | One authored document per pack version. Empty until a real pack exists; the worked example lives in RFC 0031. |

## What each example demonstrates

| Listing | Shape |
|---|---|
| `AdvancedFlightComputer` | Code mod with a Markdown `description`, two release hosts with `authority`, a derived optional dependency, and three releases, the older two stamped against an earlier state of the listing. |
| `AutoStage` | Code mod whose archive declares a hard dependency (`Optional = false`), so the derived entry has kind `required`. |
| `AutoRemoveFinishedBurns`, `DeltaVMap` | Minimal code mods: abstract only, no dependencies, for list views that need volume. |
| `MeasureTools` | A long Markdown `description`, next to the short ones. |
| `StageInfo` | `status = "deprecated"` without a successor, a closed compatibility range (`game_max`), and a pinned loader bound. |
| `StarMap` | The `mod-loader` type: single release host, no `[loader]` section, and the RFC 0035 `[install]` and `[provides]` tables, with the resolved `install.target` stamped into the release file. |

Two things are missing on purpose:

- `KittenExtensions` is depended on but not listed, which is the unlisted-dependency case clients must warn about instead of blocking (RFC 0031, client behavior).
- No release is yanked and no amendment is applied, because no real release has needed one yet.
