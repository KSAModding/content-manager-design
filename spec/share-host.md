<!-- markdownlint-disable MD029 -- rules are numbered across the whole page, so a list continues the count of the one before it -->

# Share hosts

What a share host must do to be registered in `hosts.toml` and to stay there.

[RFC 0094](../rfcs/0094-share-host.md) defines the share host and says why it works the way it does.
This page is the checklist an operator builds against and a steward ticks off.
A rule that RFC 0094 already states is one line here with a link to its section, and a rule in bold is not in RFC 0094.

Rules are numbered once, and a removed rule keeps its number, marked removed.
A change that binds a registered host needs an RFC, and any other change is a pull request ([RFC 0104](../rfcs/0104-share-host-conformance.md)).

## Registration

1. The host has a `hosts.toml` entry with every key of [Registered hosts](../rfcs/0094-share-host.md#registered-hosts), and takes no upload for the index before it merges.
2. The `policy` page is public and states the takedown process, the abuse contact, a response time for abuse reports, and the privacy policy.
3. The registration pull request states that the operator agrees to succession: to transfer `storage` by [Registered hosts](../rfcs/0094-share-host.md#registered-hosts), or rules 33 to 35 for a host without GitHub storage.
4. **`bot` is used by this host only**, and opens no pull request on the authored repository that the host did not make, so an attestation always speaks for the account that opened the pull request.

## The storage repository

5. `storage` is public, owned by the operator and not by KSAModding, and written only by the host, by [The storage repository](../rfcs/0094-share-host.md#the-storage-repository).
6. **Data files are UTF-8 JSON without a byte order mark.** A reader ignores members it does not know, so a host may add members, but never with a name RFC 0094 or this page gives another meaning.
7. One GitHub release per release, never a replaced asset or a reused tag, and immutable releases where GitHub offers them, by [Stable downloads](../rfcs/0094-share-host.md#stable-downloads).

## Publishing

8. The host runs every check of [What the host checks before it publishes](../rfcs/0094-share-host.md#what-the-host-checks-before-it-publishes) before it writes anything, and shows a failure to the player.
9. **The host writes in this order**, so that no reader sees a reference to something that does not exist yet: the published GitHub release with its asset, the owner record for a new id, the release list entry, the attestation, the pull request.
10. **The release list only grows.** An entry is never edited, and is removed only by a takedown under rule 18.
11. Versions are refused by [The release list](../rfcs/0094-share-host.md#the-release-list), and ids and owner records follow [Owners](../rfcs/0094-share-host.md#owners).

## Pull requests

12. Pull requests come from a fork by `bot`, and grouping follows [Pull requests from the host](../rfcs/0094-share-host.md#pull-requests-from-the-host).
13. **Every push gets a new attestation** for the new head, because an attestation binds the exact content.
14. **The host never merges, approves or labels** a pull request on the authored repository.

## The upload API

Paths are relative to `api` from `hosts.toml`, which ends in a version segment such as `v1/`.
A breaking change is served at a new version segment next to the old one.

15. **The host serves these requests over HTTPS:**

    | Request | Body | Answer |
    |---|---|---|
    | `POST oauth/device_authorization` | Form, `client_id` | RFC 8628 device authorization response |
    | `POST oauth/token` | Form, RFC 8628 device grant | RFC 8628 token response, a bearer token for the host account |
    | `POST oauth/token` | Form, RFC 6749 refresh grant: `grant_type` `refresh_token`, `refresh_token`, `client_id` | RFC 6749 token response, a new bearer token |
    | `POST uploads` | Multipart: `archive`, `dependencies` (RFC 0085's list as TOML), and `listing` (an id) for a new version of an existing listing | `201`, JSON: `upload`, `checks`, `version`, `listing`, `expires` |
    | `POST uploads/<upload>/publish` | JSON: `version`, `status`, and for a new id the listing fields `id`, `name`, `authors`, `abstract`, `license`, `description` and `tags` | `201`, JSON: `id`, `type`, `version`, `pull_request` |

    `client_id` is any string naming the client, such as `borea`, and the host treats every client as a public client without a secret and shows the name when the player confirms the sign-in.
    A host that puts a `refresh_token` in the device grant answer takes the newest one in the refresh grant and answers with a new `refresh_token` that replaces the old one, so a client keeps the newest one.
    A host whose device grant answer has no `refresh_token` ends the sign-in when the bearer token expires, and the client signs in again.
    `checks` is an array of `{ "name", "passed", "message" }`, one per check of rule 8, and `listing` in the answer is the listing text to show.
    `expires` is when an upload that was not published is discarded, at least 24 hours after the upload.
    The listing fields have the types and meanings of [The shared authored core](../rfcs/0031-content-metadata-format.md#the-shared-authored-core), so `authors` and `tags` are arrays of strings.
    `id`, `name`, `authors`, `abstract` and `license` are required, `description` and `tags` are sent only when set, and `type` and the dependency list come from the upload.

16. **Errors are JSON** `{ "error", "message" }` with a 4xx or 5xx status, and a client shows `message` for a code it does not know:

    | `error` | When |
    |---|---|
    | `unauthorized` | No token, or the token has expired. |
    | `type_not_accepted` | The archive's type is not in `types`. |
    | `too_large` | The archive is larger than `max_bytes`. |
    | `invalid_archive` | A check of rule 8 failed. The body also carries `checks`. |
    | `id_taken` | The id is refused by [Owners](../rfcs/0094-share-host.md#owners). |
    | `version_taken` | The version is refused by [The release list](../rfcs/0094-share-host.md#the-release-list). |
    | `not_owner` | The account does not own `listing`. |
    | `rate_limited` | `new_listings_per_day`, or a limit of the host. The body also carries `retry_after` in seconds. |
    | `upload_expired` | The upload is past `expires`. |

## What the operator owns

17. Abuse reports, privacy and erasure follow [What the operator owns](../rfcs/0094-share-host.md#what-the-operator-owns), within the response time `policy` states.
18. **A takedown also removes the release list entry**, besides what [What the operator owns](../rfcs/0094-share-host.md#what-the-operator-owns) requires, so the watcher and an auditor see the same thing.
19. Every archive has an Internet Archive mirror by [Mirrors](../rfcs/0094-share-host.md#mirrors).

## Hosts without GitHub storage

A host may keep its archives and data files on its own server, object storage or CDN, by [Hosts that do not use GitHub storage](../rfcs/0094-share-host.md#hosts-that-do-not-use-github-storage), and is registered on the same terms.
Everything in this section is new.

Such a host names these keys in `hosts.toml` instead of `storage` and `pages`:

| Key | Meaning |
|---|---|
| `data` | The base URL that serves the data files. |
| `downloads` | The URL prefixes that archives are served under. |
| `key` | The Ed25519 public key that signs the data files, as base64 of its SubjectPublicKeyInfo. |
| `retired_keys` | Earlier values of `key`, so old signatures can still be checked. |

Rules 5 and 7 do not apply, and the others apply with "the archive at its `url`" for "the GitHub release" and `data` for `storage`.

20. `data` serves the data files at the paths of `storage`, over HTTPS, with the same bytes to every reader.
21. Each release list entry carries `url`, under a prefix in `downloads`, and `date`, the time the archive first became downloadable in RFC 3339 UTC. Neither ever changes.
22. Every data file is signed: at its path with `.sig` appended, `data` serves the base64 Ed25519 signature of the file's exact bytes by `key`. A file without a valid signature does not exist for the watcher or the checks.
23. Data files carry an `ETag`, answer `If-None-Match`, and are never more than 60 seconds older than the last write, so rule 9 holds for every reader.
24. The signing key is kept apart from the server that serves `data`. When it changes, the old key moves to `retired_keys` with a steward's pull request, and the host signs every current data file again.
25. The bytes at a `url` never change, and a `url` is never reused.
26. A download needs nothing but an HTTPS GET: no login, cookie, interstitial page, bot challenge or referrer check, from any network.
27. A download answers `200` with a `Content-Length`, and a `Range` request with `206`.
28. A `url` redirects only to a URL under a prefix in `downloads`.
29. A removed archive answers `410 Gone`.
30. The ownership check accepts an attestation only with a valid signature, and posts the attestation, its signature and the key as comments on the pull request that no later run edits, so a merged proof outlives the host.
31. A takedown makes the `url` answer `410`, and signs the changed release list again.
32. An erasure replaces the owner record without `github_id` and signs it again.
33. At succession, the operator gives the successor every data file, signature and archive, in a form the stewards can read without the host's software.
34. At succession, the operator transfers the domains of `data` and `downloads`, or keeps them redirecting to the successor's copies for at least one year. The Internet Archive mirrors cover what is lost anyway.
35. The signing key is not handed over: the successor registers its own, and the old one moves to `retired_keys`.

## What a steward checks

At registration, a steward checks rules 1 to 7 by reading `hosts.toml`, `policy` and `storage`, and shares one test vehicle through the API against rules 8 to 16, then closes the test listing without merging.
For a host without GitHub storage, the steward also verifies the test upload's signatures, checks that a wrongly signed change is refused, downloads the archive with a plain HTTPS client from outside the host's network, and reads the operator's statement of where the files are stored.

After registration, the watcher and the listing checks reject what breaks a rule they can see.
A steward removes a host from `hosts.toml` when it keeps breaking a rule after being told, or when its operator does not answer at the `policy` contact, and removing a host delists nothing.
