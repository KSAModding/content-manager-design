# How KSA finds, enables, and loads mods

Verified against game build **2026.8.3.5117**.

## Where mods live

A mod is a folder containing a `mod.toml`. The game scans exactly two places:

| Location | Notes |
|---|---|
| `<GameDir>/Content/<ModId>/` | Where the stock content lives. `Content/Core` is the game itself. |
| `<Documents>/My Games/Kitten Space Agency/mods/<ModId>/` | The user mods folder. Survives game updates, and is where a manager should install. |

The user folder comes from `ModLibrary.LocalModsFolderPath`, which builds on `Constants.DocumentsFolderPath`. That constant resolves `Environment.SpecialFolder.Personal` and appends `My Games/Kitten Space Agency`. On Windows that is the user's Documents folder; note that on Linux .NET resolves the same special folder to `$HOME`, so the path there is `~/My Games/Kitten Space Agency` rather than anything XDG-shaped.

`ModLibrary.CheckDirectories`, called at application start, creates both the Documents folder and the mods folder if they are missing.

**The `Content` path is relative.** `ModLibrary.PrepareManifest`, `ModLibrary.PrepareAll`, and `ModEntry.Exists` all build it as a bare relative `Content`. `Program.Main` sets the current directory to the executable's own folder as its very first statement, so this resolves next to the game binary regardless of how the game was launched.

## Mod identity is the folder name

There is no id field anywhere. `Mod.MakeUsing` deserializes `mod.toml` and then assigns the id from the folder name, overwriting whatever the file might have contained.

Consequences worth stating plainly:

- Two mods cannot share a folder name. The folder name is the entire namespace, globally, across both locations.
- Renaming a mod's folder makes it a different mod as far as the game is concerned.

## What `mod.toml` contains

The fields the game reads (`Mod`): `name`, plus asset and capability declarations such as `systems`, `assets`, `fonts`, `planetMeshes`, `starBinaries`, `simulationSpeeds`, `console`, and several `supported*` quality lists.

What it does **not** contain:

- no version,
- no author,
- no dependencies,
- no id.

The game has no concept of a mod version at all. Nothing on disk says which version of a mod is installed, so a manager has to track that itself and cannot recover it by inspecting an installation it did not perform.

Two things you will see in real `mod.toml` files that are **not** game fields:

- a `[StarMap]` section with `EntryAssembly` and `[[StarMap.ModDependencies]]`, read by the StarMap loader, not by the game,
- a `patches` array, a convention of the community KittenExtensions mod.

The game ignores both. They are, today, the only place where anything resembling a dependency is declared.

## `manifest.toml`, and who owns it

`<Documents>/My Games/Kitten Space Agency/manifest.toml` (`ModLibrary.LocalManifestPath`) records which mods exist and whether each is enabled. The schema is exactly two keys per entry:

```toml
[[mods]]
id = "AdvancedFlightComputer"
enabled = true
```

On first run, `ModLibrary.PrepareManifest` copies `Content/manifest.toml` to that path if it is missing. The shipped file contains a single entry for `Core`.

### What the game does to this file, every launch

`ModLibrary.PrepareManifest` runs once per session and:

1. reads both the user manifest and `Content/manifest.toml`,
2. appends any entry present in the Content manifest but missing from the user manifest, and saves,
3. marks every entry that appears in both as **core**, which exempts it from removal,
4. scans `Content/` and then the user mods folder via `ModLibrary.AddMods`,
5. removes every non-core entry whose folder no longer exists, saving after each removal.

`ModLibrary.AddMods` adds a manifest entry for any subfolder that contains a `mod.toml` and is not already listed. New entries are created **disabled** until the user gets prompted to enable it in-game. This is why dropping a mod folder into place makes the game notice it but not activate it and you will have to re-launch the game so that the mod loads.

### Three properties that constrain any manager

**The file is rewritten, not edited.** `ModManifest.Save` regenerates the whole file from the in-memory list and emits only `id` and `enabled` per entry. Any other key, comment, or formatting in that file is destroyed the next time the game saves it. A manager cannot use `manifest.toml` to store its own state.

**Entry order is load order.** `ModLibrary.PrepareAll` walks the manifest in order and loads each enabled mod as it goes, and `ModManifest.IsChanged` treats a changed index as a change. Reordering entries reorders loading.

**Ids are written unescaped.** `ModManifest.Save` writes the id straight into a quoted TOML string with no escaping, so a folder name containing a quote produces a corrupt file. Windows forbids such names, other platforms do not.

The game writes this file from several places: `ModLibrary.PrepareManifest` during startup reconciliation, the in-game mod settings UI, and the confirm-mods flow. A manager must expect the file to change underneath it.

## Loading

`ModLibrary.PrepareAll` iterates the manifest in order, skips disabled entries, and for each enabled one resolves `Content/<id>` first, then the user mods folder, requiring a `mod.toml` in whichever it finds.

## There is no per-install isolation, and no way to create one

- The mods folder and the manifest are per **user**, not per install. Every copy of the game on a machine shares them.
- The game accepts exactly two command line arguments, `-build-info` and `-fixed-viewport`. Neither affects any path. `build-info` generates build information and exits; `fixed-viewport` disables multiple windows.
- The game reads **no environment variables at all**. There is not a single environment variable lookup in the shipped assemblies.
- `Program.Main` forces the working directory to the executable's folder before anything else runs, so the relative `Content` path cannot be influenced by launching from elsewhere either.

The loader does not provide an escape hatch either. StarMap reuses the game's own discovery rather than implementing its own, so pointing it somewhere else does not move where mods are found. See `research/starmap.md`.

Two installs of the game therefore actively interfere, without any manager involved: `ModLibrary.PrepareManifest` prunes any non-core entry whose folder is missing, and `ModEntry.Exists` looks in the launched install's `Content/` plus the shared user folder. A mod living in install A's `Content/` loses its manifest entry the next time install B is launched.

## Implications for a mod manager

- **A manager must own its own registry.** Since nothing on disk records versions, checksums, or which files belonged to which mod, that information has to live in the manager's own storage, outside `manifest.toml`.
