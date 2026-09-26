---
rfc: "0085"
title: Vehicles and saves as content
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-26
discussion: https://github.com/KSAModding/content-manager-design/pull/85
supersedes: []
superseded-by: []
---

# RFC 0085: Vehicles and saves as content

## Summary

The index gets two content types, `vehicle` and `save`, with one document shape: a mod listing without `[loader]`.
A release is an archive on a release host, and the watcher stamps it as it stamps a mod release.
GitHub releases, which most mods use, are not meant for vehicle and save files, so the host comes in an RFC of its own, and the index accepts these listings only once such a host exists.
The mods a vehicle or a save needs are ordinary `[[dependencies]]`, which the client that shares fills from the mods of its instance and the publisher checks.
The client that installs resolves, installs and enables those mods, and then installs the folder in one step.
Vehicles come first, saves second.

This answers design [#71](https://github.com/KSAModding/content-manager-design/issues/71) on the facts in [research/vehicles-and-saves.md](../research/vehicles-and-saves.md), which were verified on game build 2026.9.10.5438.
Every game fact here was checked again on 2026.9.22.5482, and where the builds differ, this RFC follows 2026.9.22.5482.

## Motivation

[RFC 0025](0025-scope.md) puts vehicles and saves in scope and leaves open whether their files record the mods they need.
They do not.
A save or a vehicle names part templates, characters, substances and bodies by bare ids, and no id says which mod provides it (`SerializedId.Mod` is `XmlIgnore`).
A part template or an EVA character that is not installed makes `ModLibrary.Get` throw in `PartTree.Deserialize` or in the `KittenEva` constructor, nothing catches it, and the game ends.
So a shared vehicle that says nothing about its mods is a crash that the player cannot explain.

RFC 0031 already defines the `[[vehicles]]` and `[[saves]]` entries of a pack, and RFC 0035 gives both types the anchor `user-data`.
Only the types themselves are missing.

## Guide-level explanation

**Sharing.**
You choose a vehicle in your client and share it.
The client finds the mods of your instance that the vehicle uses, one entry per mod, without the game's own parts and without the dependencies of those mods.
You check the list, and add what the file cannot show, for example a mod that only changes how parts behave, as `recommends`.

```toml
spec_version = 1
id = "ExampleRover"
type = "vehicle"
name = "Example Rover"
authors = ["Maxi"]
abstract = "A six-wheel rover for the Moon."
license = "CC-BY-4.0"

[links]
forums = "https://forums.ahwoo.com/threads/example-rover.1000/"

[[dependencies]]
id = "ExamplePartsMod"
kind = "required"
min = "1.4.0"
```

The example leaves out `[releases]`, which names the host that the hosting RFC defines.
There is no `[compatibility]` table, because the watcher takes `game_min` from the build in the archive's `meta.toml`.
The archive holds the folder as the game wrote it, named after `name` in its `meta.toml`:

```text
Example Rover/
  meta.toml
  vehicle.xml
```

**Installing.**
Your client installs and enables the mods the vehicle needs, and then the vehicle.
When a required mod cannot be installed, the client names it, says that the game can end, and lets you continue.
When your instance already has a vehicle with that name that the client did not install, the client stops and does not replace it.

## Reference-level explanation

### The types

| Type | Folder under `user-data` | Game file |
|---|---|---|
| `vehicle` | `Vehicles/<name>/` (`VehicleSaves.SaveFolderPath`) | `vehicle.xml` |
| `save` | `saves/<name>/` (`GameSaves.SaveFolderPath`) | `universe.xml` |

Both folders hold a `meta.toml` (`SaveMetaData`).
The casing of `Vehicles` and `saves` matters on a case-sensitive file system.
Both are watched types, as `mod` and `mod-loader` are: an authored document per listing, and a stamped release file per release.

### The authored document

The shared core of RFC 0031, and:

| Part | On `vehicle` and `save` |
|---|---|
| `[releases]` | Names the host of the archive, see Hosting. Without it, releases enter by release pull request (RFC 0033). |
| `[[dependencies]]` | As for a mod, with every kind and `any_of`. A listed `id` must be of type `mod`. |
| `[compatibility]` | Optional. When `game_min` is absent, the watcher stamps it from the archive. |
| `[loader]` | Invalid. |
| `[install]` | Only `root`, `steps` and `uninstall`. |
| `[images]` | As for a mod ([RFC 0058](0058-listing-images-and-dates.md)). |

The id follows RFC 0031 and is in the one global namespace.
It is never compared with `name` in `meta.toml`, because the game takes the identity of a vehicle or save from that `name` (`UncompressedVehicleSave.FromDirectory`, `UncompressedSave.FromDirectory`), and a real name contains spaces, which an id cannot.

### Hosting

The index stays on GitHub, but the archives of vehicles and saves do not, because a player should not need a repository to share a rover.
The host is a new release host kind, defined by its own RFC, in the same way as SpaceDock is one for mods.
It has to give the watcher what a mod host gives it:

- A list of the releases of one vehicle or save, each with a version, a date and one archive.
- A download URL that stays the same for a release, so that `download.sha256` keeps its meaning.
- An account that owns the upload, so that an ownership proof of RFC 0033 can name it.

A listing may name more than one host, and the `authority` and `download.mirrors` rules of RFC 0031 apply, so a client falls back to another host whose archive has the same `sha256`, and a vehicle stays installable when one host stops.
When every host of a release stops, the watcher marks the release as gone ([RFC 0078](0078-gone-releases.md)), and mods and every other listing keep working.

### The dependencies

The authored `[[dependencies]]` are the whole list, because there is no `mod.toml`, and the watcher freezes them with `source = "authored"`.
The defaults: a mod that provides an id the file names is `required`, a mod that leaves no id is at most `recommends`, and every entry has a `min` and no `max`.
A bound matters, because a mod update that removes a part template breaks a vehicle as a missing mod does.
An id that is not listed is a valid entry, and a client warns about it by RFC 0031's rule for an unlisted dependency.

A client that shares:

1. Reads the ids the file names, from the elements in the research's table "The content a file names".
2. Maps each id to the installed and enabled mod that defines it. An id from `Content/Core` needs no entry. When two mods define the same id, it names both and the publisher chooses (the game keeps the first, `SerializedCollection.Register`).
3. Makes one `required` entry per mod, with `min` set to the version that the client itself installed, and no `min` for a mod it did not install. A mod folder whose name is not a valid RFC 0031 id gets no entry, and the client names it to the publisher.
4. Leaves out the dependencies of those mods, which a resolver finds through their own listings.
5. For a save, names every file in the folder other than `meta.toml` and `universe.xml`, because the game writes none, so it is probably a mod's state.
6. Checks `name` by the name rule below. A name from an older build can fail, because only a new save goes through `SaveName.TryAccept` and an overwrite keeps the old name (`UncompressedSave.Overwrite`), so the client asks for a new save under a valid name.
7. Shows the list to the publisher, and makes the archive with one top-level directory named after `name`.

A wrong list is corrected with an amendment, which [RFC 0079](0079-author-freedom.md) allows the owner in both directions.

### What the watcher checks in the archive

The derived `root` is the archive root when `meta.toml` and the game file are there, as RFC 0035 rule 9 says, and otherwise the one top-level directory that holds them.
The listing checks and the release pull request checks of RFC 0033 use the same rules.

| What | Rule | On failure |
|---|---|---|
| `meta.toml` | Parses as TOML. | Reject, because `GameSaves.Refresh` and `VehicleSaves.Refresh` read it at start through `SaveMetaData.FromDirectory`, and nothing catches a failure, so the game does not start. |
| `name` | A string that follows the name rule. | Reject. |
| Root directory | Its name equals `name`, when the root is a top-level directory. | Reject, because the game saves into a folder named after `name` and then shows the two folders as one entry. |
| Game file | Present and well-formed XML. | Reject, because the game skips the folder (`VehicleSaveData.ExistsIn`, `UniverseData.ExistsIn`) or refuses to load it. |
| `version` | A game version by [RFC 0017](0017-game-version-ordering-and-compatibility.md), with no suffix. | Reject only when the listing authors no `game_min`. |
| Other files | Installed as they are. | A note for a `vehicle`, whose folder the game writes with only the two files (`UncompressedVehicleSave.Write`). |

The name rule is that of `SaveName.Sanitize` and `SaveName.IsSanitized`, written out so that a checker in any language agrees with the game:

- 1 to 64 UTF-16 code units.
- Each code unit is in the Unicode categories Lu, Ll, Lt, Lm, Lo or Nd (`char.IsLetterOrDigit`), or is a space, `-` or `_`. So a letter outside the Basic Multilingual Plane fails.
- No space at the start or the end, and no two spaces together.
- Not `CON`, `PRN`, `AUX`, `NUL`, `COM1` to `COM9` or `LPT1` to `LPT9`, compared without case.

The watcher does not map the ids to mods, because that needs the asset files of every mod, which the index does not hold.
It parses with its own TOML and XML parsers, so a file that passes can still fail in the game.

### The release file

Every field of a mod release file except `loader`, and:

| Field | On `vehicle` and `save` |
|---|---|
| `install.folder` | Required. The `name` from `meta.toml`. Immutable, as all install data. |
| `install.target`, `install.path` | Absent, because the type default applies. |
| `game_min`, `game_min_revision` | The authored `game_min`, or else `version` from `meta.toml`. |

```json
"install": { "root": "Example Rover", "derived": true, "folder": "Example Rover" }
```

### Install, update and uninstall

RFC 0035's defaults gain two rows: `vehicle` installs to `user-data` + `Vehicles`, and `save` to `user-data` + `saves`, each as a folder named `install.folder`.
`target`, `path` and `manages` are invalid on these types.
`manages` has no use, because the game deletes and writes the whole folder each time it saves (`SaveDirectory.TryReplace`).
A StarMap instance path overrides `Constants.DocumentsFolderPath`, so `user-data` is the instance's folder.

A client:

1. Resolves the dependencies by RFC 0031 and compatibility by RFC 0017. Only incompatible blocks.
2. Installs the dependencies first and enables them in the instance's `manifest.toml`. The game adds a new mod folder as disabled (`ModLibrary.AddMods`) and loads no disabled mod (`ModLibrary.PrepareAll`), so a dependency that is not enabled ends the game as a missing one does.
3. When a required dependency cannot be installed or enabled, names it and lets the player continue. For a vehicle it also says that the game's launch menu can end the game while this vehicle is the newest, because the menu loads the newest vehicle before the player chooses (`VehicleLaunchMenu`, sorted by `updated` in `VehicleSaves`).
4. Stops when the target folder has a folder named `install.folder`, or a `meta.toml` whose `name` equals it, unless the client installed it from the same listing. Both comparisons ignore case. The game shows two folders with the same `name` as one entry and keeps the one it read last (`LookupCollection` with `allowReplacing`).
5. Verifies `download.sha256`, unpacks into a temporary folder on the same volume and outside `Vehicles` and `saves` (the game reads every direct subfolder there), checks `meta.toml`, `name` and the game file, and moves the folder into place in one step.
6. Records the listing, the version, the folder and a hash of each file.

It changes nothing while the game of that instance runs.

The player changes an installed vehicle in the editor and a save by playing it, in the same folder.
So a client never updates or removes one by itself.
When the files differ from the recorded hashes, it replaces or removes the folder only after the player confirms, and keeps the old folder outside `Vehicles` and `saves`.

### Packs, index, snapshot and tags

- A `[[vehicles]]` entry of a pack that names a listed id must reference a `vehicle`, and a `[[saves]]` entry a `save`. Every other pack rule applies unchanged.
- The authored repository gains `vehicles/<id>.toml` and `saves/<id>.toml`. The location, collision, ownership, amendment, release notes ([RFC 0064](0064-changelog-text.md)) and gone release ([RFC 0078](0078-gone-releases.md)) rules apply as for a mod, and release files go under `releases/<id>/`.
- Download counts ([RFC 0052](0052-static-download-counts.md)) are collected for these listings in the `listings` array of `download-counts.json`, and the snapshot build joins each count to the entry with that id in any of the three arrays.
- The snapshot gains two optional top-level arrays, `vehicles` and `saves`, with the entry shape of `listings`. `listings` keeps only mods and loaders, so a client that does not know these types never sees them and never installs a vehicle as a mod.
- [spec/tags.md](../spec/tags.md) gives both types their own curated list, which starts empty, because the forum has no prefix for them. Free-form tags are valid from the start.

### Rollout and versions

A host from the hosting RFC exists, and the listing checks, the watcher and the snapshot builder support `vehicle`, before the index accepts a `vehicle` listing, and later the same for `save`.
Vehicles first, because a vehicle's needs are almost all visible in its file, while a save adds bodies, a roster and mod state beside the file.

`spec_version` and `snapshot_version` stay at `1`.
A new type needs no bump by RFC 0031, `install.folder` and the optional `[compatibility]` hold only for the new types, and the snapshot arrays are optional keys that an older client ignores.

This RFC amends RFC 0025 (its open question), RFC 0031 (the types, `install.folder`, pack entry types), [RFC 0033](0033-content-index.md) (the folders and archive checks), [RFC 0035](0035-content-install-descriptor.md) (the defaults and rule 9), RFC 0052 (counts), RFC 0058 (images), spec/snapshot.md and spec/tags.md.

## Drawbacks

- The dependency list is only as good as the sharing client and the publisher. The index cannot check it.
- Mapping ids to mods reads the asset files of installed mods, one more game format a client has to follow.
- `game_min` from the file is the publisher's build, so a player one build behind is blocked by RFC 0017.
- Nothing can be listed before the hosting RFC, and a publisher then still needs an account on that host, which is more than sharing a file on Discord.

## Alternatives

- **The index reads the list out of the file.** It would need the asset files of every mod version, and mods without ids and state beside a save would still be missing.
- **A mod in the game writes the exact list.** Each template knows its mod while the game runs (`SerializedId.OnDataLoad`), but it helps only where it ran, has to follow every game update, and a failure in the save path hits every player. It stays a future possibility.
- **Warn without resolving, or refuse to install.** A missing part template ends the game, and only incompatible blocks anywhere in this specification.
- **Vehicles and saves in `listings` of the snapshot.** A client that knows only mods would try to install them into its mods folder.

## Unresolved questions

- Which host the archives go to, and how its account proves ownership. This is the hosting RFC, and it decides who can publish.
- Which forum thread a vehicle or save links as the required `links.forums`. Whether the forum has a section for them is not verified.
- Whether the build in `meta.toml` is too tight as the default `game_min`, and a month form such as `2026.9` is better.
- Whether a client may install under another name when the name is taken (compare Borea #556), instead of stopping.
- Whether the index notes or refuses a second listing of the same type with the same `install.folder`.
- Whether `name` needs a stricter rule than `SaveName`, for example Unicode NFC for macOS.

## Future possibilities

- A listed mod that writes the exact list of mods beside a vehicle or save, in a format specified here.
- The watcher stamps the ids a file names, so a client can check them before the download.
- Packs of example vehicles pinned together with the parts mod they show.
