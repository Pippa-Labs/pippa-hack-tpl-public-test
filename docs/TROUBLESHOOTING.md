# Troubleshooting

Every heading on this page is text you will really see. If something has gone
wrong, search this page for a distinctive line from the message.

## Start here

**Tell Claude.** That is the fix for nearly everything below.

Claude Code wrote your app and pushed it. It can read the build log, correct
the file and push again. You do not have to work out which entry applies.

> The last push failed. Please read the build log and fix it.

**You never run anything yourself.** There is no Python to install, no virtual
environment, and no command to type. Pushing to `main` is the deploy. The
**build** — GitHub Actions, the automatic job that runs on every push — installs
Python, checks the app, runs the tests and publishes it. Every error on this
page comes either from that build, or from Pippa once the app is live.

### Where the build log is

1. Open your repository on GitHub.
2. Click the **Actions** tab.
3. Click the newest run, named after your last commit.
4. Click the step with a red cross. The failure is at the bottom of its log.

Copy the address of that page. Giving Claude or an organiser the link beats
describing what you saw.

A green tick means the app published. A red cross means nothing was sent to
Pippa, and whatever you had published before is still live and untouched.

---

# The app id

This is the most common reason a first deploy fails, so it is first.

## `FAIL manifest.yaml declares 'hack.your_app_name_here', but this repository publishes 'hack.tide_times'`

```
 FAIL manifest.yaml declares 'hack.your_app_name_here', but this repository publishes 'hack.tide_times'
       Change `app.id` in manifest.yaml to: hack.tide_times
```

**What it means.** `hack.your_app_name_here` is the placeholder the template
ships with, and it is deliberate. An app id is not something you pick, so the
template refuses to invent one, and the build refuses the placeholder every
time.

Your app id is decided by the name of your repository. Pippa works it out from
the repository the push came from, and your `manifest.yaml` has to agree.

The rule: take the repository name, drop the `pippa-hack-` prefix, turn every
hyphen into an underscore, and put `hack.` on the front.

| Repository | App id |
|---|---|
| `pippa-hack-tide-times` | `hack.tide_times` |
| `pippa-hack-splitthebill` | `hack.splitthebill` |
| `pippa-hack-grid-carbon` | `hack.grid_carbon` |

**The fix.** The second line of the message names the exact id. Tell Claude:

> The build says my app id is wrong. Please set it to the id in the log and
> push again.

Two things worth knowing. The check reads the repository the code was pushed
to, so renaming a folder on a laptop changes nothing. And if the repository is
renamed after a successful publish, the id changes with it and has to be
updated.

## `FAIL the repository is called 'tide-times', which does not start with 'pippa-hack-'`

**What it means.** Only repositories created for the hackathon can publish, and
the name is how that is recognised.

**The fix.** Push to the repository from your invitation email. If you or
Claude created a fresh one instead, ask an organiser — the repository needs
renaming on GitHub, and a new one needs setting up to publish at all.

## `FAIL manifest.yaml is not valid: app.id: 'hack.tide-times' is not a valid dotted lowercase id`

**What it means.** Ids are dotted and lowercase, and **hyphens are not allowed
anywhere** — not in `app.id`, not in an outcome id. Repository names use
hyphens; manifest ids use underscores.

**The fix.** `hack.tide-times` becomes `hack.tide_times`. An outcome id like
`tide-times.next` becomes `tide.next` or `tides.next`.

One extra rule that catches people: the **first** segment of an id may contain
only letters and digits. `working_days.between` is refused; `workdays.between`
is fine.

---

# The manifest

These all come from the build step named **Check the app**. They stop the
deploy, so nothing reaches Pippa.

## `FAIL manifest.yaml is not valid: app.version: '0.1' is not a semantic version`

**What it means.** `app.version` must have three numbers.

**The fix.** `0.1.0`, not `0.1` and not `v0.1.0`.

## `FAIL manifest.yaml is not valid: outcomes[0].inputs[0].type: unknown type 'str' (allowed: string, integer, number, boolean, datetime, duration, timezone, array, object)`

**What it means.** The manifest has its own small type vocabulary and it is not
Python's. `str` is not a type here; `string` is.

**The fix.** Use one of the nine listed types. Two have extra rules:

- `array` must also declare `item_type`, or you get
  `an array must declare item_type`.
- `timezone` must be a real IANA name, such as `Europe/London`.

```yaml
      - name: areas
        type: array
        item_type: string
        description: The flood areas with a warning in force.
```

## `FAIL manifest.yaml is not valid: outcomes[0].output: must be a non-empty list`

**What it means.** Every outcome has to declare at least one output field. An
outcome that returns nothing cannot be described to a user before they install
it, so it is refused.

**The fix.** Declare the fields the app really returns. `inputs` may be empty;
`output` may not.

## `FAIL manifest.yaml is not valid: persistence: an Agent App may not persist anything; the agent is the only data store, so this must be 'none' (got 'session')`

**What it means.** `persistence: none` is the only accepted value, and the
field is required rather than defaulted, so that it has to be written and
meant.

**The fix.** Put it back:

```yaml
persistence: none
```

## `FAIL manifest.yaml is not valid: while scanning for the next token found character '\t' that cannot start any token`

**What it means.** There is a tab character in `manifest.yaml`. YAML forbids
tabs for indentation.

**The fix.** Replace every tab with spaces. Tell Claude, which is a ten-second
job for it.

## `FAIL manifest.yaml is not valid: mapping values are not allowed in this context`

**What it means.** YAML lost track of the structure, nearly always because of
indentation. The line number in the error is where YAML noticed, which is
usually one or two lines after the real mistake.

**The fix.** Tell Claude. If you are reading the file yourself, check these
four things in this order.

1. **Two spaces per level, consistently.** Mixing two and four spaces inside
   one block breaks it.
2. **List items line up.** Every `- name:` under `inputs:` must start at the
   same column.
3. **A colon inside an unquoted value.** `summary: Tides: when and where` is
   invalid. Quote it: `summary: "Tides: when and where"`.
4. **A `>-` block whose text is not indented.** The continuation lines must be
   indented further than the key:

   ```yaml
   # Correct
   summary: >-
     Works out how many days there are until a date you name, and says
     which day of the week it falls on.

   # Wrong - the text is at the same indent as the key
   summary: >-
   Works out how many days there are until a date you name.
   ```

`>-` means "fold these lines into one sentence and drop the trailing newline".
It exists so a long sentence can be wrapped in the file.

## `FAIL tide.times has 2 example phrase(s)`

```
 FAIL tide.times has 2 example phrase(s)
       Pippa chooses your app by comparing the user's message against these.
       With fewer than about three, your app will rarely be picked. Five to
       ten is a good number.
```

**What it means.** Exactly what it says, and it blocks the deploy.

**The fix.** Five to ten per outcome, in a person's words. See
[My app published but Pippa never uses it](#my-app-published-but-pippa-never-uses-it)
for what good phrases look like — that section is worth reading even when the
build is green.

## `WARN owner_email is still the template's placeholder (you@example.com)`

```
 WARN owner_email is still the template's placeholder (you@example.com)
       Your app is PRIVATE until a reviewer approves it, and owner_email
       is the only thing that says who it is private to.
```

**What it means.** It is a **warning** rather than a FAIL, so the app will
publish. What it will not do is turn up anywhere you can see it.

A published app is private to its owner until a reviewer approves it, and
`owner_email` in `manifest.yaml` is the only thing that says who that owner
is — the push comes from a repository, and a repository is not an account.
With the template's placeholder still in it, the app belongs to nobody, and an
app that belongs to nobody is invisible to everybody, you included.

**The fix.** One line, above `app:` in `manifest.yaml`:

```yaml
owner_email: sam@mycollege.ac.uk
```

The address you sign in to Pippa with — the one your invitation was sent to.
In a public repository anyone can read it, and it stays in the git history even
if you change it later. Then push again. `docs/REVIEW_AND_SHARING.md` is the rest of the story.

Two more wordings of the same warning: `WARN manifest.yaml does not say who
owns this app (owner_email)` when the line is missing altogether, and `WARN
owner_email is 'Sam Harper', which is not an email address` when it has a name
in it.

---

# Shapes: inputs and outputs

## `OutputShapeViolation`

You will see one of these, either in the build log when the tests run, or from
Pippa after the app is live:

```
hack.tide_times returned a result that does not match the output shape
declared for 'tide.times': output.next_low: not declared in the manifest
(declared: height_m, next_high, port)
```

```
hack.tide_times returned a result that does not match the output shape
declared for 'tide.times': output.next_high: required value is missing
```

```
hack.tide_times returned a result that does not match the output shape
declared for 'tide.times': output.height_m: expected number, got str
```

**What it means.** `manifest.yaml` promises exactly which fields come back. The
runtime checks every result against that promise and refuses anything that does
not match — a field that was not declared, a declared field left out, or a
field of the wrong type. This is deliberate: a user sees a permission screen
built from the manifest before they install, so the manifest has to be the
truth.

**The fix.** The `output` block and the `return Result(data={...})` line have to
agree. The key names must be identical and the types must match.

```yaml
    output:
      - name: height_m
        type: number
      - name: next_high
        type: datetime
      - name: port
        type: string
```

```python
return Result(data={
    "height_m": 4.2,
    "next_high": "2026-10-22T18:14:00+01:00",
    "port": "Avonmouth",
})
```

Common causes, in rough order of frequency:

- **A field was added to `data` and not to the manifest.** Add it to `output`.
- **A code path returns fewer fields.** An error path that returns
  `{"port": port}` and nothing else still has to return every declared field —
  or should raise `AgentAppError` instead.
- **A field is sometimes absent.** Declare it `required: false`:
  ```yaml
      - name: next_low
        type: datetime
        required: false
  ```
- **`integer` received a `float`.** `3.0` is not an integer here. Use `number`,
  or cast with `int()`.
- **`integer` received a `bool`.** In Python `True` is an `int`; in a manifest
  it is not. Declare `boolean`.
- **`datetime` received a naive timestamp.** A `datetime` must carry a UTC
  offset. `datetime.now()` has none — and the code should be using
  `call.context.now` anyway.
- **`timezone` received something that is not an IANA name.** `Europe/London`,
  not `London` and not `GMT`.

You may also see:

```
hack.tide_times returned dict, not a Result
```

That means `handle` returned a plain dictionary instead of
`return Result(data={...})`.

The tests catch this in the build, because they go through `LocalRunner`, which
enforces the manifest the same way the live runtime does. If this reaches a
user, the tests were not covering that path — ask Claude to add one.

## `InputShapeViolation`

```
inputs do not match the manifest for 'tide.times': inputs.port: required value
is missing
```

```
inputs do not match the manifest for 'tide.times': inputs.postcode: not
declared in the manifest (declared: port, timezone)
```

**What it means.** The same check in the other direction. The app is handed only
the inputs the manifest declares — never more, never fewer than the required
ones. In practice this shows up in the build, while the tests run, because in
live use Pippa fills the inputs from the manifest and cannot invent a field
that was never declared.

**The fix.**

- **"required value is missing".** Either the test should pass that input, or
  the manifest should mark it `required: false` because the app can genuinely
  work without it.
- **"not declared in the manifest".** A key was passed that the manifest does
  not list. Add it to `inputs`, or drop it from the test.
- **A type complaint on `timezone`.** `'London' is not an IANA time zone`.
  Use `Europe/London`.

`required: false` means "may be absent", not "may be empty". An input the user
did not mention arrives as an empty string if the description asked for one —
which is what the description should ask for:

```yaml
        description: >-
          The port the user named. If the message does not name one, return
          an empty string rather than guessing.
```

Without that sentence the extractor will guess, and a guessed input produces a
confidently wrong answer.

## `this app does not serve outcome 'tide.time' (serves: tide.times)`

**What it means.** `UndeclaredOutcome`. Something asked for an outcome id that
is not in the manifest. Usually a typo in a test.

**The fix.** Match the id exactly, including the dot.

## `FAIL app.py does not define a class called App`

```
 FAIL app.py does not define a class called App
       The handler imports `App` from app.py. The name matters.
```

**What it means.** Pippa imports a class called `App` from `app.py`. The name is
part of the contract.

**The fix.** The class has to be called `App`, and `app.py` and `manifest.yaml`
have to sit at the top level of the repository — not in a `src/` folder.

## `ModuleNotFoundError: No module named 'app'`

**What it means.** The build could not find `app.py` where it expects it, at the
top level of the repository. A file in a subfolder is not found and, as it
happens, is not published either.

**The fix.** Move `app.py` and `manifest.yaml` back to the top level.

## `ValueError: Invalid format string`

**What it means.** `%-d` or `%-H` was used in `strftime`. Those are a GNU
extension: they work on some systems and raise on others, so this can appear in
the build or only after the app is live.

**The fix.** Build the string without them:

```python
pretty = f"{target.strftime('%A')} {target.day} {target.strftime('%B')} {target.year}"
```

---

# The build itself

## A step has a red cross

**Symptom.** The Actions run failed. The log ends with
`Error: Process completed with exit code 1`.

**What it means.** Which step failed tells you where to look.

| Step | What failed |
|---|---|
| **Check the dependencies** | `requirements-dev.txt` or a committed wheel file — see [`FAIL requirements-dev.txt line 10 installs the Pippa SDK`](#fail-requirements-devtxt-line-10-installs-the-pippa-sdk) |
| **Get permission to install the Pippa SDK**, **Install the Pippa SDK** | Not something you can fix. Ask an organiser. |
| **Check the app** | A rule above — the manifest, the app id, the class name, or the tests |
| **Publish** | The package or Pippa's own refusal — see below |
| **Get permission to publish** | Not something you can fix. Ask an organiser. |

**The fix.** Open the red step, scroll to the `FAIL` lines, and give Claude the
link to the run. Read the first `FAIL` rather than the last: the ones below it
are often knock-on effects.

## `FAIL the tests fail`

**What it means.** Claude wrote tests in `test_app.py`, and the build runs them
before it publishes. One of them did not pass, so nothing was deployed.

**The fix.** Tell Claude, with the link to the run. The pytest output directly
above that line names the failing test and the assertion.

This is the test suite doing its job. A failing test here is far better than an
app that publishes and then returns the wrong number to a real person.

## `FAIL the Pippa SDK is not installed`

**What it means.** The build's own setup did not complete. The toolkit is not
in the repository: the build installs it at the start of every run, before it
checks the app.

**The fix.** Not something you can fix in the app. Ask an organiser, with the
link to the run.

## `FAIL requirements-dev.txt line 10 installs the Pippa SDK`

**What it means.** The build installs the Pippa SDK itself, at the version your
app runs with, and refuses an app that brings its own. The same step refuses
these too, each with the file and the line:

- `sets a package index or download location` — a `-i`, `--index-url`,
  `--extra-index-url`, `-f` or `--find-links` line. Packages come from PyPI
  only.
- `installs from a file or folder` — a wheel, an archive or a path where a
  package name should be.
- `installs from a URL` — a link (`name @ https://...`, `git+https://...`)
  where a package name should be.
- `is a wheel file in the repository` — a `.whl` file anywhere, `vendor/`
  included.

**The fix.** Tell Claude, with the link to the run. It deletes the line or the
file named under the `FAIL` and pushes again. Nothing else in the app changes.

## `ERROR: the package is 5218 KB; the limit is 3072 KB.`

**Symptom.** The Publish step prints the size, then the five largest files:

```
ERROR: the package is 5218 KB; the limit is 3072 KB.

  Largest files:
    4100 KB  cities.json
     812 KB  logo.png
```

**What it means.** What ships to Pippa must stay under 3 MB. Directly above the
error, the log lists every file that was packaged:

```
Packaged 3 file(s), 14 KB:
  app.py
  manifest.yaml
  ports.json
```

Already left out, so these are never the cause: `.git`, `.github`, `vendor`,
`scripts`, `docs`, `__pycache__`, `.venv`, `venv`, `.pytest_cache`,
`.ruff_cache`, `.idea`, anything ending `.pyc`, `.pyo`, `.whl`, `.zip`,
`.tar.gz` or `.log`, plus `requirements-dev.txt`, `CLAUDE.md`, `README.md`,
`.gitignore`, `pytest.ini` and the `test_*.py` files.

**The fix.** It is a file at the top level — usually a committed data file, a
copied library folder or images. Options, in order of preference:

- Fetch the data at call time from a public API instead of shipping it.
- Trim a large JSON or CSV down to the rows the app uses.
- A library copied into the repository to dodge the import rule will not work
  anyway — see
  [ImportError or ModuleNotFoundError after the app is live](#importerror-or-modulenotfounderror-after-the-app-is-live).

## `ERROR: app.py is not in the package. It must be at the top level.`

**What it means.** `app.py` is in a subfolder, so it was not packaged.

**The fix.** Move `app.py` and `manifest.yaml` to the top level of the
repository, next to the `scripts/` folder.

## `PLATFORM_ERROR: the app was not published because of a problem on the Pippa platform`

```
PLATFORM_ERROR: the app was not published because of a problem on the Pippa
platform, not in the app. Reference: gh-1234567890-1
```

**What it means.** Something on Pippa's side failed: the build could not get
permission to publish, could not reach Pippa, or Pippa itself failed. Your app
is not the cause, and changing it will not help. The workflow in `.github/` is
managed by the organisers. Do not edit it: a push that changes it still goes
through, but Pippa only accepts a publish from the organisers' workflow,
unchanged, so an edited workflow cannot publish the app.

**The fix.** Do not change the code. You may re-run the workflow once
yourself (Claude does not): Actions tab, **Publish to Pippa** on the left,
**Run workflow** on the right. If it fails again, show an organiser the
reference from the message. A run that ended with no `pippa/publish` status and
no comment on the commit counts as the same thing.

## `Pippa refused to publish this app:` ... `hack.` namespace

**Symptom.** The Publish step prints a banner:

```
====================================================================
Pippa refused to publish this app:

  <a message about the app id and the hack. namespace>
====================================================================
```

The exact wording comes from Pippa and may differ. What matters is that it
names your app id.

**What it means.** The signed token says which repository is publishing, and
Pippa derives the app id from that and nothing else. The manifest has to agree.
You cannot publish outside `hack.`, and you cannot publish as somebody else's
app — which is also why nobody can publish as yours.

**The fix.** Make `app.id` match the repository, as described under
[The app id](#the-app-id).

## `Pippa refused to publish this app:` ... secrets or connectors

**Symptom.** The same banner, with a message naming `secrets` or `connectors`.

**What it means.** Those two blocks declare that the app needs a real person's
credentials — a Google account, for example. Hackathon apps may not ask for
them. Nobody at a workshop can consent on a user's behalf to handing a
stranger's app a credential, so registration refuses any app that declares
either.

A related error appears earlier, during **Check the app**, if a secret is
declared without its connector:

```
 FAIL manifest.yaml is not valid: secrets: secret 'google_oauth' names
 connector 'google.calendar', which this manifest does not require
```

**The fix.** Both blocks come out of `manifest.yaml` entirely, and the idea has
to change so it does not need an account. The app can still call the public
internet. If a service wants a key, remember the repository is readable — use a
free or throwaway key, never a personal one. The no-key APIs in
`docs/IDEAS.md` avoid the problem altogether.

## `Pippa refused to publish this app:` ... `has already been approved and is in use`

**Symptom.** The same banner, naming your app and the version you pushed:

```
hack.tide_times 0.1.0 has already been approved and is in use. Bump the
version in manifest.yaml and push again — the new version is yours to test
privately, and the approved one keeps working for everyone until you submit
it and it is approved in turn.
```

**What it means.** A reviewer approved that version, so other people have it.
Replacing its code in place would mean the thing that was approved and the
thing people are running were two different things, which would make approval
worthless. Every other state — draft, pending, rejected — can be re-pushed as
often as you like; approved cannot.

**The fix.** Bump `app.version` in `manifest.yaml`:

```yaml
app:
  version: 0.2.0     # was 0.1.0
```

Push again. The new version publishes privately to you, the approved one goes
on answering questions for everybody who has it, and when you submit the new
one and it is approved it takes over.

---

# Who can see it

A published app is **private to its owner** until a reviewer approves it.
`docs/REVIEW_AND_SHARING.md` is the whole story; these are the three ways it
surprises people.

## My app published and I cannot find it in the Apps list

**Symptom.** The build was green and the commit comment says the app is live.
You are signed in to Pippa, the Apps page does not have it.

**What it means.** One of three things, in order of likelihood.

1. **The page has not reloaded.** It loads the list once. Reload it.
2. **`owner_email` is wrong.** Open `manifest.yaml`. The address there has to
   be the account you are signed in as. If it is the placeholder
   (`you@example.com`), another of your addresses, or has a typo in it, the
   app is private to somebody who does not exist and nobody can see it — you
   included. Fix the line and push again; it is read on every publish.
3. **It is suspended.** See below.

`scripts/check.py` warns about the second one under **Warnings** in the commit
comment, which is cheaper than finding out here.

## My tester cannot see my app

**What it means.** Usually one of:

- **The address.** A share is matched against the address they sign in to
  Pippa with, not the one on their laptop or their badge.
- **They have no Pippa account.** Sharing an app is not an invitation to the
  platform. They need an account of their own first.
- **Their page has not reloaded**, as above.

A tester sees your app, installs it and uses it. They cannot submit it, cannot
add other testers, and cannot see anything else you have published — that is
deliberate, not a fault.

## My app was approved and now it has vanished

**Symptom.** It was public and working. Now it is not in the list, and Pippa
answers as though it had never been installed — for other people and for you.

**What it means.** It has been **suspended**: a reviewer has pulled an app
that was approved. Unlike every other private state this one stops the app for
everybody, its builder included, because the reason to suspend something is
that it should stop.

**The fix.** Your own app's page in Pippa shows the app with the reason it was
suspended. Pushing again does not undo it, and neither does submitting it
again. Read the reason, and talk to an organiser.

---

# After it is published

## My app published but Pippa never uses it

**Symptom.** The run went green. The log said:

```
  YOUR APP IS LIVE IN PIPPA

  App      Tide Times  (hack.tide_times v0.1.0)
  Can do   tide.times
```

You installed it at [app.getpippa.ai/apps](https://app.getpippa.ai/apps). You
asked Pippa a question your app clearly handles. Pippa answered in her own
words, or said she could not help, and your app is nowhere to be seen.

**This is the most common problem, and it is usually not a bug in your code.**
The app was never called. From the outside that looks identical to the app
being broken, which is why this is the longest section here.

First, a quick check: when Pippa uses an app, the answer carries a badge naming
it — `[via Tide Times 0.1.0 by Your Name]`. No badge means your app did not
answer: either it was never called, or it was called and refused, and from the
chat the two look identical.

**Then ask the same question with `@` in front.** Start the message with `@`,
pick your app from the list, and send the same words. That skips routing —
Pippa calls your app whatever the words — so it tells the two apart:

- **It fails with `@` too.** Your app or its inputs are the problem, not
  routing, and nothing in this section will fix it. Pippa says why in one
  sentence; the entry
  [`Tide Times couldn't answer: …`](#tide-times-couldnt-answer-i-could-not-find-a-port-with-that-name)
  below explains each one.
- **It answers with `@`.** Your app works, and the rest of this section is for
  you. That is all it proves: it skipped routing, so it says nothing about
  whether Pippa would pick your app herself. Test that without the `@`, and
  with **Keep using** switched off, or every message goes to your app. The
  badge should say **picked by Pippa**, not **you picked it**.

**Before reading further, ask Claude to check your manifest against the
routing checker.** `scripts/routing_check.py` covers most of what the rest of
this section describes. It needs the Pippa toolkit, which only the build has,
so Claude reads it rather than running it. The build runs it after every
passed check, and its findings appear under **Warnings** in the commit comment
of the published app.

It lists the faults that stop an app being chosen — a phrase that reduces to
one ordinary word, two of your outcomes fighting over the same vocabulary, a
word another installed app already owns, a summary whose first clause says
nothing. Every one of those has been a real
app that was never called.

It cannot promise your app *will* be chosen — the decision is made by a model
reading your manifest alongside the manifests of every other app that person
has installed, which this repository cannot see. What it can do is rule out
the causes that live in your own file. Start there, then come back here.

There are two causes, and they need different fixes.

### Cause 1: the app is the wrong shape

Measured against the live system: apps that **answer with a fact or a figure**
get used. Apps that mainly **rewrite or generate text** usually do not, because
Pippa answers those herself before an app is ever consulted.

| Gets used | Usually does not |
|---|---|
| calculations and conversions | translating |
| live lookups — weather, tides, transport, prices, air quality | summarising, rewriting |
| anything about a named place | writing poems, names, copy |
| anything about a date or a time | definitions, acronyms |
| anything worked out from numbers the user gives | explaining how something works |
| | choosing for the user, opinions |

If your app is in the right-hand column, no amount of rewording will rescue it.
It will keep losing to Pippa's own answer. The fix is a different app, and it
is cheaper than it sounds — ask Claude to repoint the same repository at a
nearby idea from the left-hand column. `docs/IDEAS.md` has more than twenty,
each with a free API that needs no sign-up.

### Cause 2: the example phrases are too weak

Pippa does not have a list of commands. When a message arrives she compares it
against the `summary` and `example_phrases` of every outcome of every installed
app, and picks the best match. `example_phrases` are not documentation. They
are the behaviour that decides whether your app runs.

Work through this in order.

**1. Is it installed?**
Publishing makes the app available. It does not install it. Open
[app.getpippa.ai/apps](https://app.getpippa.ai/apps), find it by name, install
it. If it is not in the list, reload the page — the list is loaded once. If it
is still not there, it is a visibility problem rather than a routing one: see
[My app published and I cannot find it in the Apps
list](#my-app-published-and-i-cannot-find-it-in-the-apps-list).

**2. Ask it using one of your own example phrases, word for word.**
The single most useful test. Open `manifest.yaml` on GitHub, copy a phrase, and
type it exactly.

- **It works.** Good. The app is live and installed, and the only problem is
  that the phrases do not cover how people really ask. Go to step 3.
- **It does not work.** The wording is not the problem. Check that it is
  installed, and that the Actions run really did publish the version you think.

**3. Count the phrases.**
Fewer than three and the build fails. Three is barely enough. **Five to ten per
outcome** is the number that works.

**4. Write how a person asks, not how you would name a function.**

```yaml
# Weak - nobody types this
example_phrases:
  - get_tide_times
  - tide time lookup
  - query tidal data

# Strong - how someone actually asks
example_phrases:
  - when is high tide at
  - what time is low tide
  - is the tide in or out at
  - when does the tide turn
  - how high is the tide at
  - tide times for
```

**5. Use carrier words, not one specific subject.**
The subject changes every time somebody asks. Including it dilutes the match.

```yaml
# Weak - "Avonmouth" will almost never be in the real message
  - when is high tide at Avonmouth

# Strong - the part that is always there
  - when is high tide at
```

**6. Do not use words another app owns.**
"today", "tomorrow", "this week", "my calendar", "my schedule" and "what's on"
belong to **Pippa Diary**, the built-in app that handles the user's calendar. A
phrase containing one of those will usually lose to it, however good the rest
of your app is.

```yaml
# Weak - Pippa Diary will win this
  - what are the tides today

# Strong
  - when is the next high tide at
```

**7. Give each outcome its own vocabulary.**
If two outcomes both say "tide", Pippa has to choose between them by guessing,
and will sometimes pick the wrong one. Make the words clearly different, or
merge them into one outcome with an input saying which variant was wanted.
**One good outcome beats two that tie.**

**8. Fix the `summary` as well.**
The outcome's `summary` is matched too. Write it in the user's words: "Say when
the next high and low tide are at a named port", not "Tidal data retrieval
endpoint".

**9. Check the inputs can actually be extracted.**
If an outcome requires an input that is rarely present in a real message, Pippa
may skip the outcome. Keep required inputs to the ones a person would naturally
say, mark the rest `required: false`, and tell the extractor what to do when a
value is missing:

```yaml
        description: >-
          The port or coastal place the user named. If the message does not
          name one, return an empty string rather than guessing.
```

**10. Push again.**
Routing only changes when the published manifest changes. Ask Claude to edit
`manifest.yaml`, bump `app.version` so the builds can be told apart, and push.
Wait for the green tick before testing again.

### A worked example

Before — published, installed, never used:

```yaml
outcomes:
  - id: tide.times
    summary: Tidal predictions service
    example_phrases:
      - tides
      - tide data today
```

After:

```yaml
outcomes:
  - id: tide.times
    summary: Say when the next high and low tide are at a named port
    example_phrases:
      - when is high tide at
      - what time is low tide
      - is the tide in or out at
      - when does the tide turn
      - how high is the tide at
      - next high tide for
      - tide times for
```

Two phrases became seven. The function-shaped summary became a sentence. The
word "today" went, because Pippa Diary owns it. That is usually the whole fix,
and Claude will do all of it if you say "my app is not being picked".

## The app is used, but it fails

**Symptom.** You can see the badge, or Pippa says the app could not do it. The
reply contains a short sentence such as:

```
I could not work out which date you meant.
```

or, less helpfully:

```
Something went wrong.
```

**What it means.** The app ran and raised. The important rule: **only
`user_message` is ever shown to a user.** The exception type, the message
passed to the constructor and the traceback all stay in the logs. So that
sentence is literally the `user_message` attribute of whatever was raised.

`Something went wrong.` is the default on `AgentAppError`. Seeing it means
either a bare `AgentAppError` with no `user_message`, or a plain Python
exception escaped — a `KeyError`, an `IndexError`, a JSON parse failure — and
was reported generically.

**The fix.** Tell Claude what you asked and what came back, word for word. It
will reproduce the case in a test and fix the handling. What good handling
looks like:

1. **Every failure gets a real sentence.**

   ```python
   class NoSuchPort(AgentAppError):
       user_message = "I could not find a port with that name."
       retryable = False
   ```

2. **Nothing catches everything and returns empty data.** An app that returns
   zeroes when it failed is worse than one that fails, because the user
   believes it.

3. **A service that is down or rate-limiting** has ready-made subclasses:
   `ServiceUnavailableError` ("That service could not be reached just now.")
   and `RateLimitedError` ("That service is busy. Please try again shortly.").
   Both are marked retryable.

4. **Something non-fatal** belongs in
   `Result(data={...}, warnings=("one source was unreachable",))` rather than
   failing the whole call.

## `Tide Times couldn't answer: I could not find a port with that name.`

**Symptom.** You started the message with `@` and picked your app. Instead of
an answer, Pippa replied with one sentence about it.

**What it means.** When somebody picks an app with `@`, Pippa does not choose
and does not fall back. She calls that app, and if it cannot answer she says
so, rather than answering from her own knowledge or trying another app. So the
sentence is a failure that an ordinary question would have hidden. The ones
you are likely to meet:

| Pippa says | What happened |
|---|---|
| `<App> couldn't answer: <a sentence>` | Your app raised. The sentence is its `user_message`. A generic one — `Something went wrong.` or `That app could not answer.` — means it raised without one, or a plain Python error escaped. `That app tried to do something it is not allowed to do.` is not yours: your app returned a result its manifest does not allow, and it was refused. See [`OutputShapeViolation`](#outputshapeviolation). |
| `<App> couldn't tell what you need from that message. Try something like: “<phrase>”.` | Your app was never called: a **required** input was missing, or an input — optional ones included — could not be read as the type your manifest declares (a time zone that does not exist, say). The suggestion is that outcome's first example phrase. |
| anything saying it **took too long** | Over the 20-second limit. See [The app times out](#the-app-times-out). |
| `<App> isn't installed`, `is switched off`, or `There's no app called … that you can use.` | Install it, or switch it on, on the Apps page. If it is not listed there, see [Who can see it](#who-can-see-it). |
| `Apps aren't available right now`, or anything saying **on my side** | Pippa's side, not your app. Do not change the code. Try again, and tell an organiser if it lasts. |

**The fix.** Tell Claude what you asked and what came back, word for word, as
in [The app is used, but it fails](#the-app-is-used-but-it-fails). For the
second row, when a required input was missing, the better fix is usually to
make that input `required: false`. Then your app runs, notices the input is
missing, and the person gets your own sentence saying what to type instead of
a generic one.

If the same question works with `@` and fails without it, your app is fine and
the problem is routing: see
[My app published but Pippa never uses it](#my-app-published-but-pippa-never-uses-it).

**Your app reads `call.context.explicit` and it is never `True`?** Look at the
badge on the answer first. **picked by Pippa** means the message did not go to
your app by name: start it with `@` and pick the app from the list. **you
picked it** means your app was published before the platform update that
added the flag, because the SDK your code runs on is fixed when it is
published. Picking it with `@` still works, but the flag arrives only after
you publish again: push, and once the build is green, the app sees it.

## The app times out

**Symptom.** The user is told the app failed, and nothing in the code raised.

**What it means.** Twenty seconds is a hard limit. Past it the call is killed,
with no chance to tidy up or return a partial answer.

**The fix.** Tell Claude the app is timing out. The usual causes:

1. **A request with no timeout.** Without one, a slow server can hold the call
   far past twenty seconds.

   ```python
   with urllib.request.urlopen(request, timeout=5) as response:
       payload = json.load(response)
   ```

2. **Too many requests.** One or two is comfortable. A request per item in a
   list is not — take a slice.

3. **A slow public API.** Anything doing a geographic search over a large area
   can take many seconds on its own.

4. **Not failing honestly.** Catching the timeout and raising
   `ServiceUnavailableError` tells the user something true instead of leaving
   them waiting for the kill.

## `ImportError` or `ModuleNotFoundError` after the app is live

**Symptom.** The build was green, the tests passed, and every real call fails.
The error names a library:

```
ModuleNotFoundError: No module named 'requests'
```

**What it means.** Where the app runs, only three things are installed: the
Python 3.12 standard library, `pippa_agentapp_sdk` and `PyYAML`.

**The fix.** Tell Claude, which will swap the library for the standard library.

| Instead of | Use |
|---|---|
| `requests` | `urllib.request` plus `json` |
| `beautifulsoup4` | `html.parser`, or an API that returns JSON |
| `pandas` | lists, dicts, `statistics` |
| `numpy` | `math`, `statistics` |
| `python-dateutil` | `datetime.strptime`, `datetime.fromisoformat` |
| `pytz` | `zoneinfo` (standard library since 3.9) |
| `pyyaml` | already available |

A `requests` call becomes:

```python
import json
import urllib.request

request = urllib.request.Request(
    "https://api.frankfurter.app/latest?from=GBP&to=EUR",
    headers={"User-Agent": "pippa-hack-rates (hackathon project)"},
)
with urllib.request.urlopen(request, timeout=5) as response:
    data = json.load(response)
```

**Copying the library into the repository does not work.** The build refuses
wheel files, and a library large enough to matter would break the 3 MB limit
anyway.

## I pushed changes but the app did not update

Work through these in order.

**1. Did the build run?**
Open the Actions tab. If there is no run for the latest commit, the push did
not trigger one. The build runs on a push to `main` and nowhere else. Ask
Claude which branch it pushed to.

**2. Did the run go green?**
A red run means nothing was published and the previous version is still live.
Open the run and read the failing step.

**3. Does the run say "Cancelled"?**
A newer push deliberately cancels an older run, so two quick pushes cannot land
out of order. Look at the newest run.

**4. Are you looking at the right version?**
The success banner names what went live:

```
  App      Tide Times  (hack.tide_times v0.1.0)
  Can do   tide.times
```

Asking Claude to bump `app.version` with every meaningful change costs nothing
and makes this answerable at a glance.

**5. Did the file reach the package?**
Open the Publish step of the run and read the `Packaged N file(s)` list. It
names every file that was sent.

**6. Re-publish without a commit.**
Actions tab, **Publish to Pippa** on the left, **Run workflow** on the right.
That publishes the current state of `main`.

**7. If the thing you changed was routing**, remember routing comes from the
published manifest. A change Claude made but did not push changes nothing.

---

# How to ask for help

Come and find an organiser. Bring these four things, and the answer usually
takes under a minute:

1. **The repository name.** For example `pippa-hack-tide-times`.
2. **What you asked Pippa**, word for word. Copy and paste it; do not
   paraphrase, because the exact wording is often the problem.
3. **What Pippa said back**, word for word, including whether the reply carried
   a badge naming your app.
4. **A link to the Actions run.** Repository on GitHub, Actions tab, newest
   run, copy the address from the bar at the top.

Before you queue: paste the same four things into Claude Code and ask it to
look. It can open the build log, and it fixes most of this page without help.
