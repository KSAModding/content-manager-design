<!-- markdownlint-disable MD029 -- rules are numbered across the whole page, so a list continues the count of the one before it -->

# Share hosts

What a share host must do to be registered in `hosts.toml` and to stay there.

[RFC 0094](../rfcs/0094-share-host.md) defines the share host: a release host for vehicles and saves that takes uploads from players without GitHub, keeps the archives as release assets in a storage repository its operator owns, and proves ownership to the index.
That RFC explains why it works that way.
This page is the checklist an operator builds against and a steward checks against, and nothing else.

A host conforms when it meets every numbered rule on this page.
Rules are numbered once and never renumbered: a removed rule keeps its number, marked removed, so "rule 12 of spec/share-host.md" keeps its meaning.
How the page changes is in [RFC 0104](../rfcs/0104-share-host-conformance.md).

## Registration

1. **The host has a `hosts.toml` entry** with every key RFC 0094 lists, added by a steward. The host accepts no upload for the index before the entry merges.
2. **The `policy` page is public** and states the takedown process, the abuse contact, a response time for abuse reports, and the privacy policy for accounts.
3. **The operator has agreed to succession**: when it stops operating, it transfers `storage` to a successor the stewards name, and says so in the registration pull request. A host without GitHub storage agrees to rules 45 to 47 instead.
4. **The `bot` account is used by this host only**, and opens no pull request on the authored repository that the host did not make.

## The storage repository

5. **`storage` is a public GitHub repository** that the operator owns and that the KSAModding organization does not own.
6. **Only the host writes to `storage`.** A GitHub App, if the host uses one, is installed on `storage` only, with contents write. The operator installs nothing on KSAModding repositories.
7. **The data files live on the default branch**, at these paths and nowhere else:

    ```text
    releases/<type>/<id>.json
    owners/<type>/<id>.json
    attestations/<sha256>.json
    ```

8. **Each data file is UTF-8 JSON without a byte order mark.** A reader ignores members it does not know, so a host may add members, but never with a name RFC 0094 or this page gives another meaning.
9. **One GitHub release per index release**, tagged `<type>/<id>/<version>`, with exactly one asset, named `<id>-<version>.zip`.
10. **An asset is never replaced and a tag is never reused**, also after the release is deleted.
11. **Immutable releases are on** for `storage` where GitHub offers them.

## Publishing a release

12. **The host checks the archive before it creates the GitHub release**: every archive check of [RFC 0085](../rfcs/0085-vehicles-and-saves.md) against its vector file, the `install.folder` collision check against the current snapshot, `max_bytes` for the type, and the version rules of RFC 0094. A failure is shown to the player and nothing is written.
13. **The host writes in this order**, so that no reader ever sees a reference to something that does not exist yet:
    1. The GitHub release with its asset, published.
    2. The owner record, for a new id.
    3. The entry in the release list.
    4. The attestation, when a pull request follows.
    5. The pull request.
14. **The release list only grows.** An entry is never edited, and is removed only by a takedown under rule 27.
15. **`version` is refused** when it does not parse as SemVer 2.0.0, or when the listing had it before, also when that release was deleted.
16. **When the dependency list changed**, the host opens the listing edit pull request in the same step as the release, by RFC 0094.

## Ids and owners

17. **A new id is refused** when it fails RFC 0031's id rule, or is in the snapshot, in an open pull request of the authored repository, or in the host's own owner records.
18. **One account claims at most `new_listings_per_day` new ids** in any 24 hours.
19. **The owner record carries no personal data.** `account` is opaque and stable, and never derived from a name, an e-mail address or another service's id.
20. **`github_id` is written only after the owner signed in to GitHub on the host**, never from a value the player typed.
21. **A handover is written only after both accounts confirmed it on the host.**

## Pull requests

22. **Every pull request is opened from a fork by `bot`** and carries an attestation by RFC 0094 that matches its head. When the host pushes again, it writes a new attestation for the new head.
23. **A grouped pull request** names every listing it touches in `accounts`, waits for more documents no longer than the time the operator states in `policy`, and drops a failing document and submits the rest again.
24. **The host never merges, approves or labels a pull request** on the authored repository. The checks and the self-merge rule decide.

## The upload API

The API lets a client share to any registered host without code for each one.
Paths are relative to `api` from `hosts.toml`, which ends in a version segment such as `v1/`.

25. **The host serves this API at `api`, over HTTPS:**

    | Request | Body | Answer |
    |---|---|---|
    | `POST device` | Form, `client_id` | RFC 8628 device authorization response |
    | `POST token` | Form, RFC 8628 device grant | RFC 8628 token response, a bearer token for the host account |
    | `POST uploads` | Multipart: `archive`, `dependencies` (RFC 0085's list as TOML), and `listing` (an id) for a new version of an existing listing | `201`, JSON: `upload`, `checks`, `version`, `listing_text`, `expires` |
    | `POST uploads/<upload>/publish` | JSON: `version`, `status`, and the listing fields for a new id | `201`, JSON: `id`, `type`, `version`, `pull_request` |

    `client_id` is any string naming the client, such as `borea`. The host treats every client as a public client with no secret and shows the name to the player when they confirm the sign-in.
    `checks` is an array of `{ "check", "ok", "message" }`, one per check of rule 12.
    `expires` is when an upload that was not published is discarded, at least 24 hours after the upload.

26. **Errors are JSON** `{ "error", "message" }` with a 4xx or 5xx status. `message` is for the player. `error` is one of:

    | `error` | When |
    |---|---|
    | `unauthorized` | No token, or the token has expired. |
    | `type_not_accepted` | The archive's type is not in `types`. |
    | `too_large` | The archive is larger than `max_bytes`. |
    | `invalid_archive` | A check of rule 12 failed. The body also carries `checks`. |
    | `id_taken` | Rule 17 refused the id. |
    | `version_taken` | Rule 15 refused the version. |
    | `not_owner` | The account does not own `listing`. |
    | `rate_limited` | Rule 18, or a limit of the host. The body also carries `retry_after` in seconds. |
    | `upload_expired` | The upload is past `expires`. |

    A client shows `message` for a code it does not know.
    A breaking change to the API is served at a new version segment next to the old one, and `api` in `hosts.toml` changes with a steward's pull request.

## What the operator owns

27. **Takedowns** delete the GitHub release, remove the entry from the release list, and remove every mirror the host controls, by RFC 0094. The host answers a DMCA notice that reaches GitHub within the time GitHub's policy gives.
28. **Abuse reports** are answered at the contact in `policy`, within the response time `policy` states.
29. **An erasure request** is handled on the host, and, for a linked `github_id`, by rewriting the history of `owners/`.
30. **Mirrors.** The host uploads each archive to the Internet Archive and lists it in `mirrors`, with bytes equal to the asset.

## Hosts without GitHub storage

A host may keep its archives and data files on its own server, object storage or CDN instead of in a GitHub repository.
It is registered on the same terms as a host with GitHub storage, and meets the rules below in place of what GitHub would otherwise guarantee: that a file was placed by the host, that a download URL does not change, and that the data outlives the operator.

Such a host names these keys in `hosts.toml` instead of `storage` and `pages`:

```toml
[examplehost]
kind = "share"
name = "example.org"
data = "https://example.org/share/v1/"
downloads = ["https://example.org/files/", "https://cdn.example.org/share/"]
key = "MCowBQYDK2VwAyEA..."
retired_keys = []
bot = 12345678
api = "https://example.org/api/share/v1/"
types = ["vehicle", "save"]
max_bytes = { vehicle = 10485760, save = 104857600 }
new_listings_per_day = 5
policy = "https://example.org/policy"
```

| Key | Meaning |
|---|---|
| `data` | The base URL that serves the data files of rule 7. |
| `downloads` | The URL prefixes that archives are served under. Every `url` in a release list, and every redirect from one, starts with one of them. |
| `key` | The Ed25519 public key that signs the data files, as base64 of its SubjectPublicKeyInfo. |
| `retired_keys` | Earlier values of `key`, so old signatures can still be checked. |

Rules 5, 6, 9, 10 and 11 do not apply.
Every other rule applies, with "the archive at its `url`" wherever a rule says "the GitHub release", and with the data files at `data` wherever a rule says `storage`.

### Data files

31. **`data` serves the three kinds of file of rule 7** at the same relative paths, over HTTPS, with the same bytes to every reader.
32. **Each release list entry carries `url` and `date`.** `url` starts with a prefix in `downloads`. `date` is the time the archive first became downloadable, in RFC 3339 UTC, and never changes.
33. **Every data file is signed.** Beside each file, at its path with `.sig` appended, `data` serves the base64 Ed25519 signature of the file's exact bytes by `key`. A file without a valid signature does not exist for the watcher or the checks.
34. **Data files are served fresh.** Each answer carries an `ETag`, honours `If-None-Match`, and is never more than 60 seconds older than the last write, so rule 13's order holds for every reader.
35. **The signing key is kept apart from the web server**, so that a compromise of the server that serves `data` is not enough to sign. When the key changes, the old one moves to `retired_keys` with a steward's pull request, and the host signs every current data file again with the new one.

### Downloads

36. **The bytes at a `url` never change, and a `url` is never reused**, also after a takedown.
37. **A download needs nothing but an HTTPS GET.** The host puts no login, cookie, interstitial page, bot challenge or referrer check in front of a `url`, from any network.
38. **A download answers `200` with a `Content-Length`**, and answers a `Range` request with `206`, so a client can resume a large save.
39. **A redirect stays inside `downloads`.** A `url` may redirect, for example to a signed object storage URL, only to a URL under a prefix in `downloads`.
40. **A deleted archive answers `410 Gone`**, never `200` with other bytes and never a page that says the file is gone.

### Ownership proof

41. **The attestation of rule 22 is served at `data` and signed by rule 33.** The ownership check of RFC 0094 accepts it only with a valid signature by `key`.
42. **The check records the proof.** The ownership check copies the attestation and its signature into its check run output, so a merged pull request keeps its proof when the host later goes away or changes the file.

### Takedowns and erasure

43. **A takedown** makes the archive's `url` answer `410`, removes the release list entry, signs the release list again, and removes every mirror the host controls. Rule 27 applies otherwise.
44. **An erasure** replaces the owner record without `github_id` and signs it again. There is no history to rewrite, so rule 29's rewrite does not apply.

### Succession

45. **The operator agrees to hand over the data.** When it stops operating, it gives the successor the stewards name every data file, every signature and every archive, in a form the stewards can read without the host's software.
46. **The operator agrees to keep the URLs working.** It transfers the domains of `data` and `downloads` to the successor, or keeps them redirecting to the successor's copies for at least one year.
47. **The signing key is not handed over.** The successor registers its own `key`, and the old one moves to `retired_keys`.

When the URLs stop working anyway, every stamped release stays installable from its Internet Archive mirror by rule 30.

## What a steward checks

At registration, a steward checks rules 1 to 11 by reading `hosts.toml`, `policy` and `storage`, and runs a test upload of a vehicle through the API against rules 12 to 26.
The test listing is closed without merging.

For a host without GitHub storage, the steward also:

- Verifies every data file of the test upload against `key`, and checks that an unsigned or wrongly signed change is refused by the checks.
- Downloads the test archive with a plain HTTPS client from outside the host's network, and checks rules 37 to 39.
- Reads the operator's statement of where the archives are stored and who the hosting provider is, which the registration pull request includes for rule 45.

After registration, the watcher and the listing checks enforce every rule they can see, and reject what breaks one.
A steward removes a host from `hosts.toml` when it keeps breaking a rule after being told, or when its operator does not answer at the `policy` contact.
Removing a host delists nothing, by RFC 0094.
