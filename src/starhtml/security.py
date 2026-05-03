"Refuse-to-start helpers for secure file modes and safe network binds."

import stat
from pathlib import Path

_REQUIRED_MODE = 0o600
_ALL_INTERFACES = frozenset({"0.0.0.0", "::"})


class StartupCheckError(RuntimeError):
    "Raised when the server cannot safely start; bootstrap should print str(exc), not traceback."


def assert_secure_file_modes(*paths):
    """Refuse to start if any path's mode is not exactly 0o600.

    Strict equality (not masking) so setuid/sticky also fail closed —
    a credentials file with 0o4600 is "0600 plus setuid", not safe.
    Missing paths are skipped (caller decides policy on existence).
    """
    for p in paths:
        path = Path(p) if not isinstance(p, Path) else p
        try:
            # follow_symlinks=False: a symlink users.yaml -> /etc/shadow
            # mustn't bypass the check by reporting the target's mode.
            info = path.stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        mode = stat.S_IMODE(info.st_mode)
        if mode != _REQUIRED_MODE:
            raise StartupCheckError(f"{path} mode is {mode:o}; expected 0600. Run: chmod 600 {path}")


def assert_safe_bind(host, *, i_understand_the_risks, tls_configured):
    """Refuse 0.0.0.0 / :: bind without explicit ack AND TLS.

    Both conditions required: the flag without TLS still ships plaintext
    credentials; TLS without the flag means the operator didn't think
    about exposure. Loopback binds pass through unchanged.
    """
    if host not in _ALL_INTERFACES:
        return
    missing = []
    if not i_understand_the_risks:
        missing.append("--i-understand-the-risks")
    if not tls_configured:
        missing.append("TLS config (--tls-cert / --tls-key or auto-cert)")
    if missing:
        raise StartupCheckError(
            f"refusing to bind {host}: missing {', '.join(missing)}. "
            f"See your framework's deployment docs for the supported workflow."
        )
