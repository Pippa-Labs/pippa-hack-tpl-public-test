"""No test may touch the network. This makes that true rather than advised.

The template tells you four times to keep the network out of your tests, and
until now nothing enforced it. A test that really calls the API passes on your
machine, passes in the build, and then fails on a train, in a hotel, or on the
morning the service has an outage — and the failure arrives looking like a bug
in your app rather than a bug in your test.

It is also slow, and it makes your expected numbers change overnight.

So every outbound socket is refused while the suite runs. If a test reaches
for the network it fails immediately, with a message naming the host it tried
to reach and what to do instead.

**You do not need to change anything to benefit from this.** It is on by
default for every test in the repository.

If you genuinely want one test to call the real API — to check your parsing
against reality once, by hand — mark it:

    @pytest.mark.network
    def test_the_real_api_still_returns_what_i_expect():
        ...

It is deselected by default (see `pytest.ini`), so it cannot creep into the
build, and nothing in the push loop runs it.
"""

from __future__ import annotations

import socket

import pytest


class NetworkUsedInATest(RuntimeError):
    """A test tried to open a socket."""


_real_socket = socket.socket
_real_create_connection = socket.create_connection


def _refuse(where: str, address=None):
    target = ""
    if isinstance(address, (tuple, list)) and address:
        target = f" to {address[0]}"
    raise NetworkUsedInATest(
        f"a test tried to open a network connection{target} (via {where}).\n"
        "\n"
        "Tests must not call the real API: the suite would then fail offline, "
        "and its expected values would change whenever the data does.\n"
        "\n"
        "Replace the one method that does the HTTP, on the instance:\n"
        "\n"
        "    app = App()\n"
        "    app._fetch = lambda url, timeout=6.0: SAMPLE_RESPONSE\n"
        "\n"
        "If this test is deliberately checking the live API, mark it with\n"
        "@pytest.mark.network and run it with `pytest -m network`."
    )


@pytest.fixture(autouse=True)
def _no_network(request):
    """Refuse every outbound connection for the duration of each test."""
    if request.node.get_closest_marker("network"):
        yield
        return

    class _Blocked(_real_socket):
        def connect(self, address):          # noqa: D102 - stdlib signature
            _refuse("socket.connect", address)

        def connect_ex(self, address):       # noqa: D102
            _refuse("socket.connect_ex", address)

    def _blocked_create_connection(address, *args, **kwargs):
        _refuse("socket.create_connection", address)

    socket.socket = _Blocked
    socket.create_connection = _blocked_create_connection
    try:
        yield
    finally:
        socket.socket = _real_socket
        socket.create_connection = _real_create_connection
