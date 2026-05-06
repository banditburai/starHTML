"""Hardening tests for ``starhtml.utils.get_key``: 0o600 file mode +
atomic creation + named env-var override."""

import os
import stat
import threading

import pytest

from starhtml import star_app
from starhtml.utils import get_key


def _mode(p):
    return stat.S_IMODE(p.stat().st_mode)


def test_generate_new_creates_with_mode_0600(tmp_path):
    fname = tmp_path / ".sesskey"
    key = get_key(fname=str(fname))
    assert _mode(fname) == 0o600
    assert len(key) >= 32


def test_generate_new_does_not_clobber_concurrent_writer(tmp_path):
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
        get_key(fname=str(fname), strict_mode=True)


def test_strict_mode_refuses_group_readable(tmp_path):
    fname = tmp_path / ".sesskey"
    fname.write_text("leaky-key")
    os.chmod(fname, 0o640)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(fname), strict_mode=True)


def test_non_strict_mode_warns_but_reads(tmp_path, recwarn):
    fname = tmp_path / ".sesskey"
    fname.write_text("legacy-key")
    os.chmod(fname, 0o644)
    assert get_key(fname=str(fname), strict_mode=False) == "legacy-key"
    assert any("0600" in str(w.message) or "mode" in str(w.message).lower() for w in recwarn)


def test_strict_mode_refuses_symlink_even_when_target_is_0600(tmp_path):
    target = tmp_path / "target"
    target.write_text("target-key")
    os.chmod(target, 0o600)
    link = tmp_path / ".sesskey"
    link.symlink_to(target)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(link), strict_mode=True)


def test_strict_mode_refuses_broken_symlink(tmp_path):
    link = tmp_path / ".sesskey"
    link.symlink_to(tmp_path / "missing")
    with pytest.raises(PermissionError, match=r"0600|mode"):
        get_key(fname=str(link), strict_mode=True)


def test_star_app_defaults_to_legacy_key_compatibility(tmp_path, recwarn):
    fname = tmp_path / ".sesskey"
    fname.write_text("legacy-key")
    os.chmod(fname, 0o644)
    star_app(key_fname=str(fname))
    assert any("0600" in str(w.message) or "mode" in str(w.message).lower() for w in recwarn)


def test_star_app_can_opt_into_strict_key_mode(tmp_path):
    fname = tmp_path / ".sesskey"
    fname.write_text("legacy-key")
    os.chmod(fname, 0o644)
    with pytest.raises(PermissionError, match=r"0600|mode"):
        star_app(key_fname=str(fname), key_strict_mode=True)


def test_star_app_passes_custom_secret_env(tmp_path, monkeypatch):
    fname = tmp_path / ".sesskey"
    fname.write_text("leaky-key")
    os.chmod(fname, 0o644)
    monkeypatch.setenv("MY_APP_KEY", "custom-wins")
    star_app(key_fname=str(fname), secret_env="MY_APP_KEY", key_strict_mode=True)


def test_env_var_short_circuits_before_file_mode_check(tmp_path, monkeypatch):
    fname = tmp_path / ".sesskey"
    fname.write_text("on-disk-leaky")
    os.chmod(fname, 0o644)
    monkeypatch.setenv("STARHTML_SECRET_KEY", "env-wins")
    assert get_key(fname=str(fname)) == "env-wins"


def test_custom_secret_env_wins_over_default(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_APP_KEY", "custom-wins")
    monkeypatch.setenv("STARHTML_SECRET_KEY", "default-loses")
    assert get_key(fname=str(tmp_path / ".sesskey"), secret_env="MY_APP_KEY") == "custom-wins"
