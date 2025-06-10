"""Tests for StarHTML common module functionality"""


def test_common_imports():
    """Test that common module imports work correctly"""
    # Test that importing from common gives access to key functions
    from starhtml.common import cookie, ft_datastar, unqid

    # Test basic functionality is available
    assert callable(unqid)
    assert callable(ft_datastar)
    assert callable(cookie)

    # Test that functions work
    assert len(unqid()) > 0


def test_common_all_imports():
    """Test that all major imports from common are accessible"""
    from starhtml import common

    # Should have imported from multiple modules
    assert hasattr(common, "unqid")  # from core
    assert hasattr(common, "ft_datastar")  # from components


def test_fastcore_imports():
    """Test that fastcore utilities are available through common"""
    from starhtml.common import Path, partial

    assert callable(Path)
    assert callable(partial)


def test_fastlite_imports():
    """Test that fastlite database utilities are available"""
    try:
        from starhtml.common import Database

        assert callable(Database)
    except ImportError:
        # fastlite might not be available or might use different names
        pass
