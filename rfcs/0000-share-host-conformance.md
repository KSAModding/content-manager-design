---
rfc: "0000"
title: A conformance specification for share hosts
status: Draft
authors: ["@SafeShows"]
created: 2026-10-21
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: A conformance specification for share hosts

## Summary

[RFC 0094](0094-share-host.md) defines the share host and names ksamods.gg as the first one, but what an operator has to build is spread through its design and mixed with what the index does.
This RFC adds [spec/share-host.md](../spec/share-host.md), a living page of numbered rules that every share host follows, and that a steward checks before adding a host to `hosts.toml` and while it stays there.

The page carries RFC 0094's host-side requirements as rules, and adds what RFC 0094 leaves to each operator: the order in which a host writes, a fixed set of API errors, how a client identifies itself at sign-in, and what a steward checks at registration.
RFC 0094 keeps the index side: `hosts.toml`, the watcher, the ownership check, the snapshot files and download counts.

It also puts hosts without GitHub storage on equal footing with those that have it, where RFC 0094 only allows them.
Such a host signs its data files with a key registered in `hosts.toml`, serves downloads under rules that keep a URL stable and reachable, and agrees to hand over its data and domains when it stops.

`spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0094 expects more than one share host: the upload API exists so that "a client can share to any registered host without integrating each one".
A second operator today would have to read RFC 0094 end to end and work out which sentences bind them.
Some things it would not find at all:

- **What a steward checks before registration.** RFC 0094 leaves this as an unresolved question.
- **The order of writes.** The watcher rejects a release list entry whose GitHub release does not exist yet, so a host that writes the list first gets its own release rejected on a tick that falls in between.
- **The shape of API answers and errors.** RFC 0094 says errors carry a machine-readable `error`, but names no codes, so each client would handle each host's codes on its own.
- **The OAuth client.** The device grant of RFC 8628 needs a `client_id`, and a host that expects clients to register first breaks sharing to any registered host.

An accepted RFC is never edited, by CONTRIBUTING.md, but host requirements will change as hosts appear: `max_bytes` values, sharding of `storage`, and limits learned from abuse.
The repository already keeps living rules under `spec/`, as `spec/snapshot.md` and `spec/tags.md`, and a host checklist belongs there.

If nothing is done, the first host defines the protocol by what it happens to do, and every later host and client copies its behaviour.

## Guide-level explanation

**Running a host.**
You want to run a share host.
You read spec/share-host.md, build against its rules, and create a public storage repository under your own account or organization.
You publish a policy page and open a pull request on the authored repository that adds your table to `hosts.toml`, and you state in it that you agree to the succession rule.

**Registration.**
A steward reads your entry, your policy and your storage repository, and shares one test vehicle through your API with a client.
They check each rule of the page and close the test listing without merging.
When every rule holds, they merge your entry.

**Sharing from a client.**
A client that shares to any registered host signs in with the device grant, sending its own name as `client_id`, and uses the four requests of rule 25.
It handles the error codes of rule 26 the same way for every host, for example by asking for a new id on `id_taken` and waiting `retry_after` seconds on `rate_limited`.

**When a host breaks a rule.**
The watcher and the listing checks reject what they can see.
For what they cannot see, such as an abuse report that goes unanswered, a steward contacts the operator, and removes the host from `hosts.toml` when the rule keeps being broken.

## Reference-level explanation

### The page

spec/share-host.md is a living document, like spec/snapshot.md.
Its rules are numbered across the whole page, and a number is never reused, so a pull request, a check or a client can cite "rule 13".
A removed rule keeps its number and is marked removed.

The page holds the rules and no reasons, and links RFC 0094 for the design.
Where it and RFC 0094 disagree, the page applies, and the pull request that caused the disagreement says so.

### What the page adds to RFC 0094

Most rules restate RFC 0094.
These are new:

| Rule | What it adds |
|---|---|
| 4 | `bot` is used by one host only, so an attestation in `storage` always speaks for the account that opened the pull request. |
| 8 | Data files are UTF-8 JSON without a byte order mark, and readers ignore unknown members. |
| 13 | The order of writes. |
| 14 | The release list only grows, except for a takedown. |
| 22 | A new attestation for each push, because the attestation binds the head. |
| 24 | The host never merges, approves or labels. |
| 25 | The device and token endpoints, the answer bodies, any `client_id` accepted as a public client, and a minimum of 24 hours before an unpublished upload expires. |
| 26 | A fixed set of error codes. |
| 27 | A takedown also removes the release list entry, so the watcher and an auditor see the same thing. |
| 31 to 47 | The rules for hosts without GitHub storage, below. |
| Steward checks | A test upload at registration, and removal from `hosts.toml` for repeated breaks. For a host without GitHub storage, a signature check, an outside download and a statement of where the files are stored. |

### Hosts without GitHub storage

RFC 0094 allows a host to serve its data files and archives itself, under `data`, but recommends against it: the watcher depends on the host's server, the host could answer readers differently, nobody can audit its claims, and there are no download counts.
This RFC registers such a host on the same terms, and the page makes up for each loss with rules:

| What GitHub storage gives | What replaces it | Rules |
|---|---|---|
| Only a writer of `storage` can place an attestation, and git history shows when it did. | Every data file is signed with an Ed25519 key in `hosts.toml`, and the ownership check copies the attestation and signature into its check run output. A compromise of the web server alone cannot forge a proof, and a merged proof outlives the host. | 33, 35, 41, 42 |
| An asset URL stays the same while the asset exists. | The bytes at a `url` never change, a `url` is never reused, and a removed archive answers `410`. | 36, 40 |
| Anyone can download an asset with a plain HTTP client. | No login, challenge or interstitial, `Range` support, and redirects only inside the registered `downloads` prefixes. | 37 to 39 |
| The watcher sees a write as soon as it happens. | Data files are at most 60 seconds stale and answer `If-None-Match`. | 34 |
| A transfer of `storage` keeps every file. | The operator hands over every file and keeps the domains working for a year, and the Internet Archive mirrors are the fallback. | 45 to 47 |

Signatures are detached, one `.sig` file beside each data file over its exact bytes, so no JSON canonicalization is needed and a reader that ignores signatures reads the files as before.
The key is Ed25519 because it is small, deterministic, and in the standard libraries of the languages the index and its clients use.

What it does not replace is download counts: RFC 0052 never reads a host's own counter, so a listing on such a host shows none.

### How the page changes

- **A clarification**, a fixed link, or a new example: a pull request approved by one steward.
- **A new rule, or a stricter rule**: an RFC, because it binds hosts that registered under the old page. The RFC states how long registered hosts have to comply.
- **A looser or removed rule**: a pull request approved by two stewards, because it binds no one new.
- **A new error code**: a pull request, because rule 26 already tells a client to show `message` for a code it does not know.
- **A breaking change to the API**: an RFC, and the new API is served at a new version segment next to the old one, by rule 26.

### What changes in RFC 0094

RFC 0094 is still Proposed, so its pull request can take these changes before it is accepted:

- Its section on hosts that do not use GitHub storage no longer calls GitHub storage the recommended form, and links the page.
- `hosts.toml` gains the keys `downloads`, `key` and `retired_keys` for such a host.
- The ownership check verifies the signature of an attestation from `data`, and records the attestation and signature in its check run output.
- The sections on the storage repository, the upload API, the checks before publishing and the operator's duties link the page, and its unresolved question on what a steward checks is answered by the page's last section.

## Drawbacks

- **Two places to read.** A reader of RFC 0094 has to go to the page for the binding rules, and a change to one can leave the other stale.
- **A test upload costs the operator nothing, but costs a steward an hour.** It is still cheaper than finding a broken host after players have uploaded to it.
- **Fixed error codes limit a host.** A host with a new kind of refusal has to use a generic code with a good `message` until the page gains one.
- **Any `client_id` is accepted.** A host cannot block one client by its id, because any client can send any name. It can still block accounts and rate limit them.
- **Equal footing still costs a host without GitHub storage its download counts**, and players may prefer listings that show one.
- **Key management is new work** for the operator and the stewards: a lost key stops every proof on that host until a steward registers a new one, and a leaked key lets anyone attest changes to its listings until it is retired.
- **A host without GitHub storage is harder to audit after the fact.** Signatures prove what the host said, but not that it said the same thing to every reader at every time. The check run output keeps only what the checks saw.

## Alternatives

- **Leave the rules in RFC 0094.** Once accepted, it cannot change, and every new host requirement would need an RFC that amends it.
- **A conformance test suite instead of a page.** It would check the API and storage layout by machine, but cannot check a policy page or a succession agreement, and needs the page as its source anyway. It is a future possibility.
- **A registry of OAuth clients per host.** It lets a host block a client by id, but every client would need a registration on every host, which is what RFC 0094's shared API exists to avoid.
- **Let each host define its own errors.** Clients would carry code for every host, against RFC 0094's goal.

## Unresolved questions

- How a client learns the registered hosts and their `api` URLs. `hosts.toml` is in the authored repository, and RFC 0094 does not say whether the snapshot embeds it, as it embeds `tags.toml` as `tags`.
- Whether the response time for abuse reports needs a ceiling on this page, instead of whatever `policy` states.
- How long a registered host gets to comply with a new rule.
- Whether a steward should run the test upload again after the operator changes, for example at a `storage` transfer.
- Whether hosts with GitHub storage should sign their data files too, so one ownership check fits both kinds and a proof survives a compromise of `storage`, which RFC 0094 lists as a future possibility.
- Whether one year of redirects in rule 46 is enough, and what the stewards do when an operator disappears without handing anything over.
- Whether a host without GitHub storage may publish download counts that RFC 0052 reads, for example signed by its `key`.
- Whether GitHub check run output is kept long enough to serve as the record of rule 42, or the proof should go somewhere in the authored repository.

## Future possibilities

- A conformance test suite in the authored repository that a steward points at a host's `api` and `storage`, and that a host runs in its own CI.
- A reference host under an open license, which RFC 0094 names as the quick way for a successor to take over.
- A `GET` request in the API for the listings an account owns, so a client can offer "new version" without the player picking the id.
