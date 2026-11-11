"""Everything that stops a push from publishing, checked before you push.

NOT A BUILDER TASK. Builders do not install Python and do not open a terminal.
The build runs this file on every push, after it installs the Pippa SDK; it
does not run locally, because the SDK is not in this repository. Do not put it
back into the builder instructions.

It is worth reading if a build fails, because the message it prints is the one
in the Actions log, and it names the exact line to change.

**Scope.** Everything fatal here is fatal for one reason: it is the set of
things that make the publish step refuse. It deliberately says nothing about
whether your app will ever be *chosen* — that is `scripts/routing_check.py`,
which is advice rather than a gate, because a weak example phrase is a bad app
rather than an invalid one and blocking a push for it would help nobody.

**One WARNING, and it is deliberately not a gate.** A missing or placeholder
`owner_email` does not stop anything: the app registers either way, and when
an organiser has review switched off it does not matter at all — so failing
the build for it would refuse a push the platform is perfectly happy with.
What it does instead is publish an app that belongs to nobody, and an app that
belongs to nobody is invisible to everybody, its builder included. That is the
one failure on this page that produces no error message anywhere, so it gets
the loudest thing short of a gate: a warning, printed twice.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# Windows consoles still default to a legacy code page on many machines, and
# an em dash or a tick in a message is then either mangled or raises
# UnicodeEncodeError mid-print. Forcing UTF-8 here is cheaper than policing
# every string, and `errors="replace"` means the worst case is one odd
# character rather than a traceback instead of the thing you were being told.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
REPO_PREFIX = "pippa-hack-"

# Colour only where it will render. On a plain Windows console, or when the
# output is piped into a file, the escape codes are shown literally and make
# the result harder to read rather than easier.
if sys.stdout.isatty() and os.environ.get("TERM") != "dumb":
    GREEN, RED, YELLOW, PLAIN = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
else:
    GREEN = RED = YELLOW = PLAIN = ""


def ok(message: str) -> bool:
    # Flushed, because the test run below is a subprocess writing to the same
    # terminal. Without this, Python's buffering holds everything back and the
    # tests appear above the checks that ran before them.
    print(f"{GREEN}  OK{PLAIN}  {message}", flush=True)
    return True


def bad(message: str, fix: str = "") -> bool:
    print(f"{RED} FAIL{PLAIN} {message}", flush=True)
    if fix:
        print(f"       {YELLOW}{fix}{PLAIN}", flush=True)
    return False


#: Warnings, kept so they can be said twice. See `warn`.
warnings: list[str] = []


def warn(message: str, fix: str = "") -> None:
    """Something that will not stop the publish, but will cost you an hour.

    Deliberately NOT appended to `results`, so it cannot change the exit code:
    the build runs this file, and a warning that failed the build would refuse
    a push the publisher would have accepted.

    It is collected rather than only printed because of what comes after it —
    the test run writes several screens of its own output, and a warning seen
    only above that has not really been seen. `main` prints the list again
    immediately before the verdict.
    """
    warnings.append(message)
    print(f"{YELLOW} WARN{PLAIN} {message}", flush=True)
    for line in fix.splitlines():
        # rstrip, so a blank line between paragraphs is blank rather than
        # seven spaces — which some terminals show as a stray mark.
        print(f"       {line}".rstrip(), flush=True)


def repo_name() -> str | None:
    """This repository's name on GitHub.

    Taken from the git remote rather than the folder, because the folder can
    be renamed on your machine and the publisher only ever sees the remote.
    """
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        return None
    match = re.search(r"/([^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


def expected_app_id(repo: str) -> str:
    return "hack." + repo[len(REPO_PREFIX):].replace("-", "_")


def owner_email(manifest_data) -> str:
    """`owner_email` out of the manifest — top level, or inside `app`.

    Both places, because the service that registers your app reads both and
    somebody will always write the one the guide does not show. Keeping the
    two readers identical means a manifest that looks owned here is owned
    there.

    It reads the raw YAML rather than the validated `Manifest`, and that is
    not laziness: the SDK keeps only the fields it knows about, and this is
    not one of them. It is read at registration, not at validation, so it
    never reaches the parsed object.
    """
    if not isinstance(manifest_data, dict):
        return ""
    for holder in (manifest_data, manifest_data.get("app")):
        if isinstance(holder, dict):
            value = holder.get("owner_email")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


#: Domains reserved for documentation (RFC 2606). They cannot belong to a real
#: person, so an address at one of them is a field nobody has filled in rather
#: than an address — which is exactly what the template ships.
PLACEHOLDER_DOMAINS = ("example.com", "example.org", "example.net")


def owner_problem(manifest_data) -> str:
    """What is wrong with this manifest's owner, or "" if nothing is.

    A string rather than a bool so the warning can say which of the three
    things happened. "It is missing" and "it is still the placeholder" send
    you to the same line of the same file, but being told the wrong one is
    how you end up reading the right line and not seeing anything wrong.
    """
    value = owner_email(manifest_data)
    if not value:
        return "manifest.yaml does not say who owns this app (owner_email)"
    if value.count("@") != 1 or value.startswith("@") or value.endswith("@"):
        return f"owner_email is {value!r}, which is not an email address"
    if value.rsplit("@", 1)[1].lower().strip(" .") in PLACEHOLDER_DOMAINS:
        return f"owner_email is still the template's placeholder ({value})"
    return ""


def main() -> int:
    print("\nChecking your app before you push\n")
    results = []

    # ── The files that must exist ────────────────────────────────────────────
    for name in ("app.py", "manifest.yaml"):
        path = ROOT / name
        results.append(
            ok(f"{name} is present") if path.exists()
            else bad(f"{name} is missing",
                     f"The publisher expects {name} at the top level of the repository.")
        )
    if not all(results):
        return 1

    # ── The manifest parses, and says what it must ───────────────────────────
    try:
        from pippa_agentapp_sdk import load_manifest_file, validate_manifest

        # The raw mapping is kept as well as the validated object: the owner
        # check below reads a field the SDK does not keep.
        manifest_data = load_manifest_file(ROOT / "manifest.yaml")
        manifest = validate_manifest(manifest_data)
        results.append(ok(f"manifest.yaml is valid ({manifest.app_id} v{manifest.version})"))
    except ImportError:
        bad(
            "the Pippa SDK is not installed",
            "The build installs it before this check; it is not in this "
            "repository. Do not change .github/. If the build says this, "
            "ask an organiser.",
        )
        return 1
    except Exception as exc:
        results.append(bad(f"manifest.yaml is not valid: {exc}"))
        return 1

    # ── The app id matches the repository ────────────────────────────────────
    repo = repo_name()
    if repo is None:
        print(f"{YELLOW}  --  no git remote yet, so the app id cannot be checked{PLAIN}",
              flush=True)
    elif not repo.startswith(REPO_PREFIX):
        results.append(bad(
            f"the repository is called {repo!r}, which does not start with {REPO_PREFIX!r}",
            "Only repositories created for the hackathon can publish.",
        ))
    else:
        expected = expected_app_id(repo)
        if manifest.app_id == expected:
            results.append(ok(f"the app id matches the repository ({expected})"))
        else:
            results.append(bad(
                f"manifest.yaml declares {manifest.app_id!r}, but this repository "
                f"publishes {expected!r}",
                f"Change `app.id` in manifest.yaml to: {expected}",
            ))

    # ── Somebody owns this app ───────────────────────────────────────────────
    #
    # A warning rather than a gate; the module docstring says why. The message
    # is long for a reason: this is the only failure here whose symptom is
    # nothing happening. The app publishes, the build goes green, and the app
    # is then missing from a list it was never going to appear in.
    problem = owner_problem(manifest_data)
    if problem:
        warn(problem,
             "Your app is PRIVATE until a reviewer approves it, and owner_email\n"
             "is the only thing that says who it is private to. Without it, the\n"
             "app publishes and then nobody can see it — including you, so you\n"
             "cannot install it, cannot test it and cannot submit it.\n"
             "\n"
             "Put the address you sign in to Pippa with at the top of\n"
             "manifest.yaml, above `app:`\n"
             "\n"
             "    owner_email: you@yourcollege.ac.uk\n"
             "\n"
             "In a public repository anyone can read that address, and it stays\n"
             "in the git history even if you change it later.\n"
             "\n"
             "docs/REVIEW_AND_SHARING.md explains the rest.")
    else:
        results.append(ok(f"owner_email is set ({owner_email(manifest_data)})"))

    # ── The summary must not contain " by " ──────────────────────────────────
    #
    # The badge under a reply is built as "[via <name> <version> by <publisher>]"
    # and split on the FIRST " by ". A summary containing the word steals the
    # split, and the badge then shows a fragment of your summary where the
    # publisher's name belongs. Nothing else notices, which is why it has to be
    # caught here: the symptom appears days later, on somebody else's screen.
    if " by " in f" {manifest.summary} ".lower():
        results.append(bad(
            'app.summary contains the word "by"',
            'The store badge is parsed as "... by <publisher>" and splits on '
            'the first "by", so the badge would show your summary text as the '
            "publisher. Reword the summary without it.",
        ))
    else:
        results.append(ok('app.summary does not contain "by"'))

    # ── No credentials ───────────────────────────────────────────────────────
    #
    # Registration refuses any hackathon app that asks for a connector or a
    # secret: granting a stranger's app a real user's Google account is not
    # something a workshop can consent to on that user's behalf. Without this
    # check the refusal arrives from the publisher, after the push, in a log.
    for field in ("connectors", "secrets"):
        declared = getattr(manifest, field, None) or ()
        if declared:
            results.append(bad(
                f"manifest.yaml declares {field}",
                f"Hackathon apps may not ask for credentials, and publishing "
                f"refuses any app that does. Remove the `{field}:` block. Your "
                f"app can still call a public API — put the key in your own "
                f"code, and use a free or throwaway one.",
            ))
    if not (getattr(manifest, "connectors", None) or getattr(manifest, "secrets", None)):
        results.append(ok("no connectors or secrets are declared"))

    # ── The app class is where the handler expects it ────────────────────────
    sys.path.insert(0, str(ROOT))
    try:
        import app as app_module

        App = getattr(app_module, "App", None)
        if App is None:
            results.append(bad(
                "app.py does not define a class called App",
                "The handler imports `App` from app.py. The name matters.",
            ))
        elif not hasattr(App, "handle"):
            results.append(bad("App has no handle() method"))
        else:
            results.append(ok("app.py defines App with a handle() method"))
    except Exception as exc:
        results.append(bad(f"app.py could not be imported: {type(exc).__name__}: {exc}"))

    # ── The outcomes have what routing needs ─────────────────────────────────
    for outcome in manifest.outcomes:
        phrases = list(getattr(outcome, "example_phrases", ()) or ())
        if len(phrases) >= 3:
            results.append(ok(f"{outcome.id} has {len(phrases)} example phrases"))
        else:
            results.append(bad(
                f"{outcome.id} has {len(phrases)} example phrase(s)",
                "Pippa chooses your app by comparing the user's message against "
                "these. With fewer than about three, your app will rarely be "
                "picked. Five to ten is a good number.",
            ))

    # ── The tests ────────────────────────────────────────────────────────────
    print(flush=True)
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    results.append(
        ok("the tests pass") if tests.returncode == 0
        else bad("the tests fail", "Publishing runs them too, and will stop here.")
    )

    print()
    # Said again, last. Everything above has scrolled past the test output by
    # now, and on a green run this is the only thing left that needs doing.
    for message in warnings:
        print(f"{YELLOW} WARN{PLAIN} {message}", flush=True)
    if warnings:
        print()

    if all(results):
        print(f"{GREEN}Ready to push.{PLAIN}")
        # Passing here means it will publish. It says nothing about whether
        # the app will ever be reached, and that is the failure builders
        # actually hit, so point at the tool that measures it.
        print("  Next: check manifest.yaml against scripts/routing_check.py — "
              "whether Pippa will ever choose it.\n")
        return 0
    print(f"{RED}Not ready yet — fix the FAIL lines above.{PLAIN}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
