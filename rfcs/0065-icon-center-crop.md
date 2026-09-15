---
rfc: "0065"
title: Center crop for icons that are not square
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-15
discussion: https://github.com/KSAModding/content-manager-design/pull/65
supersedes: []
superseded-by: []
---

# RFC 0065: Center crop for icons that are not square

## Summary

An icon from [RFC 0058](0058-listing-images-and-dates.md) no longer has to be square, as long as its longer side is at most twice its shorter side.
A client shows the square in the center of the icon, with the length of its shorter side, and the checks warn instead of rejecting.
Square icons keep working exactly as before.
`spec_version` and `snapshot_version` stay at `1`.

## Motivation

RFC 0058 accepts only a square icon, so an author whose only artwork is wide, such as a banner or a screenshot, has to make a second file before the listing can have an icon.
Many authors will not, and their listings show the placeholder.

Most artwork keeps its subject in the middle, so the center of a wide or tall image is usually a good icon.
Every client can compute that square the same way, so the listing still looks the same in every client.

## Guide-level explanation

### For an author

A square icon of 512 by 512 pixels or more is still the best choice, because you decide exactly what shows.
If you only have a wide or tall image, you can use it as the icon when its longer side is at most twice its shorter side, which fits a screenshot of 16 by 9.
Clients then show the square in its middle: for a wide image the full height, cut on the left and the right; for a tall image the full width, cut at the top and the bottom.
The checks tell you which part clients show, so you can decide whether a square file of your own is worth it.

### For a client

Before you show an icon, cut it to its center square, then show that square with the rules of RFC 0058.

## Reference-level explanation

### Limits for an icon

This replaces the `icon` row of the limits table of RFC 0058.

| Role | Records | Pixels | Bytes |
|---|---|---|---|
| `icon` | 0 or 1 | the shorter side 256 to 1024, the longer side at most twice the shorter side | at most 256 KiB |

So the longer side is never more than 2048 pixels.
An icon of 1280 by 640 pixels is valid, and an icon of 1500 by 500 pixels is not.
The ratio limit keeps the center square at half of the image or more, so the square still shows most of the artwork.
An icon with `width` equal to `height` meets these limits exactly when it met the limits of RFC 0058.

### What stays as in RFC 0058

Every other image rule of RFC 0058 applies to an icon that is not square without a change:

- PNG, JPEG or WebP, read from the file signature, and no animation.
- The byte cap of 256 KiB, the required record keys `url`, `sha256`, `width`, `height` and `size`, and the optional `license`, `attribution` and `source`.
- `width`, `height`, `size` and `sha256` describe the whole file and not the center square, and the checks and every client compare them with the fetched bytes.
- The fetch rules: HTTPS, at most three redirects, a public network target, no credentials, and a streamed byte limit.
- The re-check by the watcher, caching by `sha256`, the placeholder, the setting to load no images, and showing `attribution` and `source`.

### The center square

For an icon of `width` w and `height` h, the square has the side s = min(w, h) and its top left corner at x = floor((w - s) / 2) and y = floor((h - s) / 2), in pixels from the top left corner of the image.
When the difference is odd, the extra pixel is on the right or at the bottom.

A client shows only that square.
It then scales the square and fits it into its slots by the client rules of RFC 0058, so the rule "scales it without stretching or cropping it" applies to the square and not to the whole image.
A square icon is its own center square, so nothing changes for it.

### What the checks do

An icon whose `width` differs from its `height` is a warning, not a reject.
The warning names the square clients show, for example: "The icon is 1280 by 640 pixels, so clients show the square from 320,0 to 960,640."

This replaces the icon part of this row of the errors table of RFC 0058:

| Condition | Result |
|---|---|
| An icon whose shorter side is below 256 or above 1024 pixels, or whose longer side is more than twice its shorter side | Reject. |
| An icon whose `width` differs from its `height` | Warning. |

### Clients that implement only RFC 0058

Such a client finds an icon that is not square outside its limits, treats it as missing metadata and shows the placeholder, as RFC 0058 requires.
The listing stays usable, so nothing breaks, and the client gains the icon once it implements this RFC.

### Relationship to RFC 0058

This changes the icon limits, the client rule for showing an icon, and the icon rows of the errors table of RFC 0058, and nothing else.
No field is added and no field changes its meaning, and every document that was valid under RFC 0058 stays valid and shows the same, so `spec_version` stays at `1`.
The checks of the index have to accept the new limits before any listing can use them.

## Drawbacks

- The center can cut off what matters, such as text or a logo near an edge. The author sees that only in the warning of the checks or in a client.
- A wide icon of up to 2048 pixels makes a client decode more pixels than it shows.
- The ratio limit still rejects a wide banner, so its author still has to make a second file.
- There are two ways to supply an icon, and a square file stays the better one, which the listing guidance has to say.

## Alternatives

**Keep square icons only, and let the listing tool or a submission form cut the image when the listing is submitted.**
The author sees the result, and the format does not change.
Rejected because not every listing goes through such a tool, and the author still has to host a second image file.

**Show the whole image, with the surface colour of the client around it.**
Nothing is cut off.
Rejected because a wide image becomes a thin strip in a list row of 48 pixels.

**Let the author name the square, for example with a `crop` key.**
The author decides what shows.
Rejected for now because it adds a key that most authors never need, and the center is the right choice for most artwork.

**Accept any aspect ratio within the side limits.**
A banner of 2048 by 256 pixels would also be a valid icon.
Rejected because the center square of such an image is a small part of it and rarely shows the subject, and because a ratio limit can be relaxed later by an amendment, while a stricter limit later would make valid listings invalid.

**Keep rejecting icons that are not square.**
Rejected because it leaves listings without an icon although their author has usable artwork.

## Unresolved questions

- Whether the byte cap of 256 KiB is enough for a wide icon of up to 2048 by 1024 pixels.
- Whether a ratio of 2 to 1 is the right limit. A later RFC can relax it without a break.

## Future possibilities

- An optional key that names the square, if authors need more control than the center.
