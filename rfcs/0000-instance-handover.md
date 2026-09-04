---
rfc: "0000"
title: Instance handover
status: Draft
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-04
discussion: https://github.com/KSAModding/content-manager-design/discussions/20
supersedes: []
superseded-by: []
---

# RFC 0000: Instance handover

## Summary

A `mod-loader` listing gets one more table under `[provides]`, saying how the loader is told which instance to run: a command line flag that takes the instance root as the next argument, an environment variable that carries it, or both.
A manager fills in the absolute instance root and nothing else.

Nothing else in [RFC 0035](0035-content-install-descriptor.md) changes, and `spec_version` stays at `1`.

## Motivation

RFC 0035 lets a manager install a loader and start it: `[provides].launch` names the executable, rule 5 fixes the working directory, and `[provides.configure]` says where the game path goes.
It says nothing about how the loader learns which instance to run:
the section on the manager/loader boundary leaves the launch-time contract around an instance to [discussion #20](https://github.com/KSAModding/content-manager-design/discussions/20) and notes that StarMap takes `-InstancePath` and `STARMAP_INSTANCE_PATH` while `[provides]` has nothing for it.

The first code that starts the game for an instance, [Borea#77](https://github.com/KSAModding/Borea/pull/77), hit that gap and keeps a table of what it knows.
That table has one row, StarMap, and any other loader is refused.
Every manager would carry the same table, and the loader author could not correct it when a flag changes, because it lives in code that is not theirs.

The facts belong on the listing, next to `launch` and `configure`, for the reason RFC 0035 already gave for `[provides.configure]`: [RFC 0033](0033-content-index.md) binds the listing to the loader's release host, so only the loader author can state or change what their loader reads.

## Guide-level explanation

If you wrote a loader that can run an instance, you add two lines to your listing:

```toml
[provides.instance]
flag = "-InstancePath"
variable = "STARMAP_INSTANCE_PATH"
```

That says: to run instance X, pass `-InstancePath <root of X>` on the command line, or set `STARMAP_INSTANCE_PATH` to that root, and the whole profile follows.
A manager reads the two lines and does both.

If your loader reads only one of the two, you name only that one.
If your loader restarts itself into a new process, name the variable as well, because the new process inherits the environment and not the arguments.
If your loader cannot run an instance at all, you leave the table out, and a manager will say so instead of starting the game in the shared profile.

## Reference-level explanation

### `[provides.instance]`

Optional, permitted only inside `[provides]`, so only where `type = "mod-loader"`.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `flag` | string | see below | The argument that precedes the absolute instance root on the command line. |
| `variable` | string | see below | The environment variable that carries the absolute instance root. |

At least one key is required when the table is present.
Both are single tokens without whitespace.
The vocabulary is closed, new keys arrive by RFC, same as `[provides.configure]`.

### What a manager does

At launch, after resolving the executable per RFC 0035:

1. When `flag` is named, the manager appends two arguments to the command line, the flag and the absolute instance root, and it passes them as two separate arguments and not as one joined string.
2. When `variable` is named, the manager sets that variable to the absolute instance root in the environment of the process it starts.
3. When both are named, the manager does both.

The root is absolute because the loader resolves relative paths in its own working directory, which rule 5 of RFC 0035 fixes to the loader's install location.
The manager passes the root exactly as its own instance layout defines it, and nothing here says what that layout is.

### Absent is not empty

A `mod-loader` listing without `[provides.instance]` means the loader does not run instances, and a manager must not guess a flag or a variable.
Such a loader can still be installed and launched, into the shared profile, and a manager that was asked to launch an instance with it reports that it cannot.
This is the "undescribed" rule RFC 0035 already applies to a loader without `[install]`.

### Effect on the generated release file

None.
`[provides.instance]` is not stamped into a release file, like the rest of `[provides]`, because a stale copy would hand the instance to a flag the installed loader no longer reads.
A manager reads it from the live listing at every launch.

### Errors

| Condition | Result |
|---|---|
| `[provides.instance]` outside a `mod-loader` listing | File invalid. |
| The table is present and names neither key | File invalid. |
| A key that is empty or contains whitespace | File invalid. |
| An unrecognised key inside `[provides.instance]` | File invalid, same as in `[provides.configure]`. |

### StarMap

Verified against the StarMap source: `DocumentsPathPatches.TryGetOverride` reads `-InstancePath` from the raw process arguments, case-insensitively, with the next argument as the path, and falls back to `STARMAP_INSTANCE_PATH`.
`ModLibraryPatches.BeforePrepareAll` restarts the loader after new mods were enabled by starting a new process with only `--restarted`, so the variable is what keeps the instance across that restart.
The StarMap listing therefore names both keys, as in the example above.

### Relationship to RFC 0035

This adds an optional table and changes no existing key, so by RFC 0031's evolution rule `spec_version` stays at `1`.
It answers one of the questions RFC 0035 left to discussion #20, the launch-time handover of an instance, and leaves the rest of that discussion where it is.

## Drawbacks

- It is a second member of the family `[provides.configure]` started: author-named addresses that a manager fills with a value it holds. The closed vocabulary is what keeps it from growing into a template language, and every future key is a small argument.
- It carries a path without saying what is in it. What an instance is stays undefined here, so two managers can hand a loader two different layouts under the same flag.
- A loader author who does not add the table gets managers that refuse to run instances with their loader. That is the honest outcome, and it is also a queue item for the author.

## Alternatives

- **Keep the table in each manager**, which is what Borea#77 does today. Rejected because every manager repeats it and the loader author cannot correct it.
- **An argument template**, such as `args = ["-InstancePath", "{instance}"]`. More expressive, and a template language with placeholders that every manager has to implement identically. Rejected for the reason RFC 0035 rejected a script: the value side stays a closed set.
- **A key in `[provides.configure]`**, writing the instance root into the loader's configuration file. Rejected because that file is per install and a launch is per instance, so two instances would overwrite each other.
