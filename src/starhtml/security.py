"Startup checks for file permissions and public binds."

import stat
from pathlib import Path

_REQUIRED_MODE = 0o600
_ALL_INTERFACES = frozenset({"0.0.0.0", "::"})

__all__ = ["StartupCheckError", "assert_secure_file_modes", "assert_safe_bind"]


class StartupCheckError(RuntimeError):
    pass


def assert_secure_file_modes(*paths) -> None:
    """Require existing secret files to be exactly 0600.

    Strict equality rejects setuid/sticky bits; follow_symlinks=False prevents
    symlink targets from laundering the link's own unsafe mode.
    """
    for path in map(Path, paths):
        try:
            info = path.stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        if (mode := stat.S_IMODE(info.st_mode)) != _REQUIRED_MODE:
            raise StartupCheckError(f"{path} mode is {mode:04o}; expected 0600. Run: chmod 600 {path}")


def assert_safe_bind(host: str, *, public_bind_acknowledged: bool = False, tls_configured: bool = False) -> None:
    """Require explicit risk acknowledgement and TLS for public binds.

    Acknowledgement without TLS still ships plaintext credentials; TLS without
    acknowledgement can expose a server accidentally.
    """
    if host not in _ALL_INTERFACES:
        return
    missing = []
    if not public_bind_acknowledged:
        missing.append("--i-understand-the-risks")
    if not tls_configured:
        missing.append("TLS config (--tls-cert / --tls-key or auto-cert)")
    if missing:
        raise StartupCheckError(
            f"refusing to bind {host}: missing {', '.join(missing)}. "
            f"See your framework's deployment docs for the supported workflow."
        )
