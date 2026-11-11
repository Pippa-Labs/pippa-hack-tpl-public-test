# Building an app that calls an API

Everything here was measured against the live services from the place your app
actually runs. Where a number appears, it is a reading rather than an estimate.

An app that calls an API is the most useful kind you can build here, and the
one with the most ways to go quietly wrong. Those ways are not the ones people
expect: almost none of the trouble is the request itself.

---

## The budget you are spending

| | |
|---|---|
| Your app is killed after | **20 seconds** |
| Pippa stops waiting after | **20 seconds** |
| Memory | 512 MB |
| Package size | 3 MB |
| Available to import | Python 3.12 standard library, `pippa_agentapp_sdk`, `PyYAML` |

Those two twenty-second limits are the same number, which means an app that
uses its whole budget is racing the thing that called it. Aim for a few
seconds. You have far more room than you think:

```
measured from a Lambda, cold start then warm, November 2026
  nominatim.search       108ms /  7ms      openmeteo.geocode     97ms / 94ms
  nominatim.reverse      126ms /  6ms      openmeteo.forecast    75ms / 71ms
  wikipedia.summary       26ms / 27ms      postcodes.io          24ms / 22ms
  wikimedia.pageviews    109ms / 26ms      police.crimes        103ms / 99ms
  api.nasa.gov           743ms / 673ms     carbonintensity      177ms /180ms
```

A three-call chain to Nominatim costs **342ms cold**. The budget is not your
problem. What follows is.

> **Do not time an API from your laptop.** The same calls above took **10 to 30
> seconds** measured from a developer machine, every time, on the first request
> to each host — a slow resolver at that desk, nothing to do with the API. If
> you conclude "this API is too slow for a 20s budget" from a laptop reading,
> you will throw away a perfectly good idea.

---

## Put the network behind one method

One method does the HTTP. Everything else calls it. This is not tidiness: it
is the only thing that makes the failure modes testable, and the failure modes
are most of the work.

```python
def _fetch(self, url: str, timeout: float = 6.0) -> bytes:
    """Every outbound request goes through here."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()
```

In a test, replace it on the instance — so the stub takes no `self`:

```python
app = App()
app._fetch = lambda url, timeout=6.0: SAMPLE_RESPONSE
```

**`urlopen` has no default timeout.** Without one, a single unresponsive host
holds your app until it is killed, and the user is told it failed with nothing
to show.

---

## The failure you will actually hit

Not a timeout. **A successful response that contains nothing.**

Every one of these is a real, verified behaviour of an API in `IDEAS.md`:

| You asked for | What you get | What a naive app does |
|---|---|---|
| a place that does not exist (Nominatim) | **`200` with `[]`** | `results[0]` → `IndexError`, "the app broke" |
| a place that does not exist (Open-Meteo geocoding) | **`200` with no `results` key at all** | `data["results"]` → `KeyError` |
| this month's crime (data.police.uk) | **`200` with `[]`** — the data lags a month | "no crime was reported here", which is false |
| an article with no views (Wikimedia) | **`404`**, not an empty series | "the service is down", which is also false |
| a topic with no article (Wikipedia) | **`404`** | same |

So: **check for emptiness before you index**, and when a source publishes
late, say which period you actually used. An answer about August presented as
an answer about November is worse than no answer, because nothing looks wrong.

---

## Two APIs refuse you without a User-Agent

Verified: **Nominatim** and **Wikipedia/Wikimedia** both return **`403`** to a
request with no `User-Agent`. Python's `urlopen` does not send a useful one.

```python
USER_AGENT = "pippa-agent-app-<yourapp>/0.1 (https://github.com/Pippa-Labs)"
```

Send it on every request to those hosts. It costs one line and it is the
difference between an app that works and an app that 403s on its first call in
production having passed every test you stubbed.

---

## Rate limits are a design input, not an error case

- **Nominatim** asks for about **one request per second**. If your app makes
  three calls, that is three seconds of deliberate waiting, and it is fine —
  you have twenty. Space them on purpose and write down why, or somebody
  removes the `sleep` as dead weight.
- **NASA `DEMO_KEY`** allows **30 requests an hour and 50 a day, per IP** —
  and your app shares an IP with everything else running there. A `429` is an
  ordinary Tuesday, not an edge case.

Handle `429` as *retryable*, with a message that says to try shortly. Do **not**
retry inside the call: you have one budget and the user is waiting.

---

## Catch `HTTPError` before `URLError`

`urlopen` raises `HTTPError` for any non-2xx, and `HTTPError` is a **subclass**
of `URLError`. Get the order wrong and a `404` is reported as "the service is
unreachable, try again" — a wrong message, marked retryable, about a request
that will never succeed.

```python
try:
    raw = self._fetch(url)
except urllib.error.HTTPError as exc:        # MUST be first
    if exc.code == 404:
        raise PlaceNotFound(f"no such place: {place!r}")
    if exc.code == 429:
        raise ServiceBusy(f"rate limited: {exc.code}")
    raise ServiceUnavailable(f"upstream returned {exc.code}")
except (urllib.error.URLError, TimeoutError, OSError) as exc:
    raise ServiceUnavailable(f"could not reach the api: {exc}")
```

Then give each error a `user_message` that names the thing:

```python
error = PlaceNotFound(f"nominatim returned no match for {place!r}")
error.user_message = f"I could not find anywhere called {place}."
raise error
```

"I could not find anywhere called Narnia" tells somebody what to retype.
"Something went wrong" does not.

---

## API keys: read this before you pick an idea

**There is no secret store available to you.** A hackathon app may not declare
`secrets:` or `connectors:` — registration refuses any app that does — and
nothing injects a value at deploy time. Your repository is the only place a
key could live, and your repository is readable.

So there are exactly three honest options:

1. **Use a no-key API.** Almost every idea in `IDEAS.md` does. This is the
   right answer nearly every time.
2. **Use a public demo key**, where the provider publishes one on purpose.
   NASA's `DEMO_KEY` is the clear example: it belongs to nobody, it is in
   their documentation, and leaking it costs nothing. Put it in one named
   constant with a comment saying exactly that.
3. **Change the idea.** If it only works with a real key, it does not work
   here.

```python
#: NASA's public demo key, published in their own documentation. It belongs to
#: nobody and is rate limited to 30 requests an hour per IP, shared. It is in
#: this file deliberately: there is no secret store for a hackathon app, and a
#: key in a readable repository is a published key.
#:
#: A REAL key would not be safe here. If your app needs one, the idea needs
#: changing — not the hiding place.
NASA_API_KEY = "DEMO_KEY"
```

Never paste a personal key, a key tied to billing, or a key you would mind
seeing on a screen behind you. A public repository is readable by anyone, and
a key you delete stays in the git history.

Test what happens without it. Verified against `api.nasa.gov`:

| | |
|---|---|
| key missing | `403` `{"error": {"code": "API_KEY_MISSING"}}` |
| key wrong | `403` `{"error": {"code": "API_KEY_INVALID"}}` |
| over the limit | `429` |

Three different causes behind one status code. Read the body, not just the
status, and say which one happened.

---

## Do not return everything you were given

One month of street-level crime for central London is **1.25 MB and 3,245
items**. Returning that is three separate mistakes: it blows the result size,
it takes a long time to render, and nobody asked for 3,245 crimes.

Aggregate. Return the total, the top few categories with counts, and the
period you measured. The shape of a good answer is a handful of numbers a
person can read aloud.

---

## Checklist before you push

The build runs `scripts/check.py`, the tests and `scripts/routing_check.py` on
every push; they need the Pippa SDK, which is not in this repository, so
nothing runs locally. Routing findings come back under **Warnings** in the
commit comment only once the app is live, so check `manifest.yaml` against
`scripts/routing_check.py` by reading it before pushing.

And in your tests, with the network stubbed:

- [ ] the happy path, against a payload you captured from the real API
- [ ] empty result — `[]`, a missing key, no items
- [ ] `404`, `403`, `429`
- [ ] a timeout: have the stub raise `TimeoutError`
- [ ] bad user input — a place that is not a place
- [ ] each one raises **your** error subclass with a `user_message`

Call the real API once, by hand, before you trust your parsing. Then delete
that script. A test that reaches the network fails on a train, and its
expected numbers change tomorrow.

---

## Follow-ups: the words still decide

A follow-up like *"and last week?"* is answered by whichever app answered the
turn before it — that is how it is meant to work, and Pippa is given the
transcript to make it possible.

It is not reliable when the follow-up's own words belong to a different
installed app. Measured live, same question, same app, ten runs each:

| Follow-up after an app answered | Reached the right app |
|---|---|
| "and in metres" (after a unit conversion) | **every time** |
| "and over 30 years" (after a loan figure) | **every time** |
| "what about the month before" (after a crime figure) | 2 in 3 |
| **"and last week?"** (after a Wikipedia figure) | **1 in 3** — and it reached *Pippa Diary* twice |

"last week" is Pippa Diary's vocabulary. The transcript pulls one way, the
words pull the other, and the words often win.

**What to do about it.** You cannot stop a user typing "and last week?", and
you should not try. But you can make the first answer carry the subject
forward, so the follow-up is less bare:

> *"The ISS drew 66,222 Wikipedia views over the 30 days to 1 November."*

followed by *"and last week?"* is a much weaker signal than:

> *"**Wikipedia views for the ISS**: 66,222 over the 30 days to 1 November."*

Name your subject in the `narrative` — not just the number. It is the only
part of the previous turn the next one can lean on.

And when you write your own follow-up test prompts, write the realistic ones
rather than the convenient ones. A follow-up that happens to contain your own
app's vocabulary proves very little; the one that contains somebody else's is
the test.

