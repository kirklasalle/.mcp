"""Network URL validation shared by MCP tools that accept caller-supplied URLs."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


def validate_public_https_url(url: str) -> str:
    """Reject non-HTTPS, credentialed, local, and non-public destinations."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid_url") from exc

    if (
        parsed.scheme.lower() != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or hostname.lower().endswith((".localhost", ".local"))
    ):
        raise ValueError("public_https_url_required")

    try:
        address = ipaddress.ip_address(hostname)
        addresses = [address]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(info[4][0])
                for info in socket.getaddrinfo(hostname, port or 443, type=socket.SOCK_STREAM)
            ]
        except OSError as exc:
            raise ValueError("hostname_resolution_failed") from exc

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("non_public_network_destination")
    return url
