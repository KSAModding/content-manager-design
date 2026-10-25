# Keeping more than one game build

Verified against game build **2026.10.19.5638**, StarMap `main` at `fe3edd6` (0.4.8) and `dev` at `78816da`, and Borea `main` at `4fda1b86`, on 2026-10-21.

This note collects what Borea needs to keep more than one KSA build and to start each instance against its own build, as asked in discussion #97.
Every point says whether it was verified in code or on a real install, or whether it is a statement of someone else or an inference.

## Summary

| Question | Answer | Status |
|---|---|---|
| Does a build run from any folder? | Yes. The game resolves its files relative to its own folder, and nothing in it refers to the Ahwoo client. | Verified in code |
| Disk size of one build | 2.84 GB for 5638 on Windows, 1,637 files, 2.72 GB of it in `Content`. | Measured |
| Where the copies live | Under Borea's library folder, one folder per build. | Proposal |
| How an instance names its build | By the full build version in `instance.toml`; no value means the build the player set in Borea, as today. | Proposal |
| How StarMap gets the right build | StarMap reads the game only from `GameLocation` in `StarMapConfig.json`, also after its restart. Borea can write that value before each start without a StarMap change; a per-start value in StarMap is the lasting fix. | Verified in code |
| What else in Borea assumes one build | The installed version, which drives compatibility in about 20 files, the shape check, the patch notes and the platform check. | Verified in code |
| What the Ahwoo client does with a copy | It does not manage folders outside its games folder. | Statement of Ahwoo, not verified |
| The update popup on an old build | Shown on every online start, not affected by the "Check for Updates" setting, and its GET button quits the game. | Verified in code |
| Where older builds come from | Only from builds the player already has. The client keeps the newest build only, and ksa-archive.net has installers without hashes up to 5602. | Verified for the archive list, statement of Ahwoo for the client |

## A build runs from any folder

`KSA.Program.Main` sets the working directory to `AppDomain.CurrentDomain.BaseDirectory` before it does anything else, and the game reads its files through relative paths such as `FileReference.ContentPath` and the `Content` folder of `ModEntry`.
StarMap does the same for a game it loads: `GameSurveyer` sets the working directory to the game folder.
So a copied build folder starts from wherever it is, which matches what Linux players see with the archive whose folder name holds the version.

The game has no tie to the Ahwoo client.
A search of the decompiled game finds the word Ahwoo only in URLs (`VersionInfo`, `BuildInfo`), and no launch token, license check or registry access.

Player data does not live in the build.
`Constants.DocumentsFolderPath` names the profile, and StarMap replaces it per start through `DocumentsPathPatches` with the value of `-InstancePath` or `STARMAP_INSTANCE_PATH`.
So one build can serve several instances, and an instance can move to another build without moving its saves.

## Disk size and where the copies live

Build 5638 as the Ahwoo client installed it on Windows is 2,843,870,846 bytes in 1,637 files, and 2,724,899,233 bytes of that are in `Content`.
A Linux build was not measured.
Discussion #97 says about 3.7 GB per build; that figure is too high for 5638.

The copies would live in a folder of their own under the library folder (`BoreaSettings.LibraryFolderPath`, Borea's own folder by default), for example `Game Builds/<version>`.
The library folder already holds the instances and the shared mod store, and the player can move it to another drive, so the builds move with it.

Sharing unchanged files between two kept builds through hard links could save most of the space, because most of `Content` probably does not change between two builds.
This is not measured, because only one build was at hand.
Hard links into the folder of the Ahwoo client are not safe without knowing whether the client patches a file in place, which would change the kept copy too.

## How an instance names its build

An instance would name its build by the full version that Borea reads from the file version of `KSA.dll` (`InstalledGameVersionProvider`, the chain of RFC 0017), for example `2026.10.13.5602`, in its `instance.toml`.
An instance without that value runs against the game folder of Borea's settings, as every instance does today, so nothing changes for a player who never uses the feature.

The version is a better name than a folder path, because the library folder can move, and better than the build id of the client manifest, because a build the player brought in has none.
Borea can find a kept build again by reading `KSA.dll` in each folder under `Game Builds`, the same way `InstallDetector` checks a candidate.

Moving an instance to an older build than the one its saves were made with is a separate risk.
Whether an older build loads a newer save was not checked.
"Keep this build" avoids the question, because it freezes the build the saves were made with and only ever moves forward later.

## How StarMap is pointed at the right build

StarMap reads the game location only from its config file.
`LoaderConfig.TryLoadConfig` reads `./StarMapConfig.json`, relative to the working directory, takes `GameLocation` and accepts a folder or the path of `KSA.dll`.
`Program.Main` also loads `./0Harmony.dll` from the working directory.
Borea starts a loader with its own folder as the working directory (`LaunchPlan.ForLoader`, rule 5 of RFC 0035).

The restart after newly enabled mods (`ModLibraryPatches.BeforePrepareAll` on `main`, `StarMapPatches` on `dev`) starts the StarMap executable again with only `--restarted` and with the StarMap folder as the working directory.
The new process therefore reads the same `StarMapConfig.json` again and loses every launch argument, while it inherits the environment.
The instance survives the restart only because Borea passes both the `-InstancePath` flag and the `STARMAP_INSTANCE_PATH` variable that the StarMap listing declares in `[provides.instance]`.

Borea already writes `GameLocation` through the `[provides.configure]` table of the StarMap listing, when the player changes the game folder (`GameDirectoryChanger` calls `LoaderConfigurator.ConfigureAsync`).
That gives two ways to start each instance against its own build.

1. **Write `GameLocation` before each start.** Borea calls the same configurator with the build of the instance right before the launch. This needs no StarMap change and no RFC, and the restart reads the right value. Its limits: Borea installs one StarMap per loader id (`BoreaSettings.LoaderInstallations`), so the file is shared, and a start of another instance on another build between a start and its restart would send that restart to the wrong build. Borea can refuse a start while a game runs on another build. A player who starts StarMap by hand gets whichever build Borea wrote last.
2. **A per-start game location in StarMap.** StarMap reads the location from an environment variable next to `STARMAP_INSTANCE_PATH`, which survives the restart for the same reason, and the StarMap listing declares it in a new key of `[provides]`, which amends RFC 0035. This removes the shared state, but needs a StarMap release and an RFC.

The first way is enough for a first version, and the second can follow without changing anything for the player.

## What else in Borea assumes one build

`GamePathProvider` takes one game folder from the settings, and these read it:

- `InstalledGameVersionProvider`, whose version decides compatibility, update offers and the game bounds of listings in about 20 files of the App and the CLI.
- `GameShapeCheck`, which checks the assumptions of `GameAssumption` against the verified builds.
- `FileGamePatchNotesReader`, `GamePlatform` (the platform of the build in the folder), `LoaderLauncher` and `SharedProfileLauncher`.

With a build per instance, these take the build of the instance instead of the global one.
This is most of the work in Borea, and it is the same work whatever the source of the build is.

## The Ahwoo client and a copied build

On Windows the client writes the uninstall entry `Ahwoo App 019f01fc-623a-773f-8d70-f0177b16a20c` and keeps a manifest per package in `%LOCALAPPDATA%\Ahwoo\Client\Manifests\<package id>.adf`.
The KSA manifest has a `Builds` list whose entries hold `Id`, `InstallDirectory`, `UserDefinedVersion` and `ExecutablePath`; on the machine checked it holds one entry, 5638.
So the format allows several builds, and the client installs one.

According to Ahwoo (Discord, 2026-10-16), the client makes its game folder match the new build on every update, and a manager can keep a build in a folder the client does not manage, where it stays until the manager changes it.
The code of the desktop client was not read, so this is their statement and not verified.

The client gives no sign while it patches a game, so Borea cannot tell whether a copy was taken in the middle of an update.
Borea can check the version of `KSA.dll` in the copy, but it has no file list to check the rest against.

## The update popup of an old build

`VersionInfo.CheckOnLaunch` runs once the game has loaded (`Program`, after "Loading Complete").
It asks the master server for the newest version, and when that is newer than `VersionInfo.Current` by `VersionInfo.CompareTo`, it opens `UpdateAvailablePopup`.
The popup has two buttons: GET opens the URL of the master server in the browser and then calls `Program.RequestExit`, so the game quits; Cancel closes the popup.

The launch check does not look at `GameSettings.System.CheckForUpdates`.
That setting, which the popup's "Always Check" checkbox writes, only enables the "Check for Update" menu entry (`VersionInfo.AllowUpdateCheck`).
The game has no launch argument that skips the check (`Program.CliArgs` knows `build-info`, `fixed-viewport` and `wayland`).
Without a connection the check only writes an error to the log.

So every online start of a kept build shows the popup, and a player who clicks GET out of habit closes the game.
Borea can say this where the player keeps a build.

## Where older builds can come from

**The Ahwoo client.** It installs the newest build of the latest branch only. According to Ahwoo (Discord, 2026-10-16), other branches or builds may come later, depending on the developer, and everything except the latest branch is unsupported. Nothing to build on today.

**ksa-archive.net.** Its build list (`public/builds.json` in `H4ckerxx44/ksa-archive-net`, checked 2026-10-21) holds 197 builds from 1231 (2025-04-17) to 5602 (2026-10-13).
Windows builds are installers (`setup_ksa_*.exe`, a few early ones as zip), and Linux builds are `tar.gz` archives since about build 3916.
No entry has a hash, so Borea could not check what it downloaded.
Build 5638, the first that came only through the client, is not in the list.
The archive's readme quotes the CEO of RocketWerkz that caching versions is fine as long as they are not decompiled or altered; that is not a permission for every Borea to download about 3 GB from a volunteer's host, which its owner would have to agree to.
A Windows installer would also write the uninstall entry of the old installer (`{BA65F5AF-CD20-48A4-A957-410CB9660FF7}_is1`), which Borea reads to find the game, and unpacking it without installing needs a third-party tool; neither was tried.

**The player's own copies.** A copy Borea makes before an update, an old install folder or an unpacked Linux archive.
Borea can take any folder that holds `KSA.exe` and a `KSA.dll` with a version.
This is the only source that needs nobody else.

**An archive of our own.** It would redistribute the game, which needs the permission of RocketWerkz and costs storage and bandwidth. Not proposed.

## Open

- Whether the client patches files in place or replaces them, which decides whether hard links are safe.
- How much of `Content` changes between two builds, which decides what sharing files would save.
- Whether an older build loads a save made by a newer build.
- Whether Ahwoo will offer older builds or branches in the client, and whether a manager may then ask the client to install one.
