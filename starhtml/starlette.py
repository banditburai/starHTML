"""
Selective Starlette re-exports for StarHTML.

This module provides the most commonly used Starlette components as direct imports,
while offering lazy loading functions for less frequently used components.
This improves startup performance and reduces memory usage.
"""

# ============================================================================
# CORE COMPONENTS - Always imported (used frequently throughout StarHTML)
# ============================================================================

# Applications and routing - core to any web framework
from starlette.applications import Starlette
from starlette.routing import Route, Router, WebSocketRoute
from starlette.middleware import Middleware

# Request/Response - fundamental HTTP primitives
from starlette.requests import Request, HTTPConnection
from starlette.responses import (
    Response, HTMLResponse, FileResponse, 
    JSONResponse as JSONResponseOrig, RedirectResponse, StreamingResponse
)

# Essential data structures
from starlette.datastructures import FormData, UploadFile, URLPath
from starlette.exceptions import HTTPException, WebSocketException

# Core types for ASGI
from starlette.types import ASGIApp, Scope, Receive, Send

# Background tasks (commonly used)
from starlette.background import BackgroundTask, BackgroundTasks

# WebSocket support
from starlette.websockets import WebSocket, WebSocketDisconnect

# ============================================================================
# COMMONLY USED UTILITIES - Direct imports
# ============================================================================

# URL conversion and routing utilities
from starlette.convertors import Convertor, StringConvertor, register_url_convertor, CONVERTOR_TYPES
from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool

# Static files (used by fast_app)
from starlette.staticfiles import StaticFiles

# Configuration
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

# ============================================================================
# LAZY LOADING FUNCTIONS - For less common components
# ============================================================================

def get_session_middleware():
    """Get SessionMiddleware (lazy import)"""
    from starlette.middleware.sessions import SessionMiddleware
    return SessionMiddleware

def get_cors_middleware():
    """Get CORSMiddleware (lazy import)"""
    from starlette.middleware.cors import CORSMiddleware
    return CORSMiddleware

def get_auth_middleware():
    """Get authentication middleware and components (lazy import)"""
    from starlette.middleware.authentication import AuthenticationMiddleware
    from starlette.authentication import (
        AuthCredentials, AuthenticationBackend, 
        AuthenticationError, SimpleUser, requires
    )
    return {
        'AuthenticationMiddleware': AuthenticationMiddleware,
        'AuthCredentials': AuthCredentials,
        'AuthenticationBackend': AuthenticationBackend,
        'AuthenticationError': AuthenticationError,
        'SimpleUser': SimpleUser,
        'requires': requires
    }

def get_security_middleware():
    """Get security middleware (lazy import)"""
    from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    return {
        'HTTPSRedirectMiddleware': HTTPSRedirectMiddleware,
        'TrustedHostMiddleware': TrustedHostMiddleware
    }

def get_endpoints():
    """Get endpoint classes (lazy import)"""
    from starlette.endpoints import HTTPEndpoint, WebSocketEndpoint
    return {
        'HTTPEndpoint': HTTPEndpoint,
        'WebSocketEndpoint': WebSocketEndpoint
    }

def get_routing_extras():
    """Get additional routing components (lazy import)"""
    from starlette.routing import Mount
    return {'Mount': Mount}

# ============================================================================
# BACKWARDS COMPATIBILITY
# ============================================================================

# For existing code that expects these to be directly available
# We'll import them but mark them as deprecated in comments

# Session middleware is commonly used, so keep it available
SessionMiddleware = get_session_middleware()

# ============================================================================
# __all__ - Define what gets exported with "from starhtml.starlette import *"
# ============================================================================

__all__ = [
    # Core components
    'Starlette', 'Route', 'Router', 'WebSocketRoute', 'Middleware',
    'Request', 'HTTPConnection', 'Response', 'HTMLResponse', 'FileResponse',
    'JSONResponseOrig', 'RedirectResponse', 'StreamingResponse',
    'FormData', 'UploadFile', 'URLPath', 'HTTPException', 'WebSocketException',
    'ASGIApp', 'Scope', 'Receive', 'Send', 'BackgroundTask', 'BackgroundTasks',
    'WebSocket', 'WebSocketDisconnect',
    
    # Utilities
    'Convertor', 'StringConvertor', 'register_url_convertor', 'CONVERTOR_TYPES',
    'is_async_callable', 'run_in_threadpool', 'StaticFiles', 'Config',
    'CommaSeparatedStrings', 'Secret',
    
    # Backwards compatibility
    'SessionMiddleware',
    
    # Lazy loading functions
    'get_session_middleware', 'get_cors_middleware', 'get_auth_middleware',
    'get_security_middleware', 'get_endpoints', 'get_routing_extras'
]

