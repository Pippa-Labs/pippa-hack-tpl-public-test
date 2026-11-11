"""Your app. Replace this with whatever you are building.

The shape never changes, whatever your app does:

    class App:
        manifest  -> the parsed manifest.yaml sitting next to this file
        handle(call) -> Result

`handle` is called once per request and must return a `Result` whose `data`
matches the `output` your manifest declares for that outcome — exactly: every
declared field present, nothing extra, right types. The runtime checks it and
refuses anything that does not match, which is deliberate. An app that can
return surprise fields is an app Pippa cannot describe to a user before they
install it.

Three things worth knowing before you start:

**You get the inputs, and nothing about who asked.** No user id, no account,
no conversation. `call.inputs` is what Pippa extracted from the message;
besides it, `call.context` carries only the time, an id for your logs, and
whether the person picked your app by name. This is on purpose: your app
cannot leak what it was never given.

**You keep nothing.** A fresh copy of this class is built for every call and
thrown away afterwards. Writing to a file or a global will appear to work and
then silently stop, because the next call may be on a different machine.

**Errors are part of the design.** Raise `AgentAppError` with a `user_message`
when you cannot answer. That message is the one a user may see; everything
else — the exception type, the traceback — stays in the logs.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from pippa_agentapp_sdk import (
    AgentAppError,
    Call,
    Manifest,
    Result,
    load_manifest_file,
    validate_manifest,
)

MANIFEST_PATH = Path(__file__).with_name("manifest.yaml")


class CannotReadDate(AgentAppError):
    """Raised when the message did not contain a date we can work with."""

    # What a user may be shown. Write it as a sentence, not an error code.
    user_message = "I could not work out which date you meant."
    retryable = False


class App:
    """A small, complete example: count the days until a date."""

    def __init__(self) -> None:
        # Validated at construction, so an app whose manifest is wrong fails
        # immediately and loudly rather than on some later call.
        self._manifest = validate_manifest(load_manifest_file(MANIFEST_PATH))

    @property
    def manifest(self) -> Manifest:
        return self._manifest

    def handle(self, call: Call) -> Result:
        """One request in, one Result out.

        `call.outcome_id` says which of your manifest's outcomes was asked
        for. With one outcome you can ignore it; with several, branch on it.
        """
        if call.outcome_id != "days.until":
            raise AgentAppError(f"this app cannot do {call.outcome_id!r}")

        text = (call.inputs.get("date") or "").strip()
        if not text:
            # The manifest tells the extractor to send an empty string rather
            # than guess, so this is the ordinary "they did not say" path.
            #
            # A missing or unreadable date (here, and in `_parse` below) is
            # the only thing this app refuses for, which is why it never reads
            # `call.context.explicit`, True when the person picked the app
            # with @. That refusal is right whoever chose the app; the test
            # that says so is in test_app.py.
            raise CannotReadDate("no date in the message")

        # `call.context.now` is the current time, supplied by the runtime
        # rather than read from the clock. That is what makes an app testable:
        # a test can say what "now" is.
        today = self._today(call)
        target = self._parse(text, today)
        difference = (target - today).days

        return Result(
            data={
                "days": abs(difference),
                "target_date": target.isoformat(),
                "weekday": target.strftime("%A"),
                "already_passed": difference < 0,
            },
            # Optional. One plain sentence Pippa may use when it writes its
            # reply. Say what you found, not what you did.
            narrative=self._sentence(target, difference),
        )

    @staticmethod
    def _today(call: Call) -> date:
        """The user's today, not the server's.

        A server in UTC and a user in Auckland disagree about what day it is
        for twelve hours out of every twenty-four, and "how many days until"
        is exactly the question that notices.
        """
        # No try/except around ZoneInfo, and that is the point: the manifest
        # declares this input as `type: timezone`, so the runtime has already
        # rejected anything that is not a real IANA zone before your code
        # runs. Declaring the right type is cheaper than validating by hand,
        # and the user gets a better error.
        zone = call.inputs.get("timezone")
        moment: datetime = call.context.now
        if zone:
            moment = moment.astimezone(ZoneInfo(zone))
        return moment.date()

    @staticmethod
    def _parse(text: str, today: date) -> date:
        """Turn what the user wrote into a date.

        Deliberately small — real date parsing is its own project. Handles
        `YYYY-MM-DD`, `25 December`, `December 25` and a bare day number.
        """
        cleaned = text.replace(",", " ").strip()

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        for fmt in ("%d %B", "%B %d", "%d %b", "%b %d"):
            try:
                parsed = datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
            # A bare day and month has no year. "25 December" asked in
            # February means this year; asked in December means this year too,
            # until it has passed, and then it means next year.
            candidate = parsed.replace(year=today.year)
            if candidate < today:
                candidate = candidate.replace(year=today.year + 1)
            return candidate

        if cleaned.lower() == "tomorrow":
            return today + timedelta(days=1)

        raise CannotReadDate(f"could not parse {text!r} as a date")

    @staticmethod
    def _sentence(target: date, difference: int) -> str:
        # Built by hand rather than with `%-d`, which is a GNU extension: it
        # raises ValueError on Windows, where half of you are developing, and
        # the failure would only show up at the last line of a working app.
        pretty = (
            f"{target.strftime('%A')} {target.day} "
            f"{target.strftime('%B')} {target.year}"
        )
        if difference == 0:
            return f"That is today, {pretty}."
        if difference < 0:
            return f"{pretty} was {abs(difference)} days ago."
        if difference == 1:
            return f"{pretty} is tomorrow."
        return f"There are {difference} days until {pretty}."
