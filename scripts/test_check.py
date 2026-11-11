"""Tests for the owner_email warning in scripts/check.py.

NOT a test of your app, and not a file you need to touch. Your app's tests go
in `test_app.py` at the top level; this one covers the checker that ships with
the template, which is why it lives next to it. `pytest` finds it because
`testpaths` in pytest.ini is the whole repository.

It exists because the thing it guards fails silently. A manifest with no
`owner_email` publishes an app that belongs to nobody, which is then invisible
to everybody including its builder, and this warning is the only sign of it
you will ever get. A warning that has quietly stopped firing looks exactly
like a warning with nothing to report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# `scripts/` is not a package, and importing by path keeps this working
# whichever directory pytest is started from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check  # noqa: E402


def manifest(**extra) -> dict:
    """A manifest mapping with only the parts this file cares about."""
    return {"manifest_version": 1, "app": {"id": "hack.tide_times"}, **extra}


def test_it_reads_owner_email_from_the_top_level():
    assert check.owner_email(manifest(owner_email="sam@liftr.studio")) == "sam@liftr.studio"


def test_it_reads_owner_email_from_inside_app():
    """The service that registers your app looks in both places, so this must
    too — otherwise the template warns about an app that is owned perfectly
    well, which teaches builders to ignore the warning."""
    data = manifest()
    data["app"]["owner_email"] = "sam@liftr.studio"
    assert check.owner_email(data) == "sam@liftr.studio"


def test_the_top_level_wins_when_both_are_set():
    """Same order of preference as the registration path. If the two readers
    disagreed, a manifest could warn here and be owned by somebody else
    there."""
    data = manifest(owner_email="top@liftr.studio")
    data["app"]["owner_email"] = "nested@liftr.studio"
    assert check.owner_email(data) == "top@liftr.studio"


def test_surrounding_space_is_not_part_of_the_address():
    assert check.owner_email(manifest(owner_email="  sam@liftr.studio ")) == "sam@liftr.studio"


def test_a_value_that_is_not_text_counts_as_missing():
    """`owner_email: 07700900123` is a number to YAML. Treating it as missing
    matches what registration does with it, which is to record no owner."""
    assert check.owner_email(manifest(owner_email=7700900123)) == ""


def test_nothing_explodes_on_a_manifest_that_is_not_a_mapping():
    assert check.owner_email(None) == ""
    assert check.owner_email([{"owner_email": "sam@liftr.studio"}]) == ""


def test_a_real_address_is_not_a_problem():
    assert check.owner_problem(manifest(owner_email="sam@liftr.studio")) == ""


def test_a_missing_owner_is_a_problem():
    assert "does not say who owns" in check.owner_problem(manifest())


def test_the_shipped_placeholder_is_a_problem():
    """The address this template ships with. Everything else here would be
    academic if the one value every repository starts with slipped through."""
    assert "placeholder" in check.owner_problem(manifest(owner_email="you@example.com"))


def test_every_reserved_example_domain_is_a_problem():
    for domain in check.PLACEHOLDER_DOMAINS:
        assert "placeholder" in check.owner_problem(manifest(owner_email=f"me@{domain}"))


def test_something_that_is_not_an_address_is_a_problem():
    for value in ("Sam Harper", "sam@", "@liftr.studio", "sam@a@b"):
        assert "not an email address" in check.owner_problem(manifest(owner_email=value))
