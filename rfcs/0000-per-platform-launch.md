---
rfc: "0000"
title: Per-platform launch
status: Proposed
authors: ["@Maximilian-Nesslauer"]
created: 2026-09-15
discussion:
supersedes: []
superseded-by: []
---

# RFC 0000: Per-platform launch

## Summary

A `mod-loader` listing gets one more optional table under `[provides]`, with one entry per platform, saying what a manager starts there: an executable, or a known runtime that takes the entry file as its first argument.
`[provides].launch` stays the default for every platform without an entry.

It answers the launch half of the unresolved question 5 of [RFC 0035](0035-content-install-descriptor.md).
Nothing else in RFC 0035 or [RFC 0049](0049-instance-handover.md) changes, and a manager that does not know the table starts `[provides].launch` as today, so `spec_version` stays at `1`.

## Motivation

RFC 0035 gives a loader one `launch` target for all platforms, and its unresolved question 5 names StarMap as a loader that needs more.

The StarMap listing names `launch = "StarMap.exe"`, the Windows app host, but on Linux StarMap runs as `dotnet StarMap.dll` ([research/starmap.md](../research/starmap.md)).
[Borea#167](https://github.com/KSAModding/Borea/issues/167) hit this gap, and [Borea#225](https://github.com/KSAModding/Borea/pull/225) fills it with a temporary guess: on a system other than Windows, when `launch` ends in `.exe` and a `.dll` with the same name is beside it, Borea starts `dotnet` with that `.dll`.

The facts belong on the listing, for the reason RFC 0049 gave: [RFC 0033](0033-content-index.md) binds the listing to the loader's release repository, so only the loader author can state how their loader starts.

## Guide-level explanation

If your loader starts the same way on every platform, you do nothing.

If it starts differently on one platform, you add an entry for that platform:

```toml
[provides]
launch = "StarMap.exe"

[provides.platform.linux]
runtime = "dotnet"
launch = "StarMap.dll"
```

That says: on Linux, start `dotnet` with `StarMap.dll`, and on every other platform, start `StarMap.exe` as before.
If your loader has its own executable on that platform, you name it in `launch` and leave out `runtime`.

## Reference-level explanation

### `[provides.platform]`

Optional, permitted only inside `[provides]`, so only where `type = "mod-loader"`, and only together with `[provides].launch`.
Its keys are the platform names of the `os` key in [RFC 0031](0031-content-metadata-format.md): `windows`, `linux`, `macos`.
Each key holds one entry:

| Key | Type | Required | Meaning |
|---|---|---|---|
| `launch` | string | yes | Path, relative to the loader's install location, of the file a manager starts on this platform: the executable, or with `runtime` the entry file that the runtime runs. It follows rules 1 to 3 of RFC 0035, the same as `[provides].launch`. |
| `runtime` | string | no | The runtime that runs `launch`, from the table below. |

| `runtime` | What a manager starts |
|---|---|
| `dotnet` | The `dotnet` command of .NET, with the entry file as its first argument. The entry file is the main assembly of a framework-dependent .NET application. |

The platform names, the runtimes and the keys of an entry are closed, and new members arrive by RFC, same as in `[provides.configure]` and `[provides.instance]`.
A new runtime also states where its entry file goes on the command line, so a manager never needs a template.

### What a manager does

At launch:

1. The manager reads only the entry for its own platform, so a platform name, a runtime or a key that it does not know in another entry changes nothing. Without an entry for its platform, it starts `[provides].launch` as RFC 0035 says.
2. When the entry has no `runtime`, the manager starts the entry's `launch` as the executable.
3. When the entry names a `runtime`, the manager finds that runtime, at least through the `PATH`, and starts it with the absolute path of the entry's `launch` as the first argument.
4. The working directory stays the loader's install location, per rule 5 of RFC 0035. The flag and the instance root of RFC 0049 come after the entry file, and the variable of RFC 0049 is set as before.
5. When the entry names a runtime or a key that the manager does not know, when the runtime is not found, or when the entry's `launch` is not in the installed loader, the manager starts nothing and reports why. It does not fall back to `[provides].launch`, because the entry says that the default does not start here.

### Effect on the generated release file

None.
`[provides.platform]` is not stamped into a release file, like the rest of `[provides]`, because a stale copy would start a file the installed loader no longer uses.
A manager reads it from the live listing at every launch.

### Errors

These are the conditions the index rejects.
A manager that reads a published listing follows "What a manager does" instead.

| Condition | Result |
|---|---|
| `[provides.platform]` outside a `mod-loader` listing, or without `[provides].launch` | File invalid. |
| `[provides.platform]` with no entry, or an entry without `launch` | File invalid. |
| A platform name, a `runtime` or an entry key outside its vocabulary | File invalid, same as an unrecognised key in `[provides.configure]`. |
| An entry's `launch` that escapes the install location | File invalid, per rule 1 of RFC 0035. |
| An entry's `launch` naming a file absent from the release | Release rejected, reported to the author, per rule 3 of RFC 0035. |

## Drawbacks

- The listing names a runtime that nobody installs. A player without `dotnet`, or without the .NET version the loader needs, gets a start that fails, and a manager can only report it.
- It is one more closed vocabulary, so every new platform or runtime needs an RFC before a loader can use it.

## Alternatives

- **A runtime key for all platforms**, `launch = "StarMap.dll"` with `runtime = "dotnet"` directly under `[provides]`. Smaller, and it matches how StarMap runs everywhere. Rejected for three reasons. It changes the meaning of `launch`, which RFC 0031 calls a break. On Windows it replaces the app host, which the shortcuts of `installer/WindowsInstaller.iss` start, with a `dotnet` that the manager has to find. And it cannot describe platforms that differ in more than the runtime, such as the dedicated Linux build the StarMap author plans.
- **Keep the special case in each manager**, as Borea#225 does. Rejected because file names do not say whether a `.dll` runs through `dotnet`, every manager repeats the guess, and the loader author cannot correct it.
- **A launch table keyed by platform**, such as `launch.linux = "StarMap.dll"`. Rejected because it changes the type of the existing string `launch`, which breaks every listing and manager that reads it.

## Unresolved questions

- **Processor architecture.** A platform name says nothing about it, like the `os` key of RFC 0031. Should an entry name an architecture, or does that wait for a loader that ships one build per architecture?
