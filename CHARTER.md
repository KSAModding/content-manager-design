# Charter

## What we are designing

- A metadata format describing published content, a mod, mod pack, vehicle, or save, its releases, its dependencies, and what it is compatible with.
- An index: how that metadata is hosted, distributed, and kept current as the game moves.
- Install semantics: what a client may touch, what it owns, and what happens on upgrade and uninstall.
- The workflow by which a content author gets listed.

Something you can actually install content with should come out of this. The design of that client belongs here, its source lives in [Borea](https://github.com/KSAModding/Borea).

[RFC 0025](rfcs/0025-scope.md) settled how far the client reaches, published content generally with mods and mod packs first, and that StarMap stays an external dependency; the exact manager/loader boundary is still an open decision.

Anything not on that list is out of scope until an RFC puts it there.

## Constraints we did not choose

There are a handful of things about KSA that no design here can argue its way out of.
They are written up properly under `research/`, but briefly: mods live in the single user-global folder `C:\Users\YourUser\Documents\My Games\Kitten Space Agency` that every install shares, the game keeps the enabled state in its own `manifest.toml` and expects to own it, the version number is deliberately not sortable, and code mods need an out-of-process loader.

## Who decides

Stewards are the people who can merge RFCs. The current stewards:

- @Maximilian-Nesslauer
- @averageksp
- @MrJeranimo
- @PlazmaBoltz
- @KlaasWhite

Others join by being nominated in a discussion.

An RFC is accepted once two stewards have approved it and no objection is left unresolved. That does not make stewards the only voices that matter, they are just the ones who have to close the loop.

## How a decision gets made

1. **Pre-RFC.** Post the idea in the Pre-RFC discussion category.
2. **Draft.** Open a pull request adding a file under `rfcs/`, with the status set to `Draft` while you are still writing.
3. **Proposed.** Flip the status when you want people to review it properly.
4. **Final comment period.** Seven days, announced in Announcements, as a last call for objections.
5. **Accepted or rejected.** Either it merges with status `Accepted` and a row in `DECISIONS.md`, or it closes as `Rejected` with the file kept, so the reasoning survives for whoever proposes the same thing another time.

## Milestones

| | |
|---|---|
| M0 Charter | Scope, stewards, and the process itself. |
| M1 Core model | The decisions that determine whether this is buildable at all: metadata, versioning, install, loader. |
| M2 Spec v0.1 | Those decisions written up well enough that someone else could implement them. |

## Changing this charter

By RFC, like everything else.
