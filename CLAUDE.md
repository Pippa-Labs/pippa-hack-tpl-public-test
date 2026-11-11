# Building a Pippa Agent App

You are building an **Agent App** for Pippa. Assume the person you are helping
has not written one before, may not have Python installed, and would rather not
use the terminal. **Do the work yourself** — clone, write, commit, push — and
tell them what is happening in plain words as you go.

This file is the contract and the rules. Six more files in this repository
are worth opening and are not repeated here:

- `docs/IDEAS.md` — app ideas with free public APIs, and which shapes of app
  actually get used.
- `docs/API_APPS.md` — **read this before writing any app that calls an API.**
  Measured latencies, the failure that actually happens (a 200 containing
  nothing), User-Agent, rate limits, and why there is nowhere to put a key.
- `docs/TROUBLESHOOTING.md` — every build error, by its exact text.
- `docs/HOW_PIPPA_APPS_WORK.md` — what happens between a question and your code.
- `docs/REVIEW_AND_SHARING.md` — **read this before you tell anybody their app
  is live.** A published app is private to its owner until a reviewer approves
  it: how to test it privately, how to share it, how it is submitted, and what
  happens to the approved version when you push a new one.
- `docs/builder-guide.html` — the same ground as `README.md`, as a page the
  builder can read in a browser. Point them at it; do not duplicate it.

You do not have access to Pippa's own source and do not need it.

---

## What you are building

**Pippa** is a personal assistant. When someone asks it something, Pippa
decides whether one of its installed **apps** can answer. An app is a small,
stateless program that does **one job**: Pippa pulls the useful bits out of the
question, hands them to the app, and the app returns facts. Pippa writes the
sentence around them.

*"when's high tide at Brighton?"* → Pippa picks the app, extracts
`place = "Brighton"`, calls the code, and replies using what came back.

A person can also pick the app themselves, by starting the message with `@`
and choosing it from a list. Pippa then skips the picking and calls that app,
whatever the words. Step 2 says what that means for your code.

The app never talks to the user. Inputs in, structured data out.

Three things are enforced by the platform, not by convention:

1. **It remembers nothing.** A fresh instance is built per call and discarded.
2. **It is told nothing about who is asking** — no user id, no account, no
   conversation. Only its inputs, the time, an id for its logs, and whether
   the person picked it by name.
3. **It cannot return anything it did not declare.**

---

## Step 1 — Set the app id and the owner email. Do this first.

**The single most common way a first deploy fails.** The app id is fixed by the
repository name, and the build refuses any mismatch.

```
repository   Pippa-Labs/pippa-hack-tide-times
app id       hack.tide_times
```

The rule: take the repository name, drop the `pippa-hack-` prefix, replace
every hyphen with an underscore, put `hack.` on the front. **Hyphens are not
valid in an app id anywhere.**

Find the repository name with:

```bash
git remote get-url origin
```

Then set it in `manifest.yaml`:

```yaml
app:
  id: hack.tide_times     # must match the repository
```

The template ships `id: hack.your_app_name_here`. That is a placeholder and is
always refused. Replace it before anything else.

### Then the owner email

`owner_email` in `manifest.yaml` is the Pippa account the app belongs to.
**Ask the person for the address they sign in to Pippa with** — the one their
invitation was sent to — and put it in. **Tell them before they give it:** in
a public repository anyone can read `manifest.yaml`, and the address stays in
the git history even if it is changed later.

```yaml
owner_email: sam@mycollege.ac.uk
```

A published app is private to its owner until a reviewer approves it, and this
line is the only thing in the system that says who the owner is. Nothing else
does: publishing knows which repository pushed, and a repository is not an
account.

Get it wrong and nothing fails. The app publishes, the build goes green, and
the app is invisible to everybody — the person you are helping included, so
they cannot install it, cannot test it and cannot submit it. `scripts/check.py`
warns, under **Warnings** in the commit comment, and that warning is the only
sign there is.

So **do not guess the address, and do not use your own idea of their name**.
Ask. If they do not know it yet, say the app will publish and be invisible
until the line is right, and fill it in when they have checked.

---

## Step 2 — The contract

Two files at the top level, and the names matter:

- **`manifest.yaml`** — what the app is and what it can do.
- **`app.py`** — a class called `App` with a `manifest` property and
  `handle(call) -> Result`.

`handle` receives a `Call`:

| Attribute | What it is |
|---|---|
| `call.outcome_id` | Which declared outcome was asked for |
| `call.inputs` | The inputs your manifest declared, extracted from the message |
| `call.context.now` | Current time, timezone-aware. **Use this, never `datetime.now()`** |
| `call.context.request_id` | An id for logging |
| `call.context.explicit` | `True` when the person picked your app by name (`@YourApp`), so Pippa did not choose it. Read it as `getattr(call.context, "explicit", False)` — see below |
| `call.secrets` | A `SecretBundle`. Always empty here |

It returns `Result(data={...}, narrative="...")`. `data` must match the
outcome's declared `output` exactly — every declared field present, nothing
extra, right types. `narrative` is optional: one plain sentence Pippa may use.

To fail, raise `AgentAppError` (or a subclass) with a `user_message`
attribute. Only `user_message` may be shown to a user.

### When the person picks your app by name

In the Pippa chat a person can start a message with `@` and pick your app
from the list (or type `@` and its full name). Pippa then skips choosing an
app: she pulls the inputs out of the message as usual and calls yours,
whatever the words, with `call.context.explicit` set to `True`. Believe them:

- **Never refuse because the message does not look like your example
  phrases.** They have already said it is for you.
- **Refuse only for a missing or invalid input**, with a `user_message` that
  says what to type. They see it word for word, in a sentence like *"Tide
  Times couldn't answer: I do not know where Narnia is."* Pippa does not
  answer in your place, and no other app is tried.
- **Most apps never need to read the flag.** An app that already refuses only
  for missing or invalid input is right either way. The example app does not
  read it.

If yours does read it, read it like this:

```python
picked_by_name = getattr(call.context, "explicit", False)
```

`getattr`, because whether an app gets the flag depends on when it was
published, not on when somebody asks: the SDK your code runs on is fixed when
you publish. An app published before the platform update that added the flag
runs on an older SDK, where `call.context.explicit` does not exist and raises
`AttributeError`. That app is still called when somebody picks it with `@` —
that part needs nothing from the app — but it sees the flag only after you
publish it again: any push whose build goes green. So `False` never proves
the person did not pick you.

---

## Step 3 — Build an app Pippa will actually use

This decides whether the work is wasted, so read it properly.

### Pick a job that suits an app

Measured against the live system: apps that **answer with a fact or a figure**
get used. Apps that mainly **rewrite or generate text** usually do not, because
Pippa answers those herself before an app is ever consulted.

| Works | Does not |
|---|---|
| calculations and conversions | translating |
| live lookups (weather, tides, transport, prices) | summarising, rewriting |
| anything about a named place | writing poems, names, copy |
| anything about a date or a time | definitions, acronyms |
| anything worked out from numbers the user gives | explaining how something works |
| | choosing for them, opinions |

If the person asks for something in the right-hand column, say so plainly and
offer a nearby idea from the left. A translator will mostly sit unused; a "how
do I pronounce this place name" app calling a real API will not.

### Write example phrases the way people type

Pippa chooses between apps by comparing the message against each outcome's
`summary` and `example_phrases`. They are **behaviour, not documentation**. If
they are weak the app is never called, which from the outside is
indistinguishable from it being broken.

```yaml
example_phrases:
  - when is the next high tide      # how a person asks
  - what time is high tide
  - is the tide in or out
```

not `get_tide_data`, not a bare `tide`. What matters:

- Five to ten per outcome. Fewer than three and it will rarely be chosen.
- Carrier phrases, not one specific subject — the subject changes every time.
- Give each outcome its own words; two outcomes sharing vocabulary tie.
- **Avoid words another app owns:** "today", "tomorrow", "this week",
  "my calendar", "what's on" belong to Pippa's diary app, and you will lose.

Write each `inputs[].description` as an instruction to whoever fills the field
in — a model reads it to extract the value from the message. Always say what to
do when the message does not contain it ("return an empty string rather than
guessing"), or it will guess, and a guessed input produces a confidently wrong
answer.

### Give every promise in your summary its own phrases

If your summary says the app does two things, write phrases for **both**. The
summary helps decide whether your app is consulted; the phrases are what the
message is actually compared against. A capability you advertise and give no
phrases to is one your app will be asked for and then lose.

Flight Time's summary promises two things:

> Estimates how long a flight between two airports or cities takes, **and how
> far apart they are**.

Seven of its eight example phrases were about time (`how long is the flight
from`, `flight time from`, `flying time between`), and the words *distance*
and *miles* appeared nowhere. Only the **first four** phrases reach the skill
chooser, taken round-robin across outcomes, and that app has one outcome — so
those four were all the chooser saw, and two of them (`how long is the flight
from` / `...to`) differed by a single word.

`scripts/routing_check.py` does **not** check this, and that was measured
too: a version comparing summary words against outcome words fired on ten of
eighteen real apps and stayed silent on the one real case. Word overlap
cannot tell a second capability ("and how far apart they are") from a detail
of the same one ("and says where the odd pennies land"). So read it yourself,
once, before you ship: take each clause of your summary and point at the
phrase somebody would type to get it.

### Before you blame routing, check whether your app declined

This is the trap, and it cost most of a day on exactly the example above.

Those same distance questions were failing live, so the phrases got rewritten
first. It changed nothing — because routing had never been the problem:

```
skill routing: picked=1 kept=1 unknown=0 agent_apps=True
```

on every one of those turns, including the failures. The app was consulted,
was called, and **declined** — `resolve()` had no Halifax, Shannon or Palma
in its 88-airport table.

**A decline looks exactly like a routing miss from the outside.** Your app
returns SILENT, no `[via …]` badge is attached, and Pippa answers the question
herself in her own voice. Nothing errors, nothing is logged by you, and the
user sees a confident answer that did not come from your app.

So when a question does not reach you, establish which half is broken before
you change anything:

1. **Ask the person to send it again with `@` in front** — start the message
   with `@`, pick the app from the list, same words. That skips routing, and
   a decline stops being silent: instead of answering herself, Pippa replies
   `<App> couldn't answer: <your user_message>`. If it fails now, routing was
   never the problem. If it answers, the app works and routing is the
   problem — and that is all it proves. A forced answer says nothing about
   whether Pippa would choose the app, because it skipped the choosing.
2. Feed the message to your handler in a test. If it raises, your data or
   your inputs are the problem.
3. Only if the handler answers correctly is it worth touching `manifest.yaml`.

The cheap version is step 1 on its own, and it takes ten seconds. Guessing
costs considerably more.

---

## The rules

The build enforces these and names the one you broke.

- **App id must match the repository** (step 1).
- **`persistence: none`.** Do not change it.
- **No `connectors:` and no `secrets:` blocks.** Those ask for a real user's
  credentials, and registration refuses any app that declares them.
- **No database, no file writes, no state between calls.**
- **20 seconds** per call, maximum.
- **Python 3.12 standard library only**, plus `pippa_agentapp_sdk` and
  `PyYAML`. Use `urllib.request`; **`requests` is not installed** where the app
  runs and importing it fails.
- **Under 3 MB.** Never commit a virtualenv or dependencies.
- Name and publisher may not contain "pippa", "official" or "verified".

Apps **can** call public HTTP APIs. Prefer ones needing no key. If one needs a
key, remember the repository is readable — use a free or throwaway key, never a
personal account.

---

## Step 4 — Tests

Write tests in `test_app.py`, through `LocalRunner` rather than calling
`handle` directly: the runner enforces the manifest, so it catches the
output-shape mistakes that otherwise only surface after deployment.

```python
LocalRunner(App()).call(outcome_id, inputs, granted_secrets={},
                        now=FIXED_TIME, request_id="t1").result
```

Pass a fixed `now` so tests do not rot. Keep the network out of them — put the
HTTP fetch behind one method and substitute it. Add `explicit=True` to call
the app the way it is called when the person picks it with `@`; `test_app.py`
has an example.

**The build runs these and will not deploy if they fail.** Do not run them
locally: they import the Pippa SDK, which is not in this repository, and only
the build installs it. Push — the build checks.
**Do not ask the person to install Python or the SDK to run tests.**

---

## Step 5 — Ship it

**Pushing to `main` is the deploy.** The build checks the app (the same
`python scripts/check.py`), publishes it, and reports the result on the commit
you pushed: a commit status called `pippa/publish` and a commit comment.

The loop:

1. **Check.** The Pippa SDK is not in this repository, so nothing here runs
   locally: not the tests, not `scripts/check.py`, not
   `scripts/routing_check.py`. Do not install the SDK or look for it. The
   build runs `scripts/check.py` and the tests and, after a passed check,
   `scripts/routing_check.py`, whose findings never stop the publish. Read
   `routing_check.py` and check `manifest.yaml` against it and against step 3
   before you push: the build only tells you after the app is live.
2. **Push.**

   ```bash
   git add -A
   git commit -m "<what the app does>"
   git push origin main
   ```

   Tell the person: *"I've pushed it. The build takes about two minutes; I'll
   tell you when it is live."*
3. **Wait for the result.** If `gh` is installed and signed in:

   ```bash
   gh run watch "$(gh run list --commit "$(git rev-parse HEAD)" --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
   gh api "repos/{owner}/{repo}/commits/$(git rev-parse HEAD)/status" --jq '.statuses[] | select(.context == "pippa/publish")'
   gh api "repos/{owner}/{repo}/commits/$(git rev-parse HEAD)/comments" --jq '.[-1].body'
   ```

   The run can take a few seconds to appear after the push; if the first
   command finds nothing, wait and repeat it. The status is `success` or
   `failure`; the last comment carries the message.
   Without `gh`, ask the person to open the commit on GitHub
   (`https://github.com/<owner>/<repo>/commit/<sha>`) and paste you the comment
   at the bottom of the page.
4. **Act on the comment.**
   - **Success** — the comment says the app is live. It is live **privately**:
     published, and visible only to the account in `owner_email`. Tell the
     person: open **https://app.getpippa.ai**, go to **Apps**, install the app
     — it is there because it is theirs — and ask Pippa one of its example
     phrases in the chat. If Pippa answers without the app, have them ask
     again with `@` in front before you change anything; step 3, "Before you
     blame routing", says why. When they are happy with it, they press
     **Submit for review** on that page. Step 6. If the comment has a
     **Warnings** section (the `owner_email` warning, routing problems), the
     app is live anyway: fix what it names and push again.
   - **Starts with `CODE_ERROR`** — the app is at fault. Fix what the message
     names and push again. After **5 pushes in a row that end in
     `CODE_ERROR`**, whatever the error, stop and tell the person to ask an
     organiser, with the commit link.
   - **Starts with `PLATFORM_ERROR`** — the problem is on Pippa's side, not in
     the app. **Stop. Do not change the code.** Tell the person it is a platform
     problem: they may re-run the workflow once themselves (Actions tab,
     **Publish to Pippa**, **Run workflow**); you do not re-run it. If it fails
     again, they show an organiser the reference in the message.
   - **The run has ended and there is no `pippa/publish` status or comment** —
     treat it as `PLATFORM_ERROR`: stop, as above.

Never edit anything under `.github/`: the build is managed centrally. A push
that changes `.github/` still goes through, but publishing stops: Pippa only
accepts a publish from the organisers' workflow, unchanged, so an edited
workflow cannot publish the app. Keep the package under 3 MB, and write the
app in Python only. Do not make the person debug any of this.

---

## Step 6 — It is private until a reviewer approves it

Publishing is no longer publishing to everybody. Every push lands as a
**draft**: the app is installable and usable by the account in `owner_email`,
by anyone they share it with, and by the reviewers. Nobody else can see that it
exists. A reviewer approving it is what makes it public.

`docs/REVIEW_AND_SHARING.md` is the full version, written for the builder.
What matters while you are working:

- **"Live" means published, not public.** Say so. A person told their app is
  live, who then cannot find it on a friend's Pippa, will assume it is broken
  and ask you to fix something that is working correctly.
- **You cannot submit it for review from here, and must not try.** It takes a
  service key this repository does not have and a signed-in person this
  repository cannot be. A script that attempted it would fail in a way that
  looked like the app's fault. Tell the person to press **Submit for review**
  on their app's page in Pippa; that is the whole of it.
- **You cannot add testers from here either.** Same reason. Sharing is by
  email address, from the same page.
- **Pushing again never changes the status.** It is not a way to make an app
  public, and a re-push of a version already submitted leaves it submitted —
  so fixing a typo after they press the button does not withdraw them from the
  queue.
- **Once a version is approved, it is frozen.** Pushing that same version is
  refused, with a message saying so. Bump `app.version` in `manifest.yaml`
  first; the new version publishes as a private draft while the approved one
  goes on serving everyone who has it.
- **A rejection comes with a reason.** Fix what it names, push — the same
  version number is fine, a rejected version can be replaced in place — and
  tell them to submit again.
- **A suspended app stops for everybody, including its builder.** It is not
  something to push your way out of. Point them at an organiser.

---

## Things the contract does not make obvious

Each of these cost a working build or an hour of somebody's time.

**A `datetime` output must carry a UTC offset.** The SDK rejects a naive one.
Most weather, transport and finance APIs return `2026-10-29T05:00` with no
offset, so the obvious code passes your tests and fails the output check after
deploying. Attach the offset yourself, or declare the field as a `string` and
return the clock time.

**Pass a timeout to `urlopen`.** It has no default. One unresponsive host hangs
past the 20-second limit and the call is killed with nothing to show the
user. A few seconds per request, and budget for more than one request.

**`AgentAppError`'s `user_message` is a class attribute, not an argument.**
`AgentAppError(user_message="...")` raises `TypeError`. Subclass it:

```python
class PlaceNotFound(AgentAppError):
    user_message = "I could not find anywhere with that name."
    retryable = False
```

The argument you *do* pass is the internal message, which goes to the logs
and never to the user — so put the detail there:

```python
raise PlaceNotFound(f"no coordinates for {place!r}")
```

To name the thing in the message the user sees, set the attribute on the
instance before raising it. The class attribute is only a default:

```python
error = PlaceNotFound(f"no coordinates for {place!r}")
error.user_message = f"I do not know where {place} is."
raise error
```

Worth doing: "I do not know where Narnia is" tells somebody what to retype;
"I could not find anywhere with that name" does not.

**Say "it was not in the message" in a way the type can carry.** The usual
advice — tell the extractor to return an empty string rather than guess —
only works for `type: string`. A `number` or `integer` field has no empty
value, and a model asked for one will invent a plausible figure, which is
worse than nothing because it looks like an answer. For any non-string input
the user might not mention, declare it `required: false` and leave it out:

```yaml
- name: tip_percent
  type: number
  required: false
  description: >-
    The tip as a percentage, if the user named one. Leave this out
    entirely if they did not mention a tip. Never guess a customary amount.
```

Then an absent input is simply missing from `call.inputs`, and
`call.inputs.get("tip_percent")` returns `None`. Note that you must handle
**both** `None` and `""` for an optional *string* field: absent and
"deliberately blank" are different, and both reach you.

**Prefer `required: false` for anything the user might not say.** A missing
*required* input fails inside the runtime before your code runs, and the user
sees a message blaming your app for a question they asked perfectly
reasonably. Required should mean "this app is meaningless without it".

**An output field may be optional.** `output` entries take `required: false`,
and a missing optional field is allowed. You do not have to invent a sentinel
value for a branch that genuinely has nothing to report.

**`app.summary` must never contain the word "by".** The badge Pippa shows is
parsed from `[via <name> <version> by <publisher>]` and splits at the first
"by", so a summary containing it corrupts the attribution — long after a green
build, and nothing checks for it.

**An approved version is frozen.** Re-registering a version that is already
approved is refused outright — other people are running that code, and
replacing it in place would mean the thing a reviewer approved and the thing
users have are different things. Every *other* status can be re-pushed in
place as often as you like, which is what keeps the fix-push-try loop fast.
When a push is refused with `has already been approved and is in use`, the fix
is to bump `app.version` and push again.

**`owner_email` is not `publisher`.** `publisher` is free text shown to users
in the install screen and the badge. `owner_email` is not shown to users and
decides who can see the app before it is approved; in a public repository
anyone can still read it in `manifest.yaml`, and it stays in the git history.
Writing the person's name into
`owner_email`, or their email into `publisher`, each fail silently and
differently.

**Only your app's own files are deployed.** `docs/`, `scripts/`,
`README.md`, `CLAUDE.md`, `pytest.ini`, `requirements-dev.txt` and anything
named `test_*.py` are left out of the package. A lookup table in a folder
called `scripts/` passes every check and is missing in production. Keep data
files beside `app.py`.

**Two or three outcomes is usually right; the limit is vocabulary, not
count.** Outcomes compete with each other for the same question, and two that
share vocabulary tie. Three outcomes with genuinely separate words are fine —
word count, reading time and grade level each have their own — while two that
both say "how long" are already one too many. `scripts/routing_check.py`
measures the overlap and will tell you which pair is in trouble.

**`publisher` is free text and nothing refuses the placeholder.** Put a real
name on it — it is shown on the install screen and in the badge.

**`scripts/check.py` is what the build runs.** It runs only in the build,
after the build installs the Pippa SDK; read it to see what the Check step
refuses. It does *not* cover the publish step's own limits (the 3 MB package
cap, for one), so a green Check step means "the check passed", not "this is
certain to deploy".

**`scripts/routing_check.py` is the other half, and the half that usually
bites.** `check.py` answers "will it publish?". `routing_check.py` answers
"will Pippa ever choose it?" — which is what actually goes wrong, and it goes
wrong silently. The build runs it after a passed check and puts its findings
under **Warnings** in the commit comment, without stopping the publish; read it
and apply it to the manifest before pushing anyway. Do not skip it because the
app is "obviously" about its subject: so was every app that was never called.

**What you import from `pippa_agentapp_sdk`:**

| Name | What it is |
|---|---|
| `Call` | what `handle()` receives — `outcome_id`, `inputs`, `secrets`, `context` |
| `Result` | what `handle()` returns — `data`, `narrative`, **`warnings`** |
| `AgentAppError` | the base error to subclass |
| `Manifest` | the parsed manifest type |
| `load_manifest_file` | read `manifest.yaml` |
| `validate_manifest` | validate it, raising on anything wrong |
| `OutputShapeViolation`, `InputShapeViolation`, `ManifestViolation`, `UndeclaredOutcome` | what the runtime raises at you; useful in tests |
| `LocalRunner` | run your app the way the runtime does, in a test |
| `parse_datetime`, `parse_duration` | the SDK's own parsers for those two types |

**Errors the SDK already defines — do not reinvent these.** Each carries a
sensible `user_message` and the right `retryable`, which is the thing that
decides whether Pippa suggests trying again:

| Name | `retryable` | Its `user_message` |
|---|---|---|
| `RateLimitedError(message, retry_after_seconds=None)` | `True` | "That service is busy. Please try again shortly." |
| `ServiceUnavailableError` | `True` | "That service could not be reached just now." |
| `AuthenticationError` | `False` | "I no longer have access to that account." |
| `ConnectorError` | `False` | "I could not reach that service." |

A `429` is a `RateLimitedError`; an unreachable host or a timeout is a
`ServiceUnavailableError`. Subclass `AgentAppError` yourself only for the
failures that are about **your** subject — a place that does not exist, a
number that could not be read.

There is no HTTP helper, no date library and no rounding helper: the standard
library is the rest of the toolbox.

**Build URLs with `urllib.parse`, never by concatenation.** A place name with
a space in it — "New York", which is most of them — produces a malformed query
string and a `400` from the API, and the bug looks like the API rejecting you
rather than like a missing `quote`.

```python
from urllib.parse import urlencode, quote

url = "https://api.example.com/search?" + urlencode({"q": place, "format": "json"})
url = f"https://api.example.com/page/{quote(title, safe='')}"   # in a PATH
```

**The `duration` type is narrower than ISO-8601.** It accepts days, hours,
minutes and seconds only: `P1D`, `PT90M`, `PT1H30M`, `P1DT2H`. Months and
years (`P1M`, `P1Y`) are refused, because a month is not a fixed length of
time and an app returning one is saying something it cannot mean. If you
need "about two months", return a `number` of days, or a `string`.

**Keep the network out of your tests, with one seam.** Put the fetch behind a
single method and replace it on the instance in the test. An instance
attribute, so the stub takes no `self`:

```python
# app.py
#: Nominatim and the Wikimedia APIs — both recommended in docs/IDEAS.md —
#: answer 403 to a request without a descriptive User-Agent, and urllib
#: sends no useful one. Put it in the seam, so every request has it.
USER_AGENT = "pippa-agent-app-<yourapp>/0.1 (https://github.com/Pippa-Labs)"

def _fetch(self, url: str, timeout: float = 6.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()

# test_app.py
app = App()
app._fetch = lambda url, timeout=6.0: b'{"rates": {"GBP": 0.85}}'
```

A suite that calls the real API fails on a train, and its expected numbers
change daily.

`timeout` is a parameter rather than a constant because a chain of calls
needs a smaller one each — three calls sharing a twenty-second budget cannot
each wait eight seconds. The stub takes it too, or replacing `_fetch` changes
the signature and the first call fails with a `TypeError` that looks nothing
like the thing you changed.

**`urlopen` raises `HTTPError` for any non-2xx, and `HTTPError` is a subclass
of `URLError`.** So the order of `except` clauses is load-bearing: catch
`URLError` first and a 404 becomes "the service is unreachable, try again" —
a wrong message, marked retryable, on a request that will never succeed.

**A timeout is NOT a `URLError`.** `socket.timeout is TimeoutError`, and
`TimeoutError` is a sibling of `URLError` under `OSError`, not a subclass of
it — so a read timeout escapes both clauses above, no `AgentAppError` is
raised, and the user is shown the generic "something went wrong". A timeout is
the most likely network failure there is, so it needs its own clause.

```python
place = call.inputs.get("place", "")

try:
    raw = self._fetch(url)
except urllib.error.HTTPError as exc:       # MUST come first: it IS a URLError
    if exc.code in (400, 404, 422):
        raise PlaceNotFound(f"api rejected {place!r}: {exc.code}")
    if exc.code == 429:
        raise ServiceBusy(f"rate limited: {exc.code}")
    raise ServiceUnavailable(f"upstream returned {exc.code}")
except TimeoutError as exc:                 # NOT a URLError — its own clause
    raise ServiceUnavailable(f"the api did not answer in time: {exc}")
except urllib.error.URLError as exc:        # unreachable, DNS, TLS
    raise ServiceUnavailable(f"could not reach the api: {exc.reason}")
```

**Expect `429`, and do not retry inside the call.** Public APIs rate-limit:
`data.police.uk` answers `429` after roughly five quick requests, and NASA's
`DEMO_KEY` allows 30 an hour across everyone sharing your IP. You have one
twenty-second budget and a user waiting, so there is no room to sleep and try
again. Read `Retry-After` if it is there, raise a retryable error, and say
"try again shortly" — which is true, and is better than a slow failure.

**Money is integer pence, not floats.** `0.1 + 0.2` is `0.30000000000000004`,
and a bill split four ways should not produce `21.137500000000003`. Work in
the smallest unit with `int`, divide with `divmod`, and account for the
remainder rather than letting it vanish — somebody is paying that penny.

```python
total_pence = round(total * 100)
each, left_over = divmod(total_pence, people)
```

Round a `number` output at the end, once: `round(value, 2)`. An un-rounded
float in `data` is shown to the user exactly as it is.

**Ship data files beside `app.py`.** A lookup table of airports or cities is
often the right answer and avoids a network call entirely. It must sit at the
top level — `airports.py` or `airports.json` next to `app.py` — because
`docs/` and `scripts/` are not deployed. Load a JSON file relative
to the module, never the working directory:

```python
DATA = json.loads((Path(__file__).with_name("airports.json")).read_text("utf-8"))
```

Keep the whole package under 3 MB.

## What wastes the most time

- Leaving the app id as the placeholder — refused every time.
- Leaving `owner_email` as the placeholder — *not* refused. The app publishes
  and then nobody can see it, the builder included.
- `datetime.now()` instead of `call.context.now`. `call.now` does not exist.
- Returning a field not in `output`, or omitting one that is.
- Importing `requests`, or any other third-party library.
- Naming the class anything but `App`, or putting files in a subfolder.
- `%-d` in `strftime` — a GNU extension that raises on Windows.
- Catching every exception and returning empty data. Raise `AgentAppError`
  with a `user_message`, so the person is told something true.
- Building a translator, summariser or text generator — see step 3.
