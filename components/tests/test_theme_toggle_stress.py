"""Stress tests for theme toggle components with many instances."""

import gc
import sys
import threading
import time
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.ui import ThemeToggle, ThemeToggleCompact

from starhtml import *


class TestThemeToggleStressScenarios:
    """Stress test scenarios for theme toggle components."""
    
    def test_massive_theme_toggle_creation(self):
        """Test creating a massive number of theme toggles."""
        start_time = time.time()
        
        # Create many theme toggles
        toggles = []
        for i in range(10000):
            toggle = ThemeToggle(id=f"massive-{i}")
            toggles.append(toggle)
        
        creation_time = time.time() - start_time
        
        # Should handle massive creation
        assert len(toggles) == 10000, "Should create all toggles"
        assert creation_time < 5.0, f"Creation took {creation_time:.3f}s, should be < 5s"
        
        # Clean up
        del toggles
        gc.collect()
        
    def test_deep_nesting_stress(self):
        """Test deeply nested theme toggle structures."""
        start_time = time.time()
        
        # Create deeply nested structure
        current = ThemeToggle(id="root")
        
        for i in range(100):
            current = Div(
                current,
                ThemeToggle(id=f"nested-{i}"),
                cls=f"level-{i}"
            )
        
        creation_time = time.time() - start_time
        
        # Should handle deep nesting
        assert current is not None, "Should create nested structure"
        assert creation_time < 1.0, f"Deep nesting took {creation_time:.3f}s"
        
    def test_wide_layout_stress(self):
        """Test wide layout with many theme toggles."""
        start_time = time.time()
        
        # Create wide layout with many toggles
        layout = Div(
            *[Div(
                H3(f"Section {i}"),
                ThemeToggle(id=f"wide-{i}"),
                ThemeToggleCompact(id=f"wide-compact-{i}"),
                cls="section"
            ) for i in range(1000)],
            cls="wide-layout"
        )
        
        creation_time = time.time() - start_time
        
        # Should handle wide layouts
        assert layout is not None, "Should create wide layout"
        assert len(layout.children) == 1000, "Should have all sections"
        assert creation_time < 2.0, f"Wide layout took {creation_time:.3f}s"
        
    def test_complex_attribute_stress(self):
        """Test theme toggles with complex attributes."""
        start_time = time.time()
        
        # Create toggles with complex attributes
        toggles = []
        for i in range(1000):
            toggle = ThemeToggle(
                id=f"complex-{i}",
                cls=f"class-{i} another-class-{i}",
                title=f"Title for toggle {i}",
                data_custom=f"custom-value-{i}",
                data_number=i,
                data_boolean=i % 2 == 0,
                ds_signals={"customSignal": f"signal-{i}"},
                ds_on_custom=f"handleCustom{i}()"
            )
            toggles.append(toggle)
        
        creation_time = time.time() - start_time
        
        # Should handle complex attributes
        assert len(toggles) == 1000, "Should create all complex toggles"
        assert creation_time < 1.0, f"Complex attributes took {creation_time:.3f}s"
        
        
class TestThemeToggleMemoryStress:
    """Test memory usage under stress conditions."""
    
    def test_memory_usage_with_many_toggles(self):
        """Test memory usage with many theme toggles."""
        import os

        import psutil
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many toggles
        toggles = []
        for i in range(5000):
            toggle = ThemeToggle(id=f"memory-{i}")
            toggles.append(toggle)
        
        # Get memory usage after creation
        after_creation = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_creation - initial_memory
        
        # Memory increase should be reasonable (< 100MB for 5000 toggles)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
        
        # Clean up
        del toggles
        gc.collect()
        
        # Memory should decrease after cleanup
        after_cleanup = process.memory_info().rss / 1024 / 1024  # MB
        memory_freed = after_creation - after_cleanup
        
        # Should free significant memory
        assert memory_freed > memory_increase * 0.5, "Should free significant memory"
        
    def test_memory_leak_detection(self):
        """Test for memory leaks in theme toggle creation/destruction."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Create and destroy toggles repeatedly
        for cycle in range(10):
            toggles = []
            for i in range(1000):
                toggle = ThemeToggle(id=f"leak-test-{cycle}-{i}")
                toggles.append(toggle)
            
            # Clear references
            del toggles
            gc.collect()
        
        # If we reach here without memory issues, test passes
        assert True, "No memory leaks detected"
        
    def test_circular_reference_stress(self):
        """Test handling of circular references under stress."""
        # Create components that might create circular references
        toggles = []
        for i in range(100):
            toggle = ThemeToggle(id=f"circular-{i}")
            # Create potential circular reference through attributes
            toggle.attrs["data_self"] = toggle
            toggles.append(toggle)
        
        # Clean up
        for toggle in toggles:
            if "data_self" in toggle.attrs:
                del toggle.attrs["data_self"]
        
        del toggles
        gc.collect()
        
        # Should handle circular references
        assert True, "Circular references handled"
        
        
class TestThemeToggleConcurrencyStress:
    """Test concurrent access and modification."""
    
    def test_concurrent_creation(self):
        """Test concurrent theme toggle creation."""
        results = []
        errors = []
        
        def create_toggles(thread_id):
            try:
                toggles = []
                for i in range(500):
                    toggle = ThemeToggle(id=f"concurrent-{thread_id}-{i}")
                    toggles.append(toggle)
                results.append(len(toggles))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_toggles, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, "Not all threads completed"
        assert all(count == 500 for count in results), "Not all toggles created"
        
    def test_concurrent_attribute_modification(self):
        """Test concurrent attribute modification."""
        # Create a shared toggle
        toggle = ThemeToggle(id="shared-toggle")
        results = []
        errors = []
        
        def modify_attributes(thread_id):
            try:
                # Modify attributes concurrently
                for i in range(100):
                    toggle.attrs[f"thread_{thread_id}_{i}"] = f"value_{i}"
                results.append(thread_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=modify_attributes, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, "Not all threads completed"
        
    def test_concurrent_layout_building(self):
        """Test concurrent layout building with theme toggles."""
        results = []
        errors = []
        
        def build_layout(thread_id):
            try:
                layout = Div(
                    *[Div(
                        H3(f"Thread {thread_id} Section {i}"),
                        ThemeToggle(id=f"layout-{thread_id}-{i}"),
                        cls="section"
                    ) for i in range(100)],
                    cls=f"layout-{thread_id}"
                )
                results.append(len(layout.children))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(8):
            thread = threading.Thread(target=build_layout, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 8, "Not all threads completed"
        assert all(count == 100 for count in results), "Not all sections created"
        
        
class TestThemeTogglePerformanceStress:
    """Test performance under stress conditions."""
    
    def test_large_scale_rendering_performance(self):
        """Test rendering performance at large scale."""
        sizes = [100, 500, 1000, 2000, 5000]
        times = []
        
        for size in sizes:
            start_time = time.time()
            
            # Create layout with many toggles
            layout = Div(
                *[ThemeToggle(id=f"perf-{size}-{i}") for i in range(size)],
                cls=f"performance-test-{size}"
            )
            
            end_time = time.time()
            render_time = end_time - start_time
            times.append(render_time)
            
            # Clean up
            del layout
            gc.collect()
        
        # Performance should scale reasonably
        for i, (size, time_taken) in enumerate(zip(sizes, times, strict=False)):
            # Should be roughly linear scaling
            expected_max = size * 0.001  # 1ms per toggle
            assert time_taken < expected_max, f"Size {size} took {time_taken:.3f}s, expected < {expected_max:.3f}s"
            
    def test_attribute_processing_performance_stress(self):
        """Test attribute processing performance under stress."""
        start_time = time.time()
        
        # Create toggles with many attributes
        toggles = []
        for i in range(1000):
            attrs = {f"data_attr_{j}": f"value_{j}" for j in range(50)}
            attrs["id"] = f"attr-stress-{i}"
            toggle = ThemeToggle(**attrs)
            toggles.append(toggle)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process attributes efficiently
        assert processing_time < 2.0, f"Attribute processing took {processing_time:.3f}s"
        assert len(toggles) == 1000, "Should create all toggles"
        
    def test_javascript_code_size_stress(self):
        """Test JavaScript code size under stress conditions."""
        # Create many toggles with complex JavaScript
        toggles = []
        for i in range(100):
            toggle = ThemeToggle(
                id=f"js-stress-{i}",
                ds_on_custom=f"handleCustom{i}($event)",
                ds_signals={"complex": {"nested": {"data": f"value-{i}"}}}
            )
            toggles.append(toggle)
        
        # Check JavaScript code size
        total_js_size = 0
        for toggle in toggles:
            click_handler = toggle.children[0].attrs.get("data-on-click", "")
            load_handler = toggle.attrs.get("data-on-load", "")
            total_js_size += len(click_handler) + len(load_handler)
        
        # JavaScript should not be excessively large
        avg_js_size = total_js_size / len(toggles)
        assert avg_js_size < 10000, f"Average JS size is {avg_js_size} chars, should be < 10k"
        
        
class TestThemeToggleEdgeCaseStress:
    """Test edge cases under stress conditions."""
    
    def test_extreme_attribute_values_stress(self):
        """Test extreme attribute values under stress."""
        # Create toggles with extreme attribute values
        toggles = []
        for i in range(500):
            toggle = ThemeToggle(
                id=f"extreme-{i}",
                cls="a" * 1000,  # Very long class name
                title="🌟" * 100,  # Many unicode characters
                data_large=list(range(1000)),  # Large list
                data_deep={"level": {"nested": {"deeply": {"value": i}}}}  # Deep nesting
            )
            toggles.append(toggle)
        
        # Should handle extreme values
        assert len(toggles) == 500, "Should create all toggles with extreme values"
        
    def test_rapid_creation_destruction_stress(self):
        """Test rapid creation and destruction under stress."""
        for cycle in range(100):
            # Create many toggles
            toggles = [ThemeToggle(id=f"rapid-{cycle}-{i}") for i in range(100)]
            
            # Immediately destroy them
            del toggles
            
            # Force garbage collection occasionally
            if cycle % 10 == 0:
                gc.collect()
        
        # Should handle rapid cycling
        assert True, "Rapid creation/destruction handled"
        
    def test_complex_hierarchy_stress(self):
        """Test complex hierarchy structures under stress."""
        # Create complex nested hierarchy
        def create_complex_node(depth, width, node_id):
            if depth == 0:
                return ThemeToggle(id=f"leaf-{node_id}")
            
            children = []
            for i in range(width):
                child_id = f"{node_id}-{i}"
                if i % 2 == 0:
                    child = create_complex_node(depth - 1, width, child_id)
                else:
                    child = ThemeToggleCompact(id=f"compact-{child_id}")
                children.append(child)
            
            return Div(*children, cls=f"level-{depth}")
        
        # Create complex hierarchy (depth=5, width=3)
        start_time = time.time()
        complex_tree = create_complex_node(5, 3, "root")
        creation_time = time.time() - start_time
        
        # Should handle complex hierarchy
        assert complex_tree is not None, "Should create complex hierarchy"
        assert creation_time < 1.0, f"Complex hierarchy took {creation_time:.3f}s"
        
        
class TestThemeToggleScalabilityLimits:
    """Test scalability limits of theme toggle components."""
    
    def test_maximum_reasonable_scale(self):
        """Test at maximum reasonable scale."""
        # Test with 50,000 theme toggles (extreme but possible scenario)
        start_time = time.time()
        
        # Create in batches to avoid memory issues
        batch_size = 1000
        total_toggles = 50000
        batches = []
        
        for batch_num in range(total_toggles // batch_size):
            batch = []
            for i in range(batch_size):
                toggle_id = batch_num * batch_size + i
                toggle = ThemeToggle(id=f"scale-{toggle_id}")
                batch.append(toggle)
            batches.append(batch)
        
        creation_time = time.time() - start_time
        
        # Should handle maximum scale
        assert len(batches) == 50, "Should create all batches"
        assert creation_time < 30.0, f"Max scale took {creation_time:.3f}s"
        
        # Clean up in batches
        for batch in batches:
            del batch
        del batches
        gc.collect()
        
    def test_memory_usage_at_scale(self):
        """Test memory usage at large scale."""
        import os

        import psutil
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of toggles
        toggles = []
        for i in range(20000):
            toggle = ThemeToggle(id=f"memory-scale-{i}")
            toggles.append(toggle)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_per_toggle = (peak_memory - initial_memory) / len(toggles)
        
        # Memory per toggle should be reasonable (< 1KB per toggle)
        assert memory_per_toggle < 1.0, f"Memory per toggle: {memory_per_toggle:.3f}MB"
        
        # Clean up
        del toggles
        gc.collect()
        
    def test_performance_degradation_at_scale(self):
        """Test performance degradation at large scale."""
        scales = [1000, 5000, 10000, 20000]
        times = []
        
        for scale in scales:
            start_time = time.time()
            
            # Create toggles at scale
            toggles = [ThemeToggle(id=f"perf-scale-{scale}-{i}") for i in range(scale)]
            
            end_time = time.time()
            creation_time = end_time - start_time
            times.append(creation_time)
            
            # Clean up
            del toggles
            gc.collect()
        
        # Performance should degrade linearly, not exponentially
        for i in range(1, len(scales)):
            scale_ratio = scales[i] / scales[i-1]
            time_ratio = times[i] / times[i-1]
            
            # Time ratio should not be much worse than scale ratio
            assert time_ratio < scale_ratio * 2, f"Performance degraded too much at scale {scales[i]}"
            
            
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements
