"""Hardening tests for ``starhtml.utils.get_key``: 0o600 file mode +
atomic creation + named env-var override."""

import os
import stat
import threading

import pytest

from starhtml.utils import get_key


def _mode(p):
    return stat.S_IMODE(p.stat().st_mode)


def test_generate_new_creates_with_mode_0600(tmp_path):
    fname = tmp_path / ".sesskey"
    key = get_key(fname=str(fname))
    assert _mode(fname) == 0o600
    assert len(key) >= 32


def test_generate_new_does_not_clobber_concurrent_writer(tmp_path):
    # Two threads racing on the same path must agree on the key — the
    # loser of the O_EXCL race reads the winner's value.
    fname = tmp_path / ".sesskey"
    results = []
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()
        results.append(get_key(fname=str(fname)))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results[0] == results[1]
    assert _mode(fname) == 0o600


def test_strict_mode_refuses_world_readable(tmp_path):
    fname = tmp_path / ".sesskey"
    fname.write_text("leaky-key")
    os.chmod(fname, 0o644)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(fname))


def test_strict_mode_refuses_group_readable(tmp_path):
    fname = tmp_path / ".sesskey"
    fname.write_text("leaky-key")
    os.chmod(fname, 0o640)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(fname))


def test_non_strict_mode_warns_but_reads(tmp_path, recwarn):
    fname = tmp_path / ".sesskey"
    fname.write_text("legacy-key")
    os.chmod(fname, 0o644)
    assert get_key(fname=str(fname), strict_mode=False) == "legacy-key"
    assert any("0600" in str(w.message) or "mode" in str(w.message).lower() for w in recwarn)


def test_env_var_short_circuits_before_file_mode_check(tmp_path, monkeypatch):
    # Env wins so a misconfigured on-disk file isn't even statted.
    fname = tmp_path / ".sesskey"
    fname.write_text("on-disk-leaky")
    os.chmod(fname, 0o644)
    monkeypatch.setenv("STARHTML_SECRET_KEY", "env-wins")
    assert get_key(fname=str(fname)) == "env-wins"


def test_custom_secret_env_wins_over_default(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_APP_KEY", "custom-wins")
    monkeypatch.setenv("STARHTML_SECRET_KEY", "default-loses")
    assert get_key(fname=str(tmp_path / ".sesskey"), secret_env="MY_APP_KEY") == "custom-wins"
