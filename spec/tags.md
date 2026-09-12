# Curated tags

The tags a client can build a filter from.

[RFC 0031](../rfcs/0031-content-metadata-format.md) keeps `tags` free-form and says a curated vocabulary can come later. This page is that vocabulary.
Nothing changes in the format: a curated tag is a value of `tags` like any other, and free-form tags stay valid next to it.

The list is taken from the thread prefixes of the forum's [Mod Releases](https://forums.ahwoo.com/forums/kitten-space-agency/mod-releases/) section.

## Rules

1. **The vocabulary is per content type.** `mod` and `mod-loader` share the list below. `modpack` uses the same list, because a pack is described by what it bundles. `vehicle` and `save` get their own lists in the RFCs that define those types.
2. **A listing may carry several curated tags, and should carry at least one.** The forum allows one prefix per thread.
3. **Validation warns but never rejects.** A listing without a curated tag gets a note, and so does every tag outside the list, naming this page.
4. **The list grows by pull request, with no RFC per tag.** A new tag needs the schema's form (lowercase words joined by `-`), a one-sentence meaning, and a source: a prefix or section the forum has, or at least three listings that would carry it so that there is "enough demand to make sense".
5. **The machine-readable list lives in the authored index repository as `tags.toml`**, steward-owned like `index-status.toml`, and the snapshot embeds it verbatim as `tags`.

## The list for mods

Taken from the prefixes of the forum's Mod Releases section, which every KSA mod already fits.

| Tag | Forum prefix | Meaning |
|---|---|---|
| `parts` | Parts | New parts, engines and vehicles built from them. |
| `celestial` | Celestial | Changes to the star system: new or changed bodies, orbits or whole systems. |
| `gameplay` | Gameplay | Changes to what the player can do or what happens to the vehicle: mechanics, automation, contracts, multiplayer, physics. |
| `user-interface` | User Interface | Windows, readouts, HUDs and other changes to what the player sees and clicks. |
| `visual` | Visual | Looks without mechanics: models, textures, skins, effects, splash screens. |
| `audio` | Audio | Music and sound. |
| `tools` | Tools | Tools for modders and for reaching the game from outside: patchers, debug menus, telemetry bridges, editor helpers. |
| `library` | none | Code that other content depends on and that does nothing on its own. A client may keep it out of browsing and installs it through dependencies. |

## Prefill

Every listing carries a required `links.forums`, and the listing tool reads the prefix of that thread and maps it by the table above.
SpaceDock offers nothing to map since it has no categories or tags for any game.
A thread without a prefix gives no tag, and the validation note says so.

## What a client does

- Filter chips come from the curated list of the listing's type, read from the snapshot.
- Free-form tags render on the detail page and count in search.

## The machine-readable list

`tags.toml` in the authored index repository, one array of tables per content type:

```toml
spec_version = 1

[[mod]]
tag = "parts"
name = "Parts"
meaning = "New parts, engines and vehicles built from them."
forum_prefix = "Parts"

[[mod]]
tag = "library"
name = "Library"
meaning = "Code that other content depends on and that does nothing on its own."
```

`forum_prefix` is absent where the forum has no prefix.
The snapshot carries the file verbatim as JSON under the top-level key `tags`, an optional field added without a `snapshot_version` bump, per [snapshot.md](snapshot.md).
