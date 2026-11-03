---
rfc: "0066"
title: Content ratings
status: Draft
authors: ["@LaurensDeV"]
created: 2026-09-15
discussion: https://github.com/KSAModding/content-manager-design/pull/66
supersedes: []
superseded-by: []
---

# RFC 0066: Content ratings

## Summary

A thumbs up / thumbs down signal per published item, so that a user can see whether other people found something worth installing and so that index maintainers have a cheap signal for finding low-quality or broken listings.

Votes are collected by a small write endpoint and aggregated on a schedule.
The indexer copies the aggregate into a static `ratings.json` in the generated index repository, and the snapshot attaches it to each entry, the way [RFC 0052](0052-static-download-counts.md) attaches download counts.
Clients only ever read the snapshot.
Raw per-vote data stays private to whoever operates the endpoint; only a coarse aggregate is public.

The rating signal is defined as non-load-bearing: when it is unavailable, clients hide it and every other function of the manager continues unchanged.

This RFC asks for a narrow amendment to one non-goal in [RFC 0025](0025-scope.md).
That is the real decision here, and it is stated plainly in "Relationship to RFC 0025" below.

## Motivation

The index will list content of varying quality, including abandoned listings, listings broken by a game update, and the occasional deliberate junk entry.
Nothing in the design so far gives a user any way to tell these apart before installing, and nothing gives index maintainers a way to notice them at all short of someone complaining in Discord.

The one signal the index already has, the download counts of RFC 0052, measures attention rather than quality.
A mod can be downloaded heavily and be broken; that is in fact the normal pattern immediately after a game update.

This was raised in Discord, where the immediate and correct objection was that we have no infrastructure to collect live data and do not want a "sponsor stops paying, the manager stops working" scenario to be possible.
This RFC exists because that objection rules out most designs but not all of them, and the distinction is worth writing down.

## Guide-level explanation

For a user: each listing shows a rating, or shows nothing if too few people have voted.
Voting is one click inside the client, with no account and no browser redirect.
A vote can be changed or withdrawn later.

For an index maintainer: a private view shows the up/down split, the trend over time, and which listings have recently moved sharply.
That is a prompt to go look at something, never an automated delisting.

For a content author: ratings are attached to the content identity rather than to a release, so publishing a fix does not erase the history, though votes cast against newer releases can count for more, so a fix does move the score.
There are no comments and no free text anywhere in this design, which is deliberate and is discussed under Drawbacks.

For a client implementer: reading ratings is reading one more optional field in the snapshot the client already fetches.
Submitting votes is one HTTP POST, and a client that never implements it is still a conforming client.

## Reference-level explanation

### Relationship to RFC 0025

RFC 0025 lists as a non-goal: anything that needs a service somebody has to keep running and paying for.

A write endpoint is such a service, so this RFC cannot be accepted without amending that line.
The amendment proposed is to narrow it rather than remove it:

> Non-goal: anything whose failure degrades installing, updating, or resolving dependencies.

The reasoning is that the original non-goal is a proxy for a failure mode, not a value in itself.
What we actually care about is that the manager keeps working forever without anyone paying a bill.
A component that is defined as fail-open, that holds no data any other part of the system reads, and whose disappearance changes nothing except that a badge stops rendering, does not produce that failure mode.

The non-goal has already been applied to exactly this kind of signal:

- [RFC 0033](0033-content-index.md) keeps per-user state such as favorites out of the index, "since it needs a server".
- RFC 0052 rejects a live statistics service, because RFC 0025 rules out operated infrastructure.
- The [snapshot specification](../spec/snapshot.md) names votes among the per-user state it does not carry, for the same reason.

RFC 0052 could reject a service because the hosts already count downloads, so a static copy of their numbers was enough.
Nothing counts votes for us, so the choice here is between a service and no signal at all.
The narrowed line would also stop ruling out a favorites server on its own, so a proposal like that would be judged on its merits instead of refused by rule.

Whether this is a narrowing amendment recorded in `DECISIONS.md` or requires marking RFC 0025 superseded is a process question for the stewards.
There is precedent for the lighter form: [RFC 0048](0048-ownership-of-an-edit.md) replaced RFC 0033's handover rule with a `DECISIONS.md` row, and RFC 0033 is not marked superseded.
This RFC follows that precedent and leaves `supersedes` empty, but a non-goal in the scope RFC may deserve heavier treatment than a rule in the index RFC, and this RFC does not get to decide that.

If the stewards prefer to keep the non-goal absolute, the honest consequence is that this RFC should be rejected and the ratings idea dropped rather than implemented in a degraded form.
See Rationale and alternatives for why the account-based designs that would satisfy the strict reading do not produce usable data.

### Layers

The design has three layers and they have deliberately different durability.

| Layer | What it is | If it disappears |
| --- | --- | --- |
| Read | the optional `rating` field in the snapshot, built from `ratings.json` in the generated index repository | clients show no rating |
| Aggregate | a scheduled job at the endpoint that turns raw votes into the public aggregate, and the indexer run that copies it into `ratings.json` | `ratings.json` keeps its last value |
| Write | an HTTP endpoint accepting votes | clients hide the voting control |

Everything on the endpoint's side, the write layer and the aggregation, is the service this RFC asks for.
The indexer's side runs on the schedule the generated repository already has, and the read layer is the snapshot RFC 0033 already serves, with no hosting of its own.

### Published format

The endpoint serves the public aggregate at `GET /v1/ratings`, with ids lowercased, because the endpoint does not know their authored casing.

```json
{
  "spec_version": 1,
  "ratings": [
    { "id": "advancedflightcomputer", "score": 0.87, "votes": "100-500" },
    { "id": "stageinfo", "score": null, "votes": "<10" }
  ]
}
```

`score` is the fraction of positive votes, rounded to two decimals, or `null` when the vote count is below the display threshold.
`votes` is a bucket label rather than an exact number, so that the raw split cannot be reconstructed by differencing two published values.
Because `ratings.json` lives in a git repository, every value it has ever had stays in its history, so the bucketing has to hold against that whole history, not only against yesterday's file.

The indexer fetches the aggregate on its schedule and writes it to the generated repository as `ratings.json`, CC0 metadata in the same shape, with two changes:

- Each id takes the casing the index lists it under, and `ratings` is ordered by lowercased id, as RFC 0052 orders `download-counts.json`.
- An entry whose id the index does not list is dropped, because the endpoint accepts ids from anyone and a junk id must not fail the run.

The indexer commits only when the bytes change, and the format promises no refresh interval.
The file carries no timestamp, for the reason RFC 0052 gives: a timestamp that moves without a rating moving would invalidate snapshot caches for nothing.

A failed fetch, or a response that is not valid, leaves the last `ratings.json` in place and never fails or delays the rest of the indexer run.
If the endpoint is retired for good, the stewards delete `ratings.json`, and ratings disappear from clients with the next snapshot.

The key is the content id of [RFC 0031](0031-content-metadata-format.md), and this RFC introduces no identity of its own.
Ids compare case-insensitively, so the endpoint lowercases an id before storing a vote, and two casings of one id collect votes for one item.

### Snapshot

The snapshot builder attaches the matching entry to each listing and pack that is not a tombstone, as an optional `rating` field without the repeated `id`:

```json
"rating": { "score": 0.87, "votes": "100-500" }
```

A client shows nothing for an absent `rating` and nothing for a `null` score.
The builder ignores an entry whose id matches no listing or pack, since the indexer drops it on its next run.

The optional field does not change `snapshot_version`, and no authored or release document changes, so their `spec_version` stays at `1`.
The living snapshot specification gains the field once this RFC is accepted, and its line about votes under "What the snapshot does not carry" changes with it.

### Write contract

One POST endpoint, `POST /v1/vote`:

```json
{ "id": "AdvancedFlightComputer", "version": "0.7.2", "vote": 1, "voter": "<opaque token>" }
```

`vote` is `1`, `-1`, or `0` to withdraw.
`version` is the release the voter had installed at the time, recorded verbatim as the `version` of that release, which RFC 0031 normalizes to SemVer 2.0.0, and is used as described under "Versions" below.
The endpoint returns 204 on success and 4xx on rejection, with no body in either case.
A client treats any failure, including a timeout, as "voting is unavailable right now" and hides the control.

`GET /v1/ratings` serves the aggregate described under "Published format" and needs no credential, because it returns nothing that is not published anyway.

The endpoint is the only component holding a credential for ratings, and the indexer reads the aggregate without one.
No credential of any kind ships in a client, which is a hard requirement given that clients are open source and distributed as binaries.

### Versions

A rating is per content, not per release, but every vote records which release it was cast against.

Splitting the public display per release does not work: a ratio needs a few dozen votes to mean anything, and dividing a listing's votes across its release history leaves nearly every release below the display threshold.
The cold-start also runs the wrong way, since a newly published release has no votes, so the version a user should install shows nothing while an older, worse one still shows an accumulated score.

Recording the version on each vote gets the useful part without that cost:

- The published score MAY weight votes cast against recent releases more heavily, so that a fix moves the score in weeks rather than never.
- The private maintainer view can show the score broken down by release, which is what turns "this listing is disliked" into "this listing broke at 1.4.2".

The version string is stored verbatim and is not parsed by the write endpoint.
The aggregation orders versions by SemVer precedence, which RFC 0031 defines for every release version, so "recent" has a meaning without any new rule.
The weighting function itself is left open; see Unresolved questions.

`ratings.json` carries no per-version breakdown.
Publishing one would let the private split be reconstructed, and would reintroduce the sparsity problem in the client.

### Voter identity

A random opaque token is generated on first launch and persisted by the client.
It is not an account, it is not tied to anything, and a user who clears it can vote again.

This is friction, not authentication, and the RFC states that plainly rather than implying a guarantee it cannot make.
The mitigations are per-identity deduplication, a rate limit per source address, and ignoring votes from tokens first seen less than 48 hours ago.

For this to be a privacy-respecting design rather than a tracking one, the token must not be sent anywhere except the vote endpoint, and the aggregate job must not retain source addresses beyond the rate-limiting window.

### Reference implementation

A Cloudflare Worker with a D1 database holding one row per content id and voter, with `(id, voter)` as the primary key, so a repeat vote overwrites rather than accumulating and there are no counters to corrupt.
A Cron Trigger aggregates the table with one query and stores the result that `GET /v1/ratings` serves.

On the Workers Free plan, a Worker gets 100,000 requests per day, and D1 gets 100,000 rows written and 5 million rows read per day.
D1 counts a write to an indexed column as a second written row, so the write limit still allows at least 50,000 votes a day, and a daily aggregation over every stored vote stays within the read limit up to about 5 million votes.
When a daily limit is reached, D1 returns errors, the endpoint fails, and clients hide the voting control until the next day, which is the fail-open path this RFC already requires.

Workers KV looks like the obvious fit and is not: its free plan allows 1,000 writes per day to different keys, and every new vote is a new key.

These are Cloudflare's published limits, checked on 2026-09-15, and Cloudflare can change them.

This is a reference implementation, not part of the specification.
Any endpoint satisfying the write contract above is conforming, and the specification stays implementation-neutral as RFC 0025 requires.

### Client requirements

- A client MAY implement reading, MAY implement writing, and MAY implement neither.
- A client that reads MUST treat an absent `rating` field as no rating and show nothing.
- A client that reads MUST NOT use the rating in dependency resolution, install ordering, or any automated decision.
- A client that writes MUST NOT send the voter token to any endpoint other than the vote endpoint.
- A client MUST NOT block, delay, or fail any other operation on the availability of either layer.

[Borea](https://github.com/KSAModding/Borea) is expected to implement this behind an interface in `Borea.Core` with a null implementation as the registered default, so that the fail-open path is the one that exists by default rather than one that has to be remembered.
That is an implementation note, not a requirement of this specification.

### Operational requirements

If this is accepted, the account operating the write endpoint must be owned by the organisation and must have at least two people holding credentials.

A rating endpoint on one person's personal account reproduces the exact bus-factor problem that the RFC 0025 non-goal exists to prevent, at which point the objection stands and this design does not answer it.
This requirement is part of the proposal, not a deployment detail to settle afterwards.

### Ratings non-goals

- Comments, reviews, or any free-text field. Those need moderation, which needs moderators, which is a commitment this project has not made.
- Automated delisting or ranking penalties based on score.
- A per-release score shown to users, as opposed to a per-content one. Votes carry a version, but the published file does not break down by it.
- Any use of the rating in dependency resolution.

## Rationale and alternatives

**GitHub Discussions reactions.**
One discussion per listing, tallied by an Action, published as a static file.
This satisfies the RFC 0025 non-goal as literally written: no endpoint, no credential outside Actions, no bill, and real accounts giving genuinely strong sybil resistance including the ability to discard votes from accounts created last week.
It was the original proposal and it fails on reach.
Voting requires a GitHub account, being logged in, leaving the application, and finding the right reaction on a markdown page.
Casual players do not have GitHub accounts, so the sample is restricted to modders and developers, which is the population already reachable in Discord.
A quality signal that only surveys people who could have told us directly is not worth the machinery, and worse, it looks like broad data while not being broad data.

**Download counts from release hosts.**
Accepted as RFC 0052, and free because the hosts already count.
It measures attention, not quality, and is therefore complementary rather than an alternative.

**A separate `ratings.json` that clients fetch next to the snapshot.**
Simpler to describe, and rejected because RFC 0033 gives a client one snapshot to fetch, and RFC 0052 already set the pattern for a signal that changes outside the release records.

**Voting through pull requests or issues against a repository.**
Same account problem as Discussions, plus it puts unreviewed user input into a repository that clients read from.

**Doing nothing.**
Defensible, and the strongest form of the argument is that a mod ecosystem this small self-polices through Discord.
The counter is that this stops being true at the scale the index is being designed for, and by then the client format is fixed.

**A full backend with accounts.**
Solves identity properly and is rejected on cost, maintenance burden, and the fact that it genuinely does recreate the failure mode RFC 0025 is protecting against.

## Prior art

CKAN has no rating mechanism; quality signals come from the metadata review process instead, which is a real alternative strategy and one this project has partly adopted already through the authored/generated split noted in `research/prior-art-ckan.md`.

Thunderstore and Nexus both attach ratings to content rather than releases, which is the choice this RFC follows.
Both also carry comments, and both demonstrate the moderation burden that comes with them, which is why comments are a non-goal here.

## Drawbacks

- It is a service, and RFC 0025 said no services. Narrowing that line costs something even if the narrowing is correct, because the absolute version is easy to hold and the narrowed version requires judgement every time, including for services such as a favorites server that the old line refused outright.
- The voter identity is weak and trivially resettable. A determined person can move a score. The design limits the damage rather than preventing it.
- Without comments, a negative score tells a content author that people dislike something but not what is wrong. This is a real cost of the no-moderation position.
- A low score on a listing broken by a game update still decays rather than resetting after a fix. Recency weighting shortens that window but does not close it, and the weighting itself is an unspecified knob that will need tuning against real data nobody has yet.
- Recording a version with each vote makes the private data more identifying than a bare tally, since a vote now carries content, release, approximate time, and a persistent token. The retention limits under Voter identity are the mitigation.
- A retained `ratings.json` does not show its age, so ratings frozen by an unreachable endpoint look current until the stewards remove the file.
- Ratings are a mild popularity-entrenchment mechanism: things with scores get installed, things without stay without.
- This is not an M1 concern. It competes for steward attention with the metadata format, versioning, install semantics, and the loader boundary, all of which determine whether the project is buildable at all.

## Unresolved questions

- Whether the stewards accept the narrowing amendment to the RFC 0025 non-goal, and whether a `DECISIONS.md` row is enough, as it was for RFC 0048, or RFC 0025 should be marked superseded.
- Display threshold: how many votes before a score is shown rather than `null`.
- Bucket boundaries for `votes`, and whether the bucketing is enough to keep the raw split private across the whole git history of `ratings.json`.
- Who operates the endpoint, and on whose organisation account.
- Whether the private maintainer view is a second endpoint behind access control or a manual data dump.
- The recency weighting function. RFC 0031 orders versions, so it can be specified, but there are no votes yet to tune it against.
- Whether a vote should be invalidated outright when the voter later installs a newer release, rather than only down-weighted.
- Whether this should be postponed until after M1 regardless of whether the design is agreed.

## Future possibilities

- Per-game-version ratings, as distinct from the per-mod-release tagging this RFC specifies, using the revision ordering of [RFC 0017](0017-game-version-ordering-and-compatibility.md). This would answer "does this work on the build I am running", which is a different question from "is this good", and a vote would have to carry the game revision the voter was running.
- Aggregate installed-together data for recommendations, which would need its own privacy analysis and is not implied by this RFC.
- A maintainer dashboard over the private data, if the endpoint exists and there is appetite for it.
