---
rfc: "0094"
title: A share host for vehicles and saves
status: Accepted
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
In the recommended form the data plane is entirely on GitHub: each archive is a release asset in a storage repository the host operator owns, and the release lists, the owner records and the edit attestations are static files in that same repository.
The control plane is the host's own service, which takes an upload from a client or from its website, checks it by RFC 0085's rules, writes to the storage repository, and opens listing pull requests from its own bot account like any author.

A listing names a share host as `[releases] ksamods = "ExampleRover"`.
The watcher reads the release list and the GitHub releases from the storage repository, as it reads releases from a GitHub repository today.
Ownership is proven by a file in the storage repository that only the host can have placed, in the same way as the marker file of [RFC 0033](0033-content-index.md).

The host is one way to publish, not the only one.
A player with a GitHub account can publish from a repository of their own, and the release pull request path of RFC 0033 stays open for vehicles and saves.
The operator of a host owns takedowns, moderation, abuse reports, and the privacy of its accounts.

Hosts are registered by stewards in a new `hosts.toml` in the authored repository.
`spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0085 requires three things of a host before a `vehicle` or `save` listing can enter the index:

1. A list of the releases of one vehicle or save, each with a version, a date and one archive.
2. A download URL that stays the same for a release, so that `download.sha256` keeps its meaning.
3. An account that owns the upload, so that an ownership proof of RFC 0033 can name it.

Neither existing host kind fits a player without GitHub.
A GitHub release needs a repository and a GitHub account, which is more than a player sharing a rover should need.
SpaceDock is built for mods, and [RFC 0079](0079-author-freedom.md) only proves SpaceDock ownership through a GitHub repository, so a player without GitHub would still wait for a steward.

If nothing is done, vehicles and saves stay unlisted, and players keep sharing them as Discord attachments without dependency data, which RFC 0085 shows is a crash the player cannot explain.

[RFC 0025](0025-scope.md) constrains the answer: the index runs on free infrastructure and never hosts content files.
A share host is not part of the index.
It is a release host, operated by someone other than the index, in the same position as SpaceDock.

What RFC 0085 rules out is a repository per player and archives in the index's git history, and GitHub storage is neither.
No player needs a repository or a GitHub account, the archives are release assets outside git history so a takedown needs no history rewrite, and `storage` is not owned by KSAModding.

## Guide-level explanation

**Sharing without GitHub.**
You build a rover and share it from your client, which writes the archive and the dependency list by RFC 0085.
The client sends both to a registered host through the upload API, or you upload the archive on the host's website yourself.
You sign in with whatever account the host offers, for example Discord or email.
Before your first upload the host tells you that the listing text goes into a public index that keeps its history.
The host checks the archive, shows you the dependency list and the listing text, and asks for a version, proposing `1.0.0` for a first release and the next minor version after that.
When you confirm, the host stores the archive and opens the listing pull request on the authored repository from its bot account.
The checks verify it against the host, and it merges itself like any other verified listing.

**Sharing with GitHub.**
A player with a GitHub account needs no host at all.
A client that signs in to GitHub, as Borea does, creates a repository in the player's own account, for example `<login>/ksa-shares`, and uploads each share there as a release asset.
The listing names that repository under `[releases] github` with a `tag_prefix` by [RFC 0096](0096-tag-prefix.md), so one repository holds the releases of many shares, and ownership is proven as for every GitHub listing.
A player who uses a share host can also link a GitHub account on it, and then open listing and amendment pull requests from their own fork.

**A new version.**
You upload the changed vehicle to the same listing on the host.
The host writes a new release, and the watcher stamps it on its next tick.
When the dependency list changed, the host opens the listing edit pull request in the same step.

**What the listing adds.**
The listing is RFC 0085's, with the host's page as `homepage` and the host under `[releases]`:

```toml
[links]
homepage = "https://ksamods.gg/vehicles/ExampleRover"

[releases]
ksamods = "ExampleRover"
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
bot = 98765432
api = "https://ksamods.gg/api/share/v1/"
pages = "https://ksamods-content.github.io/share/"
types = ["vehicle", "save"]
max_bytes = { vehicle = 10485760, save = 104857600 }
new_listings_per_day = 5
policy = "https://ksamods.gg/policy"
```

| Key | Meaning |
|---|---|
| table name | The host key a listing uses in `[releases]`. It must not be `github`, `spacedock` or `authority`. |
| `kind` | `share`, the only kind this RFC defines. |
| `storage` | The GitHub repository that holds the host's archives and data files. It must not be owned by the KSAModding organization, because the index never hosts files. A host of the variant below names `data` instead. |
| `bot` | The numeric id of the GitHub user account the host opens pull requests as. |
| `api` | The base URL of the upload API. |
| `pages` | Optional. A GitHub Pages base URL that serves the data files of `storage`, used before `raw.githubusercontent.com`. |
| `types` | The content types the host accepts. A listing of another type may not name it. |
| `max_bytes` | The largest archive the host accepts, per type. The watcher and the listing checks reject a larger one too. |
| `new_listings_per_day` | How many new ids one host account may claim per day. The host enforces it; the index cannot see accounts. |
| `policy` | The host's policy for takedowns, abuse reports with a contact and a response time, and the privacy of accounts. `POLICY.md` links it for content on that host. |

The listing checks reject a `[releases]` key that is neither a known kind nor a table in `hosts.toml`.
Removing a host from `hosts.toml` does not delist anything: its releases stay stamped, its listings no longer verify ownership, and a steward handles them.

At registration the operator agrees that, when it stops operating, it transfers `storage` to a successor the stewards name.
A repository transfer keeps its releases; I have not verified that asset URLs redirect after one.

### The storage repository

All files a reader needs are in `storage`, on its default branch:

```text
releases/<type>/<id>.json
owners/<type>/<id>.json
attestations/<sha256>.json
```

The archives are release assets of GitHub releases in `storage`, one GitHub release per index release, tagged `<type>/<id>/<version>` with one asset named `<id>-<version>.zip`.

The watcher, the checks and the download counts read only `storage`, through the GitHub API and raw file URLs, and never the host's service.
So the index keeps working, and every stamped release stays installable, while the host's service is down, and anyone who can read GitHub can audit what the host claims.

The GitHub App, if the host uses one, is installed on `storage` only, with contents write.
KSAModding installs nothing of the host's.

### The release list

`releases/<type>/<id>.json` holds only what GitHub does not know:

```json
{
  "id": "ExampleRover",
  "type": "vehicle",
  "releases": [
    {
      "version": "1.0.0",
      "status": "stable",
      "mirrors": ["https://archive.org/download/ksamods-vehicle-ExampleRover-1.0.0/ExampleRover-1.0.0.zip"]
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `version` | SemVer 2.0.0 by RFC 0031. The host refuses a version that does not parse, or that the listing already had, also when that release was deleted. |
| `status` | `stable`, `testing` or `dev`, chosen by the publisher. It becomes `release_status` together with the version's pre-release part, by RFC 0031. |
| `mirrors` | Optional. Copies of the archive at `archive.org`, see Mirrors. |

For each entry the watcher reads the GitHub release tagged `<type>/<id>/<version>` in `storage`.
It takes `download.url` from its one asset and `release_date` from the release's publish time, and computes `download.sha256` itself.
A release without that GitHub release, or with any other asset count or name, is rejected.

The watcher treats the file as the authority's list of releases, by the scan rule of RFC 0033.
A release that leaves the list but whose asset still downloads is not removed from the index, because a stamp is never withdrawn by its host.
A release whose archive no longer downloads anywhere is gone by [RFC 0078](0078-gone-releases.md).

### Stable downloads

RFC 0085's second requirement is met by the asset URL of a GitHub release, which stays the same while the asset exists.
The host must never replace an asset and must never reuse a tag.
When it does anyway, `download.sha256` catches it: the watcher rejects the new bytes by RFC 0031, and a client refuses them.

Where GitHub offers immutable releases for `storage`, the host turns them on.
GitHub then protects the assets from deletion, and a deleted release's tag cannot be reused.
I have not verified which repository plans offer this.

### Mirrors

The host also uploads each archive to the Internet Archive and lists that URL in `mirrors`.
The watcher downloads each mirror once, checks it against `download.sha256`, and appends it to `download.mirrors`, which amends RFC 0031's rule that mirrors come only from the hosts named in `[releases]`.
A mirror whose bytes differ is dropped.
So a vehicle stays installable from a free, durable copy when GitHub disables `storage` or the operator stops, as RFC 0085 wants.
I have not verified that the Internet Archive's terms allow this use at scale.

### Owners

RFC 0085's third requirement is the owner record, `owners/<type>/<id>.json`:

```json
{
  "id": "ExampleRover",
  "type": "vehicle",
  "account": "u_7Hk2pQ",
  "github_id": 54321
}
```

| Field | Meaning |
|---|---|
| `account` | The host's opaque, stable id for the account that owns the listing. It carries no name, e-mail address or other personal data. |
| `github_id` | Present only when the owner linked a GitHub account on the host by GitHub's own login. The numeric id, so a rename on GitHub changes nothing. |

The name the player chose to publish is the listing's `authors`, so the record repeats no name.

The host creates the record with the first upload of an id.
It refuses an id that is already in the index, in the open pull requests of the authored repository, or in its own records, and it checks the id by RFC 0031.
It limits new ids per account and per day to `new_listings_per_day`.
A handover is a new record written by the host after both accounts confirm on the host, and it follows RFC 0033's handover rule.

### The ownership proof

Ownership binds to the release authority by RFC 0033, and for an edit to the authority the listing already names, by [RFC 0048](0048-ownership-of-an-edit.md).
For a share host authority, the ownership check accepts either of two proofs.

**1. Linked GitHub account.**
The owner record has a `github_id` equal to the numeric id of the pull request author.
This is the owner id fast path of RFC 0033, with the host's record in place of the repository's owner.

**2. Attestation.**
The pull request is opened by the host's `bot` account, and `storage` holds `attestations/<sha256>.json`, where `<sha256>` is the lowercase hex SHA-256 of the canonical form of the change:

```json
{
  "host": "ksamods",
  "accounts": {
    "vehicle/ExampleRover": "u_7Hk2pQ"
  },
  "created": "2026-10-11T09:14:30Z"
}
```

The canonical form is UTF-8 text with one line per path the pull request touches, `<path> <blob>`, where `<blob>` is the lowercase hex git blob id of the file at the pull request's head, or `deleted`.
Lines are sorted by the bytes of the path, and each ends with one LF, the last one included.
A rename is one `deleted` line for the old path and one line for the new path.

The check builds the form from the pull request files API, which returns each path, its status and its blob id, so it reads no pull request content.
It passes when the attestation exists, and `accounts` names every listing the pull request touches with the `account` of that listing's owner record.
Only a writer of `storage` can have placed the file, as only a writer of a repository can have placed RFC 0033's marker file.
The attestation binds the proof to the exact content, so the bot's identity alone proves nothing: a pull request that changes one byte after the host attested it does not verify.
The check is a privileged decision by RFC 0033.

The companion change in the authored repository adds a vector file of changes and their canonical forms and hashes to `schemas/`, which the check and every host test against.

A first claim is a listing pull request with an attestation whose owner record the same upload created.
So a first listing on a share host verifies without a steward, as a first listing of a personally owned GitHub repository does.

Amendments, release notes and handovers use the same two proofs.

### Pull requests from the host

The host opens listing and amendment pull requests from a fork with its `bot` account, like any author, so every one of them goes through the same checks and the same self-merge rule.

The host may group the listing documents of several players in one pull request, with one attestation for the group.
The self-merge limit of content-index applies; it is sized for mod archives, and content-index can raise it for share host documents by measurement without a change to this RFC.
When a document fails, the host removes it from the group and submits the rest again, so one player's error does not hold back the others.
The host groups for a bounded time only.

When a new release changes the dependency list, the host publishes the release and opens the listing edit pull request in the same step.
By [RFC 0081](0081-listing-narrowing.md) the edit then reaches the new release when it merges.

### The upload API

Every share host offers the same small API at `api`, so a client can share to any registered host without integrating each one.

| Step | Request | Result |
|---|---|---|
| Sign in | OAuth 2.0 device authorization grant ([RFC 8628](https://www.rfc-editor.org/rfc/rfc8628)) at `api` | A bearer token for the host account. The client never sees a password. |
| Upload | `POST uploads`, multipart with `archive`, the dependency list of RFC 0085 as `dependencies`, and `listing` for a new version of an existing id | An upload id, the result of every check, the proposed version, and the listing text to show |
| Publish | `POST uploads/<upload>/publish`, JSON with `version`, `status` and, for a new id, the listing fields | The listing id, the version, and the pull request URL |

Errors are JSON with a machine-readable `error` and a `message` for the player.
The website stays a second way to upload, and a client may offer sharing without any host.

### What the host checks before it publishes

The host runs RFC 0085's archive checks (`meta.toml`, the name rule against its vector file, the root directory, the game file, `version`), the `install.folder` collision check against the snapshot, and `max_bytes`, before it creates a GitHub release.
A failure is shown to the player at upload, so a release the watcher would reject never exists on the host.
The watcher and the listing checks still run every check themselves, and never trust the host's verdict.

### What the operator owns

The operator of a share host owns takedowns, moderation, abuse reports, and the privacy of uploads and accounts.
Abuse covers spam, offensive names and descriptions, and harmful extra files in a save; the operator handles reports, bans accounts, hears appeals, and answers at the contact its `policy` names within the response time it states.
The index owns only its listing states, by `POLICY.md`.

**Takedowns.**
The host deletes the GitHub release of that version and removes the copy from every mirror it controls, the Internet Archive one included.
The watcher then marks the release gone by RFC 0078, after that RFC's waiting time.
Content that must go faster is delisted by a steward through `index-status.toml`.
A DMCA notice can also go to GitHub directly, and the operator answers GitHub within the one business day GitHub's [DMCA policy](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy) gives.

**Privacy.**
The operator is responsible for the accounts and their personal data, publishes a privacy policy as part of `policy`, and handles erasure requests.
Because the owner record carries only an opaque `account`, an erasure is mostly done on the host: the id no longer points to anyone.
Only a linked `github_id` needs a rewrite of the history of `owners/`.

**What the forum thread did.**
RFC 0085 makes `links.forums` optional for `vehicle` and `save`.
On a share host the three jobs `POLICY.md` gives the thread are done by the host: the host account and the contact in its policy reach a person, the time of the first upload on the host breaks an id dispute, and a ban on the host is the tripwire.

### Hosts that do not use GitHub storage

A host may keep archives on its own server or object storage instead, as SpaceDock does for mods.
It then names `data`, a base URL serving the same three kinds of file, instead of `storage`, and its release list carries `url` and `date` for each release, which become `download.url` and `release_date`.
The cost is that the watcher depends on the host's server, a host could answer the watcher and a client differently, nobody outside the host can audit its claims, and a release has no download count.
GitHub storage is the recommended form for these reasons.

### Download counts

[RFC 0052](0052-static-download-counts.md) gains the host kind `share`: the indexer reads `download_count` of each asset in `storage` through the GitHub API, under the host key from `hosts.toml`.
The host's own counter is never read, so a host cannot inflate a count.

### Snapshot size

Every upload changes the snapshot, which has no delta path yet, and vehicles and saves may be published far more often than mods.
A publish rate would only slow the changes down, not shrink what every client downloads.

So vehicles and saves get snapshot files of their own, published next to the main snapshot:

```text
https://ksamodding.github.io/content-index-releases/v1/index.json
https://ksamodding.github.io/content-index-releases/v1/snapshot-vehicles.json
https://ksamodding.github.io/content-index-releases/v1/snapshot-saves.json
```

Each is built and published like the main snapshot, by the same builder and the same determinism rules of `spec/snapshot.md`, with the same envelope and its own ETag, and carries one array, `vehicles` or `saves`, with the entry shape of `listings`.
The main snapshot holds only mods, loaders and packs, as today, so an upload on a share host changes only the file of its type.
A client fetches the vehicle or save file only when it shows that type, and polls it with `If-None-Match` like the main one.

### What changes elsewhere

- RFC 0031: `[releases]` accepts a key registered in `hosts.toml`, with a listing id as its value, for the types that host accepts; `download.mirrors` also takes verified mirrors from a share host's release list.
- RFC 0033: the authored repository gains `hosts.toml`, and the ownership check gains the share host proofs.
- RFC 0052: the host kind `share`.
- RFC 0085: the `vehicles` and `saves` arrays move from the main snapshot into `snapshot-vehicles.json` and `snapshot-saves.json`, and spec/snapshot.md describes the two files. Archives may live in an operator-owned GitHub repository or on an external host, `links.forums` is optional for these types, and the index accepts `vehicle` listings once a host is registered for that type.
- content-index: the schema of `hosts.toml`, the attestation vector file in `schemas/`, and the `max_bytes` check.

## Drawbacks

- **The host is trusted for ownership.** Whoever holds write access to `storage` can attest any change to any listing on that host. This is the same trust RFC 0033 puts in whoever holds write access to a mod's repository, but it is concentrated in one operator for every vehicle on the host.
- **A bus factor of one operator.** When the operator stops, the archives stay downloadable from GitHub and the Internet Archive, but nobody can publish, amend or hand over until the stewards name a successor and `storage` is transferred. Host software under an open license would let another operator take over quickly.
- **One DMCA notice can take down every vehicle.** GitHub disables the whole repository when the owner does not remove the content in time. The mirrors keep releases installable, and sharding `storage` limits the damage.
- **GitHub as file storage for other people's uploads.** GitHub can limit a repository that uses a lot of bandwidth, and every archive on the host depends on one organization's standing with GitHub. I have not verified where GitHub draws that line for release assets.
- **Moderation of player uploads moves to the operator.** That is new work for one person or a small team, and the index cannot do it for them.
- **Id squatting is cheaper.** With a Discord or e-mail login, one person can make many accounts and claim many ids in the namespace mods share, without the GitHub account and the Actions approval that slow the GitHub path. `new_listings_per_day` slows it down, and the id dispute path of `POLICY.md` is the remedy.
- **A short window with the old dependency list.** Until the listing edit merges, a new release whose dependencies changed carries the old list.
- **Players without a GitHub account depend on the host's login.** When they lose that account, only the host can restore their ownership.

## Alternatives

- **One GitHub repository per vehicle in the host's organization.** It needs no new kind and works with the topic proof of [RFC 0038](0038-repository-topic-ownership-proof.md), but the owner the index sees is always the host's account, a player can never prove ownership directly, and the host organization fills with thousands of repositories.
- **Small archives in an index-side repository, added by pull request.** It needs no host at all, but the index would host content files against RFC 0025, every takedown would rewrite the index's git history, and the repository would grow with every upload.
- **The release pull request path only, with no host.** It stays open, but the index has no proof for a player without GitHub, so every listing and every release waits for a steward.
- **Data files served by the host's website instead of from `storage`.** It is allowed as the variant above, and not recommended for the reasons given there.
- **Discord attachments or other chat uploads.** Their URLs are not stable, which breaks RFC 0085's second requirement.

## Unresolved questions

- Whether one `storage` repository per host is enough, or whether a host shards by type or by year when the number of releases grows. The data file paths would carry the shard.
- The values of `max_bytes` per type.
- Whether GitHub's terms allow release assets as the storage of a sharing service at the scale vehicles may reach, which a host operator should confirm before registration.
- Whether asset URLs redirect after a transfer of `storage`.
- What a steward checks before adding a host to `hosts.toml`, beyond the policy link and the succession agreement.

## Future possibilities

- Splitting the main snapshot into one file for the listings and one for the releases, once it grows too big. It is about 1.1 MB today and still fine.
- The host maps the ids a file names to mods from the index's archives, and proposes the dependency list on the website for a player who uploads without a client.
- Signed attestations, when the index adopts a key story for release signatures, so a proof survives a compromise of `storage`.
- Mod packs that carry their own files, which RFC 0031 postpones, could use the same host kind.
