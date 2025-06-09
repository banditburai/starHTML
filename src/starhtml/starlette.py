"""Re-export common Starlette components for StarHTML."""

from json import loads

from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.convertors import StringConvertor, register_url_convertor
from starlette.datastructures import FormData, Headers, QueryParams, State, UploadFile, URLPath
from starlette.endpoints import HTTPEndpoint, WebSocketEndpoint
from starlette.exceptions import HTTPException, WebSocketException
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.responses import (
    JSONResponse as JSONResponseOrig,
)
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

__all__ = [
    "loads",
    "Starlette",
    "requires",
    "BackgroundTask",
    "BackgroundTasks",
    "StringConvertor",
    "register_url_convertor",
    "FormData",
    "Headers",
    "QueryParams",
    "State",
    "UploadFile",
    "URLPath",
    "HTTPEndpoint",
    "WebSocketEndpoint",
    "HTTPException",
    "WebSocketException",
    "Middleware",
    "SessionMiddleware",
    "HTTPConnection",
    "Request",
    "FileResponse",
    "HTMLResponse",
    "JSONResponseOrig",
    "PlainTextResponse",
    "RedirectResponse",
    "Response",
    "StreamingResponse",
    "Mount",
    "Route",
    "WebSocketRoute",
    "StaticFiles",
    "Jinja2Templates",
    "TestClient",
    "ASGIApp",
    "Message",
    "Receive",
    "Scope",
    "Send",
    "WebSocket",
    "WebSocketDisconnect",
    "WebSocketState",
]
