# What the Ahwoo forums offer to a program

Read on 2026-09-23 as a guest, right after the Forums v1.13.0 update, with 33 sequential requests and the user agent `KSAModding-research (github.com/KSAModding)`.
The example threads are the `links.forums` values of the index listings.

## Answer

The forums have no API that we can use, but three read-only sources carry most of what the RFCs need: the sitemap, the RSS feeds, and the thread page.
None of them sends CORS headers, so a server or a desktop program can read them, and a browser page cannot.
The Ahwoo terms of use forbid to "harvest or collect any Content either manually or via an automated software tool", so no scheduled reader should run before the Ahwoo team agrees.

## The software

The pages carry XenForo 2.3 markers: `<html id="XF" data-xf="2.3">`, scripts under `/js/xf/`, the `xf_` cookie prefix, and feed ids such as `urn:xenforo:thread:783`.
Ahwoo adds its own style, error pages ("Ahwoops!") and features, and releases them as "Forums v1.x".
This page reports only the endpoints that were tested.

## Thread URLs

A thread is identified by its numeric id.
The canonical URL is `https://forums.ahwoo.com/forums/<category>/<forum>/<slug>.<id>/`.
`/threads/<slug>.<id>/`, a wrong forum path, and a missing trailing slash all answer 301 to the canonical URL.
So a listing link survives a rename and a move, and a checker compares ids, not URLs.
The `/threads/` form in the examples of RFC 0031 still works.

## The sources

| Source | URL | Answer |
|---|---|---|
| Thread page | the canonical URL | 200 HTML |
| Forum listing | `/forums/kitten-space-agency/mod-releases/`, `page-N`, `?prefix_id=N` | 200 HTML, 20 threads per page |
| Forum RSS | `/forums/kitten-space-agency/mod-releases/index.rss`, also with `?prefix_id=N` | 200 RSS 2.0, the 20 threads with the newest posts |
| RSS of all forums | `/forums/-/index.rss` | 200 RSS 2.0, 20 items |
| Thread RSS | `/threads/783/index.rss` | 200 with an `<errors>` body, no feed |
| Sitemap | `/sitemap.xml` | 200, one `urlset` of 1268 URLs, 1224 of them threads |
| REST API | `/api/threads/783/` | 400 JSON, `no_api_key_in_request` |
| JSON view | `/threads/783/?_xfResponseType=json` | 400 JSON, "Security error occurred" for a guest |
| oEmbed | none | a thread page has no oEmbed discovery link |

What each source carries:

| Fact | Thread page | Listing | RSS | Sitemap |
|---|---|---|---|---|
| Exists for a guest | status 200 | a row | only while in the newest 20 | the URL is present |
| Thread id | URL, `data-content-key="thread-783"` | URL | `guid` | URL |
| Prefix | `<span class="label ...">` in the `h1` | label and `is-prefix9` class | no | no |
| Author | name and member URL `/members/maxi.153/` | name in `data-author` | name in `dc:creator` | no |
| Creation date | `datePublished` in JSON-LD | yes | no, `pubDate` is the last post | no, `lastmod` is the last post |
| Locked | not observed | not observed | no | no |

The thread page embeds a JSON-LD `DiscussionForumPosting` with `headline`, `datePublished`, `dateModified`, `articleSection` (the forum), the author's name and URL, the view, reply and like counts, and the first post as text.
It is the easiest part of the page to parse.
For thread 783, `datePublished` is 2026-02-20, while the RSS `pubDate` and the sitemap `lastmod` are both 2026-09-21T18:12:44, the time of the last post.

## Removed, locked, moved, and an outage

- **Never existed:** `/threads/999999/` answers 404 with the Ahwoo error page "The requested thread could not be found."
- **Removed:** three ids that the sitemap does not list (938, 1249 and 1273) answer the same 404.
- **Moved:** a thread keeps its id, and the old path answers 301 to the new one (tested with thread 783 under a wrong forum path).
- **Locked:** no locked thread showed in the forum listings read, so its answer is not verified.
- **Outage:** not observed.

A guest cannot tell a deleted thread from one that never existed, and does not learn why it is gone.
A thread that a moderator deleted but kept, or that is only hidden from guests, can answer differently, for example 403, which was not observed.
Every answer came through Cloudflare (`Server: cloudflare`, `CF-RAY`), so an outage or a bot check is expected as a 5xx, a 403, a 429 or a timeout, which is also not verified.

So a checker counts a thread as gone on a 404 whose body is the Ahwoo error page.
Any other answer that is not 200 or 301 is "unknown, try again on the next run", and when the same answer comes back on 3 runs in a row, the listing goes to a steward.

## CORS

No answer carried `Access-Control-Allow-Origin`, also not for requests that sent an `Origin` header (listing, RSS, sitemap, API, JSON view, 404).
A browser page, such as the index site, cannot read the forum.
A GitHub Actions job or Borea can.

## Rules for a reader

`https://forums.ahwoo.com/robots.txt` answers 404, and `https://ahwoo.com/robots.txt` is `User-agent: *` with an empty `Disallow:`.

The forum footer links the terms at `https://ahwoo.com/legal/terms-of-use`, and `/help/terms/` redirects there.
They were last updated on 24 October 2025 and cover "any other website that is made available by Ahwoo Limited to the public".
Clause 3.1 says a user will not "harvest or collect any Content either manually or via an automated software tool".
The feeds and the sitemap are published for machines, but the terms make no exception for them.
Our reading: a person who opens the one thread a listing links to uses the site as intended.
A scheduled reader of the sitemap and of thread pages is the "collect" case, and needs the Ahwoo team's agreement.

Guest thread and listing pages send `Cache-Control: max-age=14400, s-maxage=300`.
RSS and the sitemap send `private, no-cache` and no `ETag`, so a conditional request saves nothing.
None of the 33 requests answered 429.

## The Modpack tag

Forums v1.13.0 (2026-09-23) added the prefix "Modpack" with id 23 to the "Mod Categories" group of Mod Releases.
The other ids are Parts 4, Celestial 6, Audio 7, User Interface 8, Gameplay 9, Tools 10 and Visual 11, which match the table in [spec/tags.md](../spec/tags.md).
The update names it for "a curated pack of other people's mods" and adds pack rules to the Mod Release Rules: link to each mod's own download, list every mod with its name, version, author, licence, download link and thread, and include only mods that have their own Mod Releases thread.

No thread carried the prefix at the time of reading, and the listing with `?prefix_id=23` was empty.
The filter works on the feed too: `index.rss?prefix_id=9` returned only the 12 Gameplay threads, so `index.rss?prefix_id=23` is a feed of new packs.
A thread has one prefix, so a pack thread carries Modpack and no category prefix.
The prefix tells the content type `modpack`, and the tag prefill has nothing to map for a pack.

## What the three forum jobs can use today

The two jobs that run on a schedule assume the Ahwoo team agrees to a reader.
Until then a steward opens the linked thread by hand when a job needs it, and no tool fetches forum pages.

**Moderation tripwire ([RFC 0033](../rfcs/0033-content-index.md)).**
One sitemap read per run lists every thread id a guest can see.
A listing whose thread id is missing gets one read of its thread URL: 200 or 301 keeps it, the Ahwoo 404 flags it for a steward, and any other answer waits for the next run, up to 3 runs in a row.
That is one request per run, plus one per missing thread.
The banned author half is open: member pages are public (`/members/maxi.153/` answers 200), but no banned member was found, so what a guest sees for a ban is not verified.
A lock cannot be a trigger today, because it was not observed.

**Dispute tiebreaker ([RFC 0031](../rfcs/0031-content-metadata-format.md), RFC 0033).**
The thread page gives `datePublished`, the thread id and the author with the member id, which is enough to decide who was first.
A dispute is rare and a steward decides it, so this needs no automation.

**Tag prefill ([spec/tags.md](../spec/tags.md)).**
The `label` span in the `h1` of the thread page gives the prefix name, which maps through `forum_prefix` in `tags.toml`.
`og:title` is not a source, because it is the plain title when a thread has no prefix, and a title can contain ` - `.
That is one request when a person runs the listing tool.
9 of the 74 Mod Releases threads, one of them the rules thread, have no prefix and give no tag.

## What to ask the Ahwoo team

1. Agreement under clause 3.1 to one scheduled low-rate reader: the sitemap once a day, and one thread page when a listed thread is missing from the sitemap or a person runs the listing tool, with a user agent that names the KSAModding organization.
2. What a guest sees for a banned author, a locked thread and a thread that a moderator deleted, or that we should not read these.

Nothing else: no API key and no new endpoint.
