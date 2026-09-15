---
rfc: "0000"
title: Content ratings
status: Draft
authors: ["@LaurensDeV"]
created: 2026-09-15
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: Content ratings

## Summary

A thumbs up / thumbs down signal per published item, so that a user can see whether other people found something worth installing and so that index maintainers have a cheap signal for finding low-quality or broken listings.

Votes are collected by a small write endpoint, aggregated on a schedule, and published as a static `ratings.json` alongside the index.
Clients only ever read that static file.
Raw per-vote data stays private to whoever operates the endpoint; only a coarse aggregate is public.

The rating signal is defined as non-load-bearing: when it is unavailable, clients hide it and every other function of the manager continues unchanged.

This RFC asks for a narrow amendment to one non-goal in [RFC 0025](0025-scope.md).
That is the real decision here, and it is stated plainly in "Relationship to RFC 0025" below.

## Motivation

The index will list content of varying quality, including abandoned listings, listings broken by a game update, and the occasional deliberate junk entry.
Nothing in the design so far gives a user any way to tell these apart before installing, and nothing gives index maintainers a way to notice them at all short of someone complaining in Discord.

The alternative signal we already get for free, download counts from release hosts, measures attention rather than quality.
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

For a client implementer: reading ratings is fetching one more static JSON file from the same place the index comes from.
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

Whether this is a narrowing amendment recorded in `DECISIONS.md` or requires marking RFC 0025 superseded is a process question for the stewards.
Superseding the whole of 0025 over one line seems disproportionate, but this RFC does not get to decide that.

If the stewards prefer to keep the non-goal absolute, the honest consequence is that this RFC should be rejected and the ratings idea dropped rather than implemented in a degraded form.
See Rationale and alternatives for why the account-based designs that would satisfy the strict reading do not produce usable data.

### Layers

The design has three layers and they have deliberately different durability.

| Layer | What it is | If it disappears |
| --- | --- | --- |
| Read | `ratings.json`, static, published next to the index | clients use the cached copy, then show nothing |
| Aggregate | a scheduled job reading raw votes and writing the static file | `ratings.json` freezes at its last value |
| Write | an HTTP endpoint accepting votes | clients hide the voting control |

Only the write layer requires anything to be running at a given moment.
The read layer is subject to whatever the index RFC decides for hosting, and should not be given its own separate answer.

### Published format

`ratings.json` is a map from content identity to an aggregate.

```json
{
  "schema": 1,
  "generated": "2026-09-15T02:00:00Z",
  "ratings": {
    "com.example.coolengines": { "score": 0.87, "votes": "100-500" },
    "com.example.otherthing": { "score": null, "votes": "<10" }
  }
}
```

`score` is the fraction of positive votes, rounded to two decimals, or `null` when the vote count is below the display threshold.
`votes` is a bucket label rather than an exact number, so that the raw split cannot be reconstructed by differencing two daily snapshots.

The content identity key is whatever the format RFC settles on.
This RFC does not introduce an identity of its own and should not be accepted before that question is answered.

### Write contract

One POST endpoint, `POST /v1/vote`:

```json
{ "id": "com.example.coolengines", "version": "1.4.2", "vote": 1, "voter": "<opaque token>" }
```

`vote` is `1`, `-1`, or `0` to withdraw.
`version` is the release the voter had installed at the time, recorded verbatim as the string the metadata carries, and is used as described under "Versions" below.
The endpoint returns 204 on success and 4xx on rejection, with no body in either case.
A client treats any failure, including a timeout, as "voting is unavailable right now" and hides the control.

The endpoint is the only component holding a credential.
No credential of any kind ships in a client, which is a hard requirement given that clients are open source and distributed as binaries.

### Versions

A rating is per content, not per release, but every vote records which release it was cast against.

Splitting the public display per release does not work: a ratio needs a few dozen votes to mean anything, and dividing a listing's votes across its release history leaves nearly every release below the display threshold.
The cold-start also runs the wrong way, since a newly published release has no votes, so the version a user should install shows nothing while an older, worse one still shows an accumulated score.

Recording the version on each vote gets the useful part without that cost:

- The published score MAY weight votes cast against recent releases more heavily, so that a fix moves the score in weeks rather than never.
- The private maintainer view can show the score broken down by release, which is what turns "this listing is disliked" into "this listing broke at 1.4.2".

The version string is stored verbatim and is not parsed by the write endpoint.
How two versions are compared, and therefore what "recent" means for weighting, depends on the versioning decision that is still open, and is deliberately not specified here.
Until that is settled, an implementation MAY treat the release published most recently in the index as the current one and weight only on that, which needs no ordering.

`ratings.json` carries no per-version breakdown.
Publishing one would let the private split be reconstructed, and would reintroduce the sparsity problem in the client.

### Voter identity

A random opaque token is generated on first launch and persisted by the client.
It is not an account, it is not tied to anything, and a user who clears it can vote again.

This is friction, not authentication, and the RFC states that plainly rather than implying a guarantee it cannot make.
The mitigations are per-identity deduplication, a rate limit per source address, and ignoring votes from tokens first seen less than 48 hours ago.

For this to be a privacy-respecting design rather than a tracking one, the token must not be sent anywhere except the vote endpoint, and the aggregate job must not retain source addresses beyond the rate-limiting window.

### Reference implementation

A Cloudflare Worker with a KV namespace, keyed `v:{id}:{voter}`, so a repeat vote overwrites rather than accumulating and there are no counters to corrupt.
A scheduled trigger reads the prefix, aggregates, and publishes the static file.
The free tier covers 100k requests per day, which is not a number this ecosystem will approach.

This is a reference implementation, not part of the specification.
Any endpoint satisfying the write contract above is conforming, and the specification stays implementation-neutral as RFC 0025 requires.

### Client requirements

- A client MAY implement reading, MAY implement writing, and MAY implement neither.
- A client that reads MUST cache the last successfully fetched file and MUST tolerate its absence.
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
Free, requires no new infrastructure at all, and should probably be done regardless of this RFC.
It measures attention, not quality, and is therefore complementary rather than an alternative.

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

- It is a service, and RFC 0025 said no services. Narrowing that line costs something even if the narrowing is correct, because the absolute version is easy to hold and the narrowed version requires judgement every time.
- The voter identity is weak and trivially resettable. A determined person can move a score. The design limits the damage rather than preventing it.
- Without comments, a negative score tells a content author that people dislike something but not what is wrong. This is a real cost of the no-moderation position.
- A low score on a listing broken by a game update still decays rather than resetting after a fix. Recency weighting shortens that window but does not close it, and the weighting itself is an unspecified knob that will need tuning against real data nobody has yet.
- Recording a version with each vote makes the private data more identifying than a bare tally, since a vote now carries content, release, approximate time, and a persistent token. The retention limits under Voter identity are the mitigation.
- Ratings are a mild popularity-entrenchment mechanism: things with scores get installed, things without stay without.
- This is not an M1 concern. It competes for steward attention with the metadata format, versioning, install semantics, and the loader boundary, all of which determine whether the project is buildable at all.

## Unresolved questions

- Whether the stewards accept the narrowing amendment to the RFC 0025 non-goal, and whether that requires a supersedes entry or a `DECISIONS.md` row.
- Display threshold: how many votes before a score is shown rather than `null`.
- Bucket boundaries for `votes`, and whether the bucketing is enough to keep the raw split private across repeated snapshots.
- Whether `ratings.json` is published to the same location as the index or a sibling one. This depends on the index RFC and should not be answered here.
- Who operates the endpoint, and on whose organisation account.
- Whether the private maintainer view is a second endpoint behind access control or a manual data dump.
- The recency weighting function, which cannot be specified before versions can be ordered, and which the format and versioning RFCs own.
- Whether a vote should be invalidated outright when the voter later installs a newer release, rather than only down-weighted.
- Whether this should be postponed until after M1 regardless of whether the design is agreed.

## Future possibilities

- Download-count collection as a separate, unconditionally free signal.
- Per-game-version ratings, as distinct from the per-mod-release tagging this RFC specifies, once game version ordering is settled. This would answer "does this work on the build I am running", which is a different question from "is this good".
- Aggregate installed-together data for recommendations, which would need its own privacy analysis and is not implied by this RFC.
- A maintainer dashboard over the private data, if the endpoint exists and there is appetite for it.
