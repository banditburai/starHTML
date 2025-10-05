"""Pythonic API for Datastar attributes and signals in StarHTML.

Provides an expression system to generate Datastar-compatible JavaScript from Python,
with type safety and operator overloading for building reactive UIs.

Core types:
- Signal: Typed reactive state reference (e.g., Signal("count", 0))
- Expr: Abstract base for JavaScript expression generation
- Helpers: match(), switch(), js(), f() and others for common patterns
"""

import builtins
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Union

from fastcore.xml import NotStr
from rjsmin import jsmin


class Expr(ABC):
    """Base class for objects that compile to JavaScript with operator overloading."""

    @abstractmethod
    def to_js(self) -> str:
        """Compile to JavaScript code."""
        pass

    def __str__(self) -> str:
        return self.to_js()

    def __contains__(self, item: str) -> bool:
        return item in self.to_js()

    def __getattr__(self, key: str) -> "PropertyAccess":
        return PropertyAccess(self, key)

    def __getitem__(self, index: Any) -> "IndexAccess":
        return IndexAccess(self, index)

    @property
    def length(self) -> "PropertyAccess":
        return PropertyAccess(self, "length")

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

    def if_(self, true_val: Any, false_val: Any = "") -> "Conditional":
        """Ternary: cond.if_(yes, no) → cond ? yes : no"""
        return Conditional(self, true_val, false_val)

    def then(self, action: Any) -> "_JSRaw":
        """Execute when true: cond.then(action) → if (cond) { action }"""
        action_js = action if isinstance(action, str) else action.to_js()
        return _JSRaw(f"if ({self.to_js()}) {{ {action_js} }}")

    def toggle(self, *values: Any) -> "Assignment":
        if not values:
            return self.set(~self)
        result = values[0]
        for i in range(len(values) - 1, 0, -1):
            result = (self == values[i - 1]).if_(values[i], result)
        return self.set(result)

    def lower(self) -> "MethodCall":
        return MethodCall(self, "toLowerCase", [])

    def upper(self) -> "MethodCall":
        return MethodCall(self, "toUpperCase", [])

    def strip(self) -> "MethodCall":
        return MethodCall(self, "trim", [])

    def contains(self, text: Any) -> "MethodCall":
        return MethodCall(self, "includes", [text])

    def toggle_in(self, value: Any) -> "Assignment":
        """Toggle item in array: add if missing, remove if present."""
        val = _ensure_expr(value).to_js()
        sig = self.to_js()
        return Assignment(self, _JSRaw(f"{sig}.includes({val}) ? {sig}.filter(v => v !== {val}) : [...{sig}, {val}]"))

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

    def with_(self, **modifiers) -> tuple:
        return (self, modifiers)


class _JSLiteral(Expr):
    __slots__ = ("value", "_js")

    def __init__(self, value: Any):
        self.value = value
        try:
            self._js = json.dumps(value, separators=(",", ":"))
        except (TypeError, ValueError):
            self._js = None

    def to_js(self) -> str:
        if self._js is None:
            return json.dumps(self.value, separators=(",", ":"))
        return self._js


class TemplateLiteral(Expr):
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
    __slots__ = ("left", "op", "right")

    def __init__(self, left: Any, op: str, right: Any):
        self.left = _ensure_expr(left)
        self.op = op
        self.right = _ensure_expr(right)

    def to_js(self) -> str:
        return f"({self.left.to_js()} {self.op} {self.right.to_js()})"


class UnaryOp(Expr):
    __slots__ = ("op", "expr")

    def __init__(self, op: str, expr: Expr):
        self.op, self.expr = op, expr

    def to_js(self) -> str:
        return f"{self.op}({self.expr.to_js()})"


class Conditional(Expr):
    __slots__ = ("condition", "true_val", "false_val")

    def __init__(self, condition: Expr, true_val: Any, false_val: Any):
        self.condition, self.true_val, self.false_val = condition, _ensure_expr(true_val), _ensure_expr(false_val)

    def to_js(self) -> str:
        return f"({self.condition.to_js()} ? {self.true_val.to_js()} : {self.false_val.to_js()})"


class Assignment(Expr):
    __slots__ = ("target", "value")

    def __init__(self, target: Expr, value: Any):
        self.target, self.value = target, _ensure_expr(value)

    def to_js(self) -> str:
        return f"{self.target.to_js()} = {self.value.to_js()}"


class MethodCall(Expr):
    __slots__ = ("obj", "method", "args")

    def __init__(self, obj: Expr, method: str, args: list[Any]):
        self.obj, self.method, self.args = obj, method, [_ensure_expr(a) for a in args]

    def to_js(self) -> str:
        return f"{self.obj.to_js()}.{self.method}({', '.join(arg.to_js() for arg in self.args)})"


class PropertyAccess(Expr):
    __slots__ = ("obj", "prop")

    def __init__(self, obj: Expr, prop: str):
        self.obj, self.prop = obj, prop

    def to_js(self) -> str:
        return f"{self.obj.to_js()}.{self.prop}"

    def __call__(self, *args: Any) -> "MethodCall":
        return MethodCall(self.obj, self.prop, args)


class IndexAccess(Expr):
    __slots__ = ("obj", "index")

    def __init__(self, obj: Expr, index: Any):
        self.obj, self.index = obj, _ensure_expr(index)

    def to_js(self) -> str:
        return f"{self.obj.to_js()}[{self.index.to_js()}]"


def _ensure_expr(value: Any) -> Expr:
    return value if isinstance(value, Expr) else _JSLiteral(value)


class Signal(Expr):
    """Typed reactive state reference that auto-generates JavaScript and data attributes."""

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
        self.id = f"{namespace}_{name}" if namespace else name
        self._js = f"${self.id}"

    def _infer_type(self, initial: Any) -> type:
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

    def to_dict(self) -> dict[str, Any]:
        if self._is_computed:
            return {}
        return {self.id: self._initial}

    def get_computed_attr(self) -> tuple[str, Any] | None:
        if self._is_computed:
            return (f"data_computed_{self._name}", self._initial)
        return None

    def to_js(self) -> str:
        return self._js

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
    return _to_js(value, allow_expressions=True)


def js(code: str) -> _JSRaw:
    """Embed raw JavaScript (auto-minified)."""
    return _JSRaw(jsmin(code))


def value(v: Any) -> _JSLiteral:
    """JSON-encode Python value as JavaScript literal."""
    if isinstance(v, Expr):
        raise TypeError(
            f"value() should not be used with {type(v).__name__} objects. Use the object directly instead of wrapping it with value()."
        )
    return _JSLiteral(v)


def f(template_str: str, **kwargs: Any) -> _JSRaw:
    """Create JavaScript template literal from Python f-string-like template."""

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        val = kwargs.get(key)
        if val is None:
            return match.group(0)
        return f"${{{to_js_value(val)}}}"

    js_template = re.sub(r"\{(\w+)\}", replacer, template_str)
    return _JSRaw(f"`{js_template}`")


def regex(pattern: str) -> _JSRaw:
    """Create JavaScript regex: regex("^foo") → /^foo/"""
    return _JSRaw(f"/{pattern}/")


def match(subject: Any, /, **patterns: Any) -> _JSRaw:
    """Pattern match values: match(status, loading="...", ready="✓", default="?")"""
    subject_expr = _ensure_expr(subject)
    default_val = patterns.pop("default", "")
    result = _ensure_expr(default_val)
    for pattern, val in reversed(patterns.items()):
        check_expr = subject_expr == _ensure_expr(pattern)
        result = check_expr.if_(val, result)
    return _JSRaw(result.to_js())


def switch(cases: list[tuple[Any, Any]], /, default: Any = "") -> _JSRaw:
    """Sequential if/elif/else: switch([(cond1, val1), (cond2, val2)], default=val3)"""
    result = _ensure_expr(default)
    for condition, val in reversed(cases):
        result = _ensure_expr(condition).if_(val, result)
    return _JSRaw(result.to_js())


def collect(cases: list[tuple[Any, Any]], /, join_with: str = " ") -> _JSRaw:
    """Collect values from true conditions: useful for CSS classes."""
    if not cases:
        return _JSRaw("''")
    parts = [_ensure_expr(condition).if_(val, "").to_js() for condition, val in cases]
    array_expr = "[" + ", ".join(parts) + "]"
    return _JSRaw(f"{array_expr}.filter(Boolean).join('{join_with}')")


def seq(*exprs: Any) -> _JSRaw:
    """Comma operator sequence: seq(a, b, c) evaluates all, returns last."""
    if not exprs:
        return _JSRaw("undefined")
    expr_strs = [_ensure_expr(e).to_js() for e in exprs]
    return _JSRaw(f"({', '.join(expr_strs)})")


def _iterable_args(*args):
    return (
        args[0]
        if builtins.len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], str | Signal | Expr)
        else args
    )


def all(*signals) -> _JSRaw:
    if not signals:
        return _JSRaw("true")
    signals = _iterable_args(*signals)
    return _JSRaw(" && ".join(f"!!{_ensure_expr(s).to_js()}" for s in signals))


def any(*signals) -> _JSRaw:
    if not signals:
        return _JSRaw("false")
    signals = _iterable_args(*signals)
    return _JSRaw(" || ".join(f"!!{_ensure_expr(s).to_js()}" for s in signals))


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


console = js("console")
Math = js("Math")
JSON = js("JSON")
Object = js("Object")
Array = js("Array")
Date = js("Date")
Number = js("Number")
String = js("String")
Boolean = js("Boolean")
evt = js("evt")
document = js("document")


def _normalize_data_key(key: str) -> str:
    for prefix in ("data_computed_", "data_class_", "data_on_", "data_attr_", "data_"):
        if key.startswith(prefix):
            name = key.removeprefix(prefix)
            slug = name if prefix == "data_computed_" else name.replace("_", "-")
            return f"{prefix.removesuffix('_').replace('_', '-')}-{slug}"
    return key.replace("_", "-")


def _build_modifier_suffix(modifiers: dict[str, Any]) -> str:
    if not modifiers:
        return ""
    parts = []
    for name, value in modifiers.items():
        match value:
            case True:
                parts.append(name)
            case False:
                parts.append(f"{name}.false")
            case int() | float():
                part = f"n{abs(value)}" if value < 0 else str(value)
                parts.append(f"{name}.{part}")
            case str():
                parts.append(f"{name}.{value}")
    return f"__{'__'.join(parts)}" if parts else ""


def _expr_list_to_js(items: list[Any], collect_signals: callable) -> str:
    def process_item(item):
        if isinstance(item, Expr | Signal):
            collect_signals(item)
            return item.to_js()
        return str(item)

    return "; ".join(process_item(item) for item in items)


def _collect_signals(expr: Any, sink: set[Signal]) -> None:
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
    parts = [f"{key}: {_to_js(val, allow_expressions=False)}" for key, val in signals.items()]
    return NotStr("{" + ", ".join(parts) + "}")


def _handle_data_signals(value: Any) -> Any:
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
    if "cls" in processed and "data-attr-cls" in processed:
        base_classes = processed.pop("cls")
        reactive_classes = str(processed.pop("data-attr-cls"))
        if reactive_classes.startswith("(") and reactive_classes.endswith(")"):
            reactive_classes = reactive_classes[1:-1]
        processed["data-attr-class"] = NotStr(f"`{base_classes} ${{{reactive_classes}}}`")


def process_datastar_kwargs(kwargs: dict) -> tuple[dict, set[Signal]]:
    """Transform Python kwargs to Datastar data-* attributes and collect signals."""
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
                if key in ("data_bind", "data_ref", "data_indicator") and isinstance(expr, Signal):
                    processed[normalized_key] = expr.id
                elif key == "data_class":
                    processed["data-class"] = NotStr(js_str)
                else:
                    processed[normalized_key] = NotStr(js_str)
            case _JSLiteral() | _JSRaw() | dict() as val:
                processed[normalized_key] = NotStr(_to_js(val))
            case _:
                if key.startswith(("data_style_", "data_class_", "data_attr_")):
                    processed[normalized_key] = value if isinstance(value, str) else NotStr(_to_js(value))
                else:
                    processed[key] = value

    _apply_additive_class_behavior(processed)
    return processed, signals_found


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
    "seq",
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
    "evt",
    "document",
    "process_datastar_kwargs",
    "to_js_value",
]
