# Contributing

You do not need to write code to be useful here.

## Where to start

- **An idea, not yet a proposal:** open a thread in [Pre-RFC](https://github.com/KSAModding/mod-manager-design/discussions/categories/pre-rfc).
- **A question about how something works:** [Q and A](https://github.com/KSAModding/mod-manager-design/discussions/categories/q-and-a), or file a research task if the answer needs digging.
- **Something specific and small:** open an issue. The forms will route it.
- **A proposal:** write an RFC.

## Writing an RFC

Copy `rfcs/0000-template.md` to `rfcs/NNNN-short-title.md`, take the next free number, and open a pull request. Numbers are allocated when the pull request opens; if two land at once, whoever merges second renames.

Every RFC starts with front matter:

```yaml
---
rfc: 0002
title: Mod metadata format
status: Draft
authors: ["@your-handle"]
created: 2026-08-01
discussion: https://github.com/KSAModding/mod-manager-design/discussions/12
supersedes: []
superseded-by: []
---
```

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

## Licensing your contribution

By opening a pull request you agree that your prose is contributed under CC BY 4.0 and any code or example files under MIT, as described in the [README](README.md).
