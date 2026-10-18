"""Explicit solver subprocess entry; network denial is intentionally local here."""

import json
import socket
import ssl  # noqa: F401 — Complete SSL's socket subclass setup before denying new sockets.
import sys

from .api import solve


def no_network(*args, **kwargs):
    raise RuntimeError("network disabled in offline solver child")


def main() -> None:
    """Read one JSON solve request from stdin and write one result to stdout."""
    socket.socket = no_network
    socket.create_connection = no_network
    request = json.load(sys.stdin)
    result = solve(request["level"], stage=request.get("stage", 1), seconds=request["seconds"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
