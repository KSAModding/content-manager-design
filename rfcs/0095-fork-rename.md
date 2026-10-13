---
rfc: "0095"
title: The rename redirect follows a fork
status: Draft
authors: ["@Maximilian-Nesslauer"]
created: 2026-10-11
discussion: https://github.com/KSAModding/content-manager-design/pull/95
supersedes: []
superseded-by: []
---

# RFC 0095: The rename redirect follows a fork

## Summary

The rename redirect of [RFC 0048](0048-ownership-of-an-edit.md) follows a renamed or transferred fork like any other repository.
The new name is verified with the fork rule of [RFC 0079](0079-author-freedom.md): the owner id or the topic, never the marker file.
This amends RFC 0048 only, so `spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0048 says "A fork is excluded, as everywhere else in RFC 0033".
RFC 0079 lets a fork prove ownership, so a fork is no longer excluded everywhere else, but RFC 0079 does not list RFC 0048 as amended ([#84](https://github.com/KSAModding/content-manager-design/issues/84)).
The index has followed a renamed fork since [content-index#148](https://github.com/KSAModding/content-index/pull/148), so the code and RFC 0048 disagree.

## Reference-level explanation

In RFC 0048, the sentence "A fork is excluded, as everywhere else in RFC 0033, and a host that does not answer is could-not-evaluate rather than a rejection." becomes "A fork is followed like any other repository, and a host that does not answer is could-not-evaluate rather than a rejection."

This is safe for the same reason as for any other repository: only the owner of a repository can rename or transfer it.
The ownership check then verifies the new name with the fork rule of RFC 0079, so a renamed fork cannot pass through a marker file it inherited.
Pointing a listing at a different repository, such as a fork of its repository, stays a change of host under RFC 0048 and verifies against both.

## Alternatives

- **Keep the exclusion.** Rejected, because the owner of a fork that proves ownership under RFC 0079 would need a steward for every rename.
