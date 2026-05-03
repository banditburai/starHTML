"starhtml.security: file-mode + safe-bind preflight checks."

import os

import pytest

from starhtml.security import StartupCheckError, assert_safe_bind, assert_secure_file_modes


def test_file_mode_0600_passes(tmp_path):
    p = tmp_path / "secret"
    p.write_text("x")
    os.chmod(p, 0o600)
    assert_secure_file_modes(p)


def test_file_mode_world_readable_refused(tmp_path):
    p = tmp_path / "secret"
    p.write_text("x")
    os.chmod(p, 0o644)
    with pytest.raises(StartupCheckError, match=r"0600|chmod"):
        assert_secure_file_modes(p)


def test_file_mode_setuid_refused(tmp_path):
    # 0o4600 = setuid + 0600. Strict equality must reject.
    p = tmp_path / "secret"
    p.write_text("x")
    os.chmod(p, 0o4600)
    with pytest.raises(StartupCheckError):
        assert_secure_file_modes(p)


def test_missing_file_skipped(tmp_path):
    assert_secure_file_modes(tmp_path / "does-not-exist")


def test_symlink_to_world_readable_refused(tmp_path):
    target = tmp_path / "target"
    target.write_text("x")
    os.chmod(target, 0o644)
    link = tmp_path / "link"
    link.symlink_to(target)
    # follow_symlinks=False: mode of the symlink itself, which is 0o777.
    with pytest.raises(StartupCheckError):
        assert_secure_file_modes(link)


def test_accepts_pathlib_and_str(tmp_path):
    p = tmp_path / "secret"
    p.write_text("x")
    os.chmod(p, 0o600)
    assert_secure_file_modes(p)
    assert_secure_file_modes(str(p))


def test_loopback_bind_unchecked():
    assert_safe_bind("127.0.0.1", i_understand_the_risks=False, tls_configured=False)
    assert_safe_bind("localhost", i_understand_the_risks=False, tls_configured=False)
    assert_safe_bind("::1", i_understand_the_risks=False, tls_configured=False)


def test_zero_bind_without_ack_refused():
    with pytest.raises(StartupCheckError, match=r"i-understand-the-risks"):
        assert_safe_bind("0.0.0.0", i_understand_the_risks=False, tls_configured=True)


def test_zero_bind_without_tls_refused():
    with pytest.raises(StartupCheckError, match=r"TLS"):
        assert_safe_bind("0.0.0.0", i_understand_the_risks=True, tls_configured=False)


def test_zero_bind_with_both_passes():
    assert_safe_bind("0.0.0.0", i_understand_the_risks=True, tls_configured=True)


def test_ipv6_all_interfaces_gated():
    with pytest.raises(StartupCheckError):
        assert_safe_bind("::", i_understand_the_risks=False, tls_configured=False)
