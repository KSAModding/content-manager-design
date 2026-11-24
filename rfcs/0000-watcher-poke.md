---
rfc: "0000"
title: A poke for the watcher when its schedule stalls
status: Draft
authors: ["@LaurensDeV"]
created: 2026-11-24
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: A poke for the watcher when its schedule stalls

Amends [The watcher](0033-content-index.md#the-watcher) of [RFC 0033](0033-content-index.md) and the non-goals of [RFC 0025](0025-scope.md).
`spec_version` and `snapshot_version` stay at `1`.

## Summary

The GitHub schedule stays the watcher's clock.
A free Cloudflare Worker that the org owns starts a tick when none ran for 10 minutes.
Its credential reaches neither half of the index, and without the Worker the index works as it does today.

## Why

RFC 0033 intends a tick every ten minutes.
The run list of `watcher.yml`, read on 2026-11-24, shows 100 scheduled ticks since 2026-10-30: 3 to 6 a day, with waits of up to 11.6 hours.
A new release of a listing that did not change waits for the schedule, so it can take half a day to become installable, and the stewards start ticks by hand.

GitHub documents that scheduled runs are delayed and dropped under load ([docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
Other repositories report the same since October, with crons off the hour ([discussion](https://github.com/orgs/community/discussions/209507)), and an org on GitHub Free cannot open a ticket for it ([docs](https://docs.github.com/en/support/learning-about-github-support/about-github-support)).

An outside clock stopped before at one requirement, from @Maximilian-Nesslauer: whatever holds the credential may start that job and nothing else, also when it is compromised.
A credential on the generated repository cannot meet it, because `Actions: write` also disables workflows, cancels runs, deletes caches and starts the watcher with `backfill` ([docs](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)).
So this RFC points the credential at a different repository.

## Rules

1. A new public repository `watcher-poke` holds one workflow, `poke.yml`. Its only trigger is `workflow_dispatch`, it takes no inputs, and it has a concurrency group of its own.
2. A tick is due when the newest run of `watcher.yml` that was not cancelled was created 10 minutes ago or more. `poke.yml` checks this and then starts the watcher on `main` without inputs.
3. A Worker asks every 5 minutes whether a tick is due, and starts `poke.yml` when it is or when it cannot tell.
4. There are two GitHub Apps, each with `Actions: write` on one repository only. The Worker holds the key of the one for `watcher-poke`. `watcher-poke` holds the key of the one for the generated repository, in an environment that only `main` may use. They are two because a key reaches every repository its App is installed on. The org App is used for neither.
5. `main` of `watcher-poke` has the same ruleset as `main` of the generated repository.
6. The Worker's source is in `watcher-poke` and is deployed from there. The Cloudflare account belongs to an address of the org, with at least two stewards as members.
7. The Worker tells the stewards in Discord once when the newest tick is 45 minutes old. A tick that starts more than 60 minutes after the one before opens an issue through `tools/watchdog.py`, which closes when ticks are at most 20 minutes apart again.
8. The index may use a free service outside GitHub when the index works without it, the service holds no state, and it holds no credential that reaches a repository of the index. A service that the index needs stays a non-goal.
9. The minutes in these rules are tuning parameters and need no RFC to change.

At acceptance the README of the generated repository describes the poke and corrects "about one of these runs an hour".

## What a compromise gives

| What leaks | What the attacker can do |
|---|---|
| The key in the Worker, or the Cloudflare account | Start and cancel pokes, disable `poke.yml`, post in the stewards' Discord channel. Rule 2 still allows one tick in 10 minutes. |
| The token that deploys the Worker | Replace the Worker and read its key, which is the row above. |
| Write access to `main` of `watcher-poke` | Everything `Actions: write` allows on the generated repository, hence rule 5. |

In no row can the attacker write a release file, change a listing or use the org App.
The worst outcome of the first two rows is that the poke stops, which is today.

## Cost

Nothing here costs money unless a person chooses a paid plan.

- Standard GitHub-hosted runners are free in a public repository ([docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions)), so `watcher-poke` stays public and uses no larger runner.
- The Worker stays on Workers Free. It runs 288 times a day against a limit of 100,000, and past a limit Cloudflare returns an error ([docs](https://developers.cloudflare.com/workers/platform/limits/)).
- Workers Paid, from 5 US dollars a month, is never the answer to a limit.
- The Cloudflare account has no payment method, and the Worker needs no domain.

## Drawbacks

- With the schedule as it is today the poke starts nearly every tick. The index stays correct without Cloudflare, but how fresh it is depends on it.
- It adds a second platform, a repository and two Apps for a small group of volunteers.
- `watcher-poke` is a second place with power over the generated repository.
- It works around the schedule and does not repair it.

## Alternatives

- **Another cron.** Free and worth trying, but the other reports use crons off the hour too.
- **A workflow that sleeps ten minutes and starts itself.** It works, since a `workflow_dispatch` made with `GITHUB_TOKEN` creates a run. It keeps a runner asleep around the clock to get around GitHub's load shedding, which risks Actions for the whole org under the "disproportionate burden" rule of the [terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features).
- **Several repositories with one schedule each.** It helps only if GitHub limits each repository, which nobody has verified, and each one needs a credential for the generated repository.
- **A cron with a token for the generated repository**, on a steward's server or a cron service. The requirement above rules it out.
- **An open queue**, as @MrJeranimo proposed, where anyone names a repository to check. This RFC takes the Worker from it. One tick already checks every listing in about a minute, so the queue saves nothing and adds state and a public endpoint.

## Unresolved questions

- Whether GitHub limits scheduled runs for each repository or for everyone. A repository with one schedule, watched for a week, answers it.
- Whether the free plan's 10 ms of CPU time is enough to sign the token request of a GitHub App. This has to be tried before acceptance. If it is not, the Worker holds a personal token limited to `watcher-poke`, which is weaker.
- Whether a free Cloudflare account can have two members who can each recover it, and can exist without a payment method.
- The names `watcher-poke` and `poke.yml`.

## Future possibilities

- A second poker with its own key, if the Worker proves unreliable. Rule 2 makes any number of pokers safe.
- Release webhooks from a GitHub App that authors install, so a tick starts when a release is published. 54 of the 56 listings name a GitHub repository. It saves at most 10 minutes, so it can wait.
