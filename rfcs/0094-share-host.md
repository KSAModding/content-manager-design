---
rfc: "0094"
title: A share host for vehicles and saves
status: Draft
authors: ["@SafeShows"]
created: 2026-10-11
discussion: https://github.com/KSAModding/content-manager-design/pull/94
supersedes: []
superseded-by: []
---

# RFC 0094: A share host for vehicles and saves

## Summary

[RFC 0085](0085-vehicles-and-saves.md) adds the content types `vehicle` and `save`, and the index accepts them only once a release host exists that a player can publish to without a repository of their own.
This RFC defines that host as a new release host kind, the **share host**, and names ksamods.gg as the first instance.

A share host splits into two planes.
The data plane is entirely on GitHub: each archive is a release asset in a storage repository the host operator owns, and the release lists, the owner records and the edit attestations are static files in that same repository.
The control plane is the host's own website, which takes the upload from a player, checks it by RFC 0085's rules, and writes to the storage repository through a GitHub App.

A listing names a share host as `[releases] ksamods = "ExampleRover"`.
The watcher reads the release list from the storage repository, as it reads releases from a GitHub repository today.
Ownership is proven by a file in the storage repository that only the host can have placed, in the same way as the marker file of [RFC 0033](0033-content-index.md).

Hosts are registered by stewards in a new `hosts.toml` in the authored repository.
`spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0085 requires three things of a host before a `vehicle` or `save` listing can enter the index:

1. A list of the releases of one vehicle or save, each with a version, a date and one archive.
2. A download URL that stays the same for a release, so that `download.sha256` keeps its meaning.
3. An account that owns the upload, so that an ownership proof of RFC 0033 can name it.

Neither existing host kind fits.
A GitHub release needs a repository per vehicle and a GitHub account, which is more than a player sharing a rover should need.
SpaceDock is built for mods, and [RFC 0079](0079-author-freedom.md) only proves SpaceDock ownership through a GitHub repository, so a player without GitHub would still wait for a steward.

If nothing is done, vehicles and saves stay unlisted, and players keep sharing them as Discord attachments without dependency data, which RFC 0085 shows is a crash the player cannot explain.

[RFC 0025](0025-scope.md) constrains the answer: the index runs on free infrastructure and never hosts content files.
A share host is not part of the index.
It is a release host, operated by someone other than the index, in the same position as SpaceDock.

## Guide-level explanation

**Sharing without GitHub.**
You build a rover and share it from your client, which writes the archive and the dependency list by RFC 0085.
The client sends both to ksamods.gg, or you upload the archive on the website yourself.
You log in with whatever account the host offers, for example Discord or email.
The host checks the archive, shows you the dependency list and the listing text, and asks for a version, proposing `1.0.0` for a first release and the next minor version after that.
When you confirm, the host stores the archive on GitHub and opens the listing pull request on the authored repository for you.
The checks verify it against the host, and it merges itself like any other verified listing.

**Sharing with GitHub.**
When you link a GitHub account on the host, you can also open listing and amendment pull requests yourself, from your own fork, and they verify against the host's record of you.

**A new version.**
You upload the changed vehicle to the same listing on the host.
The host writes a new release, and the watcher stamps it on its next tick, with no pull request at all.

**What the listing looks like.**

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
homepage = "https://ksamods.gg/vehicles/ExampleRover"

[releases]
ksamods = "ExampleRover"

[[dependencies]]
id = "ExamplePartsMod"
kind = "required"
min = "1.4.0"
```

## Reference-level explanation

### Registered hosts

A share host is trusted to say who owns an upload, so the index lists the hosts it trusts.
The authored repository gains `hosts.toml`, edited by stewards only, as `tags.toml` is:

```toml
[ksamods]
kind = "share"
name = "ksamods.gg"
storage = "ksamods-content/share"
app_id = 123456
pages = "https://ksamods-content.github.io/share/"
types = ["vehicle", "save"]
policy = "https://ksamods.gg/policy"
```

| Key | Meaning |
|---|---|
| table name | The host key a listing uses in `[releases]`. It must not be `github`, `spacedock` or `authority`. |
| `kind` | `share`, the only kind this RFC defines. |
| `storage` | The GitHub repository that holds the host's archives and data files. It must not be owned by the KSAModding organization, because the index never hosts files. |
| `app_id` | The numeric id of the GitHub App the host writes to `storage` with, and opens pull requests as. |
| `pages` | Optional. A GitHub Pages base URL that serves the data files of `storage`, used before `raw.githubusercontent.com`. |
| `types` | The content types the host accepts. A listing of another type may not name it. |
| `policy` | The host's takedown and dispute policy, which `POLICY.md` links for content on that host. |

The listing checks reject a `[releases]` key that is neither a known kind nor a table in `hosts.toml`.
Removing a host from `hosts.toml` does not delist anything: its releases stay stamped, its listings no longer verify ownership, and a steward handles them.

### The storage repository

All files a reader needs are in `storage`, on its default branch:

```text
releases/<type>/<id>.json
owners/<type>/<id>.json
attestations/<sha256>.json
```

The archives are release assets of GitHub releases in `storage`, one GitHub release per index release, tagged `<type>/<id>/<version>` with one asset named `<id>-<version>.zip`.

The watcher, the checks and the download counts read only `storage`, through the GitHub API and raw file URLs, and never the host's website.
So the index keeps working, and every stamped release stays installable, while the website is down, and anyone who can read GitHub can audit what the host claims.

### The release list

`releases/<type>/<id>.json` answers RFC 0085's first requirement:

```json
{
  "id": "ExampleRover",
  "type": "vehicle",
  "releases": [
    {
      "version": "1.0.0",
      "date": "2026-10-11T09:14:02Z",
      "tag": "vehicle/ExampleRover/1.0.0",
      "url": "https://github.com/ksamods-content/share/releases/download/vehicle%2FExampleRover%2F1.0.0/ExampleRover-1.0.0.zip",
      "sha256": "9f2c…",
      "size": 48213,
      "status": "stable"
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `version` | SemVer 2.0.0 by RFC 0031. The host refuses a version that does not parse, or that the listing already had, also when that release was deleted. |
| `date` | ISO 8601 UTC time the host published the release. It becomes `release_date`. |
| `tag`, `url` | The GitHub release and the asset URL. `url` becomes `download.url`. |
| `sha256`, `size` | What the host computed at upload. The watcher recomputes both and rejects the release when they differ. |
| `status` | `stable`, `testing` or `dev`, chosen by the publisher. It becomes `release_status` together with the version's pre-release part, by RFC 0031. |

The watcher treats the file as the authority's list of releases, by the scan rule of RFC 0033.
A release that leaves the list but whose asset still downloads is not removed from the index, because a stamp is never withdrawn by its host.
A release whose asset no longer downloads is gone by [RFC 0078](0078-gone-releases.md).

### Stable downloads

RFC 0085's second requirement is met by the asset URL of a GitHub release, which stays the same while the asset exists.
The host must never delete an asset and upload different bytes under the same tag, and must never reuse a tag.
When it does anyway, `download.sha256` catches it: the watcher rejects the new bytes by RFC 0031, and a client refuses them.

Where GitHub offers immutable releases for `storage`, the host turns them on, so the storage repository itself refuses a replacement.
I have not verified which repository plans offer this.

### Owners

RFC 0085's third requirement is the owner record, `owners/<type>/<id>.json`:

```json
{
  "id": "ExampleRover",
  "type": "vehicle",
  "account": "u_7Hk2pQ",
  "display_name": "Maxi",
  "github_id": 54321
}
```

| Field | Meaning |
|---|---|
| `account` | The host's opaque, stable id for the account that owns the listing. It carries no e-mail address or other personal data. |
| `display_name` | Shown in a steward's queue and in the host's issues, never used for a decision. |
| `github_id` | Optional. The numeric id of a GitHub account the owner linked on the host by GitHub's own login, so a rename on GitHub changes nothing. |

The host creates the record with the first upload of an id.
It refuses an id that is already in the index, in the open pull requests of the authored repository, or in its own records, and it checks the id by RFC 0031.
A handover is a new record written by the host after both accounts confirm on the host, and it follows RFC 0033's handover rule.

### The ownership proof

Ownership binds to the release authority by RFC 0033, and for an edit to the authority the listing already names, by [RFC 0048](0048-ownership-of-an-edit.md).
For a share host authority, the ownership check accepts either of two proofs.

**1. Linked GitHub account.**
The owner record has a `github_id` equal to the numeric id of the pull request author.
This is the owner id fast path of RFC 0033, with the host's record in place of the repository's owner.

**2. Attestation.**
The pull request is opened by the GitHub App with the host's `app_id`, and `storage` holds `attestations/<sha256>.json`, where `<sha256>` is the hash of the canonical form of the change:

```json
{
  "host": "ksamods",
  "listing": "vehicle/ExampleRover",
  "account": "u_7Hk2pQ",
  "documents": {
    "vehicles/ExampleRover.toml": "c41e…"
  },
  "created": "2026-10-11T09:14:30Z"
}
```

The canonical form is the sorted list of every path the pull request touches, each followed by the SHA-256 of its content at the pull request's head, or by `deleted`, one per line.
The check computes it from the pull request, reads the attestation, and passes when the file exists, `account` equals the owner record's `account`, and `documents` matches the pull request exactly.
Only a writer of `storage` can have placed the file, as only a writer of a repository can have placed RFC 0033's marker file.

The attestation binds the proof to the exact content, so the App's identity alone proves nothing: a pull request by the App that changes one byte after the host attested it does not verify.
The check is a privileged decision by RFC 0033, and it reads only `storage` and the pull request's file list, never pull request content.

A first claim is a listing pull request with an attestation whose owner record the same upload created.
So a first listing on a share host verifies without a steward, as a first listing of a personally owned GitHub repository does.

Amendments, release notes and handovers use the same two proofs.

### What the host checks before it publishes

The host runs RFC 0085's archive checks (`meta.toml`, the name rule against its vector file, the root directory, the game file, `version`) and the `install.folder` collision check against the snapshot, before it creates a GitHub release.
A failure is shown to the player at upload, so a release the watcher would reject never exists on the host.
The watcher and the listing checks still run every check themselves, and never trust the host's verdict.

The host also enforces a size limit per type, which it publishes with its policy.

### Download counts

[RFC 0052](0052-static-download-counts.md) gains the host kind `share`: the indexer reads `download_count` of each asset in `storage` through the GitHub API, under the host key from `hosts.toml`.
The host's own counter is never read, so a host cannot inflate a count.

### Takedowns

Content on a share host is taken down by the host, under the policy named in `hosts.toml`.
The host deletes the asset, and the watcher marks the release gone by RFC 0078.
The index's own takedown, by `POLICY.md` and the index status data, is unchanged, and a steward can still delist a listing whose host does not act.

### What changes elsewhere

- RFC 0031: `[releases]` accepts a key registered in `hosts.toml`, with a listing id as its value, for the types that host accepts.
- RFC 0033: the authored repository gains `hosts.toml`, and the ownership check gains the share host proofs.
- RFC 0052: the host kind `share`.
- RFC 0085: the hosting requirement is met by this RFC, and the index accepts `vehicle` listings once a host is registered for that type.

## Drawbacks

- **The host is trusted for ownership.** Whoever holds write access to `storage` can attest any change to any listing on that host. This is the same trust RFC 0033 puts in whoever holds write access to a mod's repository, but it is concentrated in one operator for every vehicle on the host.
- **A bus factor of one operator.** When the operator disappears, the archives stay downloadable from GitHub, but nobody can publish, amend or hand over. The stewards' answer is the same as for a dead SpaceDock listing.
- **GitHub as file storage for other people's uploads.** GitHub can limit a repository that uses a lot of bandwidth, and every archive on the host depends on one organization's standing with GitHub. I have not verified where GitHub draws that line for release assets.
- **Moderation moves to the host.** A save may carry files beside `universe.xml` that are a mod's state, so the host reviews takedown reports for content it did not write.
- **Players without a GitHub account depend on the host's login.** When they lose that account, only the host can restore their ownership.

## Alternatives

- **One GitHub repository per vehicle, with the existing `github` host kind.** It needs no new kind and works with the topic proof of [RFC 0038](0038-repository-topic-ownership-proof.md), but the owner the index sees is always the host's account, a player can never prove ownership directly, and the host organization fills with thousands of repositories.
- **The release pull request path, with no `[releases]` section.** It works today, but the host is not a proof RFC 0033 knows, so every listing and every release waits for a steward.
- **A host on its own server or object storage.** It needs no GitHub, but RFC 0025's free infrastructure rule then holds only for the index, the archives depend on the operator paying for storage, and nothing outside the host can read its claims.
- **A host API on the website instead of static files.** The watcher would depend on the website being up, and a host could answer the watcher and a client differently.
- **Discord attachments or other chat uploads.** Their URLs are not stable, which breaks RFC 0085's second requirement.

## Unresolved questions

- Whether one `storage` repository per host is enough, or whether a host shards by type or by year when the number of releases grows. The data file paths would carry the shard.
- The size limits per type, and whether `hosts.toml` should carry them so the listing checks enforce them too.
- Which forum thread a listing on a share host links as `links.forums`, which RFC 0085 leaves open too. A host page could be allowed in its place for these types.
- Whether GitHub's terms allow release assets as the storage of a sharing service at the scale vehicles may reach, which a host operator should confirm before registration.
- What a steward checks before adding a host to `hosts.toml`, beyond the policy link.

## Future possibilities

- A second registered host as a mirror. Because a release is identified by its `sha256`, a listing can name two share hosts with an `authority`, and a client falls back to the other one by RFC 0031's mirror rule.
- The host maps the ids a file names to mods from the index's archives, and proposes the dependency list on the website for a player who uploads without a client.
- Signed attestations, when the index adopts a key story for release signatures, so a proof survives a compromise of `storage`.
- Mod packs that carry their own files, which RFC 0031 postpones, could use the same host kind.
