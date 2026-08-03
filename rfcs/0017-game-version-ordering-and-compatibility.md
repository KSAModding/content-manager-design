---
rfc: 0017
title: Game version ordering and compatibility
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-08-02
discussion: https://github.com/KSAModding/mod-manager-design/pull/17
supersedes: []
superseded-by: []
---

# RFC 0017: Game version ordering and compatibility

## Summary

Order KSA releases by their revision(, the fourth component), and by nothing else.

Express a mod's compatibility as a lower bound and an optional upper bound over that revision, where an absent upper bound means "no known upper limit". Below the lower bound is incompatible. Above a stated upper bound is untested, which warns but does not block.

Detect the installed version from `KSA.dll`'s PE FileVersion, and build the ordered list of releases from `Content/Versions/`, which is already on every user's disk.

## Motivation

A manager cannot answer either of its two basic questions without this. "Is this mod compatible with what I have installed" needs a comparison, and "is there a newer release" needs an ordering.

KSA gives neither for free. See this research in [research/ksa-versioning.md](../research/ksa-versioning.md). The four findings this RFC rests on:

1. **The build counter does not order.** The game's own build tooling replaces it with a literal `X` when naming the changelog file for a release.
2. **The revision does order.** It is strictly ascending and unique across the entire shipped history, and sorting by it alone reproduces the true release order for all 155 releases. Sorting the full four-part string instead puts 21 adjacent pairs in the wrong order.
3. **The game does this too.** `VersionInfo.CompareTo` compares revision first, then the build counter only as a tiebreak, then the suffix. Year and month are display only.
4. **The release cadence is roughly thirteen a month.** Any compatibility rule that has to be re-stated per release is stale within days and too much to maintain for modders. We should be able to specify an compatibility range + "the mod is untested with this version" non-blocking warning.

## Guide-level explanation

### For someone publishing a mod

You state the oldest game version you know your mod works with, and optionally the newest you have tested. You write them the way the game shows them to you, `2026.8.3.5117`, and the tooling takes it from there.

If you leave the upper end open, your mod stays installable as the game moves on. That is the recommended default. You are not promising it works forever but you are saying you have not found a version where it breaks. If it does break, you publish a fix release that says so.

If you do set an upper bound, users on a newer game get a warning and can install anyway.

### For someone using a manager

A mod shows one of four states:

| State | When | What happens |
|---|---|---|
| Compatible | Your game is within the stated range. | Installs normally. |
| Untested | Your game is newer than the mod's stated upper bound. | Installs after a confirmation. |
| Incompatible | Your game is older than the mod's lower bound. | Blocked, with the version it needs. |
| Unknown | The mod states no usable compatibility at all. | Listed, marked unknown, installable after confirmation. |

## Reference-level explanation

### The ordering rule

For two KSA versions, compare the revision as an integer. Higher is newer. Do not compare year, month, or the build counter for ordering.

Two consequences to state explicitly:

- **A version is not a totally ordered value.** Two builds can share a revision and differ: the developers have stated that they ship specialist builds for hardware vendors, agencies and universities, and the same revision compiled as development, release or production behaves differently.
- **This RFC scopes compatibility to the public production stream.** Within that stream the revision is unique and total, which is what the history of the past 155-releases shows. A build carrying a suffix such as `-LOCAL` is ordered by its revision and otherwise treated as out of scope: a manager may install onto it, and should say that compatibility data was not written with it in mind.

### Parsing

Accept the shape the game itself accepts:

```text
^v?(?<Year>\d+)\.(?<Month>\d+)\.(?<Build>\d+)\.(?<Revision>\d+)(?:-(?<Suffix>[^+]+))?(?:\+.*)?$
```

A leading `v`, a `-suffix`, and a `+hash` are all valid input. Anything that does not parse yields no version, and whatever carried it becomes Unknown rather than being discarded.

Note that the game's own property names do not line up with what the components mean: `Major` holds the year, `Minor` the month, `Build` the build counter, `Revision` the revision. Mapping this onto a `Major.Minor.Patch.Build` shaped type lines the parts up misleadingly and is worth avoiding.

### What a mod release declares

Two values, both denoting a revision:

- a **lower bound**, required,
- an **upper bound**, optional, absent meaning open.

**Authors should be able to write a full version string, tooling stores a revision.** An author might write `2026.8.3.5117` because that is what the game displays. A month, `2026.8`, is also accepted and means "the whole of that month". Both are resolved to a revision when the metadata is stamped, so published metadata is always self-contained and can be evaluated without consulting an index:

```toml
# what an author writes
game_min = "2026.7"

# what gets published
game_min_revision = 4892
```

If published metadata carried month strings, every compatibility check would need the release index to resolve them, and a manager could not answer "is this compatible" offline or for a release the index has not caught up with yet.

**Month granularity resolves to the first and last revision within that calendar month**, as lower and upper bound respectively. `Year.Month.Build` as a prefix is deliberately not offered.

### Evaluating compatibility

Given an installed revision `r`, a lower bound `min`, and an optional upper bound `max`:

| Condition | State |
|---|---|
| no usable `min` | Unknown |
| `r < min` | Incompatible |
| `max` absent, or `r <= max` | Compatible |
| `r > max` | Untested |

Incompatible is the only state that blocks. Untested and Unknown warn and require a confirmation, and a manager must let the user proceed. The justification is finding 4 plus the fact that the game validates nothing: a false "incompatible" is a mod the user cannot install for no reason, while a false "compatible" is a mod that does not load and can be removed again.

### Detecting the installed version

In order:

1. **`KSA.dll` PE FileVersion.** Exact four-part string, readable without loading the assembly, no suffix to strip.
2. `KSA.dll` PE ProductVersion, which is the same value with `+hash` appended.
3. The `build` field of the newest `Content/Versions/*.json`.

### The release index

`Content/Versions/` is not just changelog text. Each file is a record carrying `build`, `date`, `fromRevision` and `toRevision`, and the game reads all of them recursively and sorts by `toRevision` descending. The `fromRevision`/`toRevision` pairs chain from one release to the next, with 5 breaks across the 155 shipped files.

So **every installed copy of the game already contains a dated, ordered index of every release up to its own**, keyed by revision. A manager should build its ordering from that, since it requires no network and no service.

Two things it cannot do:

- It knows nothing about releases newer than the installed game. For "is there an update", the master server broadcast at `http://ksa-master1.rocketwerkz.com:8082/version` is the authority, and it reports exactly one version, the current public production build.
- A user who has never installed a given release has no record of it. If a manager needs to resolve a month to a revision for a period the user's install does not cover, it needs an external list. One already exists and updates itself hourly from the master server at no running cost: `builds.json` in [KSAModding/KSA-CKAN-meta](https://github.com/KSAModding/KSA-CKAN-meta).

### Display

Show the version as the game shows it, `2026.8.3.5117`, including the build counter. It is meaningless for ordering but it is what the user sees in the game, in the launcher and in a bug report, and rendering something else invites confusion.

Where a range is shown, render it in terms of those full version strings, not raw revisions.

## Drawbacks

- **Ordering by one component of four looks wrong until it is explained.** Anyone reading the metadata without the research behind it will assume a bug. This needs to be documented for mod authors.
- **An open upper bound is a false promise** A mod will eventually break silently on a newer game, and the manager will have called it "maybe compatible". The alternative, an upper bound that has to be re-stated thirteen times a month, is worse since it would be too much work for modders to update their mods with each release.
- **Nothing here helps with specialist builds.** A user on a vendor or development build gets compatibility answers computed as if they were on the production stream. This RFC names the limit and does not solve it.

## Alternatives

**Compatibility as equality: a mod declares the one build it was compiled against.** This is the conservative reading of "the version is not sortable", it needs no ordering rule at all, and it is what [Borea](https://github.com/MrJeranimo/Borea) currently implements as of 2026.08.02 . It fails on cadence: at roughly thirteen releases a month, every mod in the catalogue is marked broken within days of a game update, almost always wrongly.

**Normalize the build counter to zero and keep four-part comparison.** This is what the CKAN fork does, because CKAN's `GameVersion` type is game-agnostic and four-part comparison was the only hook available. It produces the same ordering as this RFC, since the third component becomes constant and comparison falls through to the revision. We do not have CKAN's constraint, so we can order by the revision directly and skip a normalization step that has to be applied at every ingestion point to be correct. The cosmetic cost CKAN pays, displaying `2026.8.0.5117` for a build that calls itself `2026.8.3.5117`, is also avoided.

**Treat versions as fully opaque and let the user decide.** No compatibility model at all: show what the author wrote as free text. Honest, and it matches how little the game itself cares. It also makes dependency resolution impossible, since a resolver cannot pick a version set without comparing versions, and it moves the entire burden onto users who have no way to evaluate it.

## Prior art

**CKAN, as extended for KSA.** Reached the same ordering conclusion from the same evidence, implemented as normalize-then-compare for the reason given above, with compatibility expressed as month or `year.month.0.revision` ranges. As of time of publication, it has been running against a real index of KSA mods for ~4 Weeks without issues, which is the strongest available evidence that the range model is workable in practice rather than only in principle.

**Semantic versioning**, which is what most package ecosystems assume and which does not apply here. KSA's version carries no compatibility promise of any kind. The KSA lead has been explicit that semantic versioning is not what this scheme is for.

**Thunderstore and Modrinth** both attach a game-version list to each release rather than a range, which works because their games version rarely and predictably. At thirteen releases a month an explicit list is unmaintainable.

## Unresolved questions

- **Where the authored bounds are written**, and under what field names. That belongs to the metadata format RFC.
- **Whether a manager consumes an external release list at all**, or restricts itself to what the installed game knows.
- **What happens when a mod is installed onto an Incompatible game deliberately.** This RFC blocks it; whether an override exists for people who know what they are doing is a UI decision.
- **How the upper bound gets maintained in practice.** The model makes leaving it open cheap, but a mod that genuinely breaks needs its previous release amended, and who does that and how is a publishing question.

## Future possibilities

If the developers ever expose a per-release compatibility signal of their own, the bound would become derived rather than authored. Nothing here forecloses that.

If specialist builds become common enough to matter, the suffix is available and the game already orders by it as a final tiebreak.
