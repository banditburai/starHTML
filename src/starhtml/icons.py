"""Icon component with dual-mode rendering, 2-tier caching, and CLI scanner."""

from __future__ import annotations

import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from fastcore.xml import FT, NotStr

__all__ = ["Icon", "IconData", "IconResolver", "resolver"]

log = logging.getLogger(__name__)

_project_root: Path | None = None


def _find_project_root() -> Path:
    global _project_root
    if _project_root is not None:
        return _project_root
    cwd = Path.cwd()
    for parent in (cwd, *cwd.parents):
        if (parent / "pyproject.toml").is_file():
            _project_root = parent
            return _project_root
    _project_root = cwd
    return _project_root


def _project_cache_dir() -> Path:
    return _find_project_root() / ".starhtml" / "icons"


_TW_SIZES = {
    "3": "0.75rem",
    "3.5": "0.875rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "7": "1.75rem",
    "8": "2rem",
    "9": "2.25rem",
    "10": "2.5rem",
    "11": "2.75rem",
    "12": "3rem",
}

_TW_SIZE_RE = re.compile(r"\b(size|w|h)-(\d+(?:\.\d+)?|\[[^\]]+\])")


@dataclass(frozen=True)
class IconData:
    body: str
    width: int = 24
    height: int = 24


class IconResolver:
    def __init__(self):
        self.inline: bool = False
        self._memory: dict[str, dict[str, IconData]] = {}

    def resolve(self, prefix: str, name: str) -> IconData | None:
        bucket = self._memory.get(prefix)
        if bucket is not None and (cached := bucket.get(name)) is not None:
            return cached
        return self._load_from_disk(prefix, name) or self._fetch_from_api(prefix, [name])

    def register(self, prefix: str, name: str, data: IconData) -> None:
        self._memory.setdefault(prefix, {})[name] = data

    def preload(self, prefix: str, names: list[str] | None = None, *, raw: dict | None = None) -> None:
        if raw is None:
            raw = self._read_disk_json(prefix)
        if raw is None:
            return
        if names is None:
            names = [*raw.get("icons", {}), *raw.get("aliases", {})]
        bucket = self._memory.setdefault(prefix, {})
        for n in names:
            if (data := self._parse_from_raw(raw, n)) is not None:
                bucket[n] = data

    def preload_from_disk(self) -> None:
        cache_dir = _project_cache_dir()
        if not cache_dir.is_dir():
            return
        for path in cache_dir.glob("*.json"):
            self.preload(path.stem)

    def batch_fetch(self, prefix: str, names: list[str]) -> dict[str, IconData | None]:
        result: dict[str, IconData | None] = {}
        missing: list[str] = []

        bucket = self._memory.get(prefix, {})
        for name in names:
            if name in bucket:
                result[name] = bucket[name]
            else:
                missing.append(name)

        if missing:
            self.preload(prefix, missing)
            bucket = self._memory.get(prefix, {})
            still_missing = []
            for name in missing:
                if name in bucket:
                    result[name] = bucket[name]
                else:
                    still_missing.append(name)
            missing = still_missing

        if missing:
            self._fetch_from_api(prefix, missing)
            bucket = self._memory.get(prefix, {})
            for name in missing:
                result[name] = bucket.get(name)

        return result

    def _read_disk_json(self, prefix: str) -> dict | None:
        path = _project_cache_dir() / f"{prefix}.json"
        if path.is_file():
            try:
                return json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        return None

    def _parse_from_raw(self, raw: dict, name: str) -> IconData | None:
        icons = raw.get("icons", {})
        aliases = raw.get("aliases", {})
        if name in aliases:
            name = aliases[name].get("parent", name)
        entry = icons.get(name)
        if entry is None:
            return None
        dw, dh = raw.get("width", 24), raw.get("height", 24)
        return IconData(body=entry["body"], width=entry.get("width", dw), height=entry.get("height", dh))

    def _load_from_disk(self, prefix: str, name: str) -> IconData | None:
        raw = self._read_disk_json(prefix)
        if raw is None:
            return None
        # Bulk-load entire prefix — we already paid for the JSON parse
        self.preload(prefix, raw=raw)
        return self._memory.get(prefix, {}).get(name)

    def _merge_to_disk(self, prefix: str, raw: dict) -> None:
        cache_dir = _project_cache_dir()
        path = cache_dir / f"{prefix}.json"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            try:
                existing = json.loads(path.read_text()) if path.is_file() else {}
            except (json.JSONDecodeError, OSError):
                existing = {}
            for key in ("icons", "aliases"):
                if key in raw:
                    existing.setdefault(key, {}).update(raw[key])
            for key in ("width", "height", "prefix"):
                if key in raw:
                    existing[key] = raw[key]
            path.write_text(json.dumps(existing, separators=(",", ":")))
        except OSError as exc:
            log.warning("Failed to write icon cache %s: %s", path, exc)

    def _fetch_from_api(self, prefix: str, names: list[str]) -> IconData | None:
        if not names:
            return None
        if self.inline:
            log.warning(
                "Fetching icon(s) %s:{%s} from API at runtime — run `starhtml icons scan` to pre-cache",
                prefix,
                ",".join(names),
            )
        try:
            import httpx

            resp = httpx.get(f"https://api.iconify.design/{prefix}.json?icons={','.join(names)}", timeout=10)
            resp.raise_for_status()
            raw = resp.json()
        except Exception as exc:
            log.warning("Failed to fetch icon(s) %s:{%s}: %s", prefix, ",".join(names), exc)
            return None

        self._merge_to_disk(prefix, raw)

        bucket = self._memory.setdefault(prefix, {})
        for name in names:
            if (d := self._parse_from_raw(raw, name)) is not None:
                bucket[name] = d

        return bucket.get(names[0])


resolver = IconResolver()


def _to_size(val: int | str) -> str:
    return f"{val}px" if isinstance(val, int) or val.isdigit() else val


def _extract_tw_size(cls_str: str) -> tuple[str | None, str | None]:
    if not cls_str:
        return None, None
    w = h = None
    for match in _TW_SIZE_RE.finditer(cls_str):
        prop, val = match.groups()
        if val.startswith("["):
            css_val = val[1:-1]
        else:
            css_val = _TW_SIZES.get(val, f"{float(val) * 0.25}rem")
        if prop == "size":
            w = h = css_val
        elif prop == "w":
            w = css_val
        elif prop == "h":
            h = css_val
    return w, h


def Icon(
    icon: str,
    *,
    size: int | str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    cls: str = "",
    stable: bool = True,
    **kwargs,
) -> FT:
    "Iconify icon with CLS prevention; supports size, width/height, or Tailwind size classes"
    from .html import ft_datastar
    from .tags import Span

    prefix, _, name = icon.partition(":")

    if not stable and not resolver.inline:
        return ft_datastar("iconify-icon", icon=icon, **kwargs)

    if size is not None:
        w = h = _to_size(size)
    elif width is not None or height is not None:
        w = _to_size(width) if width is not None else None
        h = _to_size(height) if height is not None else None
        w = w or h
        h = h or w
    else:
        w, h = _extract_tw_size(cls)
        w = w or h or "1em"
        h = h or w

    base_style = f"width:{w};height:{h};flex-shrink:0;vertical-align:middle;line-height:0"
    user_style = kwargs.pop("style", None)
    wrapper_style = f"{base_style};{user_style}" if user_style else base_style
    wrapper_id = kwargs.pop("id", None)

    def _wrap(inner):
        return Span(inner, style=wrapper_style, cls=cls or None, id=wrapper_id, data_icon_sh=True, **kwargs)

    if resolver.inline:
        icon_data = resolver.resolve(prefix, name) if name else None

        if icon_data is not None:
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {icon_data.width} {icon_data.height}"'
                f' width="100%" height="100%" fill="currentColor">{icon_data.body}</svg>'
            )
            if not stable:
                return NotStr(svg)
            return _wrap(Span(NotStr(svg), style="display:block;width:100%;height:100%"))

        return _wrap(Span(style="display:block;width:100%;height:100%"))

    return _wrap(ft_datastar("iconify-icon", icon=icon, width=w, height=h))


_ICON_RE = re.compile(r"""Icon\(\s*["']([a-zA-Z0-9_-]+):([a-zA-Z0-9_-]+)["']""")

_DEFAULT_EXCLUDE_DIRS = frozenset(
    {
        "test",
        "tests",
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".tox",
        ".nox",
        ".mypy_cache",
        ".pytest_cache",
        "build",
        "dist",
    }
)


def _scan_file(path: Path, found: defaultdict[str, set[str]]) -> None:
    try:
        text = path.read_text()
    except OSError:
        return
    for prefix, name in _ICON_RE.findall(text):
        found[prefix].add(name)


def _scan_icons_regex(
    paths: list[Path],
    exclude_dirs: frozenset[str] = _DEFAULT_EXCLUDE_DIRS,
    exclude_patterns: list[str] | None = None,
) -> dict[str, set[str]]:
    found: defaultdict[str, set[str]] = defaultdict(set)
    excluded = (
        (lambda p: any(fnmatch(str(p), pat) for pat in exclude_patterns)) if exclude_patterns else lambda _: False
    )
    for path in paths:
        if path.is_file():
            if not excluded(path):
                _scan_file(path, found)
            continue
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for fname in filenames:
                if fname.endswith(".py"):
                    fpath = Path(dirpath, fname)
                    if not excluded(fpath):
                        _scan_file(fpath, found)
    return dict(found)


def _cmd_icons_scan(args) -> int:
    scan_paths = [Path(p) for p in args.paths] if args.paths else [Path(".")]
    exclude_dirs = frozenset() if args.no_default_excludes else _DEFAULT_EXCLUDE_DIRS
    found = _scan_icons_regex(scan_paths, exclude_dirs, args.exclude)

    if not found:
        print("No Icon() calls found.")
        return 0

    total = sum(len(names) for names in found.values())
    print(f"Found {total} icon(s) across {len(found)} prefix(es):")
    for prefix, names in sorted(found.items()):
        print(f"  {prefix}: {', '.join(sorted(names))}")

    cache_dir = _project_cache_dir()
    to_fetch: dict[str, list[str]] = {}
    for prefix, names in found.items():
        resolver.preload(prefix)
        cached = resolver._memory.get(prefix, {})
        missing = sorted(names - cached.keys())
        if missing:
            to_fetch[prefix] = missing

    fetch_count = sum(len(names) for names in to_fetch.values())

    if not to_fetch:
        print(f"\nAll {total} icon(s) already cached in {cache_dir}")
        return 0

    print(f"\nAlready cached: {total - fetch_count}, fetching: {fetch_count}")

    failures = 0
    for prefix, names in to_fetch.items():
        results = resolver.batch_fetch(prefix, names)
        failed = sum(1 for v in results.values() if v is None)
        failures += failed
        status = "ok" if failed == 0 else f"{len(results) - failed} ok, {failed} failed"
        print(f"  {prefix}: {', '.join(names)} ... {status}")

    print(f"\nDone. Cache: {cache_dir}")
    if failures:
        print(f"  {failures} icon(s) could not be fetched.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="starhtml", description="StarHTML CLI utilities")
    sub = parser.add_subparsers(dest="command")

    icons_parser = sub.add_parser("icons", help="Icon cache management")
    icons_sub = icons_parser.add_subparsers(dest="icons_command")

    scan_parser = icons_sub.add_parser("scan", help="Scan .py files and pre-cache icons")
    scan_parser.add_argument("paths", nargs="*", help="Paths to scan (default: current directory)")
    scan_parser.add_argument(
        "--exclude", action="append", metavar="PATTERN", help="Glob pattern to exclude (repeatable)"
    )
    scan_parser.add_argument(
        "--no-default-excludes", action="store_true", help="Disable built-in excludes (tests, .venv, etc.)"
    )

    args = parser.parse_args(argv)

    if args.command == "icons":
        if args.icons_command == "scan":
            return _cmd_icons_scan(args)
        icons_parser.print_help()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
