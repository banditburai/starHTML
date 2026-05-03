"CSRF defense-in-depth: reject unsafe-method requests with mismatched Origin/Referer."

from urllib.parse import urlparse

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _origin_from_referer(referer):
    p = urlparse(referer)
    return f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else ""


class OriginValidation:
    """ASGI middleware that 403s unsafe-method requests when the Origin
    (or Referer fallback) doesn't match ``expected_origins``.

    ``bypass_paths`` is the set of paths that carry their own CSRF token
    (e.g. an OAuth callback's ``state`` parameter). ``on_reject(scope, info)``
    fires on every rejection — wire it to your audit/log/metrics."""

    def __init__(self, app, *, expected_origins, bypass_paths=frozenset(), on_reject=None):
        self._app = app
        self._expected = expected_origins
        self._bypass = bypass_paths
        self._on_reject = on_reject

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self._app(scope, receive, send)

        method = scope.get("method", "").upper()
        if method in _SAFE_METHODS:
            return await self._app(scope, receive, send)

        path = scope.get("path", "")
        if path in self._bypass:
            return await self._app(scope, receive, send)

        headers = scope.get("headers", [])
        origins = [v.decode("latin-1") for k, v in headers if k == b"origin"]
        # RFC 6454: exactly one Origin header. Multiple is a malicious-proxy
        # signal — refuse rather than rely on last-wins parsing.
        if len(origins) > 1:
            origin, referer, candidate = "<multiple>", "", ""
        else:
            origin = origins[0] if origins else ""
            referer = next((v.decode("latin-1") for k, v in headers if k == b"referer"), "")
            # ``Origin: null`` (sandboxed iframes, file://) never matches
            # an expected https://... origin, so treat it as missing.
            usable = origin if origin and origin != "null" else ""
            candidate = usable or _origin_from_referer(referer)

        if candidate and candidate in self._expected:
            return await self._app(scope, receive, send)

        if self._on_reject:
            self._on_reject(scope, {"method": method, "path": path, "origin": origin, "referer": referer})

        body = b"forbidden: origin mismatch\n"
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({"type": "http.response.body", "body": body})
