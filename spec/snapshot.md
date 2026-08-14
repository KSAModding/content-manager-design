# The snapshot artifact

The one document a client fetches, and the whole contract between the index and the clients that read it.

[RFC 0033](../rfcs/0033-content-index.md) defines the snapshot as one JSON document merging every listed authored document, the release files of listed entries, the index status data and the game release list, carrying its own format version.

Everything downstream happens locally: search, dependency resolution and compatibility evaluation need this document and nothing else, offline included ([RFC 0017](../rfcs/0017-game-version-ordering-and-compatibility.md), [RFC 0031](../rfcs/0031-content-metadata-format.md)).

## What the builder does, and what it does not

The builder joins, filters and attaches.
It never rewrites the content of a document.

- It **joins** each listing to its release files, so a client never sees the two-repository split.
- It **filters** out everything a delisted listing owns, and leaves a tombstone.
- It **attaches** the index's own state to the listing or the pack version that state names.

Every authored document and every release file appears verbatim, exactly as the repositories hold it.
A field this page does not mention is still in the document, and a client reads it against RFC 0031, not against this page.

That is what keeps the snapshot auditable: any entry can be compared against the two repositories without first knowing what the builder would have computed.
It is also what keeps this page from becoming a second copy of RFC 0031's field tables, drifting away from the original one release at a time.

## Fetching it

The index publishes at:

```text
https://ksamodding.github.io/content-index-releases/v1/index.json
```

The `v1` segment carries the snapshot format version, so a future break can be served next to what it replaces.

Poll it with `If-None-Match`, and an unchanged index answers 304.

## Determinism

The builder writes the same bytes for the same input, and an index whose bytes are already published is not published again.
Both are needed, because publishing is a deployment and a deployment issues a new ETag either way.
Together they keep a cached copy valid: an unchanged index costs a client one 304, and the scheduled backstop rebuild costs it nothing.

Four rules carry that:

- **No wall-clock field.** A `generated_at` would change the bytes on every scheduled rebuild and invalidate every cached copy for no change in content. `sources` carries the provenance instead, and how stale a copy is comes from HTTP.
- **The provenance follows the content, not the clock.** `sources` names the state the published content was built from, so it moves only when the content moves. A commit that changes nothing the snapshot carries has to leave the bytes alone, or `sources` reintroduces the problem above, only slower.
- **Every array is ordered**, by the rules below, rather than left in the order a filesystem happened to hand its entries over.
- **UTF-8, no BOM, LF line endings, two-space indent.**

Object key order is not part of the contract, and a client must not depend on it.

## The document

| Field | Required | Meaning |
|---|---|---|
| `snapshot_version` | yes | The version of this format. `1` for everything defined here. |
| `sources` | no | Which state of the index this was built from. Absent on a snapshot built from anything other than the two index repositories. |
| `listings` | yes | Mods and mod loaders. Ascending by lowercased id. |
| `packs` | yes | Mod packs. Ascending by lowercased id. |
| `game_versions` | yes | The game release list, verbatim. |

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

`releases` is an empty array for a listing whose release host has no release yet, which RFC 0033 admits as a listing that passes its checks vacuously.
A client lists it and has nothing to install.

Three voices sit side by side in one entry and never mix, which is why each has its own key: the author writes `authored`, tooling writes `releases`, and the index writes `index_status`.
The author's own `status` field, `active` or `deprecated`, is inside `authored` where it belongs, and it is not the same thing as `index_status`.

Each release also carries the `listing` block RFC 0031 freezes into it, so a release can be shown as it was described when it shipped, while `authored` stays live.

### A pack

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | The pack id, in its authored casing. |
| `versions` | no | The pack version documents, descending by SemVer precedence. Absent only on a tombstone. |
| `index_status` | no | The index's own state for the whole pack. |

Each entry of `versions` is `{ "authored": <the pack document, verbatim> }`, plus an `index_status` when that version is retracted.
A pack has no generated half, so there is no `releases` here: the document is the release.

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

A tombstone stays in the array its listing was in, which is what says whether the removed content was a listing or a pack.
Nothing is deleted from anyone's machine, and nothing is deleted from the repositories.

**`disputed` ships whole.**
The entry is complete and carries the state next to it, so a client shows a warning and lets the user proceed.

**`retracted` scopes to one pack version**, and a client treats it the way it treats a yanked release (RFC 0031).

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

## Versions, and what a client does with one it does not know

Two different version fields appear in this document, and they fail differently.

**`snapshot_version` is this envelope.**
Adding an optional field does not bump it, so a client ignores a top-level key it does not know.
Removing a field, changing what one means, or adding a required one is a break, bumps it, and moves the path segment in the address.

A client that reads a `snapshot_version` higher than it implements refuses the whole document and keeps the copy it already has.
It does not parse what it recognises: the envelope is what tells it where everything is, so a version it does not know means it cannot be sure what it is holding.
The user gets "this client is too old for the index", which is actionable, rather than an index that quietly lost half its entries.

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
- **Download counts and any other aggregated signal.** RFC 0033 names them as a possible future static aggregation, and until one exists a client cannot sort by popularity.
- **Anything a client owns.** Instances, install locations and settings are local, and the index never learns about them.
- **The files themselves.** Every release names its own host, and the index hosts nothing (RFC 0025).

## Size

Merging the seven listings and eight releases under `examples/` gives about 30 KB uncompressed, and the host serves the document compressed.

What grows fastest is not the number of listings but the `listing` block frozen into every release, which repeats a listing's descriptive text once per release of it.
If that becomes the problem, the fix needs no new field: RFC 0031 already has a client fall back to the authored document wherever the frozen block or one of its fields is absent, so a future `snapshot_version` can drop a frozen field that equals the live one.
This version does not, because the builder copying documents verbatim is worth more today than the bytes.
