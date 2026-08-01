# What StarMap is

Verified against StarMap `0.4.5` (commit `9c05b6c`, 2026-04-10) and game build **2026.8.3.5117**.

StarMap is the loader every KSA code mod depends on. It is MIT licensed, written by @KlaasWhite .

## Why a loader is needed at all

The game has no concept of a code mod. `mod.toml` declares assets, systems, fonts and meshes; there is no field that names an assembly and nothing in `ModLibrary` loads one. A mod that wants to run code needs something to load its assembly and patch the game. That is the entire reason StarMap exists.

## It does not launch the game, it hosts it

StarMap installs separately from the game, by default into `Program Files\StarMap` via an Inno Setup installer, and keeps a `StarMapConfig.json` next to its own executable:

```json
{ "GameLocation": "...", "RepositoryLocation": "", "GameArguments": [] }
```

`GameLocation` may point at the game folder or directly at `KSA.dll`; `LoaderConfig.TryLoadConfig` appends `KSA.dll` when it is given a directory, and refuses to start if the file is not there. On first run the file does not exist, so StarMap writes a template and exits.

The sequence in `Program.SoleModeInner` and `GameSurveyer.TryLoadCoreAndGame` is:

1. load `0Harmony.dll` into the default load context,
2. create a `GameAssemblyLoadContext` rooted at the game's dependency graph,
3. load `StarMap.Core.dll` into that context and instantiate it,
4. load `KSA.dll` into the same context,
5. set the process working directory to the game folder, and set the `APP_CONTEXT_BASE_DIRECTORY` AppContext slot to the same path,
6. call `StarMapCore.Init`, which discovers and loads mods and then runs `Harmony.PatchAll`,
7. invoke the game assembly's entry point in-process.

`Program.Main` in the game sets `Directory.SetCurrentDirectory(AppDomain.CurrentDomain.BaseDirectory)` as its very first statement, and that property reads the `APP_CONTEXT_BASE_DIRECTORY` slot. Without StarMap overwriting it, the game would reset its working directory to StarMap's own install folder and every relative `Content` path would resolve into `Program Files\StarMap`.

Consequences for anything that launches the game:

- The running process is `StarMap.exe`. Process-name based detection of "is the game running" needs to know that.
- Mods are already loaded and Harmony patches already applied before the game's `Main` gets control.

## Two modes, selected by argument count

`Program.Main`:

- **no arguments**: solo mode. Reads `StarMapConfig.json` and runs the sequence above.
- **one or more arguments**: loader mode. The first argument is treated as a named pipe name, and StarMap connects to a supervising process to ask it where the game is (`GameFacade.Connect`).

So passing any argument to `StarMap.exe` puts it into a mode that expects a pipe server that does not exist, and it hangs rather than starting the game. **Arguments intended for the game go into `GameArguments` in `StarMapConfig.json`**, which `GameSurveyer.RunGame` forwards to the game's entry point. In loader mode the game always receives an empty argument array.

## It reuses the game's own mod discovery

`ModLoader.PrepareMods` calls `ModLibrary.PrepareManifest`, then walks `ModLibrary.Manifest.Mods` in order and skips every entry whose `Enabled` is false. For each remaining entry, `RuntimeMod.TryCreateMod` looks for `Content/<id>/mod.toml` and then `ModLibrary.LocalModsFolderPath/<id>/mod.toml`.

- **StarMap adds no mod location.** It looks exactly where the game looks.
- **StarMap does not change enable semantics.** `manifest.toml` still decides, and the game still owns that file.
- **StarMap cannot be pointed at a different mods folder.** `LocalModsFolderPath` is the game's user-global path, and `Content` is relative to the working directory that has just been set to the game folder. `RepositoryLocation` in the config sounds like it might help and does not; see below.

A mod without a matching `<EntryAssembly>.dll` is skipped without an error, which is how part, planet and config mods pass through untouched.

One ordering detail: because StarMap calls `ModLibrary.PrepareManifest` before the game's `Main` runs, the manifest reconciliation described in `research/ksa-mod-loading.md` happens earlier than usual, and then again when the game does its own startup.

## An open pull request would add instance folders

StarMapLoader/StarMap#80 (opened 2026-07-30, no review yet) adds a `-InstancePath` command line flag and an `INSTANCE_PATH` environment variable that redirect the game to a chosen folder.

The mechanism is a Harmony prefix on the getter of `KSA.Constants.DocumentsFolderPath`, applied from `ModLoader.Init` before mod discovery and before the game's entry point runs. That property is public and is the root of every user-writable path the game has: `ModLibrary.LocalModsFolderPath` and `LocalManifestPath`, plus saves, settings, vehicles, layouts, languages, screenshots, logs and crash dumps. Overriding it moves an entire profile, not just the mods.

If it lands it is the first mechanism by which two KSA setups can hold different mod sets. One property follows from how it works:

- **A mod that does not go through `Constants.DocumentsFolderPath` escapes it** and keeps writing to the shared location. The pull request says as much.

The pull request states that a non-existent path will crash. `ModLibrary.CheckDirectories` creates both the root folder and the mods folder when they are missing, so at least those two are created rather than failing; the other consumers have not been checked here.

## The `[StarMap]` section of `mod.toml`

The game ignores this section. StarMap parses it with Tomlet into its own `StarMapConfig`:

| Field | Meaning |
|---|---|
| `EntryAssembly` | Assembly to load, without `.dll`. If the whole section is absent, it defaults to the mod id. |
| `ExportedAssemblies` | Which of the mod's assemblies dependents may use. |
| `[[StarMap.ModDependencies]]` | One block per dependency: `ModId`, `Optional` (default false), `ImportedAssemblies`. |

`ModId` is matched against the mod id, which is the folder name. This section is currently **the only place in the entire KSA ecosystem where one mod declares a dependency on another**, which makes it the only existing source of dependency data for a manager.

## Dependency handling, as implemented

`ModLoader` walks the manifest once. A mod whose dependencies are all present is initialized immediately; a mod with missing dependencies goes onto a waiting list, registered in a `WaitingModsDependencyGraph` keyed by the id it is waiting for. Whenever a mod finishes loading, `CheckForDependentMods` releases anything that was waiting on it. After the single pass, `TryLoadWaitingMods` loops: any mod whose remaining unmet dependencies are all `Optional` gets loaded, and the loop repeats until a full pass loads nothing new. Whatever is left never loads, and the only signal is a line on the console.

What is absent:

- **No versions anywhere.** Dependencies are name-only. StarMap cannot express "requires X 1.2 or newer", and nothing on disk records which version of a mod is installed.
- **No conflict detection**, no notion of incompatibility.
- **No failure surface.** A missing required dependency, a missing entry assembly, or a mod class without the `[StarMapMod]` attribute all end as a `Console.WriteLine` in a window most users never see.

## Assembly isolation

Each mod gets its own `ModAssemblyLoadContext`. Resolution order is: assemblies already in the default context, then assemblies already in the shared core context, then a load attempt against the core context, then the assemblies its declared dependencies exported to it, then the mod's own dependency graph. This is what lets two mods ship different versions of the same library without colliding, and it is the strongest technical argument for StarMap over a naive loader.

## The API mods bind to

Mods reference the `StarMap.API` NuGet package, mark one class `[StarMapMod]`, and annotate methods:

| Attribute | When it fires | Hook |
|---|---|---|
| `[StarMapBeforeMain]` | before the game's entry point is invoked | called directly by `RuntimeMod.InitializeMod` |
| `[StarMapImmediateLoad]` | as the game loads that specific mod | Harmony prefix on `Mod.PrepareSystems` |
| `[StarMapAllModsLoaded]` | after the game has loaded every mod | Harmony postfix on `ModLibrary.LoadAll` |
| `[StarMapBeforeGui]` | before the game builds its ImGui frame | Harmony prefix on `Program.OnDrawUiFrame` |
| `[StarMapAfterGui]` | after the ImGui frame | Harmony postfix on `Program.OnDrawUiViewports` |
| `[StarMapAfterOnFrame]` | after each simulation frame | Harmony postfix on `Program.OnFrame` |
| `[StarMapUnload]` | on teardown | called from `ModLoader.Dispose` |

Every one of these patch targets still exists in build 2026.8.3.5117 with a matching signature. Two of them, `Program.OnDrawUiFrame` and `Program.OnDrawUiViewports`, are private, so they are not part of any stable surface and can be renamed by a refactor without anyone noticing until mods stop drawing.

## What StarMap does not do

It has no download, index, version or uninstall capability of any kind, and no user interface.

The pieces that look like it might are all inert:

- `StarMap.Launcher` is a stub. Its `Main` prints "Currently WIP, please use the standalone version" and returns; `ModRepository`, `LoaderFacade` and `GameProcessSupervisor` are entirely commented out, and `ModDownloader.DownloadMod` returns `true` without doing anything.
- `RepositoryLocation` in `StarMapConfig.json` is referenced only inside a commented-out line. It is dead configuration.
- `StarMap.Core/Legacy/ModManagerScreen.cs` is a fully commented-out console mod manager.
- `StarMap.Types/Proto/IPC.proto` defines a complete protocol for a two-process design, including browsing available mods, mod details with versions and download locations, and applying a set of mod changes. It is implemented on the loader side and stubbed on the supervising side.

That protocol is the shape of the plan in the README: a Factorio-style in-game mod browser, where selecting mods restarts the game through a supervising process that applies the changes in between. The intended index is described as "just an index of mods, versions and download locations", with hosting left elsewhere. A separate `StarMapLoader/StarMap-Index` repository exists.

**This is the overlap that has to be talked about rather than discovered.** The author has stated he intends to continue with these plans. Nothing in the current code competes with a mod manager; the plan does.

## Packaged for Windows, but the payload is portable to Linux

The release workflow publishes `-r win-x64 --self-contained false` and ships an Inno Setup installer. Releases carry two zips, `StarMapStandalone-<version>.zip` (solo mode, the one a manager wants) and `StarMapLauncher-<version>.zip` (the WIP two-process build); in both, the published executable is renamed to `StarMap.exe`. `StarMap.API` is published to NuGet, versioned separately and only when the API actually changed.

That looks Windows-only and is not. In the shipped `0.4.5` build, `StarMap.Loader.runtimeconfig.json` is framework dependent against `Microsoft.NETCore.App 10.0.0` with no runtime pinned, and `StarMap.Loader.deps.json` carries no native and no RID-specific assets at all. Every assembly in the zip is portable managed code, and the only Windows artifact is the renamed apphost. `dotnet StarMap.Loader.dll` therefore runs the same build anywhere a .NET 10 runtime exists.

Running it on Linux is reported to work, with two obstacles that are not in StarMap's own code:

- **The game ships as a single file on `linux-x64`,** so `KSA.dll` does not exist on disk, while `LoaderConfig.TryLoadConfig` requires exactly that file. The reported workaround is to split the executable first with [SingleFileExtractor](https://github.com/Droppers/SingleFileExtractor) (`sfextract KSA -o .`), which produces the same DLL layout the Windows build has.
- **`XDG_SESSION_TYPE=x11` is reported to be required**, which points at the game's own renderer under Wayland rather than at the loader.

This has been reported at: <https://forums.ahwoo.com/threads/artemis-oem-loader.857/#post-4328>

## Implications for a mod manager

- **The `[StarMap]` section is the only dependency data that exists.** Any metadata format either reads it or duplicates it, and duplicating it means it can disagree with what the loader actually does.
- **Version constraints have to come from somewhere else.** The loader has no version concept, so "this mod needs StarMap 0.4.5 or newer" can only be expressed and enforced by a manager.
- **The plans overlap and the boundary is a decision, not a fact.** How deep the integration between manager and loader should go is one of the first things this repository has to settle, and it cannot be settled without the loader's author.
