# Copyright 2025 StarHTML Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
StarHTML - Modern web framework for Python

A reactive web framework combining Python simplicity with modern web technologies.
A FastHTML rewrite with Datastar integration for reactive UIs.

Example:
    from starhtml import *

    app, rt = star_app()

    @rt("/")
    def home():
        return Div(H1("Hello StarHTML!"))
"""

try:
    from importlib.metadata import version

    __version__ = version("starhtml")
except ImportError:
    __version__ = "0.1.0"


# Starlette re-exports for user convenience
import json
from inspect import iscoroutinefunction

from fastcore.utils import AttrDict, Path, first, listify, partition
from fastcore.xml import FT, NotStr, to_xml
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from starlette.convertors import StringConvertor, register_url_convertor
from starlette.datastructures import FormData, Headers, QueryParams, State, UploadFile, URLPath
from starlette.endpoints import HTTPEndpoint, WebSocketEndpoint
from starlette.exceptions import HTTPException, WebSocketException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
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
from starlette.responses import JSONResponse as JSONResponseOrig
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from .core import *
from .datastar import *
from .external import *
from .handlers import *
from .html import *
from .realtime import *
from .server import *
from .starapp import *
from .tags import *
from .utils import *
from .xtend import *


def loads(s):
    """JSON loads function"""
    return json.loads(s)


def is_async_callable(func):
    """Check if function is async callable"""
    return iscoroutinefunction(func)
