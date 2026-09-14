---
rfc: "0058"
title: Listing images and dates
status: Accepted
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-13
discussion: https://github.com/KSAModding/content-manager-design/pull/58
supersedes: []
superseded-by: []
---

# RFC 0058: Listing images and dates

## Summary

An authored document gets an optional `[images]` table with two roles: one square icon, and the images its Markdown description shows.
The icon is the only artwork a listing needs, and a client shows it at every size its layouts use; screenshots and any other pictures go into the description.
Each image is a record naming a URL on the author's own host, together with the SHA-256 digest, width, height and byte size of the image, and its license when that differs from the document's.
The listing checks fetch every image and verify those facts, the index copies and serves nothing, and a client verifies the bytes again before it shows them.

The snapshot gets two derived optional fields on every listing and pack entry, `published_at` and `updated_at`, computed from the release and pack version timestamps that already exist.

Everything is optional, so `spec_version` and `snapshot_version` stay at `1`.
This RFC settles the pre-RFC discussion in [#45](https://github.com/KSAModding/content-manager-design/discussions/45).

## Motivation

The Borea designs in [Borea#8](https://github.com/KSAModding/Borea/issues/8) show a square image for each listing in three places: the Discover rows, the detail header and the tiles on Home.
[RFC 0031](0031-content-metadata-format.md) has no image field, so every client and every web front end would invent its own, and a listing would look different in each.

The `description` is CommonMark, so an author can already put `![alt](https://any.host/image.png)` into it.
A renderer then loads an image from any host, of any size, with no check that it is the image the author meant, and every host learns the IP address of every reader.

The same designs show "Published 1 year ago" and "Updated 4d ago".
RFC 0031 has timestamps only per release and per pack version, and a client that aggregates them has to decide by itself whether a yanked release or a dev build counts, so two clients show two different dates for the same listing.

## Guide-level explanation

### For an author

You add a record per image to your listing:

```toml
description = """
Configure the guidance mode in the settings window.

![The guidance settings window](ksa-image:settings-window)
"""

[images.icon]
url = "https://example.invalid/my-mod-icon.png"
sha256 = "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"
width = 512
height = 512
size = 48213
license = "CC-BY-4.0"
attribution = "Artwork by Example Artist"

[[images.description]]
id = "settings-window"
url = "https://example.invalid/settings-window.png"
sha256 = "1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF"
width = 1600
height = 900
size = 402117
```

The icon is the one piece of art you make.
A client shows it in a list row, on a tile and in the detail header, so one square file of 512 by 512 pixels or more covers all three.
Everything else you want to show, screenshots, a header picture or a whole gallery, goes into your description, as many or as few images as you like within the limits.

The image stays on your host, for example in your repository or on your website.
The listing tool or a submission form fills in `sha256`, `width`, `height` and `size` from the file, and the checks fetch the image and compare.
A record without `license` falls under the document's `license`, which fits your own screenshots, and a record under a different license names it, as the icon above does.

In the description, `ksa-image:settings-window` places the image with that `id`.
A client shows no other images in a description, so a plain image URL there does not display.

When you replace the image with new bytes, the digest changes, so you change the record in the same pull request.
When you only move the same file to a different address, you change `url` and nothing else.

If your image later stops loading or changes on its host, the index tells you in the issue it keeps for your listing, and clients show a placeholder until you fix it.

### For a client

A client can lay out a list from the snapshot alone, because each record carries the size of the image.
It loads the icons the user can see and the description images only when it shows the description, checks the bytes against the record, and caches them by digest.
When an image does not load or does not match, the client shows its placeholder for the content type, and the listing works as before.

## Reference-level explanation

### The `[images]` table

Optional on `mod`, `mod-loader` and `modpack` documents.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `icon` | table | no | The square image that stands for the listing in lists, tiles and headers, at the size each of them needs. One image record. |
| `description` | array of tables | no | The images the `description` references. Description image records. |

These two roles are the whole vocabulary, and a new role arrives by RFC.
The checks reject a key inside `[images]` that they do not know, and a client ignores it, per RFC 0031's evolution rule.

### An image record

| Key | Type | Required | Meaning |
|---|---|---|---|
| `url` | string | yes | HTTPS URL of the image on the author's host. |
| `sha256` | string | yes | Hex SHA-256 of the image bytes, compared case-insensitively. |
| `width` | integer | yes | Width in pixels. |
| `height` | integer | yes | Height in pixels. |
| `size` | integer | yes | Length of the image in bytes. |
| `license` | string | no | An SPDX license expression for the image, by the same rule as the document's `license`. Absent means the image is under the document's `license`. |
| `attribution` | string | no | Credit text that a client shows with the image. The author adds it when the image's license requires credit. |
| `source` | string | no | HTTPS URL of the original work, which a client links with the image. The author adds it when the license requires a link to it. |

A description image record has one more key:

| Key | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | The name the description references. 1 to 64 ASCII letters, digits, `-` and `_`, first and last a letter or digit, case-sensitive, unique within the document. |

An image can name its own `license` because the document's `license` covers the content, and artwork is often a separate work with separate terms.
A record without `license` is under the document's `license`, so an author's own screenshots need no extra line.

### Limits

| Role | Records | Pixels per side | Bytes |
|---|---|---|---|
| `icon` | 0 or 1 | 256 to 1024, and `width` equals `height` | at most 256 KiB |
| `description` | 0 to 16 | at most 2048 | at most 1 MiB each |

For both roles, the image is PNG, JPEG or WebP, read from the file signature and not from the extension or the `Content-Type` header, and it is not animated, so an APNG or an animated WebP is invalid.

The caps bound what the checks and a client download for one listing, about 16 MiB at most.
They do not have to bound memory by count: a client loads description images only when it shows the description and decodes the ones in view, so what it holds follows the screen, and a 2048 by 2048 image takes about 16 MiB as decoded pixels.

### Live facts, and packs

For a `mod` or `mod-loader`, images are live listing facts, like `status` and `superseded_by`.
They are not frozen into the `listing` block of a release file, whose fields RFC 0031 lists, and this RFC does not add `images` to that list.
Changing an image therefore updates every view of the listing, including the view of an old release.

An old release's frozen `description` resolves its `ksa-image:` references against the live `[images]` table, and a reference whose id no longer exists renders as a missing image.

A `modpack` has no live document, because every pack version is one complete immutable document.
Its images are facts of that pack version: the view of a pack uses the images of its newest version that is not retracted, and the view of one pack version uses that version's images.
A pack changes its images only by publishing a new version.

### Description references

In `description`, an image whose destination is `ksa-image:<id>` references the description image record with that `id`.
CommonMark parses it as an ordinary image, so no renderer needs a parser extension.

Every renderer of a description, a desktop client as much as a web front end, follows these rules:

1. It resolves a `ksa-image:` reference only to a record of the same document, or of the live document for a frozen description, and loads that image by the client rules below, with the Markdown alternative text as the image's text.
2. A reference to an id that has no record renders as a missing image, and the rest of the description renders.
3. It fetches no other image in a description. An image with any other destination, and an image in raw HTML, renders as its alternative text or not at all. Links stay links.

Rule 3 is what makes the records the only images a reader loads, so the limits, the digest and the license apply to every image a listing shows.

### What the checks do

When a document with an `[images]` table is validated, the unprivileged validation job of [RFC 0033](0033-content-index.md) fetches each image record and requires:

- HTTPS on the first request and on every redirect, and at most three redirects.
- A public network target: before each connection, including after each redirect, the resolved address is checked, and loopback, private, link-local, unique local, multicast, unspecified and cloud metadata addresses are rejected. The connection goes to the address that was checked.
- No credentials and no cookies on the request.
- A streamed byte limit at the role's cap, so a response is cut off as soon as it is too large.
- A format, animation state and pixel size inside the limits above, read from the bytes.
- `width`, `height`, `size` and `sha256` equal to what the bytes show.

A host that does not answer, a timeout, a server error or a rate limit is could-not-evaluate, per RFC 0033.
A missing file, a record that does not match its bytes, or bytes outside the limits is a reject.

On an edit, only a record that is new or changed against the base branch's document can reject or hold the pull request.
A record that is identical on the base branch and fails to fetch is reported as a warning, so a dead image does not block an unrelated correction, and the sweep below already reports it.

The checks also parse the description as CommonMark:

- A `ksa-image:` reference to an id with no record is a reject.
- A description image record that nothing references is a warning.
- An image with another destination, or an image in raw HTML, is a warning that names rule 3, because no client shows it.

Because the digest pins the bytes, the verified `width`, `height` and `size` stay true for any bytes that still match the record.
That is why the author writes them and the checks verify them, the same way `sha256` is written and verified, and why no generated document has to carry measured values.

### Re-checking published images

A host can change or remove an image after the listing merged.
The watcher of RFC 0033 re-fetches the images of every listed document on its sweep, by the same rules, at an interval that is a tuning parameter and needs no RFC.

A failure or a mismatch goes into the one issue the watcher keeps current per listing on the authored repository, naming the record's `url`, the expected `sha256` and what the fetch found, and the issue closes when the image verifies again.
The sweep never edits a document, never changes `index_status` and never delists.

A dead image is not a state of the index.
`index_status` is the index's moderation voice, owned by the stewards, with a closed set of states, and a client shows a state it does not know as a warning, so a broken icon there would put a warning on content that installs and works.

### Client behavior

- A client can lay out a list from `width` and `height` and show a placeholder until the image loads.
- A client renders the one icon at every size its layouts need, such as a list row, a tile and a detail header, and scales it without stretching or cropping it. Where a slot is not square, the client fits the whole icon inside the slot with its own surface colour around it.
- Before it shows fetched bytes, a client applies the same rules as the checks: HTTPS and the redirect limit, the streamed byte limit, the format, no animation, and `width`, `height`, `size` and `sha256` equal to the record. It should also apply the public network target rule, because a host name can resolve to a different address after publication.
- An image that fails any of these is missing metadata: the client shows the placeholder for the content type, and the listing stays usable.
- A client shows a record's `attribution`, and a link to its `source`, together with the image, for example as a caption or a tooltip, so the credit a license asks for reaches the reader. For an icon in a list row, showing them on the listing's detail view is enough.
- A client fetches without credentials or cookies, and caches by `sha256`, so an image with a known digest never has to be fetched again. It should load only the icons it is about to show, and it loads description images only when it shows the description, never for a list.
- A client may present the description images of a listing as a gallery next to the description, in the order the description references them.
- A client should offer a setting to load no images from author hosts, because every fetch tells that host the reader's IP address. With the setting on, it shows placeholders.
- An image never affects installation, dependency resolution, compatibility or ownership.

### Rights

The listing guidance of the authored repository gains one submission statement: by adding an image record, the submitter states that they have the right to publish the image and to let clients fetch, display and cache it under the record's `license`, or under the document's `license` when the record names none.
When the image is third-party work, or its license requires credit, a license notice or a link to the original, the record carries that in `attribution` and `source`.

The [KSA Mod Release Rules](https://forums.ahwoo.com/forums/kitten-space-agency/mod-releases/mod-release-rules.485/) are the community precedent for crediting other people's assets, and they do not grant any right to an image by themselves.

### Derived dates

The snapshot builder attaches two optional fields to every listing entry and every pack entry that is not a tombstone, next to `id` and never inside `authored` or a release file:

| Field | Meaning |
|---|---|
| `published_at` | The earliest `release_date` of the listing's release files, or `released_at` of the pack's versions, yanked and retracted versions included, because they still record when the content first appeared. |
| `updated_at` | The latest `release_date` or `released_at` of a version that is not yanked and not retracted, of any `release_status`. |

Timestamps compare as instants, and the builder copies the winning value as the source document writes it, so the output stays deterministic.

```json
{
  "id": "AdvancedFlightComputer",
  "published_at": "2026-08-02T13:18:41Z",
  "updated_at": "2026-09-02T10:14:05Z",
  "authored": { "...": "..." },
  "releases": [{ "...": "..." }]
}
```

A listing with no indexed version has neither field.
A listing whose every version is yanked or retracted has `published_at` and no `updated_at`.
A tombstone has neither.

The values follow the index, so they can move: a yank or a retraction can move `updated_at` back, and a backfilled older release can move `published_at` earlier.

`updated_at` counts dev and testing releases, so it can show activity a user of stable releases does not see.
A client may show a date per release channel instead, computed from `release_status` and `release_date` in the snapshot, and `updated_at` stays the all-channel value.

The builder already joins, filters and attaches; these two fields add a fourth kind of entry-level field that it computes from the documents it carries, and the living [snapshot specification](../spec/snapshot.md) gains them once this RFC is accepted.

### Errors

| Condition | Result |
|---|---|
| A key inside `[images]` other than `icon` and `description` | File invalid. |
| A required record key missing, or a key the record does not define | File invalid. |
| More than one icon, or more than 16 description records | File invalid. |
| An `id` outside its rules, or two description records with the same `id` | File invalid. |
| A `url` or `source` that is not HTTPS | File invalid. |
| A `ksa-image:` reference to an id with no record | File invalid. |
| Bytes that are not PNG, JPEG or WebP, are animated, exceed the byte cap, or have pixel sizes outside the limits | Reject. |
| `width`, `height`, `size` or `sha256` different from the fetched bytes | Reject. |
| A redirect chain longer than three, a redirect to a non-HTTPS URL, or a non-public network target | Reject. |
| A host that does not answer, a timeout, a server error or a rate limit | Could-not-evaluate. |
| A description record that nothing references | Warning. |
| An image in the description that is not a `ksa-image:` reference | Warning. |
| An unchanged record that fails to fetch on an edit | Warning. |

### Relationship to other RFCs

This adds optional fields to the authored documents of RFC 0031 and to the snapshot of RFC 0033, and changes no existing field, so `spec_version` and `snapshot_version` stay at `1`.
The authored schema of the index rejects unknown fields, so the checks have to learn `[images]` before any listing can carry it.

## Drawbacks

- An author-hosted image tells its host the reader's IP address, and the link can die. The digest, the placeholder and the opt-out setting limit the damage, and they do not remove it.
- The checks and every client fetch URLs an author chose. The network target rules are what keeps that from reaching a private network, and a mistake in implementing them is a real vulnerability.
- The author has to supply four facts per image that a tool computes. Without the listing tool or a submission form, that is error-prone by hand.
- A dead or changed image is found only on the next sweep, and the author has to read the issue.
- The icon is square only. Art made for a wide layout has to be cut to a square, and a client shows it small in a list row, where fine detail is lost.
- A description with many images makes the checks and the sweep fetch more per listing.
- `published_at` and `updated_at` can move after the fact, which surprises a reader who remembers the old value.

## Alternatives

**Commit images into the index and serve them from there.**
One host, one cache, moderatable bytes, and no reader IP reaches an author host.
Rejected because RFC 0025 rules out hosting content files, binary files stay in git history forever, and the index repositories would grow with every icon change.

**A URL only, with no digest and no sizes.**
Rejected because a client then cannot bound what it downloads, cannot lay out before it loads, and cannot tell the image the author published from whatever the host serves today.

**Let the checks measure width, height and size and write them into a generated document.**
Rejected because the validation job only leaves a verdict and the snapshot builder copies documents verbatim, while an authored value verified against a pinned digest gives the same guarantee with no new document.

**Report a dead image in `index_status`.**
Rejected because that is the stewards' moderation voice, and a client warns on a state it does not know.

**An icon in several sizes, one file per layout.**
Rejected because it asks an author without art skills for several files of the same picture, while a client scales one square image down to every size its layouts need.

**A banner and a gallery as roles of their own.**
Rejected because the description already carries every further image, as many as the author wants within the limits, in the place and order the author chooses, and one square icon asks the least art of an author.
A client that wants a gallery view builds it from the description images, as the client rules allow.

**Image URLs directly in the description.**
Rejected because they bypass every limit, the digest and the license, and send the reader's IP address to any host an author names.

**Author-written listing dates, or git commit dates.**
Rejected because an authored date can disagree with the release data it describes, and a commit date changes when a repository moves or its history is rewritten.

**`updated_at` from stable releases only.**
Rejected because it hides dev and testing activity from every client, while a client that wants a per-channel date can compute it from data it already has.

**SVG icons.**
Rejected for now because rendering vector documents from arbitrary hosts has a much larger security and compatibility surface than decoding three raster formats.

## Unresolved questions

- How often the sweep re-fetches images, which is a tuning question for the watcher rather than a format question.

## Future possibilities

- A banner role or a gallery role, by RFC, if a design ever needs art that the description cannot carry.
- Download counts, proposed as RFC 0052 in [#52](https://github.com/KSAModding/content-manager-design/pull/52), cover the download numbers the designs show. A "trending" view needs counts over time, which neither RFC 0052 nor this RFC provides.
- Image caches and mirrors keyed by `sha256`, so a derived view such as a web front end can serve images and hide readers' addresses from author hosts, with clients accepting any source whose bytes match, as RFC 0031 already does for `download.mirrors`.
- The vehicle and save content types, when their RFCs arrive, can reuse the image record unchanged.
