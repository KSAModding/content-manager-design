---
rfc: "0038"
title: A repository topic as an ownership proof
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-08-09
discussion: https://github.com/KSAModding/content-manager-design/pull/38
supersedes: []
superseded-by: []
---

# RFC 0038: A repository topic as an ownership proof

## Summary

A GitHub repository topic becomes a third way to prove that the account opening a listing pull request controls the release host the listing points at.
The claimant sets `ksa-index-<login>` on the target repository, and the ownership check accepts it exactly as it accepts [RFC 0033](0033-content-index.md)'s marker file today.
Nothing else in RFC 0033 changes.

## Motivation

RFC 0033's cheap path compares the repository's numeric owner id against the pull request author's, so it only ever fires for a personally owned repository.
Every organization-owned repository falls through to the marker file, including `StarMapLoader/StarMap`, the one listing every code mod depends on.
There the first step of listing your own content is committing a file into your own repository, which under branch protection is a pull request in front of a pull request.

## Guide-level explanation

Set one topic on the repository your releases come from, the string `ksa-index-` followed by your GitHub login in lowercase, so `ksa-index-maximilian-nesslauer`.
Then open your listing pull request, with nothing added to your repository's contents, and one topic covers every listing that points at that repository.
Removing it revokes the proof for future checks, and listings already in the index stay listed.

## Reference-level explanation

The ownership check accepts any one of three proofs, evaluated cheapest first:

1. **Owner id.** A non-fork repository whose owner id equals the pull request author's. Unchanged.
2. **Topic.** The repository carries `ksa-index-<login>`, where `<login>` is the pull request author's login lowercased.
3. **Marker file.** `.github/ksa-content-index.toml`. Unchanged.

Comparison uses the lowercased login, because GitHub normalizes topics to lowercase while a login keeps the display case its owner chose.

**The topic names the claimant rather than the listing id**, because the charset cannot carry an id: RFC 0031 ids allow `.` and `_` up to 64 characters, so encoding the id would work for most listings and silently fail for a few, while the pull request already states which repository the listing points at.

**What it proves** is that the named account was an administrator of that repository at the moment of the check, GitHub's documentation being explicit that repository admins are who can add topics, which is a stronger permission than the write access a marker file needs.
Two administrators may each carry their own topic and both may then claim listings pointing at that repository, which is intended, since both control the release host.

**Forks do not inherit topics**, verified against `KSP-CKAN/CKAN`, which carries three, and its fork `KSAModding/CKAN-KSA`, which carries none; RFC 0033's blanket fork rejection stays regardless, because it also guards the marker path.

The topic is read with `GET /repos/{owner}/{repo}/topics`, which needs no pull request content, so it runs in the same privileged job as the rest of the ownership check and reports the same pass, reject, and could-not-evaluate outcomes.
Being current state rather than a record, it is re-read wherever RFC 0033 already re-checks ownership, on a maintainer handover and on the watcher's sweep.

## Drawbacks

- **No history.** A marker file arrives in a commit with an author and a timestamp, so in a first-claim dispute it is evidence and a topic is not. RFC 0033's required forums thread is already the tiebreaker, which bounds the loss.
- **Revocation is silent.** An administrator tidying up topics withdraws a proof with no signal, and nobody finds out until the next check needs it.

## Alternatives

- **Encode the listing id in the topic.** Rejected because the repository already identifies itself.

The pattern is the one every domain verification uses, place a token only the controller can place at a well-known location, with a cheaper location; the idea came from ksamods.gg.

## Unresolved questions

- SpaceDock ownership stays unresolved, as it is in RFC 0033. The same shape may transfer, a marker string only an author can place, but nothing here verifies that.
