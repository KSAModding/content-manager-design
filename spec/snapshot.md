# The snapshot artifact

What a client fetches, and the whole contract between the index and the clients that read it.

[RFC 0033](../rfcs/0033-content-index.md) defines the snapshot as one JSON document merging every listed authored document, the release files of listed entries, the index status data and the game release list, carrying its own format version.
Vehicles and saves are the exception: each of the two types has a file of its own next to that document, see [Vehicles and saves](#vehicles-and-saves).
[RFC 0094](../rfcs/0094-share-host.md) moves the arrays `vehicles` and `saves`, which RFC 0085 named for this document, into these two files.

Everything downstream happens locally: search, dependency resolution and compatibility evaluation need these files and nothing else, offline included ([RFC 0017](../rfcs/0017-game-version-ordering-and-compatibility.md), [RFC 0031](../rfcs/0031-content-metadata-format.md)).

## What the builder does, and what it does not

The builder joins, filters, attaches and derives.
It never rewrites the content of a document.

- It **joins** each listing to its release files, so a client never sees the two-repository split.
- It **filters** out everything a delisted listing owns, and leaves a tombstone.
- It **attaches** the index's own state to the listing or the pack version that state names, and the download counts to the entry they count.
- It **derives** `published_at` and `updated_at` for each listing and pack from the version timestamps it carries.

Every authored document and every release file appears verbatim, exactly as the repositories hold it.
A field this page does not mention is still in the document, and a client reads it against RFC 0031, not against this page.

That is what keeps the snapshot auditable: any entry can be compared against the two repositories without first knowing what the builder would have computed.
It is also what keeps this page from becoming a second copy of RFC 0031's field tables, drifting away from the original one release at a time.

## Fetching it

The index publishes three files:

| File | Address | Holds |
|---|---|---|
| The main document | `https://ksamodding.github.io/content-index-releases/v1/index.json` | Mods, mod loaders, packs, the game release list and the curated tags. |
| The vehicle file | `https://ksamodding.github.io/content-index-releases/v1/snapshot-vehicles.json` | Vehicles. |
| The save file | `https://ksamodding.github.io/content-index-releases/v1/snapshot-saves.json` | Saves. |

The `v1` segment carries the snapshot format version, so a future break can be served next to what it replaces.

Poll each file with `If-None-Match` against its own ETag.
A file answers 304 while the host keeps its ETag, which on this host lasts until the next deployment, see [Determinism](#determinism).
A client need not fetch the vehicle file or the save file when it does not show that type, resolves no pack member of it and checks no id against it.

## Determinism

The builder writes the same bytes for the same input, and a file whose bytes are already published is not published again.
Both are needed, because publishing is a deployment and a deployment issues a new ETag either way.
Together they keep a cached copy valid: an unchanged index costs a client one 304, and the scheduled backstop rebuild costs it nothing.

Four rules carry that:

- **No wall-clock field.** A `generated_at` would change the bytes on every scheduled rebuild and invalidate every cached copy for no change in content. `sources` carries the provenance instead, and how stale a copy is comes from HTTP.
- **The provenance follows the content, not the clock.** `sources` names the state the published content was built from, so it moves only when the content moves. Each file carries its own `sources`, which moves only with that file's content. A commit that changes nothing the snapshot carries has to leave the bytes alone, or `sources` reintroduces the problem above, only slower.
- **Every array is ordered**, by the rules below, rather than left in the order a filesystem happened to hand its entries over.
- **UTF-8, no BOM, LF line endings, two-space indent.**

Object key order is not part of the contract, and a client must not depend on it.

The builder builds and compares each file on its own, so a publish that changes one file leaves the bytes of the others as they were.
Whether the others keep their ETag depends on the host.
GitHub Pages issues a new ETag for every file of the site on each deployment, so after a change to one file a client downloads the others once more, which costs a download and never correctness.
A deployment replaces the whole site, so each one carries every file that was already published, changed or not.

## The document

The main document:

| Field | Required | Meaning |
|---|---|---|
| `snapshot_version` | yes | The version of this format. `1` for everything defined here. |
| `sources` | no | Which state of the index this was built from. Absent on a snapshot built from anything other than the two index repositories. |
| `listings` | yes | Mods and mod loaders, never vehicles or saves. Ascending by lowercased id. |
| `packs` | yes | Mod packs. Ascending by lowercased id. |
| `game_versions` | yes | The game release list, verbatim. |
| `tags` | no | The curated tag vocabulary, `tags.toml` of the authored repository verbatim ([tags.md](tags.md)). Absent until that file exists. |
| `hosts` | no | The registered share hosts, `hosts.toml` of the authored repository verbatim ([share-host.md](share-host.md)). Absent until that file exists. |

```json
{
  "snapshot_version": 1,
  "sources": {
    "authored": { "repository": "KSAModding/content-index", "commit": "9fe1c0f" },
    "generated": { "repository": "KSAModding/content-index-releases", "commit": "3a77b21" }
  },
  "listings": [],
  "packs": [],
  "game_versions": {}
}
```

An empty index is `listings` and `packs` as empty arrays, never as absent fields.

### A listing

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | The content id, in its authored casing. Compared case-insensitively (RFC 0031). |
| `authored` | no | The authored TOML document, as JSON, verbatim. Absent only on a tombstone. |
| `releases` | no | The stamped release files of this listing, verbatim, descending by SemVer precedence. Absent only on a tombstone. |
| `index_status` | no | The index's own state for this listing. |
| `downloads` | no | The download counts of this listing ([RFC 0052](../rfcs/0052-static-download-counts.md)). Absent means unknown, never zero. |
| `published_at` | no | When the listing first appeared, from its release files. See [Dates](#dates). |
| `updated_at` | no | When the listing last had a release that is not yanked. See [Dates](#dates). |

`releases` is an empty array for a listing whose release host has no release yet, which RFC 0033 admits as a listing that passes its checks vacuously.
A client lists it and has nothing to install.

Mods, mod loaders, packs, vehicles and saves share one id namespace, compared without case (RFC 0031).
So an id is taken when an entry with it is in the main document, the vehicle file or the save file, a tombstone included.

Three voices sit side by side in one entry and never mix, which is why each has its own key: the author writes `authored`, tooling writes `releases`, `downloads` and the dates, and the index writes `index_status`.
The author's own `status` field, `active` or `deprecated`, is inside `authored` where it belongs, and it is not the same thing as `index_status`.

Each release also carries the `listing` block RFC 0031 freezes into it, so a release can be shown as it was described when it shipped, while `authored` stays live.

Entries of the types `vehicle` and `save` ([RFC 0085](../rfcs/0085-vehicles-and-saves.md)) have the same shape.
Two differences come from their documents, not from the builder:

- `links.forums` can be absent in `authored` and in the `listing` block of each release, and `[compatibility]` can be absent in `authored`. A client does not treat either as an error. A release still always carries `game_min` and `game_min_revision`, which come from the authored `game_min` or else from `version` in the archive's `meta.toml`.
- Each release carries `install.folder`, the `name` from the archive's `meta.toml`, next to `install.root` and `install.derived`. It has no `install.target` or `install.path`, because the type default of RFC 0085 applies.

### A pack

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | The pack id, in its authored casing. |
| `versions` | no | The pack version documents, descending by SemVer precedence. Absent only on a tombstone. |
| `index_status` | no | The index's own state for the whole pack. |
| `published_at` | no | When the pack first appeared, from its versions. See [Dates](#dates). |
| `updated_at` | no | When the pack last had a version that is not retracted. See [Dates](#dates). |

Each entry of `versions` is `{ "authored": <the pack document, verbatim> }`, plus an `index_status` when that version is retracted.
A pack has no generated half, so there is no `releases` here: the document is the release.

### Vehicles and saves

Entries of the types `vehicle` and `save` are not in the main document.
Each type has a file of its own, at the address in [Fetching it](#fetching-it), with the envelope of the main document and one array named after the type:

| Field | Required | Meaning |
|---|---|---|
| `snapshot_version` | yes | As in the main document. |
| `sources` | no | As in the main document, for the state this file was built from. |
| `vehicles` or `saves` | yes | The entries of that type, in the shape of [A listing](#a-listing). Ascending by lowercased id. |

```json
{
  "snapshot_version": 1,
  "sources": {
    "authored": { "repository": "KSAModding/content-index", "commit": "9fe1c0f" },
    "generated": { "repository": "KSAModding/content-index-releases", "commit": "3a77b21" }
  },
  "vehicles": [
    { "id": "ExampleRover", "authored": { "...": "..." }, "releases": [{ "...": "..." }] }
  ]
}
```

The game release list and the curated tags are only in the main document, and a client reads them from there.

The builder publishes no file for a type while the authored repository holds no listing of that type, delisted ones included, so nothing published changes before the first listing of that type.
A client that holds no copy of a type file treats a 404 for it as an empty array.
A client that holds a copy keeps it on a 404 and on any other failure, because a published type file never goes away, and a fault read as "no vehicles" would show every installed vehicle as unlisted.

A pack in the main document can pin a vehicle or a save, so a client reads the file of that type before it resolves such a member.

### Index status

`index_status` carries the state, and optionally when it was set and why:

| Field | Required | Meaning |
|---|---|---|
| `state` | yes | `delisted`, `disputed`, or `retracted`. |
| `since` | no | ISO 8601 UTC timestamp. |
| `reason` | no | One sentence, written for the user the client shows it to. |

The `version` key of an entry in the authored `index-status.toml` does not appear here.
It routes a `retracted` state to one pack version, and the builder resolves it by attaching the state to that version.

**`delisted` is a tombstone.**
The entry keeps its `id` and its `index_status` and carries nothing else, so a client can tell "removed" from "never listed" and knows the id is taken:

```json
{ "id": "SomeMod", "index_status": { "state": "delisted", "since": "2026-08-10T00:00:00Z" } }
```

A tombstone stays in the array its entry was in, which is what says whether the removed content was a mod or mod loader, a pack, a vehicle or a save.
Nothing is deleted from anyone's machine, and nothing is deleted from the repositories.

**`disputed` ships whole.**
The entry is complete and carries the state next to it, so a client shows a warning and lets the user proceed.

**`retracted` scopes to one pack version**, and a client treats it the way it treats a yanked release (RFC 0031).

### Download counts

`downloads` is the listing's entry from `download-counts.json` without the repeated `id`, in the shape [RFC 0052](../rfcs/0052-static-download-counts.md) defines.
The `listings` array of `download-counts.json` holds the counts of mods, mod loaders, vehicles and saves, and the builder joins each count to the entry with that id, wherever the snapshot carries it.
A tombstone and a pack carry none, and a count whose id matches no such entry fails the build.

An absent count means unknown, and a client must not show it as zero.
A client may show the counts and sort by them, keeps listings without counts available, and never uses the counts for resolution, installation, ownership or moderation.

### Dates

`published_at` and `updated_at` are derived from timestamps the entry already carries ([RFC 0058](../rfcs/0058-listing-images-and-dates.md)).
They sit next to `id`, never inside `authored`, a release file or a pack version.
The column "Listing" holds for vehicles and saves too.

| Field | Listing | Pack |
|---|---|---|
| `published_at` | The earliest `release_date` of all its release files, yanked ones included. | The earliest `released_at` of all its versions, retracted ones included. |
| `updated_at` | The latest `release_date` of a release file that is not yanked, of any `release_status`. | The latest `released_at` of a version that is not retracted. |

Timestamps compare as instants, and as text when two instants are equal.
The builder copies the winning value as the source document writes it.

```json
{
  "id": "AdvancedFlightComputer",
  "published_at": "2026-08-02T13:18:42Z",
  "updated_at": "2026-08-11T16:41:04Z",
  "authored": { "...": "..." },
  "releases": [{ "...": "..." }]
}
```

- An entry with no version has neither field. This includes a listing whose `releases` is an empty array.
- An entry whose every version is yanked or retracted has `published_at` and no `updated_at`.
- A tombstone has neither field.

The values follow the index, so they can move.
A yank or a retraction can move `updated_at` back, and a backfilled older release can move `published_at` earlier.

`updated_at` counts `dev` and `testing` releases, so it can show activity that a user of stable releases does not see.
A client may show a date per release channel instead, computed from `release_status` and `release_date` of the releases in the snapshot, and `updated_at` stays the all-channel value.

### The game release list

`game_versions` is the document the generated repository maintains, embedded verbatim, so a client needs no second request:

```json
"game_versions": {
  "spec_version": 1,
  "source": "http://ksa-master1.rocketwerkz.com:8082/version",
  "versions": ["2025.8.33.2091", "2026.8.3.5117", "2026.8.5.5168"]
}
```

Public production builds only, ascending by revision, which is the only component that orders (RFC 0017).

A client needs it to render a revision as the version string a user recognises, and to show where a compatibility bound sits in the release history.
It does not need it to evaluate compatibility: every release file carries `game_min_revision` and, where authored, `game_max_revision`, so that evaluation stays a comparison of integers with no lookup.

### The curated tags

`tags` is `tags.toml` from the authored repository, embedded verbatim as JSON, so a client builds its filter chips without a second request.
Which tags exist and what they mean is in [tags.md](tags.md).

### The share hosts

`hosts` is `hosts.toml` from the authored repository, embedded verbatim as JSON, so a client learns the registered share hosts and their `api` without reading the repository ([RFC 0104](../rfcs/0104-share-host-conformance.md)).
What a share host is and what it must do is in [RFC 0094](../rfcs/0094-share-host.md) and [share-host.md](share-host.md).

## Versions, and what a client does with one it does not know

Two different version fields appear in this document, and they fail differently.

**`snapshot_version` is this envelope.**
Adding an optional field does not bump it, so a client ignores a top-level key it does not know.
Removing a field, changing what one means, or adding a required one is a break, bumps it, and moves the path segment in the address.

A client that reads a `snapshot_version` higher than it implements refuses the whole document and keeps the copy it already has.
It does not parse what it recognises: the envelope is what tells it where everything is, so a version it does not know means it cannot be sure what it is holding.
The user gets "this client is too old for the index", which is actionable, rather than an index that quietly lost half its entries.

The vehicle file and the save file carry their own `snapshot_version`, and a break moves them to the next path segment together with the main document.
A client that reads a higher `snapshot_version` in one of them refuses that file only and keeps its copy of it, and the main document is not affected.
The two files leave `snapshot_version` at `1`, because an older client never fetches them, and `listings` loses nothing it carried before.

**`spec_version` is one document inside the envelope**, and RFC 0031 already says what happens: an entry a client cannot interpret renders as an entry in an unknown state and is never silently dropped.
Its id still counts as taken.

An `index_status.state` a client does not know is shown as a warning and removes nothing.
Removal is only ever `delisted`, and a state nobody recognises must not be guessed into one.

## Worked example

Real data, taken from the `StarMap` documents under [`examples/`](../examples/) and trimmed to one listing and one release, with the release's own fields left out:

```json
{
  "snapshot_version": 1,
  "listings": [
    {
      "id": "StarMap",
      "published_at": "2026-08-02T16:47:50Z",
      "updated_at": "2026-08-02T16:47:50Z",
      "authored": {
        "spec_version": 1,
        "id": "StarMap",
        "type": "mod-loader",
        "name": "StarMap",
        "authors": ["KlaasWhite"],
        "abstract": "Mod loader that runs code mods for Kitten Space Agency.",
        "license": "MIT",
        "tags": ["library"],
        "releases": { "github": "StarMapLoader/StarMap" },
        "links": {
          "forums": "https://forums.ahwoo.com/threads/starmap-mod-loader.384/",
          "repository": "https://github.com/StarMapLoader/StarMap"
        },
        "compatibility": { "game_min": "2026.8.3.5117" }
      },
      "releases": [
        { "spec_version": 1, "id": "StarMap", "version": "0.4.6", "...": "..." }
      ]
    }
  ],
  "packs": [],
  "game_versions": { "...": "..." }
}
```

No listing under `examples/` is delisted, disputed or retracted, because no real one is, so the index status shapes stay the snippets above.

A whole merged document is not committed anywhere yet.
The builder in the generated index repository produces the first one, and until then `examples/` holds the documents this page says how to merge.

## What the snapshot does not carry

- **Per-user state.** Favourites, votes and comments need a server, which [RFC 0025](../rfcs/0025-scope.md) rules out.
- **Counts over time, rankings or a featured list.** `downloads` is the last known count only (RFC 0052).
- **Anything a client owns.** Instances, install locations and settings are local, and the index never learns about them.
- **The files themselves.** Every release names its own host, and the index hosts nothing (RFC 0025).

## Size

The main document published on 2026-10-20 holds 26 listings with 122 releases and one pack.
It is 1,116,389 bytes uncompressed, and the host serves it compressed, at about 108 KB.

Vehicles and saves can be many more than mods and change much more often, so RFC 0094 gives them the two files of their own in place of the two arrays `vehicles` and `saves` in the main document.
The split keeps the bytes of vehicles and saves, and the work of parsing them, out of the main document and out of a client that does not need them.
It does not by itself keep an upload from making a client download the main document again, because on one GitHub Pages site every deployment gives every file a new ETag.
Independent validators need a host that gives them, for example a separate site per file or a host whose ETag is a hash of the content.
RFC 0094 does not name such a host, and a change of host changes only the table under [Fetching it](#fetching-it).

What grows fastest is not the number of listings but the `listing` block frozen into every release, which repeats a listing's descriptive text once per release of it.
If that becomes the problem, the fix needs no new field: RFC 0031 already has a client fall back to the authored document wherever the frozen block or one of its fields is absent, so a future `snapshot_version` can drop a frozen field that equals the live one.
This version does not, because the builder copying documents verbatim is worth more today than the bytes.
