# Build an app for Pippa

You have about two hours. At the end of it, a program you built will be running
inside a real personal assistant, answering real questions.

**You don't need to install Python, and you don't need to write code yourself.**
Claude Code does the building. You decide what the app should do.

---

## What you're building

**Pippa** is a personal assistant. When someone asks it something, Pippa
decides whether one of its installed **apps** can answer.

An app is a small program that does **one job**. Pippa pulls the useful bits
out of the question, hands them to your app, and your app returns facts. Pippa
writes the sentence around them.

Ask *"when's high tide at Brighton?"* → Pippa picks your app, extracts
`place = "Brighton"`, runs your code, and replies using what you returned —
with a badge showing your app's name.

---

## What you need

| | |
|---|---|
| **Claude Code** | installed and signed in |
| **A GitHub account** you can push from | you'll have had an invitation to your repo — accept it |
| **A Pippa account** | from your Pippa invitation email — **set this up first**, see step 4. The address it arrives at goes in your app's `manifest.yaml`; that is what makes the app yours |

That's it. No Python, no local setup.

---

## Step 1 — Point Claude Code at your repo

Open Claude Code and paste your repository link with what you want built:

> https://github.com/Pippa-Labs/pippa-hack-**yourname**
>
> Here's my repo for a Pippa app. Please clone it and build me an app that
> tells me when the next high tide is at a UK beach.

Claude will clone it, read the instructions that ship inside it, and start
building. It knows the rules, the contract and the common mistakes already.

Keep going in plain language: *"add low tide too"*, *"make the error friendlier
when the beach isn't found"*.

**Stuck for an idea?** Ask Claude: *"what could I build here?"* — or read
`docs/IDEAS.md` in the repo, which has a couple of dozen — most using a free
public API that needs no sign-up, and several needing no API at all.

---

## Step 2 — Claude pushes it

When the app is ready, Claude commits and pushes to `main`. **That push is the
deploy** — there's nothing else to run.

If anything is wrong, the build stops and says exactly what. Tell Claude, and
it will fix it and push again.

---

## Step 3 — You get told when it's published

About two minutes after the push you get **an email** — a comment on your
commit — confirming your app published, with its name and what it can do.

There's also a green tick in the **Actions** tab of your repo if you'd rather
watch it happen.

**It's published to you, not to everybody.** A new app is private until a
reviewer approves it. You can install it and use it in Pippa straight away;
nobody else can even see that it exists. Step 5 is how it becomes public.

That's also why `manifest.yaml` has your email address in it — `owner_email`,
the address you sign in to Pippa with. It's the only thing that says the app
is yours. Get it wrong and the app publishes happily and then **you** can't
see it either, with nothing anywhere reporting an error.

Know this before you push it: in a public repository anyone can read that
address in `manifest.yaml`, and it stays in the git history even if you change
it later.

---

## Step 4 — Try it in Pippa

**Set your Pippa account up early** — before you start building, ideally. It
takes five minutes and needs an **authenticator app** on your phone (Google
Authenticator, Authy, 1Password — any of them).

1. **Create your account** from your Pippa invitation email. The link goes to
   **console.getpippa.ai**, not the app itself.
2. **Set up two-factor.** Not optional. Save the backup codes — they're shown
   once.
3. Open **[app.getpippa.ai/apps](https://app.getpippa.ai/apps)**, find your app
   by name — it's in the list because it's yours — and **install** it.
4. Go to the chat and **just ask it something** — start with one of your own
   example phrases. Installing it *is* how you switch it on: from then on,
   Pippa decides for herself when your app should answer.

When Pippa answers using your app, the reply carries a small green
**via &lt;your app name&gt;** badge. That's how you know it was yours. It also
says who chose it: **picked by Pippa**, or **you picked it**.

**Want to ask your app directly?** Start the message with **@** and pick your
app from the list. Pippa skips deciding and hands the question straight to
your app — the quickest way to check the app itself works. It tells you
nothing about whether Pippa would have picked it on her own, though, so ask
without the **@** too. (Switch on **Keep using** and every message in that
chat goes to your app until you switch it off.)

> **Just published and can't see it?** The Apps page loads the list once.
> Reload the page. Still missing? Check that `owner_email` in `manifest.yaml`
> is the address you're signed in as — a private app you don't own is a
> private app you can't see.

---

## Step 5 — Show it to someone, then submit it

**Show it to someone first.** On your app's page in Pippa you can add a
**tester** by email address, and they can install and use your app while it's
still private. The person next to you asking it something you never thought of
is the most useful ten minutes you'll spend on it.

**Then submit it.** When you're happy, press **Submit for review** on that same
page. A reviewer reads your manifest — the name, the summary, what the app can
do, the phrases that trigger it — and either approves it, which makes it public
to everybody, or sends it back with a reason you can read.

Rejected isn't a verdict on you; it's a list of changes. Fix them, push, submit
again. And you can keep pushing while you wait — it stays in the queue.

There's no command for any of this, and nothing for Claude to run: submitting
is a button because it's you saying "this one's ready", which is a different
thing from a push.

`docs/REVIEW_AND_SHARING.md` has the rest — including how to change an app
that's already approved. (Short version: bump the version number. The approved
one keeps working for everyone while the new one is private to you.)

---

## The one thing that decides whether this works

**Build something that answers with a fact or a figure.**

Pippa only reaches for an app when the question needs something looked up or
worked out. We measured this against the live system:

| Gets used | Usually doesn't |
|---|---|
| calculations, conversions | translating |
| live lookups — weather, tides, transport, prices | summarising, rewriting |
| anything about a named place | writing poems, names, copy |
| anything about a date or time | definitions, acronyms |
| working out numbers someone gives you | explaining how things work |

Apps in the right-hand column tend to sit unused, because Pippa answers those
herself before any app is consulted. It's not a bug in your app — it just never
gets asked.

The second thing that matters is the **example phrases** in your
`manifest.yaml`: they're how Pippa recognises your app. Claude writes them, but
if your app isn't being picked, that's almost always why — ask Claude to add
more, written the way a person would actually type.

---

## How to test your app's routing

"Routing" is Pippa deciding your app is the one to answer. It is the single
most common thing to go wrong, and it fails *quietly* — no error, no log line,
just Pippa answering in her own voice as though your app did not exist.

### First: is it routing, or is it your app?

Ask the question again with **@** in front: start the message with `@`, pick
your app from the list, and send the same words. That skips routing — Pippa
sends the question straight to your app, whatever the words.

- **It fails with @ too?** Then routing is not the problem; your app is.
  Pippa says why in one sentence. Tell Claude what you asked and what came
  back.
- **It works with @?** Then your app is fine and the rest of this section is
  for you. That answer says nothing about routing, though: it skipped it.

### Then run the routing check

You can check most of it without leaving this repo. Ask Claude:

> check my manifest against the routing check

`scripts/routing_check.py` lists the things that stop an app being chosen —
phrases too vague to carry a question, two of your own outcomes fighting over
the same words, vocabulary another app already owns, a summary whose first
clause says nothing. Claude reads it and checks your `manifest.yaml` against
it; the script itself needs the Pippa toolkit, which only the build has. The
build runs it on every push that passes the check, and its findings appear
under **Warnings** in the commit comment.

**It cannot promise your app will be picked**, and nothing that runs in here
could. The decision is made by a model reading your manifest next to the
manifests of every other app that person has installed — which this repository
cannot see. What it can do is catch the faults that have actually caused apps
to go unused.

### The two decisions your question has to survive

| | What it asks | What it reads | What a failure looks like |
|---|---|---|---|
| **Gate 1** | should *any* app answer this? | your summary's first clause, plus a few of your phrases, alongside every other installed app | Pippa answers herself; your app is never consulted |
| **Gate 2** | which app, and which outcome? | all installed outcomes | the wrong app answers, confidently |

Starting a message with **@** and picking your app skips both gates. That is
exactly why it tests your *app* and not your *routing*.

Two things follow from the gates, and they are the whole game:

- **Only the first clause of your summary is read.** Lead with what your app
  works out. Reassurance about what it does not keep belongs at the end.
- **Your example phrases are not documentation — they are behaviour.** Write
  them as someone types: lower case, no question mark, carrying the subject.
  `how long is the flight` works. `how long` matches everything and nothing.

### Then test it for real

Once your app is live, run a test matrix. Three lists, and you need all three:

1. **Should reach your app** — your own phrases. If these miss, Gate 1.
2. **Should reach it, worded differently** — write these yourself, deliberately
   *not* copying your phrases. If your declared phrases pass and these miss,
   your phrases are too literal and only you will ever trigger the app.
3. **Should NOT reach your app** — your subject, but conversation: an opinion
   about it, a request to explain it, a request to *change* something rather
   than be told about it. A hit here is worse than a miss: your app answers a
   question nobody asked.

Send each one in the chat — **without** the @, and with **Keep using**
switched off, or every message goes to your app — and check the reply carries
the green **via &lt;your app name&gt;** badge saying **picked by Pippa**. Keep
the list — when you change your phrases, run it again. That is the whole test,
and it is repeatable.

### And if your app calls an API, test how it fails

Routing decides whether your app is *asked*. This decides whether it gives a
useful answer when the world does not cooperate — which, for an app that calls
somebody else's service, is often.

Claude writes these as tests in `test_app.py`, and the build runs them on
every push, with no account and no network.

**The network is blocked during tests.** `conftest.py` refuses every outbound
socket, so a test that quietly calls the real API fails immediately instead of
passing on your machine and failing on a train. Replace the one method that
does the HTTP:

```python
app = App()
app._fetch = lambda url, timeout=6.0: SAMPLE_RESPONSE
```

Cover these, because each one is a real thing that happens:

| Make the stub do this | And check |
|---|---|
| return the payload you captured from the real API | the happy path, with the real shape |
| return **an empty result** — `[]`, `{}`, a missing key | you say "nothing found", not `IndexError` |
| raise `HTTPError(404)` | you name the thing that was not found |
| raise `HTTPError(429)` | a retryable error saying "try again shortly" |
| raise `TimeoutError` | it is caught — **a timeout is not a `URLError`** |
| hand you input that is not a real place/postcode/topic | a clear sentence, not a guess |

**The empty result is the one that matters.** A timeout is obvious. A `200`
containing nothing is not: Nominatim answers `200` with `[]` for a place that
does not exist, and an app that does `results[0]` turns that into a crash —
or worse, invents an answer. `docs/API_APPS.md` lists the ones that have been
measured.

**Check your parsing against reality once**, before you trust it: ask Claude
to fetch one real response from the API and compare it with the sample in your
tests.

Then, live in Pippa, ask the questions that break it — a place that is not a
place, a topic nobody has written about. You should get a sentence a person
can act on, and no other app should pick the question up instead.

---

## If something goes wrong

- **Tell Claude.** It can read the build log and fix it. That's the fastest
  path for nearly everything.
- `docs/TROUBLESHOOTING.md` — the errors you're most likely to hit.
- `docs/API_APPS.md` — if your app calls an API, read this one. It's the
  difference between an app that works and one that 403s in production.
- `docs/IDEAS.md` — app ideas with APIs that need no key.
- `docs/REVIEW_AND_SHARING.md` — who can see your app before it's approved,
  how to let a friend try it, and how to submit it.
- **Ask an organiser.** Bring your repo name, what you asked Pippa, and what it
  said.

---

## A tip worth taking

**Get something deployed in the first twenty minutes**, before the app is
finished. Ask Claude to set the app id, give it a name, and push the example
app as-is. Watch it go live, install it, ask it a question.

Then you know the whole pipeline works — so when something breaks later, you
know it's your app and not the plumbing.

Nothing is on show while you do it. A published app is private to you until
it's reviewed, so an unfinished one going out costs you nothing at all.
