import copy
import json
import logging
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from secrets import token_urlsafe
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.datastructures import URL
from starlette.exceptions import HTTPException

from src.core.config import CONTEXT_ID
from src.core.exceptions import JsonException

logger = logging.getLogger("root")


def valid_path_for_logging(url: URL) -> str:
    if url.query:
        return f"{url.path}?{url.query}"
    return url.path


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as exc:
        return JsonException(
            status_code=exc.status_code,
            error_name="HTTP_EXCEPTION",
            error_description=HTTPStatus(exc.status_code).description,
        ).response()

    except JsonException as exc:
        if HTTPStatus.BAD_REQUEST <= exc.status_code <= HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED:
            logging.warning(
                f"Response {exc.error_name} with status {exc.status_code}, meta={exc.error_meta}"
            )

        return exc.response()

    except RequestValidationError as exc:
        return ValidationError(exc).json()

    except Exception as exc:
        logging.exception(exc)

        return JsonException(
            status_code=500,
            error_name="INTERNAL_SERVER_ERROR",
            error_description="Internal server error",
        ).response()


async def request_logging_middleware(request: Request, call_next):
    result = await call_next(request)
    log_level = 20

    status_code = result.status_code
    if HTTPStatus.BAD_REQUEST <= status_code <= HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS:
        log_level = 30  # WARNING
    if (
        HTTPStatus.INTERNAL_SERVER_ERROR
        <= status_code
        <= HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED
    ):
        log_level = 40  # ERROR

    logging.log(
        log_level,
        f"{request.method} {valid_path_for_logging(request.url)}"
        f" {status_code} {HTTPStatus(status_code).phrase}",
    )

    return result


def log_body(
    sensitive_fields: set[str] | None = None,
    mask_string: str = "**********",
) -> Callable[[Any, Any], Awaitable[Any]]:
    def search_and_replace_sensitive_fields(_body: dict):
        if not isinstance(_body, dict):
            return

        for k, v in _body.items():
            if isinstance(v, dict):
                search_and_replace_sensitive_fields(v)
            elif k in sensitive_fields:
                _body[k] = mask_string

    async def _log(request: Request):
        if request.headers.get("Content-Type") == "application/json":
            body_type = "json"
            body = copy.deepcopy(await request.json())
        elif request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
            body_type = "form"
            body = copy.deepcopy(dict(await request.form()))
        elif request.query_params:
            body_type = "query"
            body = copy.deepcopy(dict(request.query_params))
        else:
            body_type = "unknown"
            body = {}

        # Search for sensitive fields in body
        search_and_replace_sensitive_fields(body)

        repr_body = json.dumps(body, ensure_ascii=False)
        if body:
            logger.debug(
                f"{request.url.path} request {body_type}: {repr_body}",
                extra={
                    "action": "API_REQUEST",
                    "method": request.method,
                    "path": request.url.path,
                    "body": repr_body,
                },
            )

    return _log


async def request_id_middleware(request: Request, call_next):
    CONTEXT_ID.set(request.headers.get("X-Request-ID", str(token_urlsafe(16))))
    return await call_next(request)


def setup_middlewares(app: FastAPI):
    # app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.middleware("http")(catch_exceptions_middleware)
    app.middleware("http")(request_logging_middleware)
    app.middleware("http")(request_id_middleware)
