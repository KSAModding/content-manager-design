---
rfc: "0035"
title: Content install descriptor
status: Accepted
authors: ["@SafeShows"]
created: 2026-08-09
discussion: https://github.com/KSAModding/content-manager-design/pull/35
supersedes: []
superseded-by: []
---

# RFC 0035: Content install descriptor

## Summary

One `[install]` section on the authored file of every content type, saying where the content is written and what a person still has to do by hand, plus a `[provides]` section on a `mod-loader` saying what that loader offers the content installed under it.

RFC 0031 gives content an identity, releases and versions, and it already carries half of this: an `[install]` table with a `root` key, describing where inside the archive the content lives.
It says nothing about where the content goes on disk, and deliberately so: it records that "install semantics and the manager/loader boundary are their own decisions".
This is a proposal for the first half of that sentence, for every type at once.

This RFC replaces RFC 0031's `[install]` table with a superset, and it does not bump `spec_version`.
It also decides two pieces of the manager/loader boundary ([#20](https://github.com/KSAModding/content-manager-design/discussions/20)), which the section on that boundary states in full.

## Motivation

Every type in [RFC 0025](0025-scope.md) installs somewhere, and today exactly one of them installs somewhere a manager can work out for itself.

**A mod is the easy case, and it is easy by convention rather than by statement.**
A mod folder goes into the game's mods folder under `Constants.DocumentsFolderPath`, and the folder name is the identity, because `Mod.MakeUsing` overwrites anything else (see [research/ksa-mod-loading.md](../research/ksa-mod-loading.md)).
Every manager can do that without being told.
But the convention is written down nowhere in the format, and RFC 0031 already had to break it once: `[install].root` exists precisely because some archives do not have the standard layout.
The format therefore already has an install descriptor; it just describes the inside of the archive and stops at the archive's edge.

**A loader is the hard case, and no two loaders need install the same way.**
StarMap installs into a directory of its own, outside both the game folder and the user data folder, and is pointed at the game through `GameLocation` in a `StarMapConfig.json` beside itself.
Afterwards the player launches `StarMap.exe`, not the game: the running process is the loader (see [research/starmap.md](../research/starmap.md)).
None of that is discoverable from the archive, and none of it is expressible in RFC 0031 today.

**Vehicles and saves are the case nobody has written yet.**
RFC 0025 puts them in scope and notes that every type lands under the same user-global root.
They install to a different place than a mod does, under that same root, and nothing in the format can say which place.

Two consequences do not follow from any one of those cases and are the reason to act now rather than per type:

- **Hardcoding is a one-loader ecosystem.** The moment a second loader exists, every manager needs a patch before anybody can use it, and the loader author cannot ship that patch themselves.
- **The player gets prose or nothing.** Install instructions live in a README, a forums post or a Discord pin, in whatever shape the author chose, and go stale silently.

Doing nothing keeps installation a per-type special case that each manager reimplements from each author's documentation, which is the same position mod metadata was in before RFC 0031.

## Guide-level explanation

### If you wrote a mod, you do nothing

The default is the convention, and the convention is now stated rather than assumed:

```toml
id = "AdvancedFlightComputer"
type = "mod"
# no [install] section
```

That means: unpack into the game's mods folder, as a folder named `AdvancedFlightComputer`.
It is what every manager already does, and it stays valid without an edit.

You add the section when something about your archive or your mod is not the default:

```toml
[install]
# Where inside the archive your content actually starts. This key is unchanged from RFC 0031.
root = "build/AdvancedFlightComputer"

# Anything a person still has to do, in your words. Rendered in order, one step per entry.
steps = [
  "New mods install disabled. Relaunch the game once to enable them.",
]
```

### If you wrote a loader, you say where it goes and what it offers

Your authored file already says what it is:

```toml
id = "StarMap"
type = "mod-loader"
name = "StarMap"
authors = ["KlaasWhite"]
abstract = "The loader KSA code mods run on."
license = "MIT"

[releases]
github = "StarMapLoader/StarMap"
```

Add where it is written:

```toml
[install]
# Its own directory, outside the game folder and outside the user data folder.
target = "standalone"

# How to remove it without leaving the install broken.
uninstall = [
  "Delete the StarMap directory. The game runs unmodded again with no further cleanup.",
]
```

And what it offers the content installed under it:

```toml
[provides]
# After installing, this is what the player runs, relative to where the loader was installed.
launch = "StarMap.exe"

# The anchor this loader reads content from. StarMap reuses the game's own discovery, so it is
# the game's mods folder; it adds no location of its own.
content-dir = "mods"

# The loader's own configuration file, and which well-known value a manager must write where.
[provides.configure]
file = "StarMapConfig.json"
format = "json"
game-path = "GameLocation"
```

A manager can now install your loader without knowing what a loader is, and point it at the game without a human, because every fact it needs is in the file.
An index can print your remaining steps as steps, in your words, next to the download, rather than linking to a README that says something different from what you shipped last week.

Nothing is added to `mod.toml`, and nothing is added to the archive.
The loader stays free of manager metadata, exactly as RFC 0031 requires.

## Reference-level explanation

### Where it lives

On the **authored file**, alongside `[releases]`, and not in the archive or in `mod.toml`.
RFC 0031 already settled that metadata lives in the index ([Where metadata lives](0031-content-metadata-format.md#where-metadata-lives)), an install descriptor is manager metadata by definition, and keeping it there means a wrong layout is corrected by editing the index rather than by cutting a release.

### Anchors

Every destination in this RFC is an **anchor** plus an optional relative path.
A manager resolves the anchor at install time; the format never contains an absolute path.

| Anchor | Resolves to |
|---|---|
| `mods` | The game's mods folder, `ModLibrary.LocalModsFolderPath`. Under an instance path override it moves with the profile, which is why this is an anchor and not `user-data` plus a path. |
| `user-data` | The game's user data root, `Constants.DocumentsFolderPath`. Where saves, vehicles, settings and the manifest live. |
| `game-root` | The directory holding the game executable and `Content/`. |
| `standalone` | A directory of the manager's own choosing, outside all three. The manager names it; the content does not. |

New anchors arrive by RFC.

### `[install]`

Optional on every type except `modpack`, where it is invalid: a pack ships no files and installs nothing of its own.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `root` | string | no | Directory inside the archive whose contents become the installed content. Unchanged from RFC 0031. Absent means derived, per rule 9. |
| `target` | string | see below | The anchor the content is written to. |
| `path` | string | no | Path below the anchor, relative to it. Absent means the anchor itself. |
| `manages` | array of strings | no | Paths, relative to the install location, that this content owns and rewrites. A manager must not edit them; a manager that needs one changed asks the content instead. |
| `steps` | array of strings | no | Ordered actions a person must take that a manager cannot perform. Plain sentences, in the author's voice. |
| `uninstall` | array of strings | no | Ordered actions to remove the content cleanly. |

`target` is required when the section is present and the type has no default.
A type with a default may omit it, which is what keeps an existing RFC 0031 file carrying only `root` valid and meaning exactly what it meant.

### Defaults per type

Absent is not the same answer everywhere, because the types differ in whether a convention exists.
This table is the whole meaning of an absent section; a present section with an absent key follows the key's own row above.

| Type | Absent `[install]` means |
|---|---|
| `mod` | `target = "mods"`, no `path`, installed as a folder named by the id. The universal convention, now stated. |
| `mod-loader` | Undescribed. The manager installs nothing automatically and shows the listing's links instead. There is no convention to fall back on, and a manager must not guess. |
| `modpack` | Nothing. The section is invalid on this type. |
| `vehicle`, `save` | `target = "user-data"`, with the `path` the game uses for that type. That path is named by those types' own RFCs, per RFC 0025; until one lands, `path` is required and there is no default. |

The mod default is not merely a convenience.
The folder name is the identity the game will see, so a mod's install location is not the author's to choose in the first place, and stating it as a default rather than an authorable field keeps it that way.

### `[provides]`

Optional, permitted only where `type = "mod-loader"`.
It describes what the loader offers the content installed under it, which is a different question from where the loader itself goes, and that is why it is a different section.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `launch` | string | no | Path, relative to the loader's install location, of the executable the player runs after installing, run with the working directory set to that location per rule 5. Absent means installing this loader does not change what you launch. |
| `content-dir` | string | no | The anchor this loader reads content from, from the anchor vocabulary above. Absent means the loader does not read a content directory and a manager must not invent one. |
| `content-path` | string | no | Path below `content-dir`, relative to it. Absent means the anchor itself. |

`content-dir = "mods"` is StarMap's answer, and it says something specific: the loader reuses the game's own discovery and adds no location of its own, because `ModLoader.PrepareMods` calls `ModLibrary.PrepareManifest` and looks exactly where the game looks.
A loader that did introduce its own directory would say `content-dir = "standalone"` with a `content-path`.

### `[provides.configure]`

Optional, permitted only inside `[provides]`.
It names the loader's own configuration file and where in it a manager writes the values a manager knows and the loader cannot.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `file` | string | yes | Path to the configuration file, relative to the loader's install location, which rule 5 makes the same directory the loader itself resolves relative paths against. |
| `format` | string | yes | `json` or `toml`. A manager must be able to write the file without a parser it does not have. |
| `game-path` | string | no | The key, inside that file, that receives the absolute path of the game directory. |

The value keys are a closed enum, `game-path` is its only member in `spec_version = 1`, and new members arrive by RFC, as do new `format` values.
Each member names a fact the manager already holds because it manages the install; none is author-supplied data, and none is a template.

A key is addressed by dot-separated path from the document root, so `loader.game.path` addresses the nested key.
A configuration key whose own name contains a dot cannot be addressed in `spec_version = 1`.
A manager writes only the keys named here and preserves the rest of the file, and creates a file that does not exist yet containing only those keys, which is enough for a loader that writes its own template on first run.

**This section turns the loader's own configuration file into a contract that managers machine-write, so it is only sound if the loader author authors and maintains it.**
That is not a hope: [RFC 0033](0033-content-index.md) binds ownership of a listing to its release authority, so the StarMap listing binds to `StarMapLoader/StarMap` and only an account with write access there can create or change it.
A third party cannot publish a descriptor that makes managers write into somebody else's configuration file, and a loader author who changes their configuration format changes the listing in the same pull request they already have to open.
The failure mode this leaves is a stale descriptor from an author who stopped maintaining the listing, which is the same failure mode every other authored field already has.

### The manager/loader boundary (#20)

RFC 0031 defers how a client installs a `mod-loader` to the manager/loader boundary track ([#20](https://github.com/KSAModding/content-manager-design/discussions/20)).
This RFC does not wait for that track, and it does not settle it either, so what it decides is stated here rather than left to be inferred.

Decided here, because a descriptor that omitted them would not let a manager install a loader at all:

- **The launch target, and the working directory it runs in.** `[provides].launch` names the executable the player runs after installing, and rule 5 fixes the working directory to the loader's install location. That the running process can be the loader rather than the game is a fact about StarMap (`Program.Main` hosts the game in-process), not a boundary this RFC draws; the working directory is a boundary, and it is drawn here because the alternative is a configuration contract that silently writes to a file nobody reads.
- **A manager writing the loader's configuration.** `[provides.configure]` lets a manager set the values it holds, bounded to a closed enum whose only member today is the game path.

Left to #20, and deliberately not answered here:

- **What an instance is**, and therefore the launch-time contract around it. StarMap takes `-InstancePath` and `STARMAP_INSTANCE_PATH`, which is the only mechanism by which two setups can hold different mod sets, and `[provides]` has nothing for it.
- **Whether a manager may drive the loader at runtime**, which is what unresolved question 1 about `manages` runs into.
- **Whether the loader's own in-development mod management and a manager overlap or divide**, which is the substance of #20 and untouched by anything here.

### Rules

1. **Paths are relative and must not escape.** Every path is relative to the anchor or location named in its row. A path that is absolute, that starts with `~`, or whose normalised form leaves its anchor, makes the file invalid. An install descriptor is executed by a manager with write access to a game directory, so path containment is a validity rule and not a recommendation.
2. **Separator is `/`.** Regardless of platform. A manager translates.
3. **`launch` must exist in the archive.** A descriptor naming an executable the release does not contain is invalid, and a validator can say so at import rather than a player finding out.
4. **`target = "standalone"` requires `launch`.** A directory nothing ever runs from and nothing reads is not an install, and permitting it would let a descriptor scatter files with no way to ever reach them.
5. **The launch working directory is the loader's install location.** A manager runs `launch` with the process working directory set there, and that is what makes every path in `[provides.configure]` name the file the loader will actually read. Without the rule the two ends disagree: `LoaderConfig.TryLoadConfig` resolves `StarMapConfig.json` against the process working directory rather than against the executable, so a manager launching from anywhere else reads a different file than the one it wrote, and finds no `GameLocation` in it. StarMap moving its own working directory to the game folder afterwards, in `GameSurveyer.TryLoadCoreAndGame`, does not conflict: the configuration is already loaded by then.
6. **`manages` cannot claim a file the game owns.** `manifest.toml` under `user-data` is written by `ModManifest.Save` from the game's own in-memory list, which destroys any key, comment or formatting it did not write. It is the game's, no descriptor may claim it, and a manager must expect it to change underneath both of them.
7. **`steps` and `uninstall` are prose, not instructions to a machine.** No manager may parse them for actions. They exist because some things genuinely cannot be automated, and pretending otherwise produces a manager that silently does half a job.
8. **Absent is not empty.** An absent `steps` means the author said nothing; `steps = []` means the author states there are none. A manager may report the difference.
9. **`root` derivation is per type.** For `mod`, RFC 0031's rule stands: one top-level directory containing `mod.toml`, its name matching the id. For every other type the derived root is the archive root itself, and an author whose archive differs states `root`.

### Errors

| Condition | Result |
|---|---|
| `[install]` on `type = "modpack"` | File invalid. A pack installs no files of its own. |
| `[provides]` on any type other than `mod-loader` | File invalid. |
| `target` missing on a type with no default | File invalid. |
| `target`, `content-dir`, or `format` carrying an unrecognised value | File invalid. Unrecognised rather than ignored, because a future value means a layout this manager cannot perform, and guessing would write files somewhere the author did not choose. |
| `target = "standalone"` without `[provides].launch` | File invalid. |
| An unrecognised key inside `[provides.configure]` | File invalid. The table is a closed enum, and a key silently ignored is a loader that starts misconfigured. |
| `manages` naming `manifest.toml` under `user-data` | File invalid. |
| Any path escaping its anchor | File invalid. |
| `launch` naming a file absent from the release | Release rejected, reported to the author. |

### Effect on the generated release file

RFC 0031 stamps an `install` object into each release file, currently `root` and `derived`, and says that for `type = "mod-loader"` the object is absent.
Both change: the object gains the resolved destination, and a loader's release file carries it like any other watched type.

```json
"install": { "root": "StarMap", "derived": true, "target": "standalone" }
```

`target` and `path` appear as resolved at stamp time, and are absent where the type default applies.

`[provides]` is **not** stamped into a release file.
It says what the loader offers right now, and a manager acting on a stale copy would write mods into a directory the installed loader no longer reads.

### Relationship to RFC 0031

The `[install]` table defined under RFC 0031's "Watched types" becomes the table defined here.
`root` keeps its name, its meaning, and its derivation rule for mods, so every file written against RFC 0031 stays valid and means the same thing.
The one other sentence that stops holding is the release file's, covered above.

`spec_version` stays at `1`.
Adding optional fields is not a break by RFC 0031's own evolution rule, `root` did not change meaning, and `[install]` was never permitted on a pack, so nothing that was valid became invalid.

## Drawbacks

- **It is a second vocabulary for installation**, and the boundary against the manager's own job is a judgement call that will be re-argued. `manages` in particular is close to being a lock on files a manager may otherwise reasonably touch.
- **`[provides.configure]` is the thin end of a wedge.** It writes author-named keys into an author-named file, and the only thing keeping it from becoming a configuration language is that the value side is a closed enum of one. Every future member is a small argument that will be easy to win.
- **It commits managers to a boundary #20 has not drawn yet.** Two of that track's questions get answered here by a format that ships first, and if #20 lands somewhere else, `launch` and `[provides.configure]` are what has to move.
- **Anchors are an enum, and enums in a format are a standing tax.** Every new install shape needs an RFC before any content can express it, and the first loader that does not fit will feel that.
- **Per-type defaults mean absence means four things.** A reader has to know the type to know what an absent section says, and a manager has to implement a table rather than a rule.
- **`steps` invites a README in a TOML array.** Nothing here bounds length or tone, and a manager rendering ten paragraphs of prose in a modal has a worse experience than the link it replaced.
- **Untestable against a second implementation.** There is one loader today, and the vehicle and save types do not exist yet, so this design is drawn from a sample of one and a half and will be shaped by whatever the second loader and the first vehicle turn out to need.

## Alternatives

**Keep it loader-only**, as this RFC's first draft did.
Smaller, and it needs no reconciliation with RFC 0031.
Rejected because the format then carries two install vocabularies, `[install].root` for mods and something else for loaders, describing the same operation from opposite ends, and because vehicles and saves would arrive needing a third.

**Keep hardcoding StarMap.**
Honest about the current ecosystem and free to build.
It makes the second loader an ecosystem-wide patch, and makes every manager's behaviour a fact about that manager rather than about the loader.

**Put the descriptor in the archive.**
Attractive because it travels with the bytes and needs no index.
Rejected because it reverses RFC 0031's stated principle, and because it means the install layout can only be corrected by cutting a release.

**A full install script.**
Maximum expressiveness, and the reason no ecosystem should want it: a manager would be executing author-supplied code with write access to a game directory.

**Leave loader configuration to prose.**
`steps` saying "point `GameLocation` at your game folder" is smaller, needs no enum, and keeps the format out of the loader's configuration file entirely.
Rejected because it is the exact gap the RFC exists to close: a loader that cannot be configured unattended cannot be installed unattended.
`[provides.configure]` is the bounded middle between this and a script, with the manager supplying the value, the author supplying only its address, and the set of values fixed by RFC.

**Wait for #20.**
The boundary track owns loader install, and a descriptor written after it would not have to guess.
Rejected because the two pieces decided here are the minimum for a manager to install a loader at all, and because the wait has no end date while every manager ships hardcoded StarMap support in the meantime, which is harder to undo than a format key.

**Leave it to each index.**
The status quo: ksamods.gg could serve its own answer from its own API tomorrow.
It would be one index's private extension, no more portable than hardcoding, and it would compete with rather than complete RFC 0031.

## Unresolved questions

1. **Does `manages` bind a manager, or only inform it?** A manager that can never write a file it is told is owned cannot offer to change what is in it without a channel to the owner, and no such channel exists. This is #20's to settle.
2. **Who chooses the `standalone` directory, and does the choice survive?** The manager picks it, but a player who installed the loader by hand already has one, and nothing here lets a manager adopt an existing install rather than making a second one.
3. **Should the working directory be authored rather than fixed?** Rule 5 pins it to the install location because that is what StarMap needs, and a loader that wants the game folder instead, which is where StarMap moves itself once the configuration is loaded, currently has no way to say so.
4. **Should the anchor enum allow an arbitrary relative path** instead, with containment doing the safety work? More expressive, and it moves a class of mistake from validation into runtime.
5. **Per-platform install shapes.** RFC 0031 has `os`; this section has nothing equivalent, and a loader whose layout differs on Linux currently cannot say so, which StarMap's Linux situation makes concrete rather than hypothetical.
6. **Whether an index may render `steps` at all**, or whether they belong only to a manager at install time. Rendering them on a listing page is useful and makes the index a publisher of the author's prose.
7. **Migration.** For mods there is nothing to migrate, by construction. The question is whether `[install]` and `[provides]` are required for `mod-loader` from the start or stay optional indefinitely.

## Future possibilities

- **The vehicle and save defaults**, filled in by those types' own RFCs, which is the one hole this RFC leaves open deliberately rather than guessing at folder names that do not exist yet.
- **A conformance test a content author can run**: install into a scratch directory from the descriptor alone, and report what a manager would do.
- **Declared load-order constraints**, if a loader ever needs to say more than "content goes here".
- **Adopting an existing manual install**, which needs a way to recognise a loader on disk rather than only to place one.
