# Contributing

You do not need to write code to be useful here.

## Where to start

- **An idea, not yet a proposal:** open a thread in [Pre-RFC](https://github.com/KSAModding/content-manager-design/discussions/categories/pre-rfc).
- **A question about how something works:** [Q and A](https://github.com/KSAModding/content-manager-design/discussions/categories/q-and-a), or file a research task if the answer needs digging.
- **Something specific and small:** open an issue. The forms will route it.
- **A proposal:** write an RFC.

## Writing an RFC

Copy `rfcs/0000-template.md` to `rfcs/0000-short-title.md`, fill it in, and open a pull request.

**An RFC's number is the number of the pull request that introduces it.** Leave it at `0000` in the filename and the front matter until the pull request exists, then rename the file and set `rfc:` to match, in a second commit. Nobody has to check what is free, and two proposals opened at the same time cannot collide.

Note that GitHub gives issues, pull requests and discussions numbers from the same sequence, so RFC numbers are sparse. That is fine.

Every RFC starts with front matter:

```yaml
---
rfc: "0017"
title: Game version ordering and compatibility
status: Draft
authors: ["@your-handle"]
created: 2026-08-02
discussion: https://github.com/KSAModding/content-manager-design/pull/17
supersedes: []
superseded-by: []
---
```

Keep the quotes around the `rfc` number: unquoted, GitHub's front matter display reads the leading zero as octal and shows `0017` as 15.

`status` is one of `Draft`, `Proposed`, `FCP`, `Accepted`, `Rejected`, `Postponed`, `Superseded`.
Set it to `Draft` while you are writing and `Proposed` when you want review. The rest of the lifecycle is in [CHARTER.md](CHARTER.md).

An accepted RFC is never edited afterwards. It records what was decided and why, at that time. If the decision changes, write a new RFC and mark the old one superseded. The living documents are under `spec/`.

## Style

- **No hard line wrapping.** One line per sentence or list item. Long lines are fine. This keeps diffs readable and lets people paste text into Discord and the forum without broken line breaks.
- **Cite game behavior by class and method**, like `ModLibrary.PrepareManifest`, never by file and line number. Line numbers change with every KSA release; names mostly do not.
- **Say who is claiming what.** "Verified against the decompiled source" and "I think" are different sentences.

## Checks

Pull requests run `markdownlint` and an internal link check. To run them yourself:

```sh
npx markdownlint-cli2 "**/*.md"
npx lychee --offline "**/*.md"
```

RFC front matter is validated separately by `tools/check_rfc_metadata.py`.
A pull request that touches `rfcs/` also has to be approved by at least two stewards before its `rfc-approvals` check passes.
That check, `tools/check_rfc_approvals.py`, reads the steward list from the "Who decides" section of [CHARTER.md](CHARTER.md), so that section is the single place the list is maintained.
The same check keeps the merge blocked while an approved RFC still says `Proposed`: when review has converged, set the status to a terminal one and add the DECISIONS.md row before collecting the final approvals, since a later push dismisses the ones already given.

## Licensing your contribution

By opening a pull request you agree that your prose is contributed under CC BY 4.0 and any code or example files under MIT, as described in the [README](README.md).
