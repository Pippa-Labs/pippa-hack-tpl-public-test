"""Tests for your app. Run them with `pytest`.

Keep these. Publishing runs them, and a repository whose tests fail does not
deploy — which is the fastest feedback you will get all day, because the
alternative is finding out from a user that your app answers wrongly.

`LocalRunner` is the same code the production runtime uses to call your app.
So a call that works here works deployed, and — more usefully — a `Result`
that violates your manifest fails here exactly as it would in production.
That is the whole reason to test through the runner rather than calling
`App().handle(...)` directly.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pippa_agentapp_sdk import LocalRunner, OutputShapeViolation

from app import App, CannotReadDate

# A fixed "now", so a test that passes today still passes next March.
# 21:00 UTC on purpose: it is already the next day in New Zealand, which is
# what makes the time zone test below mean anything. At 09:00 UTC it is still
# the same day everywhere that matters, and the test would pass whether or not
# the code handled time zones at all.
NOW = datetime(2026, 10, 22, 21, 0, tzinfo=timezone.utc)


def call(inputs: dict, outcome: str = "days.until", *, explicit: bool = False):
    """Run one outcome the way the runtime does, and return the Result.

    `granted_secrets` is required even though a hackathon app never has any —
    the runner takes it on every call, so an empty dict is how you say "none".

    `explicit=True` calls the app the way Pippa does when the person picked
    it by name (`@Days Until ...`) instead of Pippa choosing it. The app sees
    it as `call.context.explicit`.
    """
    return LocalRunner(App()).call(
        outcome, inputs, granted_secrets={}, now=NOW, request_id="test-1",
        explicit=explicit,
    ).result


def test_the_manifest_is_valid():
    """The first thing to break, and the easiest to miss.

    `App()` validates manifest.yaml as it is constructed, so this fails the
    moment the manifest is malformed — before anything else has a chance to
    produce a more confusing error.
    """
    app = App()
    assert app.manifest.app_id.startswith("hack.")
    assert [o.id for o in app.manifest.outcomes] == ["days.until"]


def test_it_counts_the_days():
    result = call({"date": "2026-12-25"})
    assert result.data["days"] == 64
    assert result.data["target_date"] == "2026-12-25"
    assert result.data["weekday"] == "Friday"
    assert result.data["already_passed"] is False


def test_a_date_written_in_words_works():
    result = call({"date": "25 December"})
    assert result.data["target_date"] == "2026-12-25"


def test_a_date_already_gone_rolls_to_next_year():
    """`1 January` asked in October means the January that is coming."""
    result = call({"date": "1 January"})
    assert result.data["target_date"] == "2027-01-01"
    assert result.data["already_passed"] is False


def test_the_users_timezone_decides_what_today_is():
    """21:00 UTC is already tomorrow in Auckland.

    Worth a test of its own: it is the bug every date app has, it only shows
    up for users in some parts of the world, and it is invisible if you only
    ever test from one place.
    """
    here = call({"date": "2026-10-23"}).data["days"]
    there = call({"date": "2026-10-23", "timezone": "Pacific/Auckland"}).data["days"]
    assert here == 1    # still the 22nd in UTC
    assert there == 0   # already the 23rd in Auckland


def test_a_made_up_timezone_never_reaches_the_app():
    """The platform checks declared types before your code runs.

    `type: timezone` in the manifest means the runtime validates it. So your
    app does not need to — and should not, because a hand-rolled check here
    would be dead code that looks load-bearing.
    """
    from pippa_agentapp_sdk import InputShapeViolation

    with pytest.raises(InputShapeViolation):
        call({"date": "2026-12-25", "timezone": "Mars/Olympus"})


def test_no_date_is_an_error_a_user_can_read():
    with pytest.raises(CannotReadDate) as failure:
        call({"date": ""})
    # `user_message` is the only part a user may be shown, so it is the part
    # worth asserting on. The rest stays in the logs.
    assert failure.value.user_message == "I could not work out which date you meant."


def test_nonsense_is_refused_rather_than_guessed():
    with pytest.raises(CannotReadDate):
        call({"date": "a week on Thursday-ish"})


def test_picked_by_name_it_answers_and_refuses_as_usual():
    """`@Days Until ...` in the chat: the person picked this app themselves.

    Then nothing checks whether the message suits the app. It is called
    whatever the words, and `call.context.explicit` is True. The right
    response is the ordinary one: answer what you can, and refuse only for a
    missing or unreadable input, with a sentence that says what was wrong.
    Never refuse because the message does not look like your example phrases
    — the person has already told you it is for you.

    This app never reads the flag, because it never needed to: it already
    refuses only for a missing or unreadable date. If yours does, read it as
    `getattr(call.context, "explicit", False)`. An app published before the
    platform update that added the flag runs on an SDK that does not have
    it, until you publish it again.
    """
    picked = call({"date": "2026-12-25"}, explicit=True)
    assert picked.data == call({"date": "2026-12-25"}).data

    with pytest.raises(CannotReadDate) as failure:
        call({"date": ""}, explicit=True)
    assert failure.value.user_message == "I could not work out which date you meant."


def test_the_runner_enforces_the_manifest(monkeypatch):
    """Proof that the contract is real, and the reason to test through it.

    An app returning a field it did not declare is refused. You will meet this
    error if you add something to `data` and forget to add it to `output` in
    manifest.yaml — which is the single most common way a first app fails
    after it deploys.
    """
    from pippa_agentapp_sdk import Result

    monkeypatch.setattr(
        App, "handle", lambda self, c: Result(data={"surprise": "hello"})
    )
    with pytest.raises(OutputShapeViolation):
        call({"date": "2026-12-25"})
