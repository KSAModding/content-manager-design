# Vehicles and saves, and the mods they need

Verified against game build **2026.9.10.5438** and updated for **2026.9.22.5482**, and for the Unscience case against `meow-sci/unscience` at commit `93c9a50`.

## Answer

A save and a vehicle are each a folder with a `meta.toml` and one XML file, under the user data root.
Neither records which mods it needs, and neither records a mod version.
Both name content by bare ids: part templates, module templates, substances, celestial bodies and characters.
Those ids carry no mod prefix, so the file alone cannot say which mod provides them.

The game checks nothing before it loads.
A part template, an EVA character, or (with ground clutter on) a ground clutter ecotype that is not installed throws an exception that nothing catches, and the game ends.
A missing roster character does the same later in play.
Other missing content is dropped, usually with a log line.
Mod state that a mod keeps outside the game's XML is invisible to the game, and to anybody reading the XML.

## Where they live

| Type | Folder | Files |
|---|---|---|
| Save | `<Documents>/saves/<name>/` (`GameSaves.SaveFolderPath`) | `meta.toml`, `universe.xml` |
| Vehicle | `<Documents>/Vehicles/<name>/` (`VehicleSaves.SaveFolderPath`) | `meta.toml`, `vehicle.xml` |
| Stock vehicle | `Content/Core/defaultvehicles/<name>/` (`DefaultVehicleSaves.SaveFolderPath`) | `meta.toml`, `vehicle.xml` |

`<Documents>` is `Constants.DocumentsFolderPath`, the user data root that [RFC 0035](../rfcs/0035-content-install-descriptor.md) calls `user-data`.
Note the casing: `saves` is lower case and `Vehicles` is not, which matters on a case-sensitive file system.
`GameSaves.CheckDirectories` and `VehicleSaves.CheckDirectories` create both folders at start.

The stock folder belongs to the game install.
`VehicleTemplate.OnDataLoad` reads the part tree of a vehicle that a system file places only from this folder (`DefaultVehicleSaves.FindSave`), so a mod cannot ship such a vehicle from its own folder.
Published vehicles therefore install only under `Vehicles/`.

A StarMap instance path overrides `Constants.DocumentsFolderPath`, so saves and vehicles move with the instance (see [research/starmap.md](starmap.md)).
The user mods folder and `manifest.toml` move with it, so a save and the mods enabled for it are in the same instance.
Mods under `<GameDir>/Content/` do not move, so every instance shares them (see [research/ksa-mod-loading.md](ksa-mod-loading.md)).

## The name is the identity, not the folder

`UncompressedSave.FromDirectory` and `UncompressedVehicleSave.FromDirectory` take the `name` from `meta.toml` as `GameSave.Id`.
The folder name is used only to find the files.

Normally both are equal, because `UncompressedSave.Make` writes to a folder named after the name.
When they differ, `UncompressedSave.Overwrite` and `UncompressedVehicleSave.Overwrite` write a new folder named after `name` and do not delete the folder the save came from, so two folders then carry the same name.

The lists are `LookupCollection`s created with `allowReplacing: true`.
Two folders whose `meta.toml` carry the same name show up as one entry, and the one read last wins, without a message.

A new name passes `SaveName.Sanitize`: letters and digits as `char.IsLetterOrDigit` defines them (so not only ASCII), space, `-` and `_`, at most 64 characters, single spaces, and a trailing `_` on a Windows device name.
A name that nobody sanitized, for example in a downloaded folder, is not checked on read.

## `meta.toml`

`SaveMetaData` is the same class for saves and vehicles.
A real file has this shape (values replaced):

```toml
name = "Example Save"
created = 2026-09-15T09:30:25.8301416
updated = 2026-09-15T09:30:25.8501341
version = "v2026.9.10.5438"
systems = [ "Sol", ]
```

| Field | Written by | Read by |
|---|---|---|
| `name` | The name given at save time. | Becomes `GameSave.Id`. |
| `created`, `updated` | `DateTime.UtcNow`; `SaveMetaData.Write` sets `updated`. | Shown and sorted in the load dialog. |
| `version` | `SaveMetaData.Write` stamps `VersionInfo.Current`, with the leading `v`. | Parsed with `VersionInfo.Parse(..., throwExceptions: false)`, then shown in the load dialog and sorted there as a string. Never compared with the running game. |
| `systems` | The id of `Universe.CurrentSystem` only. | Only `ToConsole`. Nothing checks it on load. |

There is no mod list, no mod version, no author and no description.
The game version is the one version the game records, and it only displays it (see [research/ksa-versioning.md](ksa-versioning.md)).

## `universe.xml` and `vehicle.xml`

Both are written by `XmlSerializer` through `XmlHelper.SerializeWithoutNaN`.
`universe.xml` is a `UniverseData`: `GameTime`, `CameraData`, one `System` with an `Id`, a `Vehicle` element per vehicle (`VehicleData`), the ground clutter of each body (`ClutterEcotypeSaveData`), and the `KittenRoster`.
`vehicle.xml` is a `VehicleSaveData`: the `Id` (the name), the part tree under `RootPartRef`, sequences, fuel links, `LaunchGameTime`, and a `Character` for a kitten.

`VehicleData` extends `VehicleSaveData`, so a vehicle inside a save has the same part tree as a vehicle file, plus orbit, flight computer and resource state.
Five real saves were 430 to 670 KB, five real vehicles 78 to 180 KB.

### The content a file names

| Content | Where in the file | Resolved by | When it is not installed |
|---|---|---|---|
| Part template | `InstanceOf` on `RootPartRef`, `PartRef` and `SubPartRef` | `PartInstance.GetTemplate`, which calls `ModLibrary.Get<PartTemplate>`, from the `Part` constructor | `ModLibrary.Get` throws `NullReferenceException`. |
| Module state | Module elements such as `TankData` or `EngineController`, with an `InstanceOf` | `ModuleList.ApplySaveData`, from `PartTree.Deserialize` | Warning "matched no module", the state is discarded. |
| Substance | `SubstancePhaseId` on a `Mole` inside `TankData` | `SubstanceLibrary.TryGetSubstancePhase`, from `Tank.ApplySaveData` | Error logged, that substance is left out of the tank. |
| Parent body (saves) | `ParentBody` `Id` of each vehicle | `CelestialSystem.Get`, from `CelestialSystem.DeserializeSave` | Error logged, the vehicle is not created. |
| Ground clutter (saves) | `Celestial` and `Ecotype` of each `GroundClutter` in `System` | `GroundClutterRenderer.DeserializeSave` | Skipped without a message when the body is missing. When the body has no ecotype with that id, a dictionary lookup throws `KeyNotFoundException`. Only with ground clutter on in the graphics settings, which is the default. |
| Celestial system (saves) | `System/Id`, and `systems` in `meta.toml` | Nothing. | `Universe.DeserializeSave` loads the vehicles into whatever system runs. |
| EVA character | `Character` on a vehicle | `ModLibrary.Get<CharacterReference>`, from the `KittenEva` constructor | `ModLibrary.Get` throws `NullReferenceException`. |
| Roster character (saves) | `Character` on each `Kitten` of the roster | `ModLibrary.Get<CharacterReference>`, from the `KittenRenderable` constructor (`IVASeat`) and the `KittenEva` constructor (`EVADoor`) | Throws later in play, when the seat renders or the kitten goes on EVA, not at load. |

Two properties of these ids matter for any dependency check:

- **No id names its mod.** `SerializedId.Mod` is set when a template loads, but it is `XmlIgnore`, so the providing mod is not written. Part ids are a single global namespace: `SerializedCollection.Register` keeps the first template with an id and silently drops any later one.
- **Mod code cannot add its own records to these files.** `XmlHelper` registers module save types only from the game assembly (`Assembly.GetExecutingAssembly`). A mod that keeps its own state must patch that or write a file of its own. Unknown elements and attributes are skipped by `XmlSerializer` by default, and the game attaches no `UnknownElement` handler, so such data is dropped on load. `UncompressedSave.Write` and `UncompressedVehicleSave.Write` delete the whole folder and create it again (`SaveDirectory.TryReplace`) before they write, so the next save also deletes any extra file in the folder. When the folder cannot be deleted, the game does not write the save and shows an alert.

## What the game does with content that is not installed

**At start**, `GameSaves.Refresh` and `VehicleSaves.Refresh` read the `meta.toml` of every folder, but not the XML files.
`universe.xml` is read only when the save is loaded, and `vehicle.xml` only when the vehicle is loaded (the `UncompressedVehicleSave.VehicleSaveData` property reads it on first use).
So neither a missing mod nor a broken XML file is noticed here.
`UncompressedSave.FromDirectory` skips a folder without `universe.xml` with a warning (`UniverseData.ExistsIn`), and `UncompressedVehicleSave.FromDirectory` skips a folder without `vehicle.xml` (`VehicleSaveData.ExistsIn`), for example after a half-finished install.
Both read `meta.toml` outside any `catch` (`SaveMetaData.FromDirectory`), and neither `GameSaves.Refresh` nor `VehicleSaves.Refresh` catches anything, so a `meta.toml` that Tomlet cannot parse stops the game from starting.
A folder without `meta.toml` is skipped with a warning in both cases.

**Loading a save**, `UncompressedSave.Load` reads `universe.xml` and then calls `Universe.DeserializeSave`.
A `universe.xml` that the serializer cannot read is logged as an error, and the save is not loaded.
`Universe.DeserializeSave` first destroys the running vehicles (`CelestialSystem.DestroyAllVehicles`), then builds each vehicle through `Vehicle.CreateVehicleFromSaveGameData` and `PartTree.Deserialize`.
A missing part template throws in the middle of that.
The `catch` in `UncompressedSave.Load` covers only the read of `universe.xml`, so there is no `catch` on this path, not in `Program.Main` either, and the only unhandled exception handler in the decompiled assemblies (in the static constructor of `Network`) only shuts networking down.
The process ends.

**Loading a vehicle** in the editor or the launch menu calls `UncompressedVehicleSave.Load(IViewport)`.
A `vehicle.xml` that the serializer cannot read is logged and shown as an alert, and no vehicle is loaded.
Otherwise it runs the same `PartTree.Deserialize` with the same result.

**Version**: nothing compares the saved `version` with the running game, and there is no migration.

## The Unscience case

The report on Discord (2026-09-20): a save made with Unscience crashes the game when Unscience is not installed.

What Unscience does, from its source:

- It keeps its own state in `unscience.json` in the save folder, next to `universe.xml` (`SaveStorage`). The file carries a schema version, a SHA-256 of `universe.xml`, and one record per feature. The game never reads it.
- Its Parts Now feature makes part templates from pasted XML while the game runs. It writes them into an ordinary mod folder, `<mods>/<mod-id>/` with `mod.toml` and XML, and enables that folder in `manifest.toml`, so the folder also loads at the next start without Unscience. Its README says the part mods must be installed before the game reads the save, and that `unscience.json` is not a portable asset bundle.
- While installed, it checks a save before the game loads it (`NativeSavePreflight`) and refuses the load with an error when a part template, a character, a parent body or the system is missing.

A vehicle built from a Parts Now template names that template in `universe.xml`.
That save needs the generated mod folder, not Unscience.
When the folder is missing, for example because the save was copied to another computer, `ModLibrary.Get<PartTemplate>` throws and the game ends as described above.
Removing only Unscience does not cause this, because the folder still loads.

So the code shows no path by which removing only Unscience ends the game.
Why the reported save failed, the decompiled code cannot answer.
What Unscience writes into `universe.xml` is decided by the mod's own code, and the save itself was not available.
Two consequences hold either way: the mod's own check runs only while the mod is installed, and a save made again without the mod loses `unscience.json` without a message.

## What could identify a vehicle or a save

For a mod the game forces the id, because `Mod.MakeUsing` uses the folder name.
For a save or a vehicle the game forces nothing: the name in `meta.toml` is its identity inside the game, and the folder only has to match it.

The two naming rules do not fit each other:

| | `SaveName` (game) | RFC 0031 id |
|---|---|---|
| Characters | Unicode letters and digits, space, `-`, `_` | ASCII letters and digits, `-`, `_`, `.` |
| Length | 1 to 64 | 1 to 64 |
| Case | Compared through `KeyHash` (not verified for case) | Case-insensitive |

Real names contain spaces, and every real save and vehicle checked here had one.
So an RFC 0031 id cannot be the save name in general.
The id can be an index id in the global namespace, like a pack's, while the install folder comes from `name` in the archive's `meta.toml`.

Two published saves with the same name collide in one instance, on disk and in the game's list.

## Facts for each point of #71

**Read from the file, declared, or both.**
The file names content ids, never mods, and a part id does not say which mod provides it.
Mapping ids to mods needs the asset files of the mods, which the index does not hold and a watcher would have to download for every mod.
Mod state outside the XML (`unscience.json`) and mods without content (code only) leave no id at all.
A mod that a player generated locally, such as a Parts Now folder, is in no index, so a publisher cannot declare it as a dependency a client can resolve, and a client can only report its ids as missing.
The ids can still check a declaration: a client that has the game and the mods installed can list the part templates, characters and bodies that neither the game nor the installed mods provide.

**What a client does when a mod is missing.**
The game refuses nothing.
A missing part template or EVA character ends the process, a missing roster character ends it later in play; a vehicle on a missing body, a missing substance or a missing module drops that piece with only a log line; a missing mod without ids loses its state silently.
So "install and warn" can mean a crash the player cannot explain, which is the reported case.

**A version per mod, or only an id.**
The game records no mod version, and no mod version exists on disk (see [research/ksa-mod-loading.md](ksa-mod-loading.md)).
A mod update that renames or removes a part template breaks a save exactly as a missing mod does.
The only version in the file is the game build in `meta.toml`.

**Which type first, and one shape or two.**
Both types use the same `SaveMetaData`, the same folder layout and the same part tree.
A vehicle's needs are its part templates, module templates, substances and at most one character.
A save adds the system, bodies, the roster, every vehicle in it, and mod state that a mod may keep beside it.

**What identifies a vehicle or a save.**
The name in `meta.toml` is the game's identity, and the folder should match it.
It allows spaces and non-ASCII letters, which an RFC 0031 id does not.

## Recommendation

- **Declared, checked against the file.** The publisher declares `[[dependencies]]` with the shape and kinds mods already use. A client checks the declaration against the ids in the file where it can, and warns about ids nothing installed provides. The watcher cannot map ids to mods, so it does not try.
- **Filled by the client that shares it.** The publisher does not type the list. The client that shares a vehicle or save has the mods of that instance on disk, so it maps each id in the file to the installed mod that provides it, and fills `[[dependencies]]` with only those mods, each with its installed version as `min`. Content of the game itself (`Content/Core`) needs no entry, and a mod that only one part comes from is one entry. The dependencies of those mods are not repeated, because a resolver finds them through the mods' own listings. The publisher checks the list and adds by hand what leaves no id: a mod that only patches existing content or only adds code changes how a vehicle behaves, not whether it loads, so it is at most `recommends`. The mapping reads the asset files of the installed mods, which is one more assumption about the game's formats that a client has to keep true.
- **A mod in the game stays optional.** While the game runs, each template knows the mod that provided it, because `SerializedId.OnDataLoad` sets `SerializedId.Mod`, so a mod could write the exact list after every save. The first version does not need it: it helps only where it ran, it has to follow every game update, and a failure in the save path hits every player who runs it. If it is needed later, it is an ordinary listed mod that does nothing when it fails, and the format of the file it writes is specified in this repository, so that every client can read it.
- **Resolve, do not only warn.** Required dependencies install with the vehicle or save, as RFC 0025 already describes. When one is unavailable, the client warns and says that loading may end the game. Blocking stays reserved for incompatible, as everywhere else.
- **Versions as bounds.** Dependencies take the same optional `min` and `max` as mod dependencies, with a `min` as the recommended default. The build in `meta.toml` is a fact the watcher can read for `game_min`.
- **Vehicles first, one shape.** One document shape for both types, differing in `type` and the folder. Vehicles first, because their needs are almost all visible in the file. Saves second, with the note that mod state beside the file is never visible.
- **Install in one step.** A client unpacks a vehicle or save into a temporary folder, checks that both files are there and parse, and then moves the folder into place in one step. The game skips a folder without its XML file, fails to load one whose XML file is cut off, and does not start when Tomlet cannot parse a `meta.toml`.
- **Id and folder apart.** The id follows RFC 0031 in the global namespace. The install folder is the `name` from `meta.toml`, which the watcher reads from the archive and checks: it passes `SaveName.IsSanitized`, and the folder in the archive matches it. A client does not overwrite a folder of that name that it did not install.
