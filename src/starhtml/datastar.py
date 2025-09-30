"""
Pythonic API for Datastar attributes and signals in StarHTML.

This module provides a powerful expression system to generate Datastar-compatible
JavaScript from Python code, enabling a type-safe and intuitive developer experience.

Key Concepts:
- Signal: A typed reference to a reactive piece of state (e.g., Signal("count", 0)).
- Expr: An abstract base class for objects that can be compiled to a JavaScript expression.
- Operators: Python operators like `+`, `-`, `==`, `&`, `|`, `~` are overloaded on
  Signal and Expr objects to build complex reactive expressions pythonically.
- Helpers: Functions like `match()`, `switch()`, `js()`, and `f()` provide
  higher-level constructs for common UI patterns.
"""

import builtins
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Union

from fastcore.xml import NotStr

# ============================================================================
# 1. Core Expression System (The Foundation)
# ============================================================================


class Expr(ABC):
    """Abstract base class for objects that can be compiled to JavaScript."""

    @abstractmethod
    def to_js(self) -> str:
        """Compile the expression to a JavaScript string."""
        pass

    def __str__(self) -> str:
        """Return the JavaScript representation of the expression."""
        return self.to_js()

    def __contains__(self, item: str) -> bool:
        """Check if string is contained in the JavaScript representation."""
        return item in self.to_js()

    # --- Property and Method Access ---
    def __getattr__(self, key: str) -> "PropertyAccess":
        """Access a property on the expression: `expr.key`."""
        return PropertyAccess(self, key)

    def __getitem__(self, index: Any) -> "IndexAccess":
        """Access an index or key on the expression: `expr[index]`."""
        return IndexAccess(self, index)

    @property
    def length(self) -> "PropertyAccess":
        return PropertyAccess(self, "length")

    # --- Logical & Comparison Operators ---
    def __and__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "&&", other)

    def __or__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "||", other)

    def __invert__(self) -> "UnaryOp":
        return UnaryOp("!", self)

    def __eq__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "===", other)

    def __ne__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "!==", other)

    def __lt__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "<", other)

    def __le__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "<=", other)

    def __gt__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, ">", other)

    def __ge__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, ">=", other)

    def eq(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "===", other)

    def neq(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "!==", other)

    def and_(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "&&", other)

    def or_(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "||", other)

    # --- Arithmetic Operators ---
    def __add__(self, other: Any) -> Union["BinaryOp", "TemplateLiteral"]:
        return TemplateLiteral([self, other]) if isinstance(other, str) else BinaryOp(self, "+", other)

    def __sub__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "-", other)

    def __mul__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "*", other)

    def __truediv__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "/", other)

    def __mod__(self, other: Any) -> "BinaryOp":
        return BinaryOp(self, "%", other)

    def __radd__(self, other: Any) -> Union["BinaryOp", "TemplateLiteral"]:
        return TemplateLiteral([other, self]) if isinstance(other, str) else BinaryOp(other, "+", self)

    def __rsub__(self, other: Any) -> "BinaryOp":
        return BinaryOp(other, "-", self)

    def __rmul__(self, other: Any) -> "BinaryOp":
        return BinaryOp(other, "*", self)

    def __rtruediv__(self, other: Any) -> "BinaryOp":
        return BinaryOp(other, "/", self)

    def __rmod__(self, other: Any) -> "BinaryOp":
        return BinaryOp(other, "%", self)

    def set(self, value: Any) -> "Assignment":
        return Assignment(self, value)

    def add(self, amount: Any) -> Union["_JSRaw", "Assignment"]:
        return _JSRaw(f"{self.to_js()}++") if type(amount) is int and amount == 1 else Assignment(self, self + amount)

    def sub(self, amount: Any) -> Union["_JSRaw", "Assignment"]:
        return _JSRaw(f"{self.to_js()}--") if type(amount) is int and amount == 1 else Assignment(self, self - amount)

    def mul(self, factor: Any) -> "Assignment":
        return Assignment(self, self * factor)

    def div(self, divisor: Any) -> "Assignment":
        return Assignment(self, self / divisor)

    def mod(self, divisor: Any) -> "Assignment":
        return Assignment(self, self % divisor)

    # --- Control Flow ---
    def if_(self, true_val: Any, false_val: Any = "") -> "Conditional":
        """Ternary expression: `condition ? true_val : false_val`."""
        return Conditional(self, true_val, false_val)

    def then(self, action: Any) -> "_JSRaw":
        """Execute action when condition is true: `if (condition) { action }`."""
        action_js = action if isinstance(action, str) else action.to_js()
        return _JSRaw(f"if ({self.to_js()}) {{ {action_js} }}")

    def toggle(self, *values: Any) -> "Assignment":
        if not values:
            return self.set(~self)
        result = values[0]
        for i in range(len(values) - 1, 0, -1):
            result = (self == values[i - 1]).if_(values[i], result)
        return self.set(result)

    # --- String Methods ---
    def lower(self) -> "MethodCall":
        return MethodCall(self, "toLowerCase", [])

    def upper(self) -> "MethodCall":
        return MethodCall(self, "toUpperCase", [])

    def strip(self) -> "MethodCall":
        return MethodCall(self, "trim", [])

    def contains(self, text: Any) -> "MethodCall":
        return MethodCall(self, "includes", [text])

    # --- Math Methods ---
    def round(self, digits: int = 0) -> "MethodCall":
        return (
            MethodCall(_JSRaw("Math"), "round", [self])
            if digits == 0
            else MethodCall(_JSRaw("Math"), "round", [self * (10**digits)]) / (10**digits)
        )

    def abs(self) -> "MethodCall":
        return MethodCall(_JSRaw("Math"), "abs", [self])

    def min(self, limit: Any) -> "MethodCall":
        return MethodCall(_JSRaw("Math"), "min", [self, limit])

    def max(self, limit: Any) -> "MethodCall":
        return MethodCall(_JSRaw("Math"), "max", [self, limit])

    def clamp(self, min_val: Any, max_val: Any) -> "MethodCall":
        return self.max(min_val).min(max_val)

    # Array methods - simple operations without callbacks
    def append(self, *items: Any) -> "MethodCall":
        return MethodCall(self, "push", [_ensure_expr(item) for item in items])

    def prepend(self, *items: Any) -> "MethodCall":
        return MethodCall(self, "unshift", [_ensure_expr(item) for item in items])

    def pop(self) -> "MethodCall":
        return MethodCall(self, "pop", [])

    def remove(self, index: Any) -> "MethodCall":
        return MethodCall(self, "splice", [_ensure_expr(index), _ensure_expr(1)])

    def join(self, separator: str = ",") -> "MethodCall":
        return MethodCall(self, "join", [_ensure_expr(separator)])

    def slice(self, start: Any = None, end: Any = None) -> "MethodCall":
        args = []
        if start is not None:
            args.append(_ensure_expr(start))
        if end is not None:
            args.append(_ensure_expr(end))
        return MethodCall(self, "slice", args)

    # --- Event Modifiers ---
    def with_(self, **modifiers) -> tuple:
        """Add event modifiers: expr.with_(prevent=True, debounce=300)"""
        return (self, modifiers)


class _JSLiteral(Expr):
    """Internal: A Python value to be safely encoded as a JavaScript literal."""

    __slots__ = ("value",)

    def __init__(self, value: Any):
        self.value = value

    def to_js(self) -> str:
        return json.dumps(self.value, separators=(",", ":"))


class TemplateLiteral(Expr):
    """JS template literal that efficiently combines parts."""

    __slots__ = ("parts",)

    def __init__(self, parts: list):
        self.parts = parts

    def to_js(self) -> str:
        if not self.parts:
            return '""'
        parts = []
        for part in self.parts:
            if isinstance(part, str):
                parts.append(part.replace("`", "\\`").replace("\\", "\\\\").replace("${", "\\${"))
            else:
                parts.append(f"${{{_ensure_expr(part).to_js()}}}")
        return f"`{''.join(parts)}`"

    def __add__(self, other: Any) -> "TemplateLiteral":
        return TemplateLiteral(self.parts + [other])

    def __radd__(self, other: Any) -> "TemplateLiteral":
        return TemplateLiteral([other] + self.parts)


class _JSRaw(Expr):
    """Internal: A raw string of JavaScript code to be passed through verbatim."""

    __slots__ = ("code",)

    def __init__(self, code: str):
        self.code = code

    def to_js(self) -> str:
        return self.code

    def __add__(self, other: Any) -> "TemplateLiteral":
        return TemplateLiteral([self, other])

    def __radd__(self, other: Any) -> "TemplateLiteral":
        return TemplateLiteral([other, self])

    def __call__(self, *args: Any) -> "_JSRaw":
        args_js = ", ".join(_ensure_expr(arg).to_js() for arg in args)
        return _JSRaw(f"{self.code}({args_js})")


class BinaryOp(Expr):
    """A binary operation like `a + b` or `x > y`."""

    __slots__ = ("left", "op", "right")

    def __init__(self, left: Any, op: str, right: Any):
        self.left = _ensure_expr(left)
        self.op = op
        self.right = _ensure_expr(right)

    def to_js(self) -> str:
        return f"({self.left.to_js()} {self.op} {self.right.to_js()})"


class UnaryOp(Expr):
    """A unary operation like `!x`."""

    __slots__ = ("op", "expr")

    def __init__(self, op: str, expr: Expr):
        self.op, self.expr = op, expr

    def to_js(self) -> str:
        return f"{self.op}({self.expr.to_js()})"


class Conditional(Expr):
    """A ternary expression: `condition ? true_val : false_val`."""

    __slots__ = ("condition", "true_val", "false_val")

    def __init__(self, condition: Expr, true_val: Any, false_val: Any):
        self.condition, self.true_val, self.false_val = condition, _ensure_expr(true_val), _ensure_expr(false_val)

    def to_js(self) -> str:
        return f"({self.condition.to_js()} ? {self.true_val.to_js()} : {self.false_val.to_js()})"


class Assignment(Expr):
    """An assignment: `target = value`."""

    __slots__ = ("target", "value")

    def __init__(self, target: Expr, value: Any):
        self.target, self.value = target, _ensure_expr(value)

    def to_js(self) -> str:
        return f"{self.target.to_js()} = {self.value.to_js()}"


class MethodCall(Expr):
    """A method call: `obj.method(arg1, arg2)`."""

    __slots__ = ("obj", "method", "args")

    def __init__(self, obj: Expr, method: str, args: list[Any]):
        self.obj, self.method, self.args = obj, method, [_ensure_expr(a) for a in args]

    def to_js(self) -> str:
        return f"{self.obj.to_js()}.{self.method}({', '.join(arg.to_js() for arg in self.args)})"


class PropertyAccess(Expr):
    """Property access: `obj.prop` that can be called like a method."""

    __slots__ = ("obj", "prop")

    def __init__(self, obj: Expr, prop: str):
        self.obj, self.prop = obj, prop

    def to_js(self) -> str:
        return f"{self.obj.to_js()}.{self.prop}"

    def __call__(self, *args: Any) -> "MethodCall":
        return MethodCall(self.obj, self.prop, args)


class IndexAccess(Expr):
    """Index access for arrays or objects: `obj[index]`."""

    __slots__ = ("obj", "index")

    def __init__(self, obj: Expr, index: Any):
        self.obj, self.index = obj, _ensure_expr(index)

    def to_js(self) -> str:
        return f"{self.obj.to_js()}[{self.index.to_js()}]"


def _ensure_expr(value: Any) -> Expr:
    """Idempotently convert a Python value into an Expr object."""
    return value if isinstance(value, Expr) else _JSLiteral(value)


class Signal(Expr):
    """A typed, validated signal reference."""

    def __init__(
        self,
        name: str,
        initial: Any = None,
        type_: type | None = None,
        namespace: str | None = None,
        _ref_only: bool = False,
    ):
        self._name = name
        self._initial = initial
        self._namespace = namespace
        self._ref_only = _ref_only
        self._is_computed = isinstance(initial, Expr)
        self.type_ = type_ or self._infer_type(initial)
        self._validate_name()

    def _infer_type(self, initial: Any) -> type:
        """Infer type from initial value, checking bool before int."""
        if initial is None:
            return str
        if isinstance(initial, bool):
            return bool
        if isinstance(initial, int | float | str):
            return type(initial)
        if isinstance(initial, list | tuple):
            return list
        if isinstance(initial, dict):
            return dict
        return type(initial)

    def _validate_name(self):
        if not re.match(r"^[a-z][a-z0-9_]*$", self._name):
            raise ValueError(f"Signal name must be snake_case: '{self._name}'")

    @property
    def full_name(self) -> str:
        return f"{self._namespace}_{self._name}" if self._namespace else self._name

    def to_dict(self) -> dict[str, Any]:
        if self._is_computed:
            return {}
        return {self.full_name: self._initial}

    def get_computed_attr(self) -> tuple[str, Any] | None:
        if self._is_computed:
            return (f"data_computed_{self._name}", self._initial)
        return None

    def to_js(self) -> str:
        return f"${self.full_name}"

    def __hash__(self):
        return hash((self._name, self._namespace))

    def __eq__(self, other) -> "BinaryOp":
        return BinaryOp(self, "===", _ensure_expr(other))

    def is_same_as(self, other: "Signal") -> bool:
        return isinstance(other, Signal) and self._name == other._name and self._namespace == other._namespace

    def __getattr__(self, key: str) -> PropertyAccess:
        return PropertyAccess(self, key)


_JS_EXPR_PREFIXES = ("$", "`", "!", "(", "'", "evt.")
_JS_EXPR_KEYWORDS = {"true", "false", "null", "undefined"}


def _to_js(value: Any, allow_expressions: bool = True) -> str:
    """Convert Python value to JavaScript string."""
    match value:
        case Expr() as expr:
            return expr.to_js()
        case None:
            return "null"
        case bool():
            return "true" if value else "false"
        case int() | float():
            return str(value)
        case str() as s:
            if allow_expressions and (s.startswith(_JS_EXPR_PREFIXES) or s in _JS_EXPR_KEYWORDS):
                return s
            return json.dumps(s)
        case dict() as d:
            try:
                return json.dumps(d)
            except (TypeError, ValueError):
                items = [f"{_to_js(k, allow_expressions)}: {_to_js(v, allow_expressions)}" for k, v in d.items()]
                return f"({{{', '.join(items)}}})"
        case list() | tuple() as l:
            try:
                return json.dumps(l)
            except (TypeError, ValueError):
                items = [_to_js(item, allow_expressions) for item in l]
                return f"[{', '.join(items)}]"
        case _:
            return json.dumps(str(value))


def to_js_value(value: Any) -> str:
    """Convert Python value to JavaScript expression."""
    return _to_js(value, allow_expressions=True)


# --- General Purpose Helpers ---


def js(code: str) -> _JSRaw:
    """Mark a string as raw JavaScript code."""
    return _JSRaw(code)


def value(v: Any) -> _JSLiteral:
    """Mark a Python value to be safely encoded as a JavaScript literal."""
    if isinstance(v, Expr):
        raise TypeError(
            f"value() should not be used with {type(v).__name__} objects. Use the object directly instead of wrapping it with value()."
        )
    return _JSLiteral(v)


def f(template_str: str, **kwargs: Any) -> _JSRaw:
    """Create reactive JavaScript template literal, like a Python f-string."""

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        val = kwargs.get(key)
        if val is None:
            return match.group(0)
        return f"${{{to_js_value(val)}}}"

    js_template = re.sub(r"\{(\w+)\}", replacer, template_str)
    return _JSRaw(f"`{js_template}`")


def regex(pattern: str) -> _JSRaw:
    """Create JavaScript regex literal: regex("^todo_") → /^todo_/"""
    return _JSRaw(f"/{pattern}/")


# --- Conditional Logic Helpers ---


def match(subject: Any, /, **patterns: Any) -> _JSRaw:
    """Pattern matching for conditional values (like Python match/case)."""
    subject_expr = _ensure_expr(subject)
    default_val = patterns.pop("default", "")
    result = _ensure_expr(default_val)
    for pattern, val in reversed(patterns.items()):
        check_expr = subject_expr == _ensure_expr(pattern)
        result = check_expr.if_(val, result)
    return _JSRaw(result.to_js())


def switch(cases: list[tuple[Any, Any]], /, default: Any = "") -> _JSRaw:
    """Sequential condition evaluation (if/elif/else chain)."""
    result = _ensure_expr(default)
    for condition, val in reversed(cases):
        result = _ensure_expr(condition).if_(val, result)
    return _JSRaw(result.to_js())


def collect(cases: list[tuple[Any, Any]], /, join_with: str = " ") -> _JSRaw:
    """Combines values from all true conditions (for CSS classes, etc.)."""
    if not cases:
        return _JSRaw("''")
    parts = [_ensure_expr(condition).if_(val, "").to_js() for condition, val in cases]
    array_expr = "[" + ", ".join(parts) + "]"
    return _JSRaw(f"{array_expr}.filter(Boolean).join('{join_with}')")


# --- Logical Aggregation Helpers ---


def _iterable_args(*args):
    """Support Python built-in style: if passed a single iterable, unpack it."""
    return (
        args[0]
        if builtins.len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], str | Signal | Expr)
        else args
    )


def all(*signals) -> _JSRaw:
    """Check if all signals are truthy: all(a, b, c) → !!a && !!b && !!c"""
    if not signals:
        return _JSRaw("true")
    signals = _iterable_args(*signals)
    return _JSRaw(" && ".join(f"!!{_ensure_expr(s).to_js()}" for s in signals))


def any(*signals) -> _JSRaw:
    """Check if any signal is truthy: any(a, b, c) → !!a || !!b || !!c"""
    if not signals:
        return _JSRaw("false")
    signals = _iterable_args(*signals)
    return _JSRaw(" || ".join(f"!!{_ensure_expr(s).to_js()}" for s in signals))


# --- Action Helpers ---


def post(url: str, data: dict[str, Any] | None = None, **kwargs) -> _JSRaw:
    return _action("post", url, data, **kwargs)


def get(url: str, data: dict[str, Any] | None = None, **kwargs) -> _JSRaw:
    return _action("get", url, data, **kwargs)


def put(url: str, data: dict[str, Any] | None = None, **kwargs) -> _JSRaw:
    return _action("put", url, data, **kwargs)


def patch(url: str, data: dict[str, Any] | None = None, **kwargs) -> _JSRaw:
    return _action("patch", url, data, **kwargs)


def delete(url: str, data: dict[str, Any] | None = None, **kwargs) -> _JSRaw:
    return _action("delete", url, data, **kwargs)


def clipboard(text: str = None, element: str = None, signal: str = None) -> _JSRaw:
    if not ((text is None) ^ (element is None)):
        raise ValueError("Must provide exactly one of: text or element")

    signal_suffix = f", {to_js_value(signal)}" if signal else ""

    if text is not None:
        return _JSRaw(f"@clipboard({to_js_value(text)}{signal_suffix})")

    # Element mode: generate appropriate DOM access
    if element == "el":
        js_expr = "el"
    elif element.startswith(("#", ".")):
        js_expr = f"document.querySelector({to_js_value(element)})"
    else:
        js_expr = f"document.getElementById({to_js_value(element)})"

    return _JSRaw(f"@clipboard({js_expr}.textContent{signal_suffix})")


def _action(verb: str, url: str, data: dict[str, Any] | None = None, **kwargs) -> _JSRaw:
    payload = {**(data or {}), **kwargs}
    if not payload:
        return _JSRaw(f"@{verb}('{url}')")
    parts = [f"{k}: {to_js_value(v)}" for k, v in payload.items()]
    return _JSRaw(f"@{verb}('{url}', {{{', '.join(parts)}}})")


# --- JavaScript Global Objects ---

console = js("console")
Math = js("Math")
JSON = js("JSON")
Object = js("Object")
Array = js("Array")
Date = js("Date")
Number = js("Number")
String = js("String")
Boolean = js("Boolean")


# --- Core Datastar Keyword Argument Processing Engine ---


def _normalize_data_key(key: str) -> str:
    """Normalizes a Pythonic key to its `data-*` attribute equivalent."""
    for prefix in ("data_computed_", "data_on_", "data_attr_", "data_"):
        if key.startswith(prefix):
            name = key.removeprefix(prefix)
            slug = name if prefix == "data_computed_" else name.replace("_", "-")
            return f"{prefix.removesuffix('_').replace('_', '-')}-{slug}"
    return key.replace("_", "-")


def _build_modifier_suffix(modifiers: dict[str, Any]) -> str:
    """Builds a modifier suffix (e.g., `__debounce__300ms`) from a dictionary."""
    if not modifiers:
        return ""
    parts = []
    for name, value in modifiers.items():
        match value:
            case True:
                parts.append(name)
            case False:
                parts.append(f"{name}.false")  # Preserve explicit false
            case int() | float():
                part = f"n{abs(value)}" if value < 0 else str(value)
                parts.append(f"{name}.{part}")
            case str():
                parts.append(f"{name}.{value}")
    return f"__{'__'.join(parts)}" if parts else ""


def _expr_list_to_js(items: list[Any], collect_signals: callable) -> str:
    """Joins a list of expressions into a semicolon-separated JS string."""

    def process_item(item):
        if isinstance(item, Expr | Signal):
            collect_signals(item)
            return item.to_js()
        return str(item)

    return "; ".join(process_item(item) for item in items)


def _collect_signals(expr: Any, sink: set[Signal]) -> None:
    """Recursively traverses an expression to find all Signal references."""
    if isinstance(expr, Signal):
        sink.add(expr)
    elif isinstance(expr, Expr):
        attrs = (
            (getattr(expr, slot, None) for slot in expr.__slots__)
            if hasattr(expr, "__slots__")
            else expr.__dict__.values()
            if hasattr(expr, "__dict__")
            else ()
        )

        for attr in attrs:
            if isinstance(attr, Signal | Expr):
                _collect_signals(attr, sink)
            elif isinstance(attr, list | tuple):
                for item in attr:
                    _collect_signals(item, sink)


def build_data_signals(signals: dict[str, Any]) -> NotStr:
    """Builds a non-escaped JavaScript object literal for `data-signals`."""
    parts = [f"{key}: {_to_js(val, allow_expressions=False)}" for key, val in signals.items()]
    return NotStr("{" + ", ".join(parts) + "}")


def _handle_data_signals(value: Any) -> Any:
    """Processes the value for a `data_signals` keyword argument."""
    signal_dict = {}
    match value:
        case list() | tuple():
            for s in value:
                if isinstance(s, Signal) and not s._ref_only:
                    signal_dict.update(s.to_dict())
        case dict() as d:
            signal_dict = d
        case Signal() as s:
            signal_dict = s.to_dict()
    return build_data_signals(signal_dict) if signal_dict else value


def _apply_additive_class_behavior(processed: dict) -> None:
    """Combines cls and data_attr_cls for SSR + reactive classes."""
    if "cls" in processed and "data_attr_cls" in processed:
        base_classes = processed.pop("cls")
        reactive_classes = str(processed.pop("data_attr_cls"))
        if reactive_classes.startswith("(") and reactive_classes.endswith(")"):
            reactive_classes = reactive_classes[1:-1]
        processed["data-attr-class"] = NotStr(f"`{base_classes} ${{{reactive_classes}}}`")


# --- Main Engine ---


def process_datastar_kwargs(kwargs: dict) -> tuple[dict, set[Signal]]:
    """Maps Pythonic kwargs to Datastar data-* attributes."""
    processed: dict[str, Any] = {}
    signals_found: set[Signal] = set()

    def collect(expr: Any) -> None:
        _collect_signals(expr, signals_found)

    for key, value in kwargs.items():
        if key == "data_signals":
            processed["data-signals"] = _handle_data_signals(value)
            continue

        normalized_key = _normalize_data_key(key)
        match value:
            case list():
                processed[normalized_key] = NotStr(_expr_list_to_js(value, collect))
            case (expr, modifiers) if isinstance(modifiers, dict):
                js_str = ""
                if isinstance(expr, Expr | Signal):
                    collect(expr)
                    js_str = expr.to_js()
                elif isinstance(expr, list):
                    js_str = _expr_list_to_js(expr, collect)
                else:
                    js_str = str(expr)
                final_key = f"{normalized_key}{_build_modifier_suffix(modifiers)}"
                processed[final_key] = NotStr(js_str)
            case Expr() as expr:
                collect(expr)
                js_str = expr.to_js()
                if key == "data_bind" and isinstance(expr, Signal):
                    processed["data-bind"] = expr.full_name
                elif key == "data_class":
                    processed["data-class"] = NotStr(js_str)
                else:
                    processed[normalized_key] = NotStr(js_str)
            case _JSLiteral() | _JSRaw() | dict() as val:
                processed[normalized_key] = NotStr(_to_js(val))
            case _:
                processed[key] = value

    _apply_additive_class_behavior(processed)
    return processed, signals_found


# ============================================================================
# 8. Public API Exports
# ============================================================================

__all__ = [
    "Signal",
    "Expr",
    "js",
    "value",
    "f",
    "regex",
    "match",
    "switch",
    "collect",
    "all",
    "any",
    "post",
    "get",
    "put",
    "patch",
    "delete",
    "clipboard",
    "console",
    "Math",
    "JSON",
    "Object",
    "Array",
    "Date",
    "Number",
    "String",
    "Boolean",
    "process_datastar_kwargs",
    "to_js_value",
]
