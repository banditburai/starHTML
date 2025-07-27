"""Mock Datastar context and browser APIs for testing."""

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock


class MockStorage:
    """Mock localStorage/sessionStorage for testing."""

    def __init__(self):
        self._storage = {}
        self._events = []

    def setItem(self, key: str, value: str):
        self._storage[key] = value
        self._events.append(("set", key, value))

    def getItem(self, key: str) -> str | None:
        return self._storage.get(key)

    def removeItem(self, key: str):
        if key in self._storage:
            del self._storage[key]
            self._events.append(("remove", key, None))

    def clear(self):
        self._storage.clear()
        self._events.append(("clear", None, None))

    def key(self, index: int) -> str | None:
        keys = list(self._storage.keys())
        return keys[index] if 0 <= index < len(keys) else None

    @property
    def length(self) -> int:
        return len(self._storage)

    def keys(self):
        return self._storage.keys()

    def get_events(self) -> list[tuple]:
        return self._events.copy()

    def reset_events(self):
        self._events.clear()


class MockResizeObserver:
    """Mock ResizeObserver for testing."""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.observed_elements: set[Mock] = set()
        self.entries: list[dict[str, Any]] = []

    def observe(self, element: Mock):
        self.observed_elements.add(element)

    def unobserve(self, element: Mock):
        self.observed_elements.discard(element)

    def disconnect(self):
        self.observed_elements.clear()

    def trigger_resize(self, element: Mock, width: int, height: int, top: int = 0, left: int = 0):
        """Trigger a resize event for testing."""
        if element in self.observed_elements:
            entry = {"target": element, "contentRect": {"width": width, "height": height, "top": top, "left": left}}
            self.entries.append(entry)
            self.callback([entry])


class MockWindow:
    """Mock window object for testing."""

    def __init__(self):
        self.innerWidth = 1024
        self.innerHeight = 768
        self.localStorage = MockStorage()
        self.sessionStorage = MockStorage()
        self.ResizeObserver = MockResizeObserver
        self.requestAnimationFrame = self._mock_raf
        self.cancelAnimationFrame = self._mock_cancel_raf
        self._raf_callbacks = {}
        self._raf_id = 0
        self._event_listeners = defaultdict(list)

    def _mock_raf(self, callback: Callable) -> int:
        """Mock requestAnimationFrame."""
        self._raf_id += 1
        self._raf_callbacks[self._raf_id] = callback
        # Execute immediately for testing
        callback(time.time() * 1000)
        return self._raf_id

    def _mock_cancel_raf(self, id: int):
        """Mock cancelAnimationFrame."""
        if id in self._raf_callbacks:
            del self._raf_callbacks[id]

    def addEventListener(self, event: str, callback: Callable, options=None):
        """Mock addEventListener."""
        self._event_listeners[event].append(callback)

    def removeEventListener(self, event: str, callback: Callable):
        """Mock removeEventListener."""
        if callback in self._event_listeners[event]:
            self._event_listeners[event].remove(callback)

    def dispatchEvent(self, event: Mock):
        """Mock dispatchEvent."""
        event_type = getattr(event, "type", "unknown")
        for callback in self._event_listeners[event_type]:
            callback(event)

    def resize(self, width: int, height: int):
        """Helper to trigger resize event."""
        self.innerWidth = width
        self.innerHeight = height
        self.dispatchEvent(Mock(type="resize"))


class MockElement:
    """Mock DOM element for testing."""

    def __init__(self, tag_name: str = "div"):
        self.tagName = tag_name
        self.attributes = {}
        self.dataset = {}
        self.style = {}
        self.children = []
        self.parentNode = None
        self.textContent = ""
        self.innerHTML = ""
        self.classList = MockClassList()
        self.boundingClientRect = {"width": 100, "height": 100, "top": 0, "left": 0, "right": 100, "bottom": 100}
        self._event_listeners = defaultdict(list)

    def getAttribute(self, name: str) -> str | None:
        return self.attributes.get(name)

    def setAttribute(self, name: str, value: str):
        self.attributes[name] = value
        # Update dataset for data-* attributes
        if name.startswith("data-"):
            key = name[5:].replace("-", "_")
            self.dataset[key] = value

    def removeAttribute(self, name: str):
        if name in self.attributes:
            del self.attributes[name]

    def hasAttribute(self, name: str) -> bool:
        return name in self.attributes

    def addEventListener(self, event: str, callback: Callable, options=None):
        self._event_listeners[event].append(callback)

    def removeEventListener(self, event: str, callback: Callable):
        if callback in self._event_listeners[event]:
            self._event_listeners[event].remove(callback)

    def dispatchEvent(self, event: Mock):
        event_type = getattr(event, "type", "unknown")
        for callback in self._event_listeners[event_type]:
            callback(event)

    def getBoundingClientRect(self) -> dict[str, float]:
        return self.boundingClientRect.copy()

    def setBoundingClientRect(self, **kwargs):
        self.boundingClientRect.update(kwargs)


class MockClassList:
    """Mock element classList."""

    def __init__(self):
        self._classes: set[str] = set()

    def add(self, *classes: str):
        self._classes.update(classes)

    def remove(self, *classes: str):
        self._classes.difference_update(classes)

    def toggle(self, class_name: str) -> bool:
        if class_name in self._classes:
            self._classes.remove(class_name)
            return False
        else:
            self._classes.add(class_name)
            return True

    def contains(self, class_name: str) -> bool:
        return class_name in self._classes

    def __contains__(self, class_name: str) -> bool:
        return class_name in self._classes


class MockDocument:
    """Mock document object for testing."""

    def __init__(self):
        self.elements = []
        self._event_listeners = defaultdict(list)

    def createElement(self, tag_name: str) -> MockElement:
        element = MockElement(tag_name)
        self.elements.append(element)
        return element

    def querySelectorAll(self, selector: str) -> list[MockElement]:
        # Simple mock implementation
        if selector.startswith("[data-"):
            attr_name = selector[1:-1]  # Remove brackets
            return [el for el in self.elements if el.hasAttribute(attr_name)]
        return self.elements

    def querySelector(self, selector: str) -> MockElement | None:
        results = self.querySelectorAll(selector)
        return results[0] if results else None

    def addEventListener(self, event: str, callback: Callable, options=None):
        self._event_listeners[event].append(callback)

    def removeEventListener(self, event: str, callback: Callable):
        if callback in self._event_listeners[event]:
            self._event_listeners[event].remove(callback)

    def dispatchEvent(self, event: Mock):
        event_type = getattr(event, "type", "unknown")
        for callback in self._event_listeners[event_type]:
            callback(event)


class MockDatastarContext:
    """Mock Datastar context for testing."""

    def __init__(self):
        self.signals = {}
        self.signal_updates = []
        self.evaluations = []
        self.merge_patches = []
        self.plugins = {}
        self.element_instances = {}

        # Mock functions
        self.sendSignalUpdate = Mock(side_effect=self._track_signal_update)
        self.evaluate = Mock(side_effect=self._track_evaluation)
        self.mergePatch = Mock(side_effect=self._track_merge_patch)
        self.registerPlugin = Mock(side_effect=self._register_plugin)

    def _track_signal_update(self, *args, **kwargs):
        """Track signal updates for testing."""
        self.signal_updates.append(
            {"timestamp": time.time(), "signals": self.signals.copy(), "args": args, "kwargs": kwargs}
        )

    def _track_evaluation(self, expression: str, context: dict[str, Any] = None):
        """Track evaluations for testing."""
        self.evaluations.append({"expression": expression, "context": context or {}, "timestamp": time.time()})

    def _track_merge_patch(self, patch: dict[str, Any]):
        """Track merge patches for testing."""
        self.merge_patches.append({"patch": patch, "timestamp": time.time()})
        # Apply patch to signals
        self.signals.update(patch)

    def _register_plugin(self, plugin_class):
        """Register a plugin."""
        self.plugins[plugin_class.pluginName] = plugin_class

    def reset_tracking(self):
        """Reset all tracking arrays."""
        self.signal_updates.clear()
        self.evaluations.clear()
        self.merge_patches.clear()

    def get_signal_history(self) -> list[dict[str, Any]]:
        """Get history of signal updates."""
        return self.signal_updates.copy()

    def get_evaluation_history(self) -> list[dict[str, Any]]:
        """Get history of evaluations."""
        return self.evaluations.copy()


class MockEvent:
    """Mock event object for testing."""

    def __init__(self, event_type: str, detail: Any = None):
        self.type = event_type
        self.detail = detail
        self.target = None
        self.currentTarget = None
        self.timestamp = time.time()
        self.defaultPrevented = False
        self.bubbles = True
        self.cancelable = True

    def preventDefault(self):
        self.defaultPrevented = True

    def stopPropagation(self):
        self.bubbles = False


def create_mock_browser_environment():
    """Create a complete mock browser environment for testing."""
    window = MockWindow()
    document = MockDocument()

    return {
        "window": window,
        "document": document,
        "localStorage": window.localStorage,
        "sessionStorage": window.sessionStorage,
        "ResizeObserver": MockResizeObserver,
        "requestAnimationFrame": window.requestAnimationFrame,
        "cancelAnimationFrame": window.cancelAnimationFrame,
    }


def create_mock_datastar_context():
    """Create a mock Datastar context for testing."""
    return MockDatastarContext()


def create_test_element(tag_name: str = "div", **attributes) -> MockElement:
    """Create a test element with attributes."""
    element = MockElement(tag_name)
    for name, value in attributes.items():
        if name.startswith("data_"):
            # Convert data_foo to data-foo
            attr_name = name.replace("_", "-")
            element.setAttribute(attr_name, value)
        else:
            element.setAttribute(name, value)
    return element


def simulate_scroll_event(element: MockElement, x: int = 0, y: int = 0):
    """Simulate a scroll event on an element."""
    event = MockEvent("scroll")
    event.target = element
    element.scrollLeft = x
    element.scrollTop = y
    return event


def simulate_resize_event(width: int, height: int) -> MockEvent:
    """Simulate a window resize event."""
    event = MockEvent("resize")
    return event


def wait_for_throttle(delay_ms: int = 20):
    """Wait for throttled functions to execute."""
    time.sleep(delay_ms / 1000)


class MockThrottleManager:
    """Test utilities for throttle management."""

    def __init__(self):
        self.execution_count = 0
        self.last_execution_time = 0
        self.execution_history = []

    def create_tracked_function(self):
        """Create a function that tracks executions."""

        def tracked_function(*args, **kwargs):
            self.execution_count += 1
            self.last_execution_time = time.time()
            self.execution_history.append(
                {"count": self.execution_count, "timestamp": self.last_execution_time, "args": args, "kwargs": kwargs}
            )

        return tracked_function

    def reset(self):
        """Reset tracking data."""
        self.execution_count = 0
        self.last_execution_time = 0
        self.execution_history.clear()

    def get_execution_times(self) -> list[float]:
        """Get list of execution timestamps."""
        return [entry["timestamp"] for entry in self.execution_history]

    def get_time_deltas(self) -> list[float]:
        """Get list of time deltas between executions."""
        times = self.get_execution_times()
        return [times[i] - times[i - 1] for i in range(1, len(times))]
