---
rfc: "0000"
title: Which releases of a repository are mod releases
status: Draft
authors: ["@Maximilian-Nesslauer"]
created: 2026-10-11
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: Which releases of a repository are mod releases

## Summary

`[releases]` gets an optional key `tag_prefix`, for example `tag_prefix = "gatos-v"`: the watcher takes only the GitHub releases whose tag starts with it, and reads the version from the rest of the tag.
It amends `[releases]` of [RFC 0031](0031-content-metadata-format.md) and `since` of [RFC 0079](0079-author-freedom.md), and `spec_version` stays at `1`.

## Motivation

gatOS of @alex-sherwin publishes releases that carry only VM images next to its mod releases, in one repository.
The watcher takes every release that is not a draft, and `since` only cuts off older ones, so an image release is reported as a tag that does not parse, or is taken as a mod release and can even be stamped.

## Reference-level explanation

`tag_prefix` is a non-empty ASCII string without whitespace, valid only next to a `github` key, and it filters that host both as the authority and as a mirror, but not SpaceDock, which has no tags and lists the versions of one mod only.
A GitHub release is a candidate only when its tag starts with the prefix, compared case-sensitively as GitHub compares tags.
The rest of the tag goes through `normalize_version` as every tag does ([RFC 0072](0072-version-forms.md)), so one leading lowercase `v` is allowed there, and `"gatos-"` accepts both `gatos-1.2.0` and `gatos-v1.2.0`.
A candidate whose rest does not parse is reported as today, and the asset name is matched against the rest without its leading `v`.
A release that is not a candidate leaves the release list before every pass that reads it, the listing check of content-index included, so it is never stamped and never reported.
`since` compares with the version of the rest and reaches candidates only, and the release file gets no new field.

A changed prefix changes no stamped release file, so a stamped release that the new prefix does not match keeps its release notes as they are, and [RFC 0078](0078-gone-releases.md) marks it only when its archive is gone.
A release that only the new prefix matches is history when it is older than the newest stamped release, unless `since` reaches it.
The listing check rejects a prefix that no release matches in a repository that has releases, so a typo does not hide every release.
Borea and the listing page write `[releases]` from the keys they know and would drop an unknown `tag_prefix` on an edit, so both read, show and keep the key first, then the watcher and the listing check apply it, and only then does the schema of content-index accept it.

## Drawbacks

- A release that does not match is silent, so an author who changes the form of the tags must change the prefix too, or the watcher stamps nothing new.

## Alternatives

- **A glob or a regular expression:** rejected, because the watcher, the listing page and Borea must read it the same way in three languages whose regular expressions differ, and a pattern can match tags the author did not mean. A prefix covers every known case.
- **A filter on asset names:** rejected, because an image release without the mod archive would still be a candidate and be reported, and the question is which releases are mod releases, not which asset to take.
