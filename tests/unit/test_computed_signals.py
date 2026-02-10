"""Tests for computed signals functionality."""

from starhtml.datastar import Signal, _handle_data_signals, js


class TestComputedSignals:
    """Test computed signal creation and processing."""

    def test_regular_signal_properties(self):
        """Test that regular signals work as expected."""
        signal = Signal("counter", 0)

        assert not signal._is_computed
        # Default ifmissing=True means to_dict() is empty (uses individual attr)
        assert signal.to_dict() == {}
        # get_signal_attr() returns the ifmissing attribute
        attr = signal.get_signal_attr()
        assert attr is not None
        assert attr[0] == "data-signals:counter__ifmissing"
        assert attr[1] == 0
        assert signal.get_computed_attr() is None

    def test_regular_signal_with_ifmissing_false(self):
        """Test signal with ifmissing=False uses combined format."""
        signal = Signal("counter", 0, ifmissing=False)

        assert not signal._is_computed
        # ifmissing=False uses to_dict() for combined format
        assert signal.to_dict() == {"counter": 0}
        # get_signal_attr() returns None when ifmissing=False
        assert signal.get_signal_attr() is None
        assert signal.get_computed_attr() is None

    def test_computed_signal_detection(self):
        """Test that computed signals are correctly identified."""
        regular = Signal("counter", 0)
        computed = Signal("doubled", regular * 2)

        assert not regular._is_computed
        assert computed._is_computed

    def test_computed_signal_to_dict(self):
        """Test that computed signals return empty dict regardless of ifmissing."""
        regular_ifmissing = Signal("counter", 0, ifmissing=True)
        regular_override = Signal("counter2", 0, ifmissing=False)
        computed = Signal("doubled", regular_ifmissing * 2)

        # ifmissing=True: to_dict() empty, uses get_signal_attr() instead
        assert regular_ifmissing.to_dict() == {}
        # ifmissing=False: to_dict() returns the signal
        assert regular_override.to_dict() == {"counter2": 0}
        # computed: always empty
        assert computed.to_dict() == {}

    def test_computed_signal_attr_generation(self):
        """Test that computed signals generate correct data_computed attributes."""
        regular = Signal("counter", 0)
        computed = Signal("doubled", regular * 2)

        assert regular.get_computed_attr() is None

        attr_name, attr_value = computed.get_computed_attr()
        assert attr_name == "data_computed_doubled"
        assert hasattr(attr_value, "to_js")  # It's an Expr object

    def test_data_signals_processing_excludes_computed(self):
        """Test that computed signals are excluded from data-signals."""
        regular = Signal("counter", 0)
        computed = Signal("doubled", regular * 2)

        # Test with list of mixed signals
        signal_list = [regular, computed]
        result = _handle_data_signals(signal_list)

        # Result should only contain the regular signal
        result_str = str(result)
        assert "counter" in result_str
        assert "doubled" not in result_str

    def test_complex_computed_expressions(self):
        """Test computed signals with complex expressions."""
        name = Signal("name", "")
        age = Signal("age", 0)
        is_valid = Signal("is_valid", (name.length > 0) & (age >= 18))

        assert is_valid._is_computed
        assert is_valid.to_dict() == {}  # Computed always empty

        attr_name, attr_value = is_valid.get_computed_attr()
        assert attr_name == "data_computed_is_valid"

    def test_computed_with_js_expressions(self):
        """Test computed signals with js() expressions."""
        playlist = Signal("playlist", [])
        song_count = Signal("song_count", playlist.filter(js("song => song && song.trim().length > 0")).length)

        assert song_count._is_computed
        assert song_count.to_dict() == {}  # Computed always empty

        attr_name, attr_value = song_count.get_computed_attr()
        assert attr_name == "data_computed_song_count"

        # The expression should contain the filter logic
        expr_js = attr_value.to_js()
        assert "$playlist" in expr_js
        assert "filter" in expr_js


class TestComputedSignalIntegration:
    """Test computed signals in HTML generation context."""

    def test_mixed_signals_data_processing(self):
        """Test that mixed regular and computed signals are processed correctly."""
        # Create a mix of regular and computed signals
        counter = Signal("counter", 0)
        name = Signal("name", "test")
        doubled = Signal("doubled", counter * 2)
        is_valid = Signal("is_valid", name.length > 0)

        signals = [counter, name, doubled, is_valid]

        # Process as data-signals
        result = _handle_data_signals(signals)
        result_str = str(result)

        # Only regular signals should appear
        assert "counter" in result_str
        assert "name" in result_str
        assert "doubled" not in result_str
        assert "is_valid" not in result_str

    def test_computed_signal_attr_name_format(self):
        """Test that computed signal attribute names follow correct format."""
        test_cases = [
            ("simple", "data_computed_simple"),
            ("snake_case", "data_computed_snake_case"),
            ("with_numbers_123", "data_computed_with_numbers_123"),
        ]

        for signal_name, expected_attr in test_cases:
            base = Signal("base", 0)
            computed = Signal(signal_name, base + 1)

            attr_name, _ = computed.get_computed_attr()
            assert attr_name == expected_attr
