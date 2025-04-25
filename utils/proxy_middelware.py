from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


class ProxiedHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        headers = list(request.scope.get("headers", []))
        headers_dict = {k.lower(): v for k, v in headers}

        updated = False

        # Host anpassen
        if b"x-forwarded-host" in headers_dict:
            new_host = headers_dict[b"x-forwarded-host"]
            headers = [(k, new_host) if k == b"host" else (k, v) for k, v in headers]
            updated = True

        # Schema anpassen (http/https)
        if b"x-forwarded-proto" in headers_dict:
            request.scope["scheme"] = headers_dict[b"x-forwarded-proto"].decode()

        if updated:
            request.scope["headers"] = headers

        return await call_next(request)
