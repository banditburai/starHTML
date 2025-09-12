"""Unit tests for the container parameter in ds_position."""

from starhtml.datastar import ds_position


def test_ds_position_default_container():
    """Test that container defaults to 'auto' and is not included in modifiers."""
    result = ds_position(anchor="test-anchor")
    assert result.attrs == {"data-position-anchor": "test-anchor"}


def test_ds_position_container_none():
    """Test container='none' is included in modifiers."""
    result = ds_position(anchor="test-anchor", container="none")
    assert result.attrs == {"data-position-anchor__container.none": "test-anchor"}


def test_ds_position_container_parent():
    """Test container='parent' is included in modifiers."""
    result = ds_position(anchor="test-anchor", container="parent")
    assert result.attrs == {"data-position-anchor__container.parent": "test-anchor"}


def test_ds_position_container_auto_explicit():
    """Test that explicitly setting container='auto' doesn't add modifier."""
    result = ds_position(anchor="test-anchor", container="auto")
    # Should not include container modifier since 'auto' is the default
    assert result.attrs == {"data-position-anchor": "test-anchor"}


def test_ds_position_container_with_other_modifiers():
    """Test container parameter combined with other modifiers."""
    result = ds_position(anchor="test-anchor", placement="right", container="none", offset=20, flip=False)
    expected_key = "data-position-anchor__placement.right__offset.20__flip.false__container.none"
    assert result.attrs == {expected_key: "test-anchor"}


def test_ds_position_container_preserves_existing_behavior():
    """Test that adding container parameter doesn't break existing usage."""
    # Without container (should default to 'auto')
    result1 = ds_position(
        anchor="test-anchor",
        placement="bottom",
        strategy="absolute",
        offset=8,
        flip=True,
        shift=True,
        hide=False,
        auto_size=False,
    )

    # With explicit container='auto'
    result2 = ds_position(
        anchor="test-anchor",
        placement="bottom",
        strategy="absolute",
        offset=8,
        flip=True,
        shift=True,
        hide=False,
        auto_size=False,
        container="auto",
    )

    # Both should produce the same result
    assert result1.attrs == result2.attrs
    assert result1.attrs == {"data-position-anchor": "test-anchor"}


def test_ds_position_all_container_values():
    """Test all valid container values."""
    for container_value in ["auto", "parent", "none"]:
        result = ds_position(anchor="test", container=container_value)
        if container_value == "auto":
            # Auto is default, shouldn't be in modifiers
            assert "container" not in str(result.attrs)
        else:
            # Other values should be in modifiers
            assert f"container.{container_value}" in str(result.attrs)
