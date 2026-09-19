from __future__ import annotations

import ipaddress
import socket
import urllib.request
from urllib.parse import urlparse


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None):
        raise ValueError("Source URL must be public HTTP(S), without credentials")
    try:
        addresses = {row[4][0] for row in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as exc:
        raise ValueError("Source hostname could not be resolved") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("Source URL resolves to a non-public address")


class PublicRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_public(request: urllib.request.Request, timeout: float):
    validate_public_url(request.full_url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), PublicRedirectHandler())
    return opener.open(request, timeout=timeout)
