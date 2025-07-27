"""Basic scaffolding for handling OAuth and authentication"""

import re
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from fastcore.utils import AttrDictDefault, Path, load_pickle, save_pickle, store_attr
from fastcore.xml import patch
from oauthlib.oauth2 import WebApplicationClient

from .core import Beforeware, RedirectResponse

__all__ = [
    "OAuth",
    "GoogleAppClient",
    "GitHubAppClient",
    "HuggingFaceClient",
    "DiscordAppClient",
    "Auth0AppClient",
    "load_creds",
    "url_match",
    "redir_url",
    "http_patterns",
]

# ============================================================================
# Base OAuth2 Client Infrastructure
# ============================================================================


class _AppClient(WebApplicationClient):
    """Base OAuth2 client with common functionality for all providers"""

    id_key: str = "sub"
    base_url: str
    token_url: str
    info_url: str

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        code: str | None = None,
        scope: str | list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client_id, code=code, scope=scope, **kwargs)
        self.client_secret = client_secret


# ============================================================================
# Provider-Specific OAuth2 Clients
# ============================================================================


class GoogleAppClient(_AppClient):
    """A `WebApplicationClient` for Google OAuth2"""

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    info_url = "https://openidconnect.googleapis.com/v1/userinfo"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        code: str | None = None,
        scope: list[str] | None = None,
        project_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        scope_pre = "https://www.googleapis.com/auth/userinfo"
        if not scope:
            scope = ["openid", f"{scope_pre}.email", f"{scope_pre}.profile"]
        super().__init__(client_id, client_secret, code=code, scope=scope, **kwargs)
        self.project_id = project_id

    @classmethod
    def from_file(
        cls, fname: str, code: str | None = None, scope: list[str] | None = None, **kwargs: Any
    ) -> "GoogleAppClient":
        """Create client from Google credentials JSON file"""
        try:
            cred = Path(fname).read_json()["web"]
            return cls(
                cred["client_id"],
                client_secret=cred["client_secret"],
                project_id=cred["project_id"],
                code=code,
                scope=scope,
                **kwargs,
            )
        except (KeyError, FileNotFoundError, ValueError) as e:
            raise ValueError(f"Invalid Google credentials file {fname}: {e}") from e


class GitHubAppClient(_AppClient):
    """A `WebApplicationClient` for GitHub OAuth2"""

    prefix = "https://github.com/login/oauth/"
    base_url = f"{prefix}authorize"
    token_url = f"{prefix}access_token"
    info_url = "https://api.github.com/user"
    id_key = "id"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        code: str | None = None,
        scope: str | list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client_id, client_secret, code=code, scope=scope, **kwargs)


class HuggingFaceClient(_AppClient):
    """A `WebApplicationClient` for HuggingFace OAuth2"""

    prefix = "https://huggingface.co/oauth/"
    base_url = f"{prefix}authorize"
    token_url = f"{prefix}token"
    info_url = f"{prefix}userinfo"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        code: str | None = None,
        scope: list[str] | None = None,
        state: str | None = None,
        **kwargs: Any,
    ) -> None:
        if not scope:
            scope = ["openid", "profile"]
        if not state:
            state = secrets.token_urlsafe(16)
        super().__init__(client_id, client_secret, code=code, scope=scope, state=state, **kwargs)


class DiscordAppClient(_AppClient):
    """A `WebApplicationClient` for Discord OAuth2"""

    base_url = "https://discord.com/oauth2/authorize"
    token_url = "https://discord.com/api/oauth2/token"
    revoke_url = "https://discord.com/api/oauth2/token/revoke"
    info_url = "https://discord.com/api/users/@me"
    id_key = "id"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        is_user: bool = False,
        perms: int = 0,
        scope: str | None = None,
        **kwargs: Any,
    ) -> None:
        if not scope:
            scope = "applications.commands applications.commands.permissions.update identify"
        self.integration_type = 1 if is_user else 0
        self.perms = perms
        super().__init__(client_id, client_secret, scope=scope, **kwargs)

    def login_link(self, redirect_uri: str | None = None, scope: str | None = None, state: str | None = None) -> str:
        """Generate Discord-specific login link with integration type"""
        use_scope = scope or self.scope
        d = dict(
            response_type="code", client_id=self.client_id, integration_type=self.integration_type, scope=use_scope
        )
        if state:
            d["state"] = state
        if redirect_uri:
            d["redirect_uri"] = redirect_uri
        return f"{self.base_url}?" + urlencode(d)

    def parse_response(self, code: str, redirect_uri: str | None = None) -> None:
        """Parse Discord OAuth2 response with custom auth"""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = dict(grant_type="authorization_code", code=code)
        if redirect_uri:
            data["redirect_uri"] = redirect_uri
        try:
            r = httpx.post(self.token_url, data=data, headers=headers, auth=(self.client_id, self.client_secret))
            r.raise_for_status()
            self.parse_request_body_response(r.text)
        except httpx.HTTPError as e:
            raise ValueError(f"Discord OAuth2 token exchange failed: {e}") from e


class Auth0AppClient(_AppClient):
    """A `WebApplicationClient` for Auth0 OAuth2"""

    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        code: str | None = None,
        scope: str | list[str] | None = None,
        redirect_uri: str = "",
        **kwargs: Any,
    ) -> None:
        self.redirect_uri, self.domain = redirect_uri, domain
        try:
            config = self._fetch_openid_config()
            self.base_url, self.token_url, self.info_url = (
                config["authorization_endpoint"],
                config["token_endpoint"],
                config["userinfo_endpoint"],
            )
        except (httpx.HTTPError, KeyError) as e:
            raise ValueError(f"Failed to fetch Auth0 configuration for {domain}: {e}") from e
        super().__init__(client_id, client_secret, code=code, scope=scope, redirect_uri=redirect_uri, **kwargs)

    def _fetch_openid_config(self) -> dict[str, str]:
        """Fetch OpenID Connect configuration from Auth0"""
        r = httpx.get(f"https://{self.domain}/.well-known/openid-configuration", timeout=10.0)
        r.raise_for_status()
        return r.json()

    def login_link(self, req: Any) -> str:
        """Generate Auth0-specific login link"""
        d = dict(
            response_type="code",
            client_id=self.client_id,
            scope=self.scope,
            redirect_uri=redir_url(req, self.redirect_uri),
        )
        return f"{self.base_url}?{urlencode(d)}"


# ============================================================================
# Client Extension Methods (via @patch)
# ============================================================================


@patch
def login_link(
    self: WebApplicationClient,
    redirect_uri: str,
    scope: str | list[str] | None = None,
    state: str | None = None,
    **kwargs: Any,
) -> str:
    """Get a login link for this client"""
    if not scope:
        scope = self.scope
    if not state:
        state = getattr(self, "state", None)
    return self.prepare_request_uri(self.base_url, redirect_uri, scope, state=state, **kwargs)


@patch
def parse_response(self: _AppClient, code: str, redirect_uri: str) -> None:
    """Get the token from the OAuth2 server response"""
    payload = dict(
        code=code,
        redirect_uri=redirect_uri,
        client_id=self.client_id,
        client_secret=self.client_secret,
        grant_type="authorization_code",
    )
    try:
        r = httpx.post(self.token_url, json=payload, timeout=10.0)
        r.raise_for_status()
        self.parse_request_body_response(r.text)
    except httpx.HTTPError as e:
        raise ValueError(f"OAuth2 token exchange failed: {e}") from e


@patch
def get_info(self: _AppClient, token: str | None = None) -> dict[str, Any]:
    """Get the info for authenticated user"""
    if not token:
        token = self.token["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = httpx.get(self.info_url, headers=headers, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise ValueError(f"Failed to fetch user info: {e}") from e


@patch
def retr_info(self: _AppClient, code: str, redirect_uri: str) -> dict[str, Any]:
    """Combines `parse_response` and `get_info`"""
    self.parse_response(code, redirect_uri)
    return self.get_info()


@patch
def retr_id(self: _AppClient, code: str, redirect_uri: str) -> Any:
    """Call `retr_info` and then return id/subscriber value"""
    return self.retr_info(code, redirect_uri)[self.id_key]


# ============================================================================
# OAuth2 Authentication Orchestrator
# ============================================================================


class OAuth:
    """
    OAuth2 authentication handler that integrates with StarHTML apps.

    This class adds the necessary middleware and routes for login, logout,
    and the redirect callback. It orchestrates the complete authentication flow
    using one of the provider clients defined above.

    Usage:
        client = GoogleAppClient("client_id", "client_secret")
        oauth = OAuth(app, client)
        # Now your app has OAuth2 authentication!
    """

    def __init__(
        self,
        app: Any,
        cli: _AppClient,
        skip: list[str] | None = None,
        redir_path: str = "/redirect",
        error_path: str = "/error",
        logout_path: str = "/logout",
        login_path: str = "/login",
        https: bool = True,
        http_patterns: tuple[str, ...] = None,
    ) -> None:
        if not skip:
            skip = [redir_path, error_path, login_path]
        if http_patterns is None:
            http_patterns = (r"^(localhost|127\.0\.0\.1)(:\d+)?$",)
        store_attr()

        def before(req, session):
            """Before middleware to check authentication"""
            if "auth" not in req.scope:
                req.scope["auth"] = session.get("auth")
            auth = req.scope["auth"]
            if not auth:
                return self.redir_login(session)
            res = self.check_invalid(req, session, auth)
            if res:
                return res

        app.before.append(Beforeware(before, skip=skip))

        @app.get(redir_path)
        def redirect(req, session, code: str = None, error: str = None, state: str = None):
            """Handle OAuth2 redirect callback"""
            if not code:
                session["oauth_error"] = error
                return RedirectResponse(self.error_path, status_code=303)

            try:
                scheme = "http" if url_match(req.url, self.http_patterns) or not self.https else "https"
                base_url = f"{scheme}://{req.url.netloc}"
                info = AttrDictDefault(cli.retr_info(code, base_url + redir_path))
                ident = info.get(self.cli.id_key)
                if not ident:
                    return self.redir_login(session)
                res = self.get_auth(info, ident, session, state)
                if not res:
                    return self.redir_login(session)
                req.scope["auth"] = session["auth"] = ident
                return res
            except ValueError as e:
                session["oauth_error"] = str(e)
                return RedirectResponse(self.error_path, status_code=303)

        @app.get(logout_path)
        def logout(session):
            """Handle logout"""
            session.pop("auth", None)
            return self.logout(session)

    def redir_login(self, session: Any) -> RedirectResponse:
        """Redirect to login page"""
        return RedirectResponse(self.login_path, status_code=303)

    def redir_url(self, req: Any) -> str:
        """Get redirect URL for OAuth2 callback"""
        scheme = "http" if url_match(req.url, self.http_patterns) or not self.https else "https"
        return redir_url(req, self.redir_path, scheme)

    def login_link(self, req: Any, scope: str | list[str] | None = None, state: str | None = None) -> str:
        """Generate OAuth2 login link"""
        return self.cli.login_link(self.redir_url(req), scope=scope, state=state)

    def check_invalid(self, req: Any, session: Any, auth: Any) -> RedirectResponse | None:
        """Override to add custom auth validation logic"""
        return None

    def logout(self, session: Any) -> RedirectResponse:
        """Override to customize logout behavior"""
        return self.redir_login(session)

    def get_auth(self, info: Any, ident: Any, session: Any, state: Any) -> Any:
        """Override to customize auth result - must return response or None"""
        raise NotImplementedError("Subclass must implement get_auth method")


# ============================================================================
# Utility Functions
# ============================================================================

http_patterns = (r"^(localhost|127\.0\.0\.1)(:\d+)?$",)


def url_match(url: Any, patterns: tuple[str, ...] = http_patterns) -> bool:
    return any(re.match(pattern, url.netloc.split(":")[0]) for pattern in patterns)


def redir_url(request: Any, redir_path: str, scheme: str | None = None) -> str:
    """Get the redirect URL for the host in `request`"""
    if scheme is None:
        scheme = "http" if request.url.hostname in ("localhost", "127.0.0.1") else "https"
    return f"{scheme}://{request.url.netloc}{redir_path}"


# ============================================================================
# Optional: Google Credentials Support
# ============================================================================
# This section provides helpers for working with the google-auth library,
# which is an optional dependency.

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    Request = None

    class Credentials:
        """Fallback Credentials class when google-auth not available"""

        pass


@patch()
def consent_url(self: GoogleAppClient, proj: str | None = None) -> str:
    """Get Google OAuth consent screen URL"""
    loc = "https://console.cloud.google.com/auth/clients"
    if proj is None:
        proj = self.project_id
    return f"{loc}/{self.client_id}?project={proj}"


@patch
def update(self: "Credentials") -> "Credentials":
    """Refresh the credentials if they are expired, and return them"""
    if self.expired and Request:
        self.refresh(Request())
    return self


@patch
def save(self: "Credentials", fname: str) -> None:
    """Save credentials to `fname`"""
    save_pickle(fname, self)


def load_creds(fname: str) -> Any:
    """Load credentials from `fname`"""
    try:
        return load_pickle(fname).update()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Credentials file not found: {fname}") from e


@patch
def creds(self: GoogleAppClient) -> "Credentials":
    """Create `Credentials` from the client, refreshing if needed"""
    if not Request:
        raise ImportError("google-auth package required for Credentials")
    return Credentials(
        token=self.access_token,
        refresh_token=self.refresh_token,
        token_uri=self.token_url,
        client_id=self.client_id,
        client_secret=self.client_secret,
        scopes=self.scope,
    ).update()
