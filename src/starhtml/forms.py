"""Form validation, lifecycle wiring, and submission coordination for StarHTML."""

from dataclasses import asdict, is_dataclass
from typing import Any

from fastcore.xml import FT
from starlette.datastructures import FormData
from starlette.exceptions import HTTPException
from starlette.requests import Request

from .datastar import Expr, Signal, _JSRaw, any_, post, regex, scroll_to, seq, switch, to_js_value

__all__ = [
    "required",
    "email",
    "min_length",
    "max_length",
    "pattern",
    "matches",
    "checked",
    "FormAttrs",
    "form_submit",
    "form_validate_on_click",
    "form_reset",
    "fill_form",
    "fill_dataclass",
    "find_inputs",
    "parse_form",
    "form2dict",
]


_EMAIL_RE = r"[^\s@]+@[^\s@]+\.[^\s@]+"


def _require(signal: Signal) -> None:
    signal._constraint_attrs.update({"required": True, "aria-required": "true"})


def required(signal: Signal, label: str = "This field") -> Expr:
    "Error message when empty, empty string when valid."
    _require(signal)
    return (~signal).if_(f"{label} is required")


def email(signal: Signal, *, re: str = _EMAIL_RE) -> Expr:
    "Email validation: required + regex."
    _require(signal)
    return switch(
        [
            (~signal, "Email is required"),
            (~regex(re).test(signal), "Please enter a valid email"),
        ]
    )


def min_length(signal: Signal, n: int, label: str = "This field") -> Expr:
    "Required + minimum length."
    _require(signal)
    signal._constraint_attrs["minlength"] = str(n)
    return switch(
        [
            (~signal, f"{label} is required"),
            (signal.length < n, f"Must be at least {n} characters"),
        ]
    )


def max_length(signal: Signal, n: int) -> Expr:
    "Maximum length (does not check required)."
    signal._constraint_attrs["maxlength"] = str(n)
    return (signal.length > n).if_(f"Must be at most {n} characters")


def pattern(signal: Signal, pat: str, message: str, *, optional: bool = False) -> Expr:
    "Regex pattern validation. Set optional=True to skip when empty."
    signal._constraint_attrs["pattern"] = pat
    if optional:
        return (signal & ~regex(pat).test(signal)).if_(message)
    _require(signal)
    return switch(
        [
            (~signal, "This field is required"),
            (~regex(pat).test(signal), message),
        ]
    )


def matches(signal: Signal, other: Signal, message: str = "Fields must match", *, label: str = "This field") -> Expr:
    "Must match another field (e.g., password confirmation)."
    _require(signal)
    return switch(
        [
            (~signal, f"{label} is required"),
            (signal != other, message),
        ]
    )


def checked(signal: Signal, message: str = "This field is required") -> Expr:
    "Checkbox must be checked."
    _require(signal)
    return (~signal).if_(message)


class FormAttrs(dict[str, Any]):
    "Spreadable form attrs with .submitting, .submitted, and .error signals."

    def __init__(
        self,
        data: dict[str, Any],
        *,
        submitting: Signal,
        submitted: Signal | None,
        error: Signal | list[Signal] | None,
    ) -> None:
        super().__init__(data)
        self.submitting, self.submitted, self.error = submitting, submitted, error


def _unwrap(s: Signal | FT) -> Signal:
    if isinstance(s, Signal):
        return s
    sig = getattr(s, "signal", None)
    if isinstance(sig, Signal):
        return sig
    raise TypeError(f"Expected Signal or FT with .signal attr, got {type(s).__name__}")


def _validate_signals(signals: tuple[Signal | FT, ...]) -> dict[Signal, Expr]:
    sigs = [_unwrap(s) for s in signals]
    if bad := next((s for s in sigs if "_validation_expr" not in s.__dict__), None):
        raise ValueError(f"Signal {bad._name!r} has no validation — call .validate() first")
    return {s.err: s.__dict__["_validation_expr"] for s in sigs}


def form_submit(
    endpoint: str,
    *signals: Signal | FT,
    name: str | None = None,
    submitting: Signal | None = None,
    submitted: Signal | None = None,
    error: Signal | list[Signal] | None = None,
    focus_first_error: bool = True,
    reset_on_success: bool = False,
) -> FormAttrs:
    "Datastar attrs for form submission. Auto-creates submitting/submitted/error signals from name=."
    orig = (submitting, submitted, error)
    pfx = name.replace("-", "_") if name else None
    submitting = submitting or (Signal(f"{pfx}_submitting", False) if pfx else None)
    submitted = submitted or (Signal(f"{pfx}_submitted", False) if pfx else None)
    error = error or (Signal(f"{pfx}_error", "") if pfx else None)
    if not submitting:
        raise ValueError("Provide name= or explicit submitting=")

    fields = _validate_signals(signals)
    validate_all = [err.set(val) for err, val in fields.items()]
    can_submit = ~any_(*fields.keys()) & ~submitting
    clears = [e.set("") for e in (error if isinstance(error, list) else [error] if error else [])]
    submit_action = seq(*clears, post(endpoint, contentType="form"))

    actions = [*validate_all, can_submit.then(submit_action)]
    if focus_first_error:
        actions.append((~can_submit).then(scroll_to("[aria-invalid]", focus=True)))

    attrs = dict(data_on_submit=(actions, {"prevent": True}), action=endpoint, method="post", novalidate=True)
    auto_created = [
        s for s, o in zip((submitting, submitted, error), orig, strict=False) if s is not o and s is not None
    ]
    if auto_created:
        attrs["data_signals"] = auto_created
    if reset_on_success and submitted:
        attrs["data_on_signal_patch"] = submitted & form_reset(*signals)
        attrs["data_on_signal_patch_filter"] = f"{{include: /^{submitted._id}$/}}"
    return FormAttrs(attrs, submitting=submitting, submitted=submitted, error=error)


def form_validate_on_click(*signals: Signal | FT, focus_first_error: bool = True) -> dict[str, Any]:
    "Datastar attrs for a submit button that validates before native POST."
    fields = _validate_signals(signals)
    actions = [err.set(val) for err, val in fields.items()]
    if focus_first_error:
        actions.append(any_(*fields.keys()).then(scroll_to("[aria-invalid]", focus=True)))
    return dict(data_on_click=actions)


def form_reset(*signals: Signal | FT, **extras: Any) -> _JSRaw:
    "Reset signals to initial values; auto-clears .err for validated signals."
    sigs = [_unwrap(s) for s in signals]
    resets = [s.set(s._initial) for s in sigs]
    resets += [s.err.set(s.err._initial) for s in sigs if "_validation_expr" in s.__dict__]
    resets += [_JSRaw(f"${k} = {to_js_value(v)}") for k, v in extras.items()]
    return seq(*resets)


async def parse_form(req: Request) -> FormData | dict[str, Any]:
    "Works around Starlette crashing on empty multipart bodies."
    ctype = req.headers.get("Content-Type", "")
    if ctype == "application/json":
        return await req.json()
    if not ctype.startswith("multipart/form-data"):
        return await req.form()
    if "boundary=" not in ctype:
        raise HTTPException(400, "Invalid form-data: no boundary")
    boundary = ctype.split("boundary=")[1].strip()
    min_len = len(boundary) + 6
    clen = int(req.headers.get("Content-Length", "0"))
    if clen <= min_len:
        return FormData()
    return await req.form()


def form2dict(form: FormData) -> dict[str, Any]:
    if isinstance(form, dict):
        return form
    return {k: _formitem(form, k) for k in form}


def fill_form(form: FT, obj: Any) -> FT:
    "Fills named items in `form` using attributes in `obj`."
    if is_dataclass(obj):
        obj = asdict(obj)
    elif not isinstance(obj, dict):
        obj = obj.__dict__
    return _fill_item(form, obj)


def fill_dataclass(src: Any, dest: Any) -> Any:
    "Modifies dataclass in-place and returns it."
    for nm, val in asdict(src).items():
        setattr(dest, nm, val)
    return dest


def find_inputs(e: FT | list | tuple, tags: str | list[str] = "input", **kw: Any) -> list[FT]:
    if not isinstance(e, list | tuple | FT):
        return []
    inputs = []
    tags = [tags] if isinstance(tags, str) else (tags or [])
    cs = e
    if isinstance(e, FT):
        tag, cs, attr = e.list
        if tag in tags and kw.items() <= attr.items():
            inputs.append(e)
    for o in cs:
        inputs += find_inputs(o, tags, **kw)
    return inputs


def _formitem(form: FormData | dict[str, Any], k: str) -> Any:
    if isinstance(form, dict):
        return form.get(k)
    o = form.getlist(k)
    return o[0] if len(o) == 1 else o or None


def _fill_item(item: Any, obj: dict[str, Any]) -> Any:
    if not isinstance(item, FT):
        return item
    tag, cs, attr = item.list
    if isinstance(cs, tuple):
        cs = tuple(_fill_item(o, obj) for o in cs)
    name = attr.get("name")
    val = obj.get(name) if name else None
    if val is not None and "skip" not in attr:
        if tag == "input":
            itype = attr.get("type", "")
            if itype in ("checkbox", "radio"):
                hit = (
                    (attr["value"] in val if isinstance(val, list) else bool(val))
                    if itype == "checkbox"
                    else (val and val == attr["value"])
                )
                if hit:
                    attr["checked"] = "1"
                else:
                    attr.pop("checked", "")
            else:
                attr["value"] = val
        elif tag == "textarea":
            cs = (val,)
        elif tag == "select":
            if isinstance(val, list):
                for opt in cs:
                    if opt.tag == "option" and opt.get("value") in val:
                        opt.selected = "1"
            elif option := next((o for o in cs if o.tag == "option" and o.get("value") == val), None):
                option.selected = "1"
    return FT(tag, cs, attr, void_=item.void_)
