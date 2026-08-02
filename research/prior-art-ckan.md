# CKAN, as extended for KSA

Between 2026-06-30 and mid-July 2026, KSA support was built into [a fork of CKAN](https://github.com/KSAModding/CKAN-KSA) in <https://github.com/KSAModding> , the mod manager that has served Kerbal Space Program for over a decade.

It does work and an upstream pull request was created.

The upstream pull request ([KSP-CKAN/CKAN#4688](https://github.com/KSP-CKAN/CKAN/pull/4688), 52 files, CI green) has been open since 2026-07-06 and has not received a maintainer review as of this writing.

That work is the closest thing this project has to a field study since we have a real manager, adapted to this exact game, used by real testers, with every decision recorded in public issues.

**This document is what it teaches, sorted by what transfers here**.

Fork: [KSAModding/CKAN-KSA](https://github.com/KSAModding/CKAN-KSA). Issue and PR numbers below refer to that repo unless prefixed.

Related Forks are also:

- <https://github.com/KSAModding/KSA-NetKAN>
- <https://github.com/KSAModding/KSA-CKAN-meta>
- <https://github.com/KSAModding/NetKAN-Infra>
- <https://github.com/KSAModding/NetKAN-status>
- <https://github.com/KSAModding/xKAN-meta_testing>

## The shape / architecture of CKAN

| Component | What it is | Where it runs |
|---|---|---|
| Client | Desktop app: detects installs, downloads, installs, upgrades, removes | user's PC |
| NetKAN repo | One authored template per mod, saying where releases come from | GitHub |
| CKAN-meta repo | One generated file per mod release, fully resolved: URL, hash, sizes, compatibility | GitHub |
| Bot + tester + status page | Watches for releases, generates the per-release files, validates PRs, shows health | CKAN team's AWS + GitHub Actions |

## The authored/generated split

A mod author writes one small template once ([KSA-NetKAN](https://github.com/KSAModding/KSA-NetKAN)):

identifier, license, a `$kref` pointing at where releases appear (a GitHub repo, a SpaceDock id), install directives, dependencies

Everything per-release, the version, download URL, hashes, download and install sizes, resolved compatibility, is produced by tooling ("inflation") and committed to [KSA-CKAN-meta](https://github.com/KSAModding/KSA-CKAN-meta) as one file per release.

Nobody should hand-write a release file; the one time somebody did, it was invalid JSON and shipped a wrong install path ([KSA-NetKAN#1](https://github.com/KSAModding/KSA-NetKAN/issues/1)).

Why this matters at KSA's release pace: the author's file changes when the mod's facts change which does happen less often
The generated files appear whenever a release appears, and a watcher can produce them unattended which might also be necessary to reduce the modders and maintainers work since KSA does update very often.

Details:

- **Validation happens at publish time, against a schema.** A malformed template failed inflation with the error in front of the wrangler so that it does get caught before it is in front of the user.
- **Install directives** say which paths inside the archive go where. Without them every archive is assumed to have the same layout, and they do not.
- **`spec_version`** stamps each file with the metadata format version it was written against, so the format can evolve without breaking old files.

## The game-version problem, as solved there

CKAN's `GameVersion` is a sealed, game-agnostic four-integer type, compared positionally.
For KSA that compares the meaningless build counter before the meaningful revision, which is wrong (see [research/ksa-versioning.md](ksa-versioning.md)).
The fork's answer: pin the third component to 0 on every KSA version at every ingestion point, so comparison falls through to the revision, matching `KSA.VersionInfo.CompareTo`. Declared compatibility is normalized the same way at inflation, and a validator rejects hand-authored files that bypass it.

It works and has run against a live index since July. But it is a workaround for a type that could not be changed: normalization must be applied everywhere a version enters the system or the guarantee silently breaks, and users see `2026.8.0.5117` for a build that calls itself `2026.8.3.5117`. A fresh design gets to order by the revision directly, which is what RFC 0017 proposes.

Two supporting pieces proved cheap and valuable:

- **A remote build map** (`builds.json` in KSA-CKAN-meta) that a GitHub Action updates hourly by polling the game's master server, the same endpoint the game itself asks for "is there an update" (`VersionInfo.GetServerVersionAsync`). Zero running cost, and it has kept itself current since 2026-07-02 without human attention ([KSA-CKAN-meta#1](https://github.com/KSAModding/KSA-CKAN-meta/issues/1)).
- **An embedded copy** in the client as offline fallback, refreshed manually before releases ([CKAN-KSA#42](https://github.com/KSAModding/CKAN-KSA/issues/42)).

## What the game forced for the CKAN fork

Each of these is a KSA fact that any manager hits, with the fork's answer as one worked example:

- **Mods live outside the game folder.** CKAN installs relative to the game directory and refused to write anywhere else. The fork added `IGame.ModDirectoryIsExternal` plus a path mapping so registry keys stay portable while files land in the user-global `Documents` mods folder ([CKAN-KSA#4](https://github.com/KSAModding/CKAN-KSA/issues/4), [CKAN-KSA#18](https://github.com/KSAModding/CKAN-KSA/issues/18)). This was the single largest change and the expected main review point upstream. A KSA-native design starts from the external root instead of retrofitting it.
- **The game owns `manifest.toml`.** The fork writes `enabled = true` for mods it installs and removes entries it managed on uninstall, but never flips the enabled state of an existing entry, and re-derives ids from on-disk folder names because that is what the game keys on ([CKAN-KSA#21](https://github.com/KSAModding/CKAN-KSA/issues/21), [CKAN-KSA#29](https://github.com/KSAModding/CKAN-KSA/issues/29)). It tracks which entries it manages in a sidecar file of its own, because the manifest itself cannot carry foreign keys: the game rewrites it from scratch (`ModManifest.Save`). The hardening round ([CKAN-KSA#29](https://github.com/KSAModding/CKAN-KSA/issues/29)) added exactly the cases the game creates: an in-game disable must survive a CKAN operation, parsing must tolerate quoting and comments, matching must be case-insensitive on Windows.
- **Version detection** reads the PE FileVersion of `KSA.dll` first, with the newest `Content/Versions` file as fallback ([CKAN-KSA#40](https://github.com/KSAModding/CKAN-KSA/issues/40), [CKAN-KSA#43](https://github.com/KSAModding/CKAN-KSA/issues/43)), the same order `research/ksa-versioning.md` recommends.
- **CI needs fake instances.** The metadata tester verifies a mod by installing it into a faked install. That required teaching instance faking to write the version file the detector reads ([CKAN-KSA#30](https://github.com/KSAModding/CKAN-KSA/issues/30), [CKAN-KSA#34](https://github.com/KSAModding/CKAN-KSA/issues/34)), and an end-to-end run proving the whole chain, inflate, install, remove, against a real faked KSA instance ([CKAN-KSA#41](https://github.com/KSAModding/CKAN-KSA/issues/41)).

## Friction that was structural, not fixable in a fork

- **Everything downstream gated on one merge.** The metadata tester and the indexer bot run Docker images built from the upstream client repo, so PR validation, automated indexing, and the status page all waited on the upstream review that has not come. The fork proved the full pipeline anyway by rebuilding the image from its own sources ([CKAN-KSA#41](https://github.com/KSAModding/CKAN-KSA/issues/41)), but the production path has a single choke point that is somebody else's calendar. A design that self-hosts its automation on GitHub Actions avoids inheriting one.
- **The shared format could not say "KSA".** Compatibility fields are literally named `ksp_version` in KSA metadata, and the schema is shared across games, so per-game rules had to live in validators rather than the schema. Renaming was judged a cross-cutting spec change touching every already-published file, raisable upstream but never a fork decision ([CKAN-KSA#52](https://github.com/KSAModding/CKAN-KSA/issues/52) has the discussion).
- **A fork of a mature project carries its history.** WinForms, Kerbal branding throughout, and conventions (default branch `master`, merge-heavy history) that generated review friction of their own before any KSA line was read.

## What is live today and consumable by any client

The metadata side needs no CKAN client and no permission:

- Full index as one tarball: `<https://github.com/KSAModding/KSA-CKAN-meta/archive/main.tar.gz>`
- One JSON file per mod release under `KSA-CKAN-meta/<Mod>/`, format documented in the fork's `Spec.md`
- Game version list, self-updating hourly: `https://raw.githubusercontent.com/KSAModding/KSA-CKAN-meta/main/builds.json`

## Implications for Proposals for this project

- **Copy the authored/generated split.**
- **Validate at publish time, in front of the author via GitHub actions checks.**
- **Take the versioning model, skip the workaround.** Revision ordering is proven in production; the build-counter normalization was CKAN's constraint, not ours (RFC 0017).
