"""Static checks over rendered FT trees.

``check_signal_order`` finds a Datastar footgun the hoist in ``process_datastar_kwargs`` cannot cover: Datastar applies
``data-*`` attributes in document order, and a reader (``data-text="$x"``, ``data-attr:…``, ``data-bind``…) that runs
before ``$x`` is declared auto-creates the signal as ``""``, which a later ``data-signals:x__ifmissing`` then leaves in
place. Same-element order is fixed at render time (declarations are hoisted); a declaration on a *later* element than
its first reader is still a bug, and that is what this reports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_READ = re.compile(r"(?<![$\w])\$([A-Za-z_][\w.]*)")  # `$name` (not `$$name`, which is StarElements-local)
_OBJECT_KEY = re.compile(r"(?:^|[{,])\s*['\"]?([A-Za-z_][\w.]*)['\"]?\s*:")
_DECLARING_PREFIXES = ("data-signals", "data-computed")


@dataclass(frozen=True)
class SignalOrderIssue:
    signal: str
    reader_tag: str
    reader_attr: str
    declaring_tag: str

    def __str__(self) -> str:
        return (
            f"${self.signal} is read by <{self.reader_tag} {self.reader_attr}> before <{self.declaring_tag}> declares it "
            f"(Datastar applies attributes in document order; the early read creates ${self.signal} as '')"
        )


def _declared_names(attr: str, value: Any) -> list[str]:
    if attr.startswith("data-signals:") or attr.startswith("data-computed:"):
        return [attr.split(":", 1)[1].split("__", 1)[0]]
    if attr.split("__", 1)[0] == "data-signals":  # object form, possibly with modifiers
        return [m.group(1) for m in _OBJECT_KEY.finditer(str(value))]
    return []


def _walk(node: Any):
    """Yield FT elements in document order (strings and Signals are skipped)."""
    if getattr(node, "tag", None) is not None and hasattr(node, "attrs"):
        yield node
        for child in getattr(node, "children", ()) or ():
            yield from _walk(child)
    elif isinstance(node, list | tuple):
        for child in node:
            yield from _walk(child)


def check_signal_order(ft: Any) -> list[SignalOrderIssue]:
    """Report signals read on an earlier element than the one declaring them.

    Only signals the tree eventually declares are reported: a read of a signal nothing in this tree declares may be
    legitimate (declared by a parent layout, persisted, or patched in later). Attribute order within one element
    follows the rendered order, which ``process_datastar_kwargs`` already puts declarations first.
    """
    declared: set[str] = set()
    pending: dict[str, tuple[str, str]] = {}  # signal -> first (tag, attr) that read it before any declaration
    issues: list[SignalOrderIssue] = []
    for el in _walk(ft):
        for attr, value in el.attrs.items():
            if not attr.startswith("data-"):
                continue
            declaring = _declared_names(attr, value)
            for name in declaring:
                if name in pending and name not in declared:
                    tag, reader_attr = pending.pop(name)
                    issues.append(SignalOrderIssue(name, tag, reader_attr, el.tag))
                declared.add(name)
            if attr.startswith(_DECLARING_PREFIXES) and not attr.startswith("data-computed"):
                continue  # data-signals values are literals, not reads
            for m in _READ.finditer(str(value)):
                name = m.group(1)
                if name not in declared and name not in pending:
                    pending[name] = (el.tag, f'{attr}="{value}"')
    return issues
