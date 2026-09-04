"""One error shape for the whole API.

Clients on three platforms parse these responses. Every failure - a bad
request, a missing task, a rate limit, an unexpected crash - comes back in the
same envelope so no client has to special-case anything.
"""

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Machine-readable labels so a client can react without parsing prose.
KINDS = {
    400: "bad_request",
    401: "unauthenticated",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "invalid_request",
    429: "rate_limited",
    500: "internal_error",
}


def error_body(status_code, message, **extra):
    body = {"error": {"status": status_code,
                      "kind": KINDS.get(status_code, "error"),
                      "message": message}}
    body["error"].update(extra)
    return body


def install_error_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return JSONResponse(status_code=error.status_code,
                            content=error_body(error.status_code, error.detail),
                            headers=getattr(error, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Say which fields were wrong; clients show this to a person.
        fields = [{"field": ".".join(str(part) for part in item.get("loc", [])[1:]),
                   "problem": item.get("msg", "")}
                  for item in error.errors()]
        return JSONResponse(
            status_code=422,
            content=error_body(422, "That request was not valid.", fields=fields))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        # The detail goes to the log, never to the client.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_body(500, "Something went wrong on this end."))

    return app
