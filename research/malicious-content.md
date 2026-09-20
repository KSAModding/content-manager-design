# Malicious content, and what an index without a server can do about it

Research for [issue #69](https://github.com/KSAModding/content-manager-design/issues/69).

This page answers four questions:

- What does the current index prove, and what does it not prove?
- What do comparable indexes do?
- What can a free automated check reliably detect?
- What protection belongs in the client instead?

Note that i used LLMs for this research.

## The gap

A listing merges itself when its checks pass. Those checks prove four things:

- The document is valid, and its id is free.
- The account that opened the pull request controls the release host. It proves this through the repository owner id, a repository topic, or a marker file ([RFC 0033](../rfcs/0033-content-index.md), [RFC 0038](../rfcs/0038-repository-topic-ownership-proof.md)).
- The archive is at the address in the release record, and its bytes have the `download.sha256` value in that record ([RFC 0031](../rfcs/0031-content-metadata-format.md)).
- The install paths in the listing are relative and stay inside the install folder. This rule applies to the authored descriptor. It does not walk the entries in the archive.

None of these checks says anything about the behavior of the content:

- No check opens an assembly.
- Nobody reads the code of a listed mod.
- The index never hosts a file, so a delisting removes discovery and nothing else.
- `index-status.toml` lets a steward act after the fact.
- The required forums link ties a listing to an Ahwoo account. That gives a person a lever, but it does not constrain a program.

RFC 0033 states the risk in its drawbacks: "Auto-merge on green means a schema-valid malicious listing can land without human eyes, and moderation is reactive, not preventive."

The index `POLICY.md` also names "the archive carries something harmful" as a reason for a takedown that holds. The takedown form offers it as a reason, so a steward can act on a report.

Both statements are written for a steward. Neither tells a player what a green check proves. The gap has no statement that a player will ever read.

## What comparable indexes do

We examined five ecosystems through policy text, open source code, and post-incident disclosures.

| Index | Human review before listing | Automated code inspection | Published malware rule | Real backstop |
|---|---|---|---|---|
| CKAN | Metadata template only | None | None | De-indexing at the team's discretion |
| Thunderstore | Off by default, per-community opt-in | None found in the codebase | Yes | User reports plus moderator takedown |
| Modrinth | Every new project | In-house scanner, not published | Yes, as a disclosure rule | User reports |
| CurseForge | Project page plus every uploaded file | Decompile, hash, static analysis | Only in a blog post, not in the policy page | User and researcher reports |
| Factorio | None | One file-extension refusal | None found | The game is the sandbox |

### CKAN does nothing about malicious code, and says nothing about it

Its published indexing policy covers author permission, licensing, adoption of abandoned mods, and de-indexing. The words malware, malicious, virus, and security do not appear in it.

Its nearest safety lever is discretionary and addresses a different problem:

> The CKAN team may reject a request to index a mod for any reason. Primarily the CKAN team will consider the impact on users and other mod authors when making this decision - for example mods that are likely to cause conflicts, data loss, compatibility issues, etc.

The remaining controls have the same limits:

- A `SECURITY.md` is absent from KSP-CKAN/CKAN, KSP-CKAN/NetKAN, KSP-CKAN/.github, and KSAModding/KSA-NetKAN.
- A code search for malware across the KSP-CKAN organization returns nothing.
- CKAN has a human gate, but it applies to the metadata template and not to the code.
- Automated validation inflates the metadata and installs into a sandbox instance. It never opens the assemblies in the archive.
- After the template merges, an unattended bot inflates and commits each later release. No human sees release N+1.

This is the same authored and generated split described in [prior-art-ckan.md](prior-art-ckan.md), with the same blind spot as our design.

CKAN also publishes a disclaimer that our index could almost use verbatim:

> Note that CKAN does not host or distribute any mod content - it only links to mod content on sites like SpaceDock, GitHub, etc., and provides a method to fetch that content similar to a web browser.

### Thunderstore, the closest analogue to us, ships with review off

Thunderstore is the largest index of .NET mods that load into a game process. Its `require_package_listing_approval` option defaults to false in the community model. The visible-status query includes unreviewed packages unless a community opts into review. A package is therefore public as soon as it uploads in each community that has not enabled review.

Its controls are as follows:

- Its written rule is a moderation rule, not a technical control. "Packages containing malware are not allowed." This covers "keyloggers, crypto miners, token stealers, and other malicious programs", which "remain prohibited even if the author discloses that they contain such capabilities."
- Its one code-transparency feature is decompilation, not scanning. `Community` and `Package` both contain `show_decompilation_results`. The backend is a separate public repository whose only endpoint writes the uploaded file to a temporary file and runs `ilspycmd` on it.
- Reports have types. "Suspected malware" is a first-class reason, and urgent cases go to a Discord support channel.
- Thunderstore documents one important limit. If it rejects a package, the download links continue to work because they are not specific to a community.

### Modrinth reviews every new project, and that did not save it

Modrinth publishes its queue times honestly:

- The target is 24 to 48 hours.
- Fluctuations average two to four weeks, and sometimes longer.
- The queue can exceed one month while moderators are in training.

It also runs "an in-house malware scanning tool". A hit goes to one technical moderator for code review.

Its own disclosure about the "Windows Borderless" mod shows the limit of both controls:

- The clean submission arrived on 29 April 2024 and passed review.
- Malicious versions appeared from 2 May onwards.
- The incident was found on 6 May, when "A user submits a report against the mod, alleging that their Discord account got compromised after using the mod."

The scanner did not find it. The reviewer did not find it. A user did.

That failure mode has exactly our shape. No check looks at the content, and later releases are stamped without a person in the loop. Modrinth's stated answer was not more review. It proposed a shared quarantine API that launchers could query, but we could not establish that it shipped.

### CurseForge publishes the deepest pipeline, and it still failed for months

Every submitted Minecraft mod file goes through this process:

- CurseForge decompiles it.
- CurseForge compares its hash with known malicious files.
- CurseForge runs "several static analysis tools, these are not very smart but they do know how to spot a bunch of common issues and potential security risks".
- Suspicious files go to a human.

CurseForge states its own false positive problem in the same post.

The fractureiser incident still used compromised author accounts to reach CurseForge and BukkitDev. It spread into modpacks with millions of downloads. Independent community researchers found it in June 2023, not the pipeline. The resulting advice was that "Any download from CurseForge or the Bukkit plugin repository made from February to June 2023 should be treated as potentially malicious."

### Factorio does nothing, and is right to

Factorio can rely on properties of the game itself:

- Mods use Lua interpreted by the engine.
- Mods cannot run native code.
- The API can reach outside the game only to write log files and send keyboard or mouse input.

The portal has exactly one automated check, visible only through its error text:

> Error: It is not permitted to distribute executable files with your mod. Please remove all files ending in exe, bat, ps1, sh, py.

This protection is a property of the game, not the portal. It is the one example on this page that does not transfer to us at all.

### The common result

Two observations hold across all five ecosystems:

- Nobody promises that listed code is safe.
- Users or outside researchers found both documented breaches. Both breaches came through identities that had already been verified, which is also what our ownership proof checks.

## What a free automated check could reach

The runner is not the constraint:

- Standard GitHub-hosted runners are free for public repositories.
- An `ubuntu-latest` runner has 4 vCPU and 16 GB of RAM.
- The release tooling already streams the archive into a temporary file and hashes it while it streams, with a 4 GiB ceiling.

Any scan adds only marginal CPU work to bytes that we already have. Reliability is the constraint.

### ClamAV catches roughly six in ten samples of malware it already knows

Splunk scanned 416,561 MalwareBazaar samples. ClamAV detected 249,696, or 59.94 percent. It did poorly on the categories that matter here, including info stealers and remote access tools.

That number is a ceiling for known commodity malware. It does not describe a payload written for one KSA mod, which has no prevalence and no signature.

The default limits create another problem:

- `--max-filesize` defaults to 25 MB.
- `--max-scansize` defaults to 100 MB.
- Our archive limit is 4 GiB.

A mod with a native solver or texture assets could therefore report clean because the scanner did not inspect it. Increasing heuristic sensitivity makes the result worse. ClamAV's own documentation warns that PUA signatures "are not as carefully curated" and cause more false positives.

The marketplace actions that wrap ClamAV are free and honest about this limit. The best of them says in its README that it does "not provide any guarantee that carefully hidden objects will be scanned".

### Static metadata inspection is exact, fast, and shallow

`System.Reflection.Metadata` can read the ECMA-335 tables directly from a PE file. It can list referenced assemblies, type references, and declared P/Invoke entries in milliseconds without loading the file.

Microsoft's trimming documentation states the limit clearly. Code is not analyzable when it does any of the following:

- Loads types through `Type.GetType` with a runtime string.
- Loads assemblies through `Assembly.LoadFrom`.
- Generates code at run time through `System.Reflection.Emit`.

There are direct bypasses for each kind of list:

- `Assembly.Load(byte[])` defeats the full assembly-reference list in one call.
- `TypeBuilder.DefinePInvokeMethod` creates a P/Invoke that never appears in the ImplMap table.
- `NativeLibrary.GetExport` with `Marshal.GetDelegateForFunctionPointer` reaches native code without a `DllImport` entry.

A reference list therefore shows only what an author did not try to hide.

### The false positives would reach our own mods first

Our reference mod already gives a useful test case. Its current source tree does all of the following:

- Ships `clarabel_c.dll` and `scs.dll`.
- Declares eleven `[DllImport]` entries for these two unsigned native libraries.
- Installs a resolver for each library through `NativeLibrary.SetDllImportResolver`.
- Calls `Assembly.LoadFrom` in `GuidanceFeature`.
- Uses `System.Reflection.Emit` in three separate files.
- Writes configuration files under the game's documents folder.
- Patches game methods with Harmony throughout.

A scanner aimed at the index today sees none of this. The newest stamped AdvancedFlightComputer release is 0.7.5 from 2026-09-02, with a download size of 129,696 bytes. The guidance code lands after it. This is a forecast of the next release, not a reading of the current release. A naive flag list would still meet all of these signals at once.

P/Invoke into a native blob together with `Assembly.LoadFrom` is a stronger malware signal than a socket. Other normal mod behavior also creates strong signals:

- Harmony patching is normal for the nine code mods among the twelve listings. Two of the twelve are data-only packs, and the final listing is the loader itself.
- The loader also triggers such a heuristic because StarMap's `Program.Main` loads `0Harmony.dll` into the default load context.
- `ModLibraryPatches.BeforePrepareAll` calls `Process.Start` on the StarMap executable and then calls `Environment.Exit`. A static reader sees a program that relaunches the game. In practice, this path runs only when a newly enabled mod is present and the user clicks restart in `ConfirmRestart`.
- A mod never needs to ship Harmony because `ModAssemblyLoadContext.Load` resolves it from the default context first. Its presence or absence in an archive therefore proves nothing.

There is also documented precedent for a loader false positive. VirusTotal flagged BepInEx's `winhttp.dll`, and its maintainers closed the report as a known false positive. Norton separately flagged `BepInEx.Preloader.dll`.

One premise from the start of this research also needs a correction. No currently listed mod is documented to open a socket. The issue names networking as something a check could inspect. KSATelemetryOverlay may sound like it uses a network, but it reads the active vehicle and writes a local configuration file.

### Published behavior detection performs worse than intuition suggests

Cerebro is a peer-reviewed behavior-sequence detector and is much more capable than anything we would build. It flagged 3,746 of 599,493 new PyPI versions. Of those flags, 3,053 were false positives. The paper reports these false positive rates:

- 81.5 percent for PyPI.
- 64.2 percent for npm.

Its named false positive classes match our two cases exactly:

- Packages that "encapsulate RESTful APIs, which enable data transmission to remote servers".
- Packages whose behavior resembles malicious packages "in using features about Payload Execution".

The same paper estimates a review queue of about one hour per day for one researcher across two of the largest registries in the world. Our number of flags would be small, but the work for each flag does not shrink. The reviewer still has to read IL.

### Nobody is on call to answer a refused author

The organization has limited review capacity:

- The charter names five stewards.
- The index `SECURITY.md` says that "The stewards are volunteers and have no on-call rota" and cannot guarantee a response time.
- RFC 0033 already creates a residual steward queue for SpaceDock-only listings, first pack claims, failed ownership proofs, and the first pull request from a brand-new account.

A scanner appeal would join that queue. A queue that blocks merges but receives no timely review is worse for authors than auto-merge is for players.

### Two cheap checks have value, but neither should be a gate

The GitHub users endpoint returns the account creation date, follower count, and repository count. It is free and stays well inside the Actions token budget. It can identify a case such as "this is a first release from an account created last week" and route that pull request into the steward queue that RFC 0033 already defines. This replaces a manual observation with data.

Stars are not useful for this purpose. The ICSE 2026 fake-star study found 4,530,000 suspected fake stars across 22,915 repositories. It states that most of them promote short-lived malware repositories.

A VirusTotal hash lookup would offer the highest value per runner second:

- We already calculate the sha256.
- VirusTotal returns verdicts from more than 70 engines.
- A lookup does not require an upload.

However, the public API terms say it "must not be used in business workflows that do not contribute new files". A lookup-only workflow contributes no file. We need a ruling from VirusTotal before anybody relies on this option.

## What belongs to the client

### There is no sandbox to use

The platform settles this question, not us. StarMap loads each mod through `ModAssemblyLoadContext`, a plain `AssemblyLoadContext` subclass that overrides only `Load` to resolve dependencies.

Microsoft documents the relevant limits:

- An `AssemblyLoadContext` is a loader, not a security boundary.
- Code Access Security is no longer a security boundary.
- .NET 6 and later do not support sandboxing.
- Additional `AppDomain` instances are not supported and are not planned.

The only supported isolation is an operating-system boundary. StarMap's own README calls it "A POC/Prototype arbitrary code modloader for Kitten Space Agency", which is accurate.

### Enabling a mod is enough to run its code

The load sequence has no safe inspection point after assembly load:

1. `ModLoader.PrepareMods` walks `ModLibrary.Manifest.Mods` and skips each entry whose `Enabled` value is false.
2. For each enabled entry, `RuntimeMod.TryCreateMod` checks only that `mod.toml` and the entry assembly exist.
3. It loads the assembly through `LoadFromAssemblyName`.
4. That load can run the author's code. A `[ModuleInitializer]` runs during assembly load and before any constructor. AdvancedFlightComputer uses one in each guidance assembly to install its native library resolver.
5. `TryFindModType` reads `ModAssembly.GetTypes()` and matches the mod attribute by type name, not type identity.
6. `RuntimeMod.InitializeMod` calls `Activator.CreateInstance` on the first matching type. This runs its constructors before the loader reads an entry-point attribute.
7. All of this happens before `GameSurveyer.RunGame` calls the game's entry point.

Nothing in StarMap verifies a hash or signature before the load.

The game itself never loads mod code. `KSA.ModLibrary` and `KSA.Mod` handle TOML manifests and declarative assets. The only assembly load in the decompiled tree is `KSA.VersionInfo` reading its own version attribute.

The game offers one consent prompt. `ConfirmModPopup` says only `A new mod with id '<id>' has been found, do you want it enabled?` and offers the buttons "Enable" and "No".

### A permission list would be wrong in both directions

It would flag AdvancedFlightComputer on its first day. It would also clear a mod that uses `TypeBuilder.DefinePInvokeMethod` to reach native code, or that fetches a second assembly and runs it through `Assembly.Load(byte[])`.

Felt and others measured how users respond to permission lists during each installation:

- 17 percent of participants paid attention to the permissions.
- 3 percent answered all three comprehension questions correctly.

Attacker-controlled input together with a list that almost nobody reads is worse than no list. It teaches the player that somebody checked.

### What the client can say honestly, without an index change or server

`HttpModDownloader.DownloadAsync` streams the archive and hashes it. `ModArchive.Extract` opens it afterwards. File-level descriptions can fit between those two operations.

One simple fact is worth more than a long list. The client can tell the player whether the content runs code at all, and the index can answer this before the download:

- A stamped release has a `loader` object exactly when the content needs a code loader.
- Nine of the twelve current listings have one.
- The two data-only packs do not have one.
- The loader itself does not have one because its listing declares `type = "mod-loader"`.
- `RuntimeMod.TryCreateMod` returns false without a managed entry assembly, while the game's own path is declarative.

The client can therefore make a checkable distinction between "this content adds data only, it runs no code" and "this mod runs code inside the game". A player can understand and judge that distinction.

The client can also describe the download without claiming that it is safe:

- A file inventory can separate managed assemblies, native PE files, and data through `PEReader.HasMetadata`. This is a description, not a verdict, and it lets an interested reader investigate.
- A change from the previously installed release is easier to judge than an absolute profile. The client can say that an update adds a native library, changes the download host, or grows the archive from 129 KB to 4 MB.

This kind of change report would have caught the Modrinth case, where version one was clean.

`ModArchive.Extract` already refuses an entry when its resolved target leaves the install folder, and it fails the full extraction. This is a hard stop, not a judgement call. The client should explain the refusal in plain words and make it easy to report through the takedown form.

### Build provenance can raise the guarantee above identity

This mechanism still needs no server. `actions/attest-build-provenance` binds an artifact digest to a signed SLSA provenance statement through the Sigstore public-good instance. It is free for public repositories and can be verified offline.

Borea already documents this process for its own releases:

- `gh attestation verify` checks the signer workflow.
- An attested CycloneDX software bill of materials describes the build contents.

Provenance does not describe behavior. It does connect a release to source that a person can review, and it closes the gap where an author builds a file on a laptop with no record of its source.

An optional badge costs the index nothing when it is absent. A provenance requirement would keep mods out, so it must not be required.

## What we could not establish

- No published measurement exists for ClamAV against novel, targeted, non-commodity .NET payloads. We do not believe one exists, and the 59.94 percent figure does not stand in for it.
- We could not establish whether ClamAV unpacks any .NET protector. The documentation names UPX, Petite, and FSG. We found no mention of ConfuserEx, .NET Reactor, Eazfuscator, or SmartAssembly. Treat an obfuscated assembly as an unmeasured but probably complete bypass.
- The widespread claim that Thunderstore scans uploads with ClamAV comes from search-optimized blog pages. The open source codebase contradicts it. Searches for clamav and virus return no results, and malware appears once as a user-report label. We treat the claim as unsupported, not false.
- We could not establish whether Modrinth shipped its announced shared quarantine API for launchers. Its scanner is also not public.
- We could not establish why malicious extensions reached Open VSX after mandatory pre-publish scanning. Press reports describe the mechanism, but we could not reach an Eclipse primary source. We do not use it as evidence above.
- We could not establish whether the VirusTotal public API terms permit a lookup-only workflow. VirusTotal must answer this question.
- We could not establish the maturity or licence of sigstore-dotnet, which is the alternative to calling `gh` for an in-client attestation check.
- We found no malware or malicious-code clause in CurseForge's published moderation policy. A blog post describes the pipeline, but the policy page does not.

## Recommendation

### Open a narrow disclosure RFC

The RFC should contain only the disclosure. It should not change a merge rule or add a scanner.

The disclosure needs three locations and one source of truth:

1. The long form belongs in the index `POLICY.md`. It must state what a green check proves, what it does not prove, that nobody reads the code, that a mod is a program with the game's own privileges, and what a player can do instead.
2. The listing page needs a short form that links to the policy.
3. Borea needs the same short form and link, so the three copies cannot drift.

In the client, use one consent prompt before the first installation of code content, not a dialog for every installation. Keep a permanent line in the listing view. This follows Obsidian's Restricted Mode pattern.

Obsidian is the closest structural analogue with effective wording. Although it scans content, it still says that "Obsidian cannot reliably restrict plugins to specific permissions or access levels" and recommends an independent audit for sensitive work.

The AUR puts the same principle on its front page:

> DISCLAIMER: AUR packages are user produced content. Any use of the provided files is at your own risk.

Keep the sentence that nobody reads the code. It is literally true of our tooling. It makes the rest of the disclosure credible, and it is normal for an index to print such a statement on its front page.

### Do not add an automated scanner

Each available option is either blind or wrong:

- ClamAV detects 59.94 percent of malware for which signatures already exist. It has no signature for a payload written for us and skips files above 25 MB by default.
- A single call to `Assembly.Load(byte[])`, `TypeBuilder.DefinePInvokeMethod`, or reflection with a runtime string defeats a static reference list.
- The best published behavior detector has an 81.5 percent false positive rate and names our exact cases.
- Our own reference mod will trigger five separate naive flags when its guidance code ships. The loader triggers two more.
- A check that cannot block is only another published fact. The disclosure already covers that fact.
- A check that can block creates an appeals queue for five volunteers whose own `SECURITY.md` promises no rota.

One exception is worth including in the RFC as a routing rule, not a gate. RFC 0033 already sends the first pull request from a brand-new account to a steward. A free account-age lookup makes that trigger data-driven.

This still adds a network call to every listing pull request and creates a new automated routing decision. That is why the recommendation says no scanner, not no check.

### Do not leave the disclosure informal

The content of the current design is right, and the merge rule should not move. The problem is where the warning lives.

There is no player-facing statement today:

- The index `POLICY.md` says that "The index holds metadata and nothing else". It mentions a harmful archive only as a reason for a takedown after the fact.
- The index `SECURITY.md` says that stewards do not decide whether an archive is safe. It does not say that nobody else makes that decision either.
- A search of the Borea tree finds no wording of this kind.

The client part is therefore new user-facing behavior, not an edit. The wording also binds three repositories together.

The charter says that every change goes through an RFC. Today, the nearest record of this gap is one drawback bullet in an accepted RFC. That is not a policy, and no player will read it.

A new RFC turns the warning into policy, adds a row to `DECISIONS.md`, and gives the next person who asks renancamm's question a document to point to.
