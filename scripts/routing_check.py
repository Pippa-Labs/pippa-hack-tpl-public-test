"""Will Pippa ever actually choose your app?

`scripts/check.py` answers "will this publish?". This answers the question
that decides whether anybody ever sees your work, and it is a different
question with a different answer. An app that is never chosen behaves exactly
like an app that is broken, except that nothing fails and no log line appears.

It needs the Pippa SDK, which is not in this repository. The build runs it
after a passed check and puts its findings under Warnings in the commit
comment, without stopping the publish. Read it too, and check `manifest.yaml`
against it whenever you change the manifest: every rule below is visible from
the manifest alone.

────────────────────────────────────────────────────────────────────────────
HOW A QUESTION REACHES YOUR APP

It has to survive two separate decisions, and they fail for different reasons.

  GATE 1   "should any installed app answer this at all?"
           Pippa shows a model one line per skill. The line for Agent Apps is
           generated from the manifest of EVERY app the user has installed —
           each app's name, the first clause of its summary, and a few of its
           example phrases. If your summary and phrases do not make the shape
           of your question obvious, the whole app layer is skipped and Pippa
           answers from her own head.

  GATE 2   "which app, and which outcome?"
           Pippa lists the installed outcomes and asks a model to pick one.
           Your competition here is every other app the user has installed —
           which, at a hackathon, means everybody else's.

  NEITHER  when the person starts the message with @ and picks your app.
           Then no app is chosen: yours is called, whatever the words. If it
           has several outcomes, which of YOURS runs is still picked from
           their summaries and phrases. That is the fastest test of your
           APP, and no test of routing.

WHAT THIS SCRIPT CAN AND CANNOT TELL YOU

Both gates are decided by a model reading your manifest alongside manifests
this repository cannot see. So no local script can promise your app will be
picked, and any that claimed to would be lying.

What it CAN do is check the properties that make those decisions go wrong,
all of which are visible from your manifest alone: phrases too vague to carry
a question, two of your own outcomes competing for the same words, vocabulary
that another app already owns, a summary whose first clause says nothing.
Every failure below has been a real app that was never called.

It ends by printing the prompts to try once your app is live, which is the
only way to be certain.
"""

from __future__ import annotations

import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent

if sys.stdout.isatty():
    GREEN, RED, YELLOW, DIM, PLAIN = (
        "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m")
else:
    GREEN = RED = YELLOW = DIM = PLAIN = ""

# ── Reference data ──────────────────────────────────────────────────────────

#: Words carrying no subject of their own. A copy of the list the agent's
#: matcher uses, so "how many content words is this phrase" means the same
#: thing here as it does there. Data, not a second matching algorithm — this
#: script never scores anything.
STOPWORDS = frozenset("""
a an the my me i i'm im is are was were be been do does did doing done
have has had got get getting of on in at to for with and or but if then
this that these those it its so just please can could would will shall
about any some what whats what's
""".split())

#: Vocabulary that first-party apps and Pippa's own skills already own. A
#: phrase built on one of these competes with something installed for
#: everybody, and loses. Add your own subject word instead of relying on one
#: of these to carry the phrase.
RESERVED = {
    "calendar": "Pippa Diary",
    "diary": "Pippa Diary",
    "meeting": "Pippa Diary",
    "schedule": "Pippa Diary",
    "today": "Pippa Diary / the current date",
    "tomorrow": "Pippa Diary / the current date",
    "remind": "the reminder skill",
    "reminder": "the reminder skill",
    "alarm": "the reminder skill",
    "remember": "the memory skill",
    "forget": "the memory skill",
    "search": "Pippa Web Search",
    "google": "Pippa Web Search",
    "news": "Pippa Web Search",
}

#: How much of your summary the chooser actually sees. pippa_pa clips it to
#: roughly this, first sentence first, because a summary written for the
#: install screen may open with three sentences of reassurance.
SUMMARY_CLIP = 110

#: How many of your phrases reach the Gate 1 line, taken round-robin across
#: your outcomes. Writing twenty will not get twenty in front of the chooser.
PHRASES_SHOWN = 4

_WORD = re.compile(r"[a-z0-9']+")


def content_words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in STOPWORDS}


# ── Reporting ───────────────────────────────────────────────────────────────

errors: list[str] = []
warnings: list[str] = []


def fail(line: str, fix: str = "") -> None:
    errors.append(line)
    print(f"{RED} FAIL{PLAIN} {line}")
    if fix:
        print(f"       {DIM}{fix}{PLAIN}")


def warn(line: str, fix: str = "") -> None:
    warnings.append(line)
    print(f"{YELLOW} WARN{PLAIN} {line}")
    if fix:
        print(f"       {DIM}{fix}{PLAIN}")


def good(line: str) -> None:
    print(f"{GREEN}  OK {PLAIN} {line}")


# ── Checks ──────────────────────────────────────────────────────────────────


def check_summary(manifest) -> None:
    summary = " ".join((manifest.summary or "").split())
    if not summary:
        fail("app.summary is empty",
             "It is the one line the chooser reads about your app.")
        return

    clipped = summary.split(". ")[0]
    if len(clipped) > SUMMARY_CLIP:
        clipped = clipped[:SUMMARY_CLIP].rsplit(" ", 1)[0]
    words = content_words(clipped)
    if len(words) < 4:
        fail(f"the first clause of app.summary says very little: {clipped!r}",
             "The chooser sees roughly the first sentence and nothing more. "
             "Lead with what the app works out, not with reassurance about "
             "what it does not keep.")
    else:
        good(f"summary leads with something specific ({len(clipped)} chars seen)")

    tail = summary[len(clipped):].strip(" .")
    if tail:
        print(f"       {DIM}chooser sees: {clipped!r}{PLAIN}")
        print(f"       {DIM}not seen:     {tail[:70]!r}...{PLAIN}")


def check_phrases(manifest) -> None:
    by_outcome: dict[str, list[str]] = {}

    for outcome in manifest.outcomes:
        phrases = [p for p in (outcome.example_phrases or []) if p.strip()]
        by_outcome[outcome.id] = phrases

        if len(phrases) < 3:
            fail(f"{outcome.id}: {len(phrases)} example phrase(s)",
                 "Fewer than three and the outcome is rarely matched. "
                 "Five to ten, written the way a person types.")
        elif len(phrases) > 12:
            warn(f"{outcome.id}: {len(phrases)} example phrases",
                 f"Only about {PHRASES_SHOWN} per app reach the chooser's "
                 "line. Past ten you are writing for nobody.")
        else:
            good(f"{outcome.id}: {len(phrases)} example phrases")

        seen: dict[frozenset, str] = {}
        for phrase in phrases:
            words = content_words(phrase)

            if len(words) < 2:
                fail(f"{outcome.id}: {phrase!r} reduces to "
                     f"{sorted(words) or 'nothing'}",
                     "Once ordinary words are discarded this carries one "
                     "subject word or none, so it matches almost any "
                     "question or none at all. Add the subject: not "
                     '"how long", but "how long is the flight".')

            if phrase.strip().endswith("?"):
                warn(f"{outcome.id}: {phrase!r} ends with a question mark",
                     "Phrases are matched against what people type, which is "
                     "usually unpunctuated. Drop it.")

            if phrase != phrase.lower():
                warn(f"{outcome.id}: {phrase!r} is not all lower case",
                     "People type in lower case. Match that.")

            if len(phrase.split()) > 9:
                warn(f"{outcome.id}: {phrase!r} is {len(phrase.split())} words",
                     "A long phrase only matches a long question. Keep the "
                     "carrier, drop the specifics.")

            key = frozenset(words)
            if key and key in seen and seen[key] != phrase:
                warn(f"{outcome.id}: {phrase!r} and {seen[key]!r} are the "
                     "same phrase once ordinary words are removed",
                     "One of them is doing no work. Spend it on a different "
                     "way of asking.")
            seen[key] = phrase

            for word in sorted(words & set(RESERVED)):
                fail(f"{outcome.id}: {phrase!r} uses {word!r}, which belongs "
                     f"to {RESERVED[word]}",
                     "That app or skill is installed for everyone and will "
                     "win the word. Rephrase around your own subject.")

    check_siblings(by_outcome)


def check_siblings(by_outcome: dict[str, list[str]]) -> None:
    """Two of your own outcomes must not compete for the same question.

    This is the one routing problem entirely within your control, and the one
    the docs warn about most: when two outcomes tie, something has to break
    the tie, and whatever breaks it is not your intent.
    """
    ids = list(by_outcome)
    if len(ids) < 2:
        return

    for i, left in enumerate(ids):
        for right in ids[i + 1:]:
            lw = set().union(*(content_words(p) for p in by_outcome[left])) \
                if by_outcome[left] else set()
            rw = set().union(*(content_words(p) for p in by_outcome[right])) \
                if by_outcome[right] else set()
            if not lw or not rw:
                continue
            shared = lw & rw
            overlap = len(shared) / min(len(lw), len(rw))

            exact = {frozenset(content_words(p)) for p in by_outcome[left]} & \
                    {frozenset(content_words(p)) for p in by_outcome[right]}
            if exact:
                fail(f"{left} and {right} share an identical phrase",
                     "Whichever is listed first will take every question of "
                     "that shape. Give each outcome its own words.")
            elif overlap > 0.5:
                fail(f"{left} and {right} share {int(overlap * 100)}% of their "
                     f"vocabulary: {sorted(shared)[:6]}",
                     "A question using those words is a coin toss between "
                     "your own two outcomes.")
            elif overlap > 0.3:
                warn(f"{left} and {right} share {sorted(shared)[:5]}",
                     "Close. Make sure each outcome has at least one word "
                     "the other never uses.")
            else:
                good(f"{left} and {right} are distinct")


def check_identity(manifest) -> None:
    if manifest.app_id.endswith("your_app_name_here"):
        fail("manifest.yaml still has the placeholder app id",
             "Nothing publishes until app.id is set. scripts/check.py prints "
             "the exact value for this repository.")
    if manifest.name.strip().lower() in ("days until", "your app", ""):
        warn(f"the app is still called {manifest.name!r}",
             "The name is shown to the chooser and on the badge.")


# ── The part no script can do for you ───────────────────────────────────────


def print_test_matrix(manifest) -> None:
    print(f"\n{DIM}{'─' * 74}{PLAIN}")
    print("TRY THESE ONCE IT IS LIVE\n")
    print("Install your app, then send each of these in the chat and check the")
    print(f"reply carries the {GREEN}via {manifest.name}{PLAIN} badge.\n")

    # The @ check comes first: it splits "never chosen" from "chosen and
    # refused", which look identical from the chat. Picking the app with @
    # skips both gates, so a pass proves the app works and nothing more.
    first = next((p for o in manifest.outcomes
                  for p in (o.example_phrases or []) if p.strip()), "")
    example = f"@{manifest.name} {first}".rstrip()
    print("  First, with @: does your app itself work?")
    print(f"  {DIM}(start the message with @ and pick {manifest.name}, then "
          f"finish the{PLAIN}")
    print(f"  {DIM} question the way a person would. That skips routing.){PLAIN}")
    print(f"    - {example} ...")
    print(f"  {DIM}If it fails, the fault is your app or its inputs, and no "
          f"change to{PLAIN}")
    print(f"  {DIM}the phrases will fix it. If it answers, your app works — and "
          f"that is{PLAIN}")
    print(f"  {DIM}all it proves, because the @ skipped routing.{PLAIN}\n")
    print("  Everything below goes WITHOUT the @, and with Keep using switched")
    print(f"  off. The badge should say {GREEN}picked by Pippa{PLAIN}, not "
          "you picked it.\n")

    print("  Should reach your app")
    for outcome in manifest.outcomes:
        for phrase in list(outcome.example_phrases or [])[:3]:
            print(f"    - {phrase}")
    print()
    print("  Should reach your app, but are NOT phrases you declared")
    print(f"  {DIM}(write three yourself — the same questions asked differently."
          f"{PLAIN}")
    print(f"  {DIM} If these miss, your phrases are too literal.){PLAIN}")
    print("    - ...\n    - ...\n    - ...\n")
    print("  Should NOT reach your app")
    print(f"  {DIM}(your subject, but conversation: an opinion about it, a "
          f"request to{PLAIN}")
    print(f"  {DIM} explain it, a request to CHANGE something rather than be "
          f"told){PLAIN}")
    print("    - ...\n    - ...\n")
    print(f"{DIM}A miss on 'Should reach your app' is a Gate 1 problem: "
          f"usually the{PLAIN}")
    print(f"{DIM}summary or the phrases. A hit on 'Should NOT reach your app' "
          f"is a false{PLAIN}")
    print(f"{DIM}positive, which is worse — your app answers a question nobody "
          f"asked,{PLAIN}")
    print(f"{DIM}in a confident voice.{PLAIN}")


def main() -> int:
    print("\nWill Pippa choose your app?\n")
    try:
        from pippa_agentapp_sdk import load_manifest_file, validate_manifest

        manifest = validate_manifest(load_manifest_file(ROOT / "manifest.yaml"))
    except ImportError:
        print(f"{RED} FAIL{PLAIN} the Pippa SDK is not installed")
        print("       It is not in this repository. Read this file and check "
              "manifest.yaml against it instead.")
        return 1
    except Exception as exc:
        print(f"{RED} FAIL{PLAIN} manifest.yaml is not valid: {exc}")
        print("       Fix that first: the build's check names the line.")
        return 1

    check_identity(manifest)
    check_summary(manifest)
    check_phrases(manifest)
    print_test_matrix(manifest)

    print()
    if errors:
        print(f"{RED}{len(errors)} problem(s) that will stop your app being "
              f"chosen.{PLAIN}")
        if warnings:
            print(f"{YELLOW}{len(warnings)} warning(s) as well.{PLAIN}")
        print()
        return 1
    if warnings:
        print(f"{YELLOW}{len(warnings)} warning(s). Worth a look, none fatal."
              f"{PLAIN}\n")
        return 0
    print(f"{GREEN}Nothing here will stop your app being chosen.{PLAIN}")
    print("Now try the prompts above in the real thing.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
