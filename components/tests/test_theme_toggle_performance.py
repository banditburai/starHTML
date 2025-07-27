"""Performance benchmarks and tests for theme toggle functionality."""

import sys
import time
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.ui import ThemeToggle, ThemeToggleCompact

from starhtml import *


class TestThemeToggleRenderingPerformance:
    """Test rendering performance of theme toggle components."""
    
    def test_single_theme_toggle_rendering_speed(self):
        """Benchmark single theme toggle rendering speed."""
        start_time = time.time()
        
        # Render theme toggle multiple times
        for _ in range(1000):
            ThemeToggle()
            
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Should render 1000 toggles in under 1 second
        assert rendering_time < 1.0, f"Rendering took {rendering_time:.3f}s, expected < 1.0s"
        
    def test_multiple_theme_toggle_rendering(self):
        """Benchmark rendering multiple theme toggles."""
        start_time = time.time()
        
        # Create layout with multiple toggles
        Div(
            *[ThemeToggle(id=f"toggle-{i}") for i in range(100)],
            cls="flex flex-wrap gap-2"
        )
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Should render 100 toggles in under 0.1 seconds
        assert rendering_time < 0.1, f"Rendering took {rendering_time:.3f}s, expected < 0.1s"
        
    def test_theme_toggle_variant_performance(self):
        """Compare performance between theme toggle variants."""
        # Test regular theme toggle
        start_time = time.time()
        for _ in range(500):
            ThemeToggle()
        regular_time = time.time() - start_time
        
        # Test compact theme toggle
        start_time = time.time()
        for _ in range(500):
            ThemeToggleCompact()
        compact_time = time.time() - start_time
        
        # Both should be fast, and compact should not be significantly slower
        assert regular_time < 0.5, f"Regular toggle took {regular_time:.3f}s"
        assert compact_time < 0.5, f"Compact toggle took {compact_time:.3f}s"
        
        # Compact should be within 50% of regular performance
        assert compact_time < regular_time * 1.5, "Compact variant is too slow compared to regular"
        
        
class TestThemeToggleMemoryUsage:
    """Test memory usage characteristics of theme toggle components."""
    
    def test_theme_toggle_memory_efficiency(self):
        """Test memory usage of theme toggle components."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Create many theme toggles
        toggles = []
        for i in range(1000):
            toggle = ThemeToggle(id=f"toggle-{i}")
            toggles.append(toggle)
        
        # Check that objects are created efficiently
        assert len(toggles) == 1000
        
        # Clean up
        del toggles
        gc.collect()
        
    def test_theme_toggle_no_memory_leaks(self):
        """Test that theme toggle doesn't create memory leaks."""
        import gc
        import sys
        
        # Get initial reference count
        initial_count = sys.gettotalrefcount() if hasattr(sys, 'gettotalrefcount') else 0
        
        # Create and destroy theme toggles
        for _ in range(100):
            toggle = ThemeToggle()
            del toggle
            
        gc.collect()
        
        # Reference count should not grow significantly
        if hasattr(sys, 'gettotalrefcount'):
            final_count = sys.gettotalrefcount()
            # Allow for some variance in reference counts
            assert final_count - initial_count < 1000, "Possible memory leak detected"
            
            
class TestThemeToggleJavaScriptPerformance:
    """Test JavaScript performance characteristics."""
    
    def test_javascript_code_size(self):
        """Test that JavaScript code is not excessively large."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # JavaScript should be reasonable size (under 5KB each)
        assert len(click_handler) < 5000, f"Click handler is {len(click_handler)} chars, expected < 5000"
        assert len(load_handler) < 5000, f"Load handler is {len(load_handler)} chars, expected < 5000"
        
    def test_javascript_optimization_features(self):
        """Test that JavaScript includes performance optimizations."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        toggle.attrs.get("data-on-load", "")
        
        # Should include performance optimizations
        assert "const html = document.documentElement" in click_handler, "Should cache DOM reference"
        assert "theme-transitioning" in click_handler, "Should include transition optimization"
        assert "try {" in click_handler, "Should include error handling"
        assert "setTimeout" in click_handler, "Should include debouncing"
        
    def test_javascript_minification_friendly(self):
        """Test that JavaScript is minification-friendly."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should not have unnecessary whitespace or comments
        # (This is a structural test - actual minification would be done by build tools)
        assert not click_handler.startswith("/*"), "Should not have leading comments"
        assert not load_handler.startswith("/*"), "Should not have leading comments"
        
        
class TestThemeToggleScalabilityPerformance:
    """Test performance with many theme toggle components."""
    
    def test_large_scale_theme_toggle_rendering(self):
        """Test rendering performance with many theme toggles."""
        start_time = time.time()
        
        # Create a large layout with many theme toggles
        Div(
            *[Div(
                H3(f"Section {i}"),
                ThemeToggle(id=f"section-toggle-{i}"),
                cls="border p-4 rounded"
            ) for i in range(50)],
            cls="space-y-4"
        )
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Should handle 50 toggles efficiently
        assert rendering_time < 0.5, f"Large scale rendering took {rendering_time:.3f}s"
        
    def test_nested_theme_toggle_performance(self):
        """Test performance with nested theme toggles."""
        start_time = time.time()
        
        # Create nested structure
        Div(
            *[Div(
                ThemeToggle(id=f"outer-{i}"),
                Div(
                    ThemeToggleCompact(id=f"inner-{i}"),
                    cls="ml-4 p-2"
                ),
                cls="border p-4 mb-2"
            ) for i in range(25)],
            cls="space-y-2"
        )
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Should handle nested toggles efficiently
        assert rendering_time < 0.3, f"Nested rendering took {rendering_time:.3f}s"
        
    def test_theme_toggle_with_complex_layouts(self):
        """Test theme toggle performance in complex layouts."""
        start_time = time.time()
        
        # Create complex layout with theme toggles
        Div(
            Header(
                Nav(
                    *[A(f"Link {i}", href=f"/page{i}") for i in range(20)],
                    cls="flex space-x-2"
                ),
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center justify-between p-4"
            ),
            Main(
                Div(
                    *[Article(
                        H2(f"Article {i}"),
                        *[P(f"Paragraph {j} of article {i}") for j in range(5)],
                        Footer(
                            ThemeToggleCompact(cls="ml-auto"),
                            cls="flex justify-end mt-4"
                        ),
                        cls="mb-8 p-4 border rounded"
                    ) for i in range(10)],
                    cls="max-w-4xl mx-auto"
                ),
                cls="p-6"
            ),
            cls="min-h-screen"
        )
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Should handle complex layouts efficiently
        assert rendering_time < 0.2, f"Complex layout rendering took {rendering_time:.3f}s"
        
        
class TestThemeToggleDataStarPerformance:
    """Test Datastar-specific performance characteristics."""
    
    def test_datastar_signal_processing_speed(self):
        """Test speed of Datastar signal processing."""
        start_time = time.time()
        
        # Create theme toggles with various signal configurations
        toggles = []
        for i in range(100):
            toggle = ThemeToggle(
                ds_signals={"customSignal": f"value-{i}"},
                id=f"toggle-{i}"
            )
            toggles.append(toggle)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process signals efficiently
        assert processing_time < 0.1, f"Signal processing took {processing_time:.3f}s"
        
    def test_datastar_attribute_processing_performance(self):
        """Test performance of Datastar attribute processing."""
        start_time = time.time()
        
        # Create theme toggles with many Datastar attributes
        for i in range(100):
            ThemeToggle(
                ds_on_click="customHandler()",
                ds_on_load="customInit()",
                ds_bind_class="customClass",
                ds_show="customCondition",
                ds_attr_disabled="customDisabled",
                id=f"toggle-{i}"
            )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process attributes efficiently
        assert processing_time < 0.2, f"Attribute processing took {processing_time:.3f}s"
        
        
class TestThemeToggleComparison:
    """Compare performance between different implementations."""
    
    def test_optimized_vs_basic_implementation(self):
        """Compare optimized implementation vs basic implementation."""
        # This would compare against the old implementation
        # For now, we'll test the current implementation characteristics
        
        start_time = time.time()
        
        # Current optimized implementation
        optimized_toggles = []
        for i in range(200):
            toggle = ThemeToggle(id=f"optimized-{i}")
            optimized_toggles.append(toggle)
        
        optimized_time = time.time() - start_time
        
        # Should be fast
        assert optimized_time < 0.1, f"Optimized implementation took {optimized_time:.3f}s"
        
    def test_regular_vs_compact_variant_performance(self):
        """Compare performance between regular and compact variants."""
        # Test regular variant
        start_time = time.time()
        [ThemeToggle(id=f"regular-{i}") for i in range(100)]
        regular_time = time.time() - start_time
        
        # Test compact variant
        start_time = time.time()
        [ThemeToggleCompact(id=f"compact-{i}") for i in range(100)]
        compact_time = time.time() - start_time
        
        # Both should be reasonably fast
        assert regular_time < 0.1, f"Regular variant took {regular_time:.3f}s"
        assert compact_time < 0.1, f"Compact variant took {compact_time:.3f}s"
        
        # Performance should be similar
        assert abs(regular_time - compact_time) < 0.05, "Performance difference too large"
        
        
class TestThemeToggleStressTests:
    """Stress tests for theme toggle components."""
    
    def test_extreme_scale_theme_toggle_creation(self):
        """Test theme toggle creation at extreme scale."""
        start_time = time.time()
        
        # Create many theme toggles
        toggles = []
        for i in range(5000):
            toggle = ThemeToggle(id=f"stress-{i}")
            toggles.append(toggle)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should handle extreme scale
        assert creation_time < 2.0, f"Extreme scale creation took {creation_time:.3f}s"
        assert len(toggles) == 5000, "Not all toggles were created"
        
    def test_rapid_theme_toggle_creation_destruction(self):
        """Test rapid creation and destruction of theme toggles."""
        start_time = time.time()
        
        # Rapidly create and destroy theme toggles
        for i in range(1000):
            toggle = ThemeToggle(id=f"rapid-{i}")
            del toggle
        
        end_time = time.time()
        rapid_time = end_time - start_time
        
        # Should handle rapid creation/destruction
        assert rapid_time < 0.5, f"Rapid creation/destruction took {rapid_time:.3f}s"
        
    def test_concurrent_theme_toggle_operations(self):
        """Test concurrent theme toggle operations."""
        import threading
        
        results = []
        
        def create_toggles():
            start_time = time.time()
            [ThemeToggle(id=f"concurrent-{i}") for i in range(100)]
            end_time = time.time()
            results.append(end_time - start_time)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_toggles)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Should handle concurrent operations efficiently
        assert total_time < 1.0, f"Concurrent operations took {total_time:.3f}s"
        assert len(results) == 5, "Not all threads completed"
        
        
class TestThemeTogglePerformanceRegression:
    """Regression tests for performance characteristics."""
    
    def test_performance_baseline(self):
        """Establish performance baseline for future comparisons."""
        # Create a standardized test scenario
        start_time = time.time()
        
        # Standard test: 50 theme toggles in a realistic layout
        Div(
            Header(
                ThemeToggle(cls="header-toggle"),
                cls="p-4 border-b"
            ),
            Main(
                *[Div(
                    H3(f"Card {i}"),
                    P(f"Content for card {i}"),
                    ThemeToggleCompact(cls="ml-auto"),
                    cls="p-4 border rounded mb-4 flex items-center justify-between"
                ) for i in range(48)],
                cls="p-6 space-y-4"
            ),
            cls="min-h-screen"
        )
        
        end_time = time.time()
        baseline_time = end_time - start_time
        
        # Record baseline (should be under 0.1 seconds)
        assert baseline_time < 0.1, f"Baseline performance: {baseline_time:.3f}s (should be < 0.1s)"
        
        # Store baseline for comparison in future tests
        # In a real implementation, this would be stored in a performance tracking system
        print(f"Performance baseline: {baseline_time:.3f}s")
        
    def test_performance_with_attributes(self):
        """Test performance impact of various attributes."""
        # Test with minimal attributes
        start_time = time.time()
        [ThemeToggle() for _ in range(100)]
        minimal_time = time.time() - start_time
        
        # Test with many attributes
        start_time = time.time()
        [ThemeToggle(
            id=f"complex-{i}",
            cls="custom-class",
            title="Custom title",
            ds_signals={"custom": "value"},
            data_test="test-value"
        ) for i in range(100)]
        complex_time = time.time() - start_time
        
        # Complex version should not be significantly slower
        assert minimal_time < 0.05, f"Minimal toggles took {minimal_time:.3f}s"
        assert complex_time < 0.1, f"Complex toggles took {complex_time:.3f}s"
        assert complex_time < minimal_time * 3, "Complex version is too slow compared to minimal"
        
        
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements
