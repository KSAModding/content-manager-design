---
rfc: "0048"
title: Ownership of an edit
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-08-15
discussion: https://github.com/KSAModding/content-manager-design/pull/48
supersedes: []
superseded-by: []
---

# RFC 0048: Ownership of an edit

## Summary

The ownership check of [RFC 0033](0033-content-index.md) evaluates an edit against the authority the listing already names, and not against the authority the submitted document names.
An edit that points the listing at a different host verifies against both, and a repository that GitHub redirects to a new address did not change host.

Nothing else in RFC 0033 or [RFC 0038](0038-repository-topic-ownership-proof.md) changes, and the proofs themselves are untouched.

## Motivation

RFC 0033 binds ownership to "the host named in `[releases]`, or by `authority` when several are named", read out of the document being checked.
For a new listing that is the only document there is; for an edit it is the wrong one, because the submitted document is written by whoever opened the pull request.

Anybody can open a pull request against an existing listing, repoint its `[releases]` at a repository they own, verify against that, and auto-merge.
The listing keeps its id, and the watcher starts stamping the new repository's archives under it.

RFC 0033 makes this explicit rather than accidental: "A maintainer handover is a pull request to the listing, verified against the new authority or reviewed by a steward."
Verifying a handover against the new authority is the takeover, written down as the intended behaviour.

The index carries listings today and the listing flow auto-merges on green, so this is not theoretical.

## Guide-level explanation

Editing a listing that already exists is checked against the release host that listing names right now, on the default branch.
Editing your own listing therefore works as it did, because the host is yours before and after.

Renaming or transferring your repository is not a change of host: the old address answers as the new one, only its owner can arrange that, and the check reads the redirect.
Pointing your listing at a separate repository is a change of host, and it needs both proved, so a handover of that shape reaches a steward unless the outgoing owner first puts the incoming account's proof on the old host.

## Reference-level explanation

The check takes two versions of the document, the submitted one at the head commit and the base one at the base branch.
The base is read at the branch and not at the commit the pull request was cut from, because a pull request that predates a handover must not still verify against the previous owner.

| The change | Verified against |
|---|---|
| The document is not on the base branch | The submitted document. |
| It is there, authority unchanged | The base document. |
| It is there, authority moved | The base document, then the submitted one. Both have to verify. |
| It is there, and the base authority redirects to the submitted one | The submitted document. |

Whether the document already exists is read from the base branch and never from the file status a host reports, since that status is computed against the merge base.

Two documents name the same authority when `(kind, target)` is equal, compared case-insensitively, and two that bind to nothing name the same one because neither moves anything.

The three outcomes of RFC 0033 are unchanged.
A base authority that is unverified, or that cannot be evaluated, ends the check there and the new host is never asked.
A message about a failure names which of the two hosts it is about.

`GET /repos/{owner}/{repo}` answers a renamed or transferred repository under its current `full_name`, and that redirect is the whole rename rule.
A fork is excluded, as everywhere else in RFC 0033, and a host that does not answer is could-not-evaluate rather than a rejection.

## Drawbacks

- A handover between two separate repositories needs a steward, which is a queue item where there was none.
- A handover carried out as a transfer needs nobody, and its only record is the transfer itself.

## Alternatives

- **Forbid changing `[releases]` at all.** Closes the same hole, makes every repository rename a steward action, and cannot express a handover.
- **Require a steward for every edit.** Trivially safe, and it puts a human in front of every corrected typo, which is the queue this design exists to avoid.

## Unresolved questions

- **The authority is a name, not an identity.** GitHub frees a login when an account is deleted, so whoever re-registers it and creates the same repository becomes the provable owner. Storing the numeric repository id at first listing would close that, and it is a format change rather than a rule change.
- **Packs.** RFC 0033 says later pack versions are verified against the first-claim account, and nothing implements it: a new version is a new file, so it is an addition and verifies against what it declares. This RFC does not change that.
