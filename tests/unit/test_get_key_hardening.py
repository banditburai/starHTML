"""Hardening tests for ``starhtml.utils.get_key``.

Ensures the auto-generated ``.sesskey`` file is created atomically with
mode ``0o600`` and that we refuse to read existing files whose mode
leaks the signing key to other local users.

Existing behavior tests (env-var precedence, explicit-key bypass,
generate-new) live in ``test_utils_comprehensive.py``; this file adds
the security-focused cases.
"""

from __future__ import annotations

import os
import stat
import threading
from pathlib import Path

import pytest

from starhtml.utils import get_key


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


# --- mode on auto-generation ----------------------------------------------


def test_generate_new_creates_with_mode_0600(tmp_path: Path) -> None:
    fname = tmp_path / ".sesskey"
    key = get_key(fname=str(fname))
    assert fname.exists()
    assert _mode(fname) == 0o600
    assert isinstance(key, str)
    assert len(key) >= 32


def test_generate_new_does_not_clobber_concurrent_writer(
    tmp_path: Path,
) -> None:
    """Two threads racing on ``get_key`` for the same path must both
    return the *same* key — the loser of the O_EXCL race reads the
    winner's value rather than overwriting it.
    """
    fname = tmp_path / ".sesskey"
    results: list[str] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        barrier.wait()
        results.append(get_key(fname=str(fname)))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 2
    assert results[0] == results[1]
    assert _mode(fname) == 0o600


# --- mode on existing files -----------------------------------------------


def test_existing_0600_file_is_read(tmp_path: Path) -> None:
    fname = tmp_path / ".sesskey"
    fname.write_text("preset-key-aaaaaaaaaaaaaaaaaaa")
    os.chmod(fname, 0o600)
    assert get_key(fname=str(fname)) == "preset-key-aaaaaaaaaaaaaaaaaaa"


def test_strict_mode_refuses_world_readable_file(tmp_path: Path) -> None:
    fname = tmp_path / ".sesskey"
    fname.write_text("leaky-key")
    os.chmod(fname, 0o644)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(fname), strict_mode=True)


def test_strict_mode_refuses_group_readable_file(tmp_path: Path) -> None:
    fname = tmp_path / ".sesskey"
    fname.write_text("leaky-key")
    os.chmod(fname, 0o640)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(fname), strict_mode=True)


def test_non_strict_mode_warns_but_reads_loose_file(
    tmp_path: Path, recwarn: pytest.WarningsRecorder
) -> None:
    fname = tmp_path / ".sesskey"
    fname.write_text("legacy-key-xxxxxxxxxxxxxxxxxxxxxxx")
    os.chmod(fname, 0o644)
    key = get_key(fname=str(fname), strict_mode=False)
    assert key == "legacy-key-xxxxxxxxxxxxxxxxxxxxxxx"
    assert any(
        "mode" in str(w.message).lower() or "0600" in str(w.message)
        for w in recwarn
    )


# --- env-var precedence preserved -----------------------------------------


def test_env_var_short_circuits_before_file_mode_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ``STARHTML_SECRET_KEY`` env var wins over file inspection;
    a world-readable on-disk file should never even be statted."""
    fname = tmp_path / ".sesskey"
    fname.write_text("on-disk-leaky")
    os.chmod(fname, 0o644)
    monkeypatch.setenv("STARHTML_SECRET_KEY", "env-wins")
    assert get_key(fname=str(fname), strict_mode=True) == "env-wins"


# --- secret_env ----------------------------------------------------------


def test_custom_secret_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fname = tmp_path / ".sesskey"
    monkeypatch.setenv("MY_APP_SIGNING_KEY", "from-custom-env")
    monkeypatch.delenv("STARHTML_SECRET_KEY", raising=False)
    assert (
        get_key(fname=str(fname), secret_env="MY_APP_SIGNING_KEY")
        == "from-custom-env"
    )
    # Custom env shouldn't trigger file creation.
    assert not fname.exists()


def test_custom_secret_env_falls_through_to_file_when_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fname = tmp_path / ".sesskey"
    monkeypatch.delenv("MY_APP_SIGNING_KEY", raising=False)
    monkeypatch.delenv("STARHTML_SECRET_KEY", raising=False)
    key = get_key(fname=str(fname), secret_env="MY_APP_SIGNING_KEY")
    assert fname.exists()
    assert _mode(fname) == 0o600
    assert key == fname.read_text().strip()


def test_custom_secret_env_wins_over_starhtml_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When both ``STARHTML_SECRET_KEY`` and the user-named env var are
    set, the user's variable wins — that's the whole point of allowing
    apps to name their own."""
    fname = tmp_path / ".sesskey"
    monkeypatch.setenv("MY_APP_SIGNING_KEY", "custom-wins")
    monkeypatch.setenv("STARHTML_SECRET_KEY", "default-loses")
    assert (
        get_key(fname=str(fname), secret_env="MY_APP_SIGNING_KEY")
        == "custom-wins"
    )


# --- backward compat ------------------------------------------------------


def test_default_strict_mode_is_on(tmp_path: Path) -> None:
    """Strict mode defaults to True so existing apps inherit safer
    behavior. Apps that need the legacy behavior must opt in explicitly."""
    fname = tmp_path / ".sesskey"
    fname.write_text("k")
    os.chmod(fname, 0o644)
    with pytest.raises(PermissionError):
        get_key(fname=str(fname))
