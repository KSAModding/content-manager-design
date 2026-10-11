# Mod load and crash reports

Verified against StarMap `0.4.6` at commit `57846b2`, StarMap development commit `418c64f`, game build **2026.9.7.5402**, and Borea commit `ac1ed3c`.

## Answer

StarMap can identify a mod while it loads the mod and while it calls a StarMap hook.
It can write that identity and the result to a file that Borea can read.

StarMap does not write such a file today.
It writes most load results to the console, leaves some results silent, and lets many exceptions end the process without a StarMap record.

The game log is useful after the game starts, but it does not close this gap.
StarMap loads code mods and calls each `[StarMapBeforeMain]` method before the game creates `KittenSpaceAgency.log`.
Later managed exceptions reach the game log, but the stack trace does not give Borea a reliable mod id.

The useful design is a dedicated, structured StarMap report inside the active instance.
StarMap must put the mod id in each failure record instead of making Borea infer it from a namespace or an exception message.

## The launch order creates two diagnostic periods

`GameSurveyer.TryLoadCoreAndGame` loads `KSA.dll`, sets the game working directory, and then calls `StarMapCore.Init`.
`StarMapCore.Init` calls `ModLoader.Init` before it applies the other StarMap patches.
`ModLoader.Init` applies `DocumentsPathPatches` and then calls `ModLoader.PrepareMods`.

This first period includes assembly discovery, dependency checks, object construction, method discovery, and every `[StarMapBeforeMain]` call.
The game entry point has not run yet.

After `StarMapCore.Init` returns, `GameSurveyer.RunGame` invokes the game entry point.
`KSA.Program.Main` constructs `KSA.Program`, and the constructor creates `Constants.LogsFolderPath`, configures `KittenSpaceAgency.log`, installs the last-chance exception collector, and initializes the logging system.
The constructor later calls `ModLibrary.PrepareAll` and `ModLibrary.LoadAll`, which run the `[StarMapImmediateLoad]` and `[StarMapAllModsLoaded]` hooks through StarMap's patches.
Frame and user interface hooks run after that.

The result is a clear boundary:

- A failure before the game finishes its monitor, logger, collector, and logging-system setup has no reliable game log or game crash collector.
- A managed exception after that setup can reach `KittenSpaceAgency.log` and the crash collector.

Constructor entry is not the boundary.
`KSA.Program` creates the console window and log directory before it finishes the diagnostic setup, and an exception in those earlier operations still has no installed game logger and collector.

## What StarMap reports today

`ModLoader.PrepareMods` calls `Console.WriteLine` for these results:

- a manifest entry is disabled,
- a mod waits for dependencies,
- initialization returns `false`,
- a mod loads,
- a waiting mod loads after its dependencies,
- a waiting mod cannot load because dependencies are absent.

These messages go to the inherited console only.
The StarMap source has no file logger and does not redirect standard output or standard error.
Borea's `ProcessStarter.Start` also keeps the inherited console and does not redirect either stream.

`RuntimeMod.TryCreateMod` returns `false` without a message when it cannot find `mod.toml`, cannot find the entry assembly, or cannot find a class with `[StarMapMod]`.
A missing assembly is not always an error because an asset-only mod has no code for StarMap to load.
StarMap must distinguish a normal non-code mod from a code mod whose declared entry assembly is absent before it reports a failure.

Many other operations are not guarded at the mod boundary.
Examples include parsing the StarMap table, loading the assembly, enumerating its types, constructing the mod class, discovering attributed methods, and invoking `[StarMapBeforeMain]`.
An exception from one of these operations leaves no StarMap record and can stop the complete launch before the game log exists.

The same attribution problem continues after game startup.
`ModPatches.OnLoadMod`, `ModLibraryPatches.AfterLoad`, and `ProgramPatcher` invoke mod methods through `MethodInfo.Invoke` without a mod-specific exception record.
An unhandled exception can reach the game monitor, but the resulting stack trace uses .NET type and method names.
A namespace can differ from the folder name that is the mod id, so matching a stack frame to an installed folder is only a guess.

## What the game log can provide

`KSA.Program` writes `KittenSpaceAgency.log` under `Constants.LogsFolderPath`.
`DocumentsPathPatches.Apply` runs first, so this path is under the active instance when StarMap receives an instance path.

The game's last-chance handler records the unhandled exception object.
For a managed exception, that normally includes the exception type, message, inner exception, and stack trace.
This is useful supporting evidence for failures in `[StarMapImmediateLoad]`, `[StarMapAllModsLoaded]`, frame hooks, user interface hooks, and other code that runs after the game monitor starts.

It does not provide these guarantees:

- It cannot record a failure that ends StarMap before the game finishes its diagnostic setup.
- It does not include a trusted mod id.
- It cannot prove that the mod named by one stack frame is the root cause.
- A native crash or immediate process termination can have less information than a managed exception.

Borea should offer the game log when there is no structured StarMap result, but it must not tell the user to disable a mod from a namespace match alone.

## Recommended StarMap report

StarMap should write a machine-readable report under `Constants.LogsFolderPath` after `DocumentsPathPatches.Apply` succeeds.
This keeps the report inside the same instance as the manifest, mods, game log, and crash dumps.
A separate StarMap file avoids a race with the game logger and keeps loader events distinct from game events.
StarMap must create `Constants.LogsFolderPath` before it opens the report because the game creates this directory later and a new instance might not contain it yet.

JSON Lines is a good fit because StarMap can append and flush one complete record at a time.
An exception or process termination then leaves the earlier records readable.
A single JSON document written only at shutdown would lose the exact evidence this feature is intended to keep.

Each StarMap process should have one report file with a unique launch id.
The first record should identify the report format, StarMap version, process id, instance root, and start time.
Each later record should include:

- the launch id,
- the UTC time,
- the mod id when one is known,
- the phase, such as `discovery`, `dependency`, `before-main`, `immediate-load`, `all-mods-loaded`, `frame`, or `unload`,
- a stable result code,
- a short message for a person,
- exception details when an exception occurred.

Stable result codes are necessary because Borea must not parse English console text.
Useful results include `loaded`, `disabled`, `not-code`, `missing-required-dependency`, `entry-assembly-missing`, `entry-type-missing`, and `hook-threw`.
The report should name missing dependency ids as data and should record whether each dependency is optional.

StarMap should use one operation lifecycle for all risky work attributed to a mod.
It should write and flush an `operation-started` record with the mod id, phase, and operation before it loads an assembly, enumerates types, constructs the mod object, discovers methods, or invokes a hook.
A normal return gets a matching `operation-completed` record, and a caught managed exception gets a matching `operation-threw` record with the exception details.
This includes module initializers and constructors because they are mod code even when no StarMap hook has started.
An unmatched `operation-started` record identifies the mod boundary that was active when the report stopped.
It is context for a native crash, `Environment.FailFast`, process termination, or hang, but it is not proof that the named mod caused the failure.

StarMap should flush each record before it calls mod code, continues, or rethrows.
It can catch a managed exception at a mod boundary, write the record, and rethrow it to keep the current failure behavior.
Continuing after an unknown loader or hook exception is a separate policy decision and is not required for diagnostics.

StarMap restarts itself when the user enables newly discovered mods.
The replacement process inherits `STARMAP_INSTANCE_PATH`, but Borea tracks only the original process id today.
The report contract must therefore make a restart chain observable.
Before it starts the replacement, StarMap should create its successor launch id and pass that id to the new process.
After `Process.Start` returns, it should write a `restarting` record with the successor launch id, process id, and process start identity.
The successor header must repeat that identity so Borea can reject a reused process id.
Borea must follow each successor and must not treat the first process exit as the end of the session.
`restarting` is a successful terminal record for the predecessor process because current StarMap calls `Environment.Exit` after it starts the successor.

The report should finish with a `completed` record on a normal exit.
An absent completion record means that the file is partial, not invalid.
Borea considers a linked process complete when the matching operating system process identity no longer exists.
A linked process that has ended without `completed` or `restarting` is a completed partial launch, while a matching process that still exists is still running.

## What Borea can safely tell the user

Borea has no game-log or StarMap-report reader at `ac1ed3c`.
`LoaderLauncher` retains the process id and `HasExited` state only, and `ProcessStarter` does not capture console output.
A Borea implementation therefore needs a report reader and a session-completion rule in addition to the StarMap change.

Borea can give an actionable message when the structured record carries an explicit mod id:

- For `missing-required-dependency`, tell the user which dependency to install or enable before suggesting removal of the dependent mod.
- For `entry-assembly-missing` or `entry-type-missing`, report that the mod installation or release is incomplete or invalid.
- For `operation-threw`, name the mod and operation, show the exception summary, and offer to disable that mod for the next launch when the operation ran mod code.
- For an unmatched `operation-started`, name the active mod and operation as the last known execution context without claiming that it caused the crash.
- For a partial report with no explicit mod failure, show the StarMap report, game log, and crash dump location without naming a cause.

Disabling a mod is a recovery action, not proof of the cause.
Borea should say that the named mod failed during a known loader operation, not that disabling it will always fix the instance.

## Design work still required

This needs an agreed contract with the StarMap maintainer before Borea depends on a path or JSON shape.
The contract belongs to the manager and loader boundary tracked in [discussion #20](https://github.com/KSAModding/content-manager-design/discussions/20).

The smallest complete implementation has two parts:

1. StarMap writes the structured, instance-local, restart-aware report and records explicit mod ids at each hook boundary.
2. Borea reads the report after the complete restart chain ends and presents only the conclusions supported by stable result codes.

No index metadata change is necessary if every compatible loader uses one agreed instance-relative path and report format.
If loaders can choose different paths or formats, the design needs a new loader capability in `[provides]` before a general client can discover the report safely.
