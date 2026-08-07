---
rfc: "0031"
title: Content metadata format
status: Proposed
authors: ["@Maximilian-Nesslauer", "@MrJeranimo"]
created: 2026-08-05
discussion: https://github.com/KSAModding/content-manager-design/pull/31
supersedes: []
superseded-by: []
---

# RFC 0031: Content metadata format

## Summary

One metadata format for every published content type, as a shared core plus a small per-type extension.

For a mod, the metadata is two files with two different writers.

- The author writes one TOML file, once, carrying the facts that rarely change:
  - identity
  - links
  - license
  - compatibility bounds
  - loader
  - dependencies
- Tooling stamps one JSON file per release, unattended, carrying the facts of that release:
  - version
  - download location
  - checksum
  - sizes
  - install root
  - the resolved dependency list
  - a snapshot of how the listing described itself at that moment

A mod pack has no generated half.

A pack is pure reference metadata: one authored TOML document per pack version, pinning exact `(id, version)` pairs for mods and, with the same entry shape, vehicles and saves.

Metadata lives in the index, not inside the mod archive.
Nothing is added to `mod.toml`, and the loader stays free of manager metadata.

This RFC defines the format and the client behavior it implies.
How the index stores, updates, moderates, and serves these files is the index RFC ([#27](https://github.com/KSAModding/content-manager-design/discussions/27)); install semantics and the manager/loader boundary ([#20](https://github.com/KSAModding/content-manager-design/discussions/20)) are their own decisions.

## Motivation

A manager needs to answer "what is this, what does it need, and is it compatible" without downloading and unpacking archives first, and nothing in the ecosystem can answer that today.

The game reads no version, author, or dependency data from a mod: `mod.toml` carries none of it, and the game has no concept of a mod version at all (see [research/ksa-mod-loading.md](../research/ksa-mod-loading.md)).

The only dependency data that exists anywhere is the `[StarMap]` section of `mod.toml`, which is loader configuration, name-only and deliberately without versions (see [research/starmap.md](../research/starmap.md)).

Without a shared format, every client invents its own guesses.
[Borea](https://github.com/KSAModding/Borea) already normalizes other people's free-text version strings because nothing enforces a scheme at publish time, and every further client would repeat that.

This format is the ground the index RFC, the install semantics, and Borea's storage model all build on.

It records the convergence of the pre-RFC discussions [#15](https://github.com/KSAModding/content-manager-design/discussions/15) (mods) and [#16](https://github.com/KSAModding/content-manager-design/discussions/16) (packs) as one format, because the two field lists overlapped by about eighty percent, and separate formats would drift apart with every future content type adding another copy.

## Guide-level explanation

### Publishing a mod

You write one file and you are listed.
It states who you are, where releases appear, what the mod needs, and the oldest game version it works with:

```toml
spec_version = 1
id = "AdvancedFlightComputer"
type = "mod"
name = "Advanced Flight Computer"
authors = ["Maxi"]
abstract = "Extra maneuver planning tools for Kitten Space Agency."
license = "MIT"
tags = ["control"]

# Where releases appear; the watcher picks new ones up from here.
[releases]
github = "Maximilian-Nesslauer/KSA-AdvancedFlightComputer"

[links]
forums = "https://forums.ahwoo.com/threads/advanced-flight-computer.783/"
repository = "https://github.com/Maximilian-Nesslauer/KSA-AdvancedFlightComputer"
spacedock = "https://spacedock.info/mod/4253/AdvancedFlightComputer"
bugtracker = "https://github.com/Maximilian-Nesslauer/KSA-AdvancedFlightComputer/issues"

# Oldest game version known to work, written the way the game displays it.
# A month is also accepted: game_min = "2026.7"
# game_max exists too and is optional; above it a client warns instead of blocking.
# os = ["windows"] names the platforms known to work; absent means no known restriction.
[compatibility]
game_min = "2026.8.3.5117"

# Only for code mods. Absent means the mod runs without a loader.
# The recommended default is a min with an open upper end.
[loader]
id = "StarMap"
min = "0.4.5"
```

From then on you tag a release on GitHub or upload to SpaceDock and go to bed.

The watcher fetches the archive, computes the checksum, reads the code dependencies out of the archive's own `mod.toml`, stamps a release file, and your release is installable.

A version that does not parse is rejected at publish time with the error in front of you, instead of surfacing later in front of users.

You touch the authored file again only when the mod's facts change: a new dependency bound, a new link, or the day you stop maintaining it:

```toml
status = "deprecated"
superseded_by = "AdvancedFlightComputerNG"
```

Clients then warn and point users at the successor, but never block the install.
A single broken release can be yanked the same way: it stays in the history, but clients stop offering it.
A release that turns out to break only above a certain game build gets its compatibility tightened after the fact instead of a yank, so it stays installable where it works; a dependency bound that was stamped too loose, or an entry that was missing, is corrected the same way.

### Publishing a mod pack

A pack is one TOML document per pack version, and publishing it is a human act: there is no release archive, so there is nothing for a watcher to watch.

The document is self-contained and pins the exact set you curated and tested:

```toml
spec_version = 1
id = "NavigationStarterPack"
type = "modpack"
name = "Navigation Starter Pack"
authors = ["Maxi"]
abstract = "Everything you need for maneuver planning, tested together."
license = "CC0-1.0"
tags = ["navigation"]
version = "1.0.0"
released_at = "2026-08-05T12:00:00Z"

[links]
forums = "https://forums.ahwoo.com/threads/navigation-starter-pack.999/"

[compatibility]
game_min = "2026.8.3.5117"

# Exact pins, not ranges: a pack is a curated, tested set.
[[mods]]
id = "AdvancedFlightComputer"
version = "0.7.0"

[[mods]]
id = "KittenExtensions"
version = "0.4.0"

[[vehicles]]
id = "ReusableBoosterDemo"
version = "1.2.0"

[[saves]]
id = "ApolloRecreation"
version = "1.0.0"
```

The pack never redistributes anyone's files; each member downloads from its own release host.

### What a client shows

A client renders its listing from the authored files and evaluates a concrete release from the generated files, joined by id.

A release also remembers how the listing described it at the time it shipped, so browsing version 3 does not show features that only arrived with version 4.

Compatibility follows [RFC 0017](0017-game-version-ordering-and-compatibility.md): incompatible blocks, untested and unknown warn and let the user proceed.

## Reference-level explanation

### Where metadata lives

Authored and generated files both live in the index.

Nothing is added to the mod archive or to `mod.toml`: the game overwrites any id a file declares with the folder name (`Mod.MakeUsing`), so in-archive identity would lie, and the loader's own section stays loader configuration rather than manager metadata (recorded in [RFC 0025](0025-scope.md)).

The watcher reads the archive's `mod.toml` as a data source, it never writes to it.

This also means fixing authored metadata is an index change, not a mod re-release.

Listing facts (name, abstract, links, tags, status) apply to the whole listing the moment they change; the facts a resolver acts on (compatibility, loader, dependencies) are frozen into each release file.
Each release file additionally carries a snapshot of the listing facts as they stood at stamp time (the `listing` block below), so a release can be displayed as it was described then, while listing views stay live.

### The id

The id is the identity of the content, and for mods it is not something this spec gets to choose: the folder name is the entire namespace, because `Mod.MakeUsing` assigns the id from the folder name and overwrites whatever `mod.toml` declared (see [research/ksa-mod-loading.md](../research/ksa-mod-loading.md)).

The spec is deliberately stricter than any single filesystem, because the id must be a valid folder name on Windows, Linux, and macOS at once, and `ModManifest.Save` writes it into the manifest unescaped, so a quote in a folder name corrupts the file.

Rules:

- 1 to 64 characters, ASCII letters, digits, `-`, `_`, and `.` only.
- The first and last character must be a letter or a digit.
- Ids compare case-insensitively; the authored casing is preserved for display and on disk.
- The namespace is global across content types: a mod, a pack, and a loader can never share an id, so every reference to an id stays type-free.
- Reserved, compared case-insensitively against the id up to its first `.`, because Windows treats dotted forms such as `CON.mod` as devices too: `Core` (the game ships `Content/Core` and exempts its manifest entry from cleanup in `ModLibrary.PrepareManifest`), and the Windows device names `CON`, `PRN`, `AUX`, `NUL`, `COM1` through `COM9`, `LPT1` through `LPT9`.

As a regex:

```text
^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,62}[A-Za-z0-9])?$
```

The rationale for each boundary:

- ASCII only, because macOS normalizes non-ASCII folder names differently than other platforms, so the same id could be two different byte sequences on two machines.
- No leading dot, because that hides the folder on Unix.
- No trailing dot and no space anywhere, because Windows silently strips or rejects them.
- Case-insensitive uniqueness, because folder names are case-insensitive on Windows and case-sensitive on Linux, so `MyMod` and `mymod` would be one mod on one platform and two on the other.
- 64 characters, because the id lands inside real paths under the user's Documents folder, and Windows caps a path at 260 characters unless long paths are enabled.

Everything expressive the id forbids belongs in the display name.

Machine-local identifiers, such as a manager's instance ids, are not published content and are not governed by these rules.

### The shared authored core

Every authored document, regardless of type, carries these fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `spec_version` | integer | yes | The version of this metadata format. `1` for everything this RFC defines. |
| `id` | string | yes | The content id, per the rules above. |
| `type` | string | yes | `mod`, `modpack`, or `mod-loader`. New types are added by RFC, per [RFC 0025](0025-scope.md). |
| `name` | string | yes | The display name. Free choice of characters and length. |
| `authors` | array of strings | yes | Display names of the authors. |
| `abstract` | string | yes | One or two sentences for list and search views. |
| `description` | string | no | Longer free text on top of the abstract, written as CommonMark Markdown; plain text is valid as-is, and a client that does not render Markdown shows the source. |
| `license` | string | yes | An SPDX license expression, such as `MIT` or `CC-BY-4.0`. |
| `tags` | array of strings | no | Free-form lowercase tags. A curated vocabulary can come later without a format change. |
| `status` | string | no | `active` (the default) or `deprecated`. The author's declaration about their own content. |
| `superseded_by` | string | no | The id of the successor. Only meaningful together with `status = "deprecated"`, because content can be abandoned without a successor. |

`status` exists because a renamed mod is unavoidably a different mod (the id is the folder name), so without a successor pointer every rename or continuation fork strands its users on a dead id.
Succession is a property of the mod, not a dependency: "I am replaced by X" does not mean "I need X", so it lives here rather than in the dependency list where every resolver would have to filter it back out.

`status` is deliberately not the index's voice: delisted, taken down, or disputed are statements about a listing, made by the index, and must not be writable by the author.
Their shape belongs to the index RFC.

The `[links]` table:

| Key | Required | Meaning |
|---|---|---|
| `forums` | yes | The KSA forums thread for this content. Required because the modding rules expect one, it ties the listing to an Ahwoo account, and the index uses it as a tiebreaker in id disputes and as a takedown tripwire (#27). |
| `repository`, `spacedock`, `bugtracker`, `homepage` | no | Plain links, shown as such. Further keys are allowed and treated the same way. |

The `[compatibility]` table; the game version fields follow [RFC 0017](0017-game-version-ordering-and-compatibility.md):

| Key | Required | Meaning |
|---|---|---|
| `game_min` | yes | Oldest game version known to work, written as the game displays it, or as a month such as `2026.7`. |
| `game_max` | no | Newest tested game version. Absent means no known upper limit, which is the recommended default. |
| `os` | no | The platforms the content is known to work on, from `windows`, `linux`, `macos`. Absent means no known restriction, which is the right default for portable managed code. New values arrive by RFC. |

The authored file of a mod carries no mod version.
Versions exist per release and are stamped by tooling; a pack's document carries one because the document is the release.

### Watched types: mods and mod loaders

`mod` and `mod-loader` share the release machinery: their releases appear on a host, a watcher picks them up, and each release gets a generated file.
The `mod-loader` type exists so loaders are listed, versioned, and referenced like everything else, while resolvers never have to ask whether a dependency is a loader.

Their authored files add:

**`[releases]`** names where releases appear: `github = "owner/repo"` or `spacedock = 4253` (the SpaceDock mod id).
With one host key, that host is the release authority the watcher polls.
More than one host key is allowed and then an `authority` key naming one of them is required: the authority defines which releases exist and when, and the other hosts are only checked for an archive with the same bytes, which is how `download.mirrors` gets populated.
The section is optional; without it, releases enter the index by pull request, which stays the path for content hosted anywhere the watcher does not watch (#27).

**`[loader]`** declares the loader a code mod needs, for `type = "mod"` only:

| Key | Required | Meaning |
|---|---|---|
| `id` | yes | The loader's id. Must reference content of type `mod-loader`. |
| `min` | yes | Oldest loader version known to work, inclusive, SemVer. |
| `max` | no | Newest known-working loader version, inclusive. Absent means open, which is the recommended default. |

An absent `[loader]` section means the content runs without a loader, which is how asset-only mods look.
The bounds are authored because they cannot be derived: the `[StarMap]` section of `mod.toml` deliberately carries no versions.

**`[[dependencies]]`** is an array of tables:

| Key | Required | Meaning |
|---|---|---|
| `id` | yes | The dependency's id. Must reference content of type `mod`. |
| `kind` | yes | One of the kinds below. |
| `min`, `max` | no | Inclusive SemVer bounds on the dependency's version. Absent `max` means open; the recommended default is a `min` only. |

| Kind | Resolver behavior |
|---|---|
| `required` | The content does not function without it. Installed always. |
| `optional` | Used when present, not installed by default. This is the authored mirror of StarMap's `Optional = true`, and what derived entries use. |
| `recommends` | Selected by default, deselectable by the user. |
| `suggests` | Listed, not selected. |
| `conflict` | Must not be installed together. Bounds narrow the conflicting range; no bounds means every version conflicts. |

An entry may carry `any_of` in place of `id`: an array of tables, each with an `id` and optional `min`/`max` bounds of its own, satisfied by any one of them.
It is valid with kind `required` or `recommends`.

```toml
[[dependencies]]
kind = "required"
any_of = [ { id = "OpenALRouter", min = "2.0.0" }, { id = "ClassicALRouter", min = "1.1.0" } ]
```

The loader is not repeated under `[[dependencies]]`, and the game is not a dependency; game compatibility has its own section.

An optional **`[install]`** table with a single `root` key overrides the derived install root for archives with an unusual layout; the standard layout needs nothing.

### The generated release file

One JSON file per release of a watched type, written by tooling at publish time and immutable afterwards, with the narrow class of post-publish amendments defined below.
Nobody hand-writes one: the single hand-written file in the CKAN-for-KSA index was invalid JSON and shipped a wrong install path (see [research/prior-art-ckan.md](../research/prior-art-ckan.md)).

The worked example, continuing the authored file above:

```json
{
  "spec_version": 1,
  "id": "AdvancedFlightComputer",
  "type": "mod",
  "version": "0.7.0",
  "version_scheme": "semver",
  "release_status": "stable",
  "release_date": "2026-08-02T13:18:41Z",
  "game_min": "2026.8.3.5117",
  "game_min_revision": 5117,
  "download": {
    "url": "https://github.com/Maximilian-Nesslauer/KSA-AdvancedFlightComputer/releases/download/v0.7.0/AdvancedFlightComputer.zip",
    "sha256": "ABC2A72E348AB26960FF59EDD019F160B12844099C30BF00F7D4E4D3D1ED5E74",
    "size": 131042,
    "content_type": "application/zip"
  },
  "install_size": 329449,
  "install": { "root": "AdvancedFlightComputer", "derived": true },
  "loader": { "id": "StarMap", "min": "0.4.5", "source": "authored" },
  "dependencies": [
    { "id": "KittenExtensions", "kind": "optional", "source": "derived" }
  ],
  "changelog": "https://github.com/Maximilian-Nesslauer/KSA-AdvancedFlightComputer/releases/tag/v0.7.0",
  "listing": {
    "name": "Advanced Flight Computer",
    "authors": ["Maxi"],
    "abstract": "Extra maneuver planning tools for Kitten Space Agency.",
    "license": "MIT",
    "tags": ["control"],
    "links": {
      "forums": "https://forums.ahwoo.com/threads/advanced-flight-computer.783/",
      "repository": "https://github.com/Maximilian-Nesslauer/KSA-AdvancedFlightComputer"
    }
  }
}
```

Field semantics:

| Field | Meaning |
|---|---|
| `spec_version`, `id`, `type` | As in the authored file. |
| `version` | The release version, normalized to [SemVer 2.0.0](https://semver.org/): a leading `v` on the tag is stripped, and a version that does not parse rejects the release at publish time, with the error in front of the author. SemVer's own pre-release ordering applies. |
| `version_scheme` | `semver`, the only value in `spec_version = 1`. Ordering is defined only within one scheme; admitting another scheme is a future RFC. |
| `release_status` | `stable`, `testing`, or `dev`. Derived from the host's release flags and the version's pre-release part, so a nightly does not look like a release. |
| `release_date` | ISO 8601 UTC timestamp of the release on its host. |
| `game_min`, `game_min_revision` | The authored bound as displayed, plus its resolved revision, so compatibility is evaluable offline with no index lookup (RFC 0017). `game_max` and `game_max_revision` appear when authored. |
| `os` | The authored platform list current at release time. Absent when unrestricted. |
| `download.url` | Direct download of the release archive from its own host; the index never hosts files (RFC 0025). |
| `download.mirrors` | Optional list of further URLs for the same archive, stamped when a non-authority host from `[releases]` serves an archive with the identical bytes. Any source whose bytes match `download.sha256` is acceptable, which also lets clients fall back to caches. |
| `download.sha256` | Hex SHA-256 of the archive, case-insensitive. Verifies the download and keys caches. |
| `download.size` | Archive size in bytes. |
| `download.content_type` | The archive format. Clients must support `application/zip`. |
| `install_size` | Unpacked size in bytes. Download and install size differ, so both exist. |
| `install.root` | The directory inside the archive whose contents become the installed folder. `derived` is `true` when the watcher found the standard layout: one top-level directory containing `mod.toml`, its name matching the id. A name mismatch is a validation error, because the folder name is the identity the game will see. |
| `loader` | The authored loader bounds current at release time, with `source`. Absent when the mod runs without one. |
| `dependencies` | The merged dependency list, each entry carrying `source`. |
| `changelog` | URL of the release's changelog. |
| `listing` | The shared authored core as it stood at stamp time, minus `status` and `superseded_by`: `name`, `authors`, `abstract`, `description` when present, `license`, `tags`, `links`. Lets a client display a release as it was described when it shipped. |
| `yanked` | `true` when the author has retracted this release; absent otherwise. Set as a post-publish amendment. |
| `yanked_reason` | Optional free text shown alongside the yank warning. |

The dependency merge: `derived` entries are read per release from the archive's own `mod.toml` (`[[StarMap.ModDependencies]]`, including `Optional`), `authored` entries come from the authored file, and an authored entry replaces the derived entry with the same id.
Derived entries carry no version bounds because the loader's section has none; authored entries are how bounds get added.
There is no way to suppress a derived entry, because the loader acts on that data at runtime, so it is ground truth for code dependencies.
An authored `any_of` entry joins the merge through its members: it replaces the derived entry of every member it names.
It is a validation error when a named member's derived entry did not carry `Optional = true`, because the loader refuses to start the mod without that specific dependency, so an alternative set would claim a choice that does not exist at runtime.

Stamping freezes the authored facts current at release time.
Editing the authored file affects future releases only, which is what keeps old releases correct without re-authoring them.

The `listing` block is that freeze applied to the descriptive facts, so version 3's entry never advertises what only version 4 ships.
`status` and `superseded_by` are deliberately not in it: deprecation and succession must reach every release the moment they are declared, so a client always reads them live from the authored file, and moderation reads the live `links.forums` for the same reason.
The block is display history, not an amendable surface: a typo in an old stamp stays, and corrections land in the authored file, where they fix the listing view and every future stamp.

A version is stamped exactly once.
If the host's tag for an already stamped version reappears with different bytes, the watcher rejects it and never overwrites; how that gets flagged is the index's business (#27).
The author's way forward is a new version, or a yank of the broken one.

A published release accepts a narrow class of post-publish amendments, and nothing else.
Every amendment records knowledge gained after publish, and it can only narrow what the release claims to support; who may make one is part of the index's publishing flow (#27).

- Setting `yanked = true`, with an optional `yanked_reason`: the author retracts the release entirely.
- Tightening game compatibility: adding or lowering `game_max` and `game_max_revision`, or raising `game_min` and `game_min_revision`.
- Tightening a dependency or loader bound: adding or lowering a `max`, or adding or raising a `min`, on an existing entry.
- Adding a dependency entry that was missing, including a `conflict`.

The invariant every amendment must satisfy: a release file can never become more permissive after publish, only less.
Widening or removing a bound and removing an entry are therefore never amendments; a release that turns out to support more than it was stamped with keeps its stamp, because nobody re-verified the wider claim against the actual archive.
Identity facts, the version, the download, and the install data, are what immutability protects, and they never change; the way forward for those is a new version, or a yank of the broken one.
A yank is the author's statement about one build, distinct from `deprecated`, which covers the whole listing, and from an index-side takedown, which is not the author's voice at all.

What `download.sha256` does and does not promise: a client that verifies it gets exactly the bytes the watcher stamped, so an archive swapped on its host after stamping fails verification instead of installing.
It does not say who built the archive, and it does not help when the host was already compromised at stamp time.
Signatures are deliberately out of `spec_version = 1`: they need a key story, who holds keys, how they rotate, what a client does on a mismatch, and that is its own decision, named under future possibilities.

For `type = "mod-loader"` the `install` object is absent: a loader installs outside the game's mods folder by its own mechanism, and how a client performs that is client-defined until the manager/loader boundary (#20) settles it.

### Mod packs

A pack is one authored TOML document per pack version, complete in itself, and immutable once published.
The mod side splits into authored and generated because a watcher stamps releases without a human; a pack has no download URL, so there is nothing to watch, no generated half, and the per-release fields are authored by hand.
The core fields repeat in every version's document, and that redundancy is accepted: a self-contained document beats cross-file merging where no tooling is involved.

On top of the shared core, a pack document carries:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `version` | string | yes | The pack's own version, SemVer 2.0.0, same rules as a mod release. |
| `released_at` | string | yes | ISO 8601 UTC timestamp, authored by hand. |
| `changelog` | string | no | URL or free text for this pack version. |
| `[[mods]]` | array of tables | yes | The curated set, each entry `id` plus exact `version`. |
| `[[vehicles]]`, `[[saves]]` | array of tables | no | Same entry shape as `[[mods]]`. |

Exact pins are deliberate, and they do not contradict the range model for dependencies: a dependency says "I need X to function", and that is a range because any X in the range works; a pack says "this exact set is what I curated and tested".

`[[vehicles]]` and `[[saves]]` are defined now even though the vehicle and save content types are not: [RFC 0025](0025-scope.md) already puts them in scope, the entry shape is the same, and defining the sections in `spec_version = 1` costs nothing today while saving a format bump the day those types land.

What a pack does not have:

- No download, checksum, or install data: a pack is its metadata, it carries no archive and never redistributes a member's files. Members download from their own release hosts.
- No `[releases]` section: nothing to watch.
- No `[loader]` section: loader requirements follow from the pinned mods, and an authored pin could only agree with or contradict them.
- No nested packs: a pack listing another pack is out for `spec_version = 1`.

The pack's `license` covers the pack's own list, description, and artwork, which is why something permissive is the natural default.
Packs that carry files of their own, such as config tweaks, reopen hosting, checksums, and third-party licensing, and are a deliberately postponed extension.

### Client behavior

The line taken everywhere in this format is warn, do not block, consistent with RFC 0017's rationale: the game validates nothing, so a false "incompatible" takes a working mod away from the user, while a false "compatible" is a mod that does not load and can be removed again.

- Listing and search views render live from the authored file. A release view may render the release's `listing` block, presented as what the listing said when the release shipped, and falls back to the authored file where the block or a field is absent. Deprecation, succession, and index status always evaluate from the live data.
- `deprecated` warns and surfaces `superseded_by` when present; it never blocks an install.
- A dependency or pack member whose id is not listed in the index warns, points at wherever the author says it lives, and lets the user proceed (#27).
- Game compatibility evaluates per RFC 0017; only incompatible blocks.
- A platform outside the stated `os` list warns and lets the user proceed: the list states what the author knows works, not everything that can.
- A yanked release is not offered for new installs or updates; an already installed copy stays untouched and shows the reason. A pack pinning a yanked version warns and lets the user proceed. A yank, like every post-publish amendment, exists only in the index: a cached release file cannot show it, so a client refreshes its index data before offering installs or updates.
- Metadata a client cannot interpret, including a `spec_version` newer than it implements, renders as an entry in an unknown state; it is never silently dropped.

### Format evolution

`spec_version` is a single integer stamped into every file.
Adding an optional field is not a break and does not bump it; clients ignore fields they do not know.
Removing a field, changing a field's meaning, or adding a required field is a break and bumps it.
New content types arrive by RFC and extend the `type` enum without a bump, because a client that does not know a type already treats it as unknown.

## Drawbacks

- A global id namespace across types means a pack can occupy a name a mod later wants, first come, first served.
- Authored metadata living in the index means an author touches the index, directly or through tooling, at least once. The self-service listing flow (#27) is what keeps that cheap.

## Alternatives

**A self-describing file inside the archive**, the Thunderstore and Modrinth model.
Rejected: `Mod.MakeUsing` overwrites the declared id with the folder name, so in-archive identity can silently lie; every metadata fix forces a re-release; and the loader author's position, recorded in RFC 0025, is that `mod.toml` should not carry manager metadata.

**One syntax for both halves**, all TOML or all JSON.
Rejected in #15: humans already write TOML here and machines already exchange JSON, and each half is only ever written by one side.

**Fully self-contained generated files**, the CKAN model where the release file is the only file and a client never needs the authored one.
Rejected in #15: a client needs the authored file anyway, because the live facts, status, succession, and current links, must not be frozen.
What this format does take from that model is the `listing` snapshot for release-accurate display, while the authored file stays the single live source, and offline compatibility evaluation is kept via `game_min_revision`.

**Version range expressions** such as `>=0.1.0 <0.2.0`.
Rejected in #15: an expression needs a parser whose edge cases we would have to specify ourselves, npm, cargo, and NuGet all differ subtly, while two typed inclusive fields are schema-validatable and map one to one onto what a resolver evaluates.

**Exact game version pins per release.**
Rejected by [RFC 0017](0017-game-version-ordering-and-compatibility.md): at KSA's release pace, equality marks the whole catalogue broken within days, wrongly.

**A generic content list in packs**, one `[[content]]` array with a `type` key per entry, so new types need no format change at all.
Rejected in #16 for the typed sections, which read better; new types still arrive cheaply because the entry shape is shared.

## Prior art

**StarMap's `[StarMap]` section** (see [research/starmap.md](../research/starmap.md)) is the only dependency data that exists today.
This format reads it as the derived baseline instead of duplicating it, so the manager's data can never disagree with what the loader actually does, and layers authored version bounds on top, which the loader deliberately does not carry.

**Debian's relationship kinds** (Depends, Recommends, Suggests, Conflicts) are the naming precedent for the dependency kinds.

## Unresolved questions

- Everything the index RFC owns (#27): storage layout, one repository or two, the stable fetch URL, the watcher, publish-time validation and ownership verification, and the moderation and takedown path.
- The index-side listing status (delisted, disputed): deliberately not authorable, shape to be defined with the index.
- The vehicle and save content types beyond their entry shape in packs: own RFC, per RFC 0025.
- Packs that carry their own files: postponed extension, see above.
- How a client installs a `mod-loader`: client-defined until the manager/loader boundary RFC (#20).

## Future possibilities

- New content types by RFC, cheap by construction: the required `type` field and the shared core were designed for exactly that (RFC 0025).
- A second loader, including an official one, would slot into `[loader]` and the `mod-loader` type as they stand; per-loader alternative builds of one mod would need a format extension.
- Release signing on top of the checksum, once a key management answer exists; the `download` object is where a signature field would land without a break.
