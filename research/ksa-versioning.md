# How KSA versions work, and why they cannot be sorted

Verified against game build **2026.8.3.5117**.

## The shape

A KSA version is four numbers, optionally followed by a suffix and a git hash. `VersionInfo` parses it with this pattern:

```text
^v?(?<Year>\d+)\.(?<Month>\d+)\.(?<Build>\d+)\.(?<Revision>\d+)(?:-(?<Suffix>[^+]+))?(?:\+.*)?$
```

| Component | What it is |
|---|---|
| Year | Calendar year of the release. |
| Month | Calendar month of the release. |
| Build | A counter local to the machine that produced the build. |
| Revision | The commit count on the main branch. |
| Suffix | Optional, e.g. `-LOCAL`. Nothing in the shipped game produces one; it comes from the build process. |
| `+hash` | The git commit, present in the informational version and discarded by the parser. |

`VersionInfo.Current` is built once at startup from the `AssemblyInformationalVersionAttribute` of `KSA.dll`. A leading `v` is accepted on input; `VersionString` always renders one back.

Note that the property names do not match what the components mean: `Major` holds the year, `Minor` the month, `Build` the build counter and `Revision` the revision. Anything mapping this onto a `Major.Minor.Patch.Build` shaped type will line the parts up in a misleading way.

## How the game itself orders two versions

`VersionInfo.CompareTo` compares, in this order:

1. **Revision**
2. **Build counter**, only as a tiebreak when the revisions are equal
3. **Suffix**, ordinal string comparison, only when both of the above are equal

**Year and month are are just display, not ordering.**

This comparator is called in exactly one place in the whole game: deciding whether the version the master server reports is newer than the running one. Nothing else in KSA orders, gates, or validates a version.

## The build counter is not part of a release's identity

Two independent pieces of evidence, both from the game itself.

**The build tooling erases it.** `BuildInfo.WriteJson` runs the version string through

```csharp
Regex.Replace(buildVersion, "^((?:\\d+\\.){2})\\d+(\\..*)?$", "$1X$2")
```

before naming the changelog file. The release deployed as `2026.8.3.5117` is therefore shipped as `Content/Versions/v2026.8.X.5117.json`. The full string survives inside the file, in the `build` field. The name, which is what identifies the release, has the build counter replaced by a literal `X`.

**The shipped history shows**:

- Revisions are strictly ascending and unique across the entire history. No duplicates, no reuse.
- The build counter **decreases 32 times** while the revision increases, so it does not track release order at all.
- Only 46 distinct build counter values appear across 155 releases. One value is reused 16 times.

The developers have described the third component as local to whichever machine produced the build, and any machine with the source can build and deploy.

## What happens if you sort the version string

Sorting the 155 shipped releases by `Year.Month.Build.Revision`, the way any ordinary four-part version comparison would, **puts 21 adjacent pairs in the wrong order**. For example:

| Naive sort says this is older | when it is actually newer than |
|---|---|
| `2025.8.24.2263` (2025-08-30) | `2025.8.33.2091` (2025-08-18) |
| `2025.9.2.2383` (2025-09-18) | `2025.9.3.2279` (2025-09-02) |
| `2025.9.3.2404` (2025-09-20) | `2025.9.4.2290` (2025-09-03) |

Sorting by revision alone reproduces the true release order for all 155 releases.

## What a version range can and cannot mean

This matters for expressing "this mod works with these game versions".

**`Year.Month.Build` as a prefix is meaningless.** 20 of the 133 distinct year-month-build combinations match more than one release, and **19 of those 20 select a set that is not contiguous in time**. `2025.9.2.*` matches three releases spread across revisions 2270 to 2383, with unrelated releases in between. A range expressed at that granularity does not describe a period of the game's history; it describes an accident of which machine did the build.

So there are exactly two granularities worth offering: a month, or an explicit revision bound. Anything in between is noise.

## Reading the installed version off disk

| Source | Notes |
|---|---|
| `KSA.dll` PE **FileVersion** | `2026.8.3.5117`. Clean four-part string, readable without loading the assembly. The best source. |
| `KSA.dll` PE ProductVersion | `2026.8.3.5117+6b87889f...`. Same version with the git hash appended. Usable, but the hash has to be stripped. |
| `Content/Versions/*.json` | The `build` field of the newest file. The file **name** carries `X` instead of the build counter, so the name is not a substitute for the field. |
| Save metadata | Every save records the version it was written by. |

Prefer FileVersion. It is exact, cheap, and has no suffix to strip.

## The shipped revision history is an ordered index

`Content/Versions/` is not just changelog text. Each file is a `ChangeLog`:

```json
{
  "build": "2026.8.3.5117",
  "date": "2026-08-01",
  "fromRevision": 5056,
  "toRevision": 5117,
  "commits": [ ... ]
}
```

`VersionHistory.Initialize` reads every `*.json` under `Content/Versions` recursively and sorts them by `ToRevision` descending.

The `fromRevision`/`toRevision` pairs chain: each release picks up where the previous one ended. Across the 155 shipped files there are 5 breaks in that chain, so it is nearly but not perfectly continuous.

This means an installed copy of the game carries a dated, ordered list of every release up to its own, keyed by revision. It is the only ordering source that does not require inference, and it is already on the user's disk.

## "Latest" only exists on the master server

`VersionInfo` polls `http://ksa-master1.rocketwerkz.com:8082/version` and deserializes a `VersionMetaInfo` of `{ Version, Url }`. If `Master.CompareTo(Current) > 0`, `UpdateAvailablePopup` offers the download link.

There is no way to derive "is this the newest release" from a version string alone, because the string does not say when it was built and the build counter does not order. The master server broadcast is the authority, and it reports one version: the current public production build. It says nothing about anything older, and nothing about builds produced for other purposes.

The developers have been explicit that specialist builds exist, produced for hardware vendors, agencies and universities, and that two builds of the same revision compiled in development, release or production configuration behave very differently. The revision pins the source; it does not pin the binary.

## The game validates nothing

Worth stating on its own, because it is easy to assume otherwise.

`SaveMetaData` stamps `VersionInfo.Current` into every save, and `UncompressedSave` parses it back with exceptions disabled, so an unreadable version silently becomes `0.0.0.0`. That value is then only displayed in the load dialog. There is no migration path, no refusal to load an old save, and no comparison anywhere.

Nothing in the game rejects a mod, a save, or anything else on version grounds. Any compatibility rule a manager enforces is one the manager invented.

## Implications for a mod manager

- **Order by revision.** It is the only component that orders correctly, it is unique across the whole shipped history, and it matches what the game does internally.
- **Read FileVersion from `KSA.dll`** to detect what is installed.
- **Do not treat compatibility as equality.** 155 builds in under twelve months is roughly thirteen a month. A mod pinned to the exact build it was compiled against is marked broken within days, almost always wrongly. Compatibility has to be a range, and its upper end has to be something a mod author can leave open.
