---
rfc: "0112"
title: Per-platform downloads
status: Accepted
authors: ["@Maximilian-Nesslauer"]
created: 2026-11-02
discussion: "https://github.com/KSAModding/content-manager-design/pull/112"
supersedes: []
superseded-by: []
---

# RFC 0112: Per-platform downloads

## Summary

A release of a `mod` or a `mod-loader` may carry an optional `platform_downloads` object next to its `download`, with a smaller archive per platform that a client takes instead of the archive for every platform.
`download` stays unchanged and required, and `spec_version` stays at `1`, because a client ignores a field it does not know and installs `download` as today.
It amends the release file of [RFC 0031](0031-content-metadata-format.md), the watcher of [RFC 0033](0033-content-index.md), the counts of [RFC 0052](0052-static-download-counts.md) and the gone mark of [RFC 0078](0078-gone-releases.md), and it answers unresolved question 5 of [RFC 0035](0035-content-install-descriptor.md) for files that differ per platform.

## Motivation

kRPC for KSA carries ASP.NET Core runtime packs that cannot be shared between Windows and Linux, so its archive is about 25 MB zipped while one platform needs about 12 MB, and every player downloads about 12 MB that their platform never loads ([discussion #75](https://github.com/KSAModding/content-manager-design/discussions/75)).
Its author asked for an `<id>-<os>.zip` next to `<id>.zip`, and the archive for every platform has to stay, because SpaceDock keeps one file per version and a manual install needs every platform.

## Reference-level explanation

`platform_downloads` comes after `install_size` and is absent, never an empty object, when a release has no platform archive, and its keys are the platform names of `os`, `windows`, `linux` and `macos`, in that order.
Each entry has `url`, `sha256`, `size`, `content_type` and `install_size`, all stamped, with the meaning they have for the release, no `mirrors`, and only the watcher adds `unavailable_since`, while `os`, `install`, `loader` and `dependencies` stay one value for the whole release.

```json
"platform_downloads": { "linux": { "url": "https://github.com/krpc/krpc/releases/download/ksa-v0.3.0/krpc-ksa-0.3.0-linux.zip", "sha256": "C3A1...", "size": 13100000, "content_type": "application/zip", "install_size": 30000000 } },
```

Only a `mod` or `mod-loader` listing whose authority is GitHub gets platform archives, and SpaceDock, share hosts, vehicles, saves and releases by pull request stay as today.
A zip of the release is platform-shaped when its name, compared case-insensitively, is `<stem>-<platform>.zip` or `<stem>_<platform>.zip` and `<stem>.zip` is also among its zips.
The universal archive is picked from the other zips by the rules of today, and the platform archives are its platform-shaped zips, so `krpc-ksa-0.3.0.zip` stays the universal archive and `krpc-ksa-0.3.0-linux.zip` is its Linux archive without a rename, and other platform-shaped zips are not used.
The watcher rejects the release when two zips name one platform, and when it has platform-shaped zips but no universal archive, with a message that the archive for every platform has to be there too.
The watcher downloads the platform archives one at a time, each within the same size limit as `download`, and rejects the whole release unless each has the same install root as the universal archive, for a `mod` the same derived dependencies from its `mod.toml`, and for a `mod-loader` every `launch` file that `[provides]` names and the `launch` of its `[provides.platform.<platform>]` entry of [RFC 0067](0067-per-platform-launch.md), and a transient host failure of one archive is a transient failure of the release.

The swap check of RFC 0033 and the gone mark of RFC 0078 apply to each entry on its own, so a gone platform archive gets `unavailable_since` in its entry and loses it when the same bytes come back, while only `download` decides whether the release is missing.
`platform_downloads` is identity like `download`, so no amendment changes it, and the release check of a pull request rejects a submitted `platform_downloads`, because that path stamps no platform archive until a later RFC says how.
The GitHub count of a release in RFC 0052 is its universal asset plus its platform assets, and the snapshot copies the key verbatim.

A client takes the entry for its own platform when there is one without `unavailable_since`, and otherwise `download`, and it verifies and records the hash of the archive it took.
It accepts an archive whose bytes match any archive of the release, for example a mod that a player installed by hand from the universal archive, it shows and checks space for the size of the archive it will take, and it may try `download` after a failed platform archive.

## Unresolved questions

- **Processor architecture.** As in RFC 0067, a platform name says nothing about it.
- **A listing id that ends in a platform name.** For a listing `Foo-linux` whose release holds `Foo-linux.zip` and `Foo.zip`, `Foo-linux.zip` is platform-shaped and `Foo.zip` becomes `download`, and a rule that `<id>.zip` is never platform-shaped would keep the pick of today.
