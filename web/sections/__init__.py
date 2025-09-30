"""Centralized section definitions for StarHTML documentation."""

import importlib.util
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Section:
    id: str
    title: str
    description: str
    filename: str
    function_name: str
    route: str
    level: str = "Foundation"
    needs_embedded_headers: bool = False

    @property
    def file_path(self) -> Path:
        return Path(__file__).parent / self.filename

    def load_module(self) -> Any:
        spec = importlib.util.spec_from_file_location(f"section_{self.id}", self.file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def load_function(self) -> Callable:
        return getattr(self.load_module(), self.function_name)

    def get_standalone_headers(self):
        if not self.needs_embedded_headers:
            return []
        from starhtml.handlers import split_handler

        return [split_handler(signal="code_split", responsive=True)]


SECTIONS: list[Section] = [
    Section(
        id="hero",
        title="Hero Section",
        description="Clean, composable hero section for docs integration",
        filename="00_hero.py",
        function_name="hero_section",
        route="/hero",
        level="Foundation",
    ),
    Section(
        id="python-first",
        title="Python First",
        description="Python First philosophy section for docs integration",
        filename="01_philosophy_python_first.py",
        function_name="python_first_section",
        route="/python-first",
        level="Philosophy",
        needs_embedded_headers=True,
    ),
    Section(
        id="type-safety",
        title="Type Safety",
        description="StarHTML's Signals automatically infer types from initial values",
        filename="02_philosophy_type_safety.py",
        function_name="type_safety_section",
        route="/type-safety",
        level="Philosophy",
    ),
    Section(
        id="explicit",
        title="Explicit Philosophy",
        description="Explicit is Better philosophy section for docs integration",
        filename="03_philosophy_explicit.py",
        function_name="explicit_section",
        route="/explicit",
        level="Philosophy",
    ),
    Section(
        id="composable",
        title="Composable Philosophy",
        description="Composable Primitives philosophy section for docs integration",
        filename="04_philosophy_composable.py",
        function_name="composable_section",
        route="/composable",
        level="Philosophy",
    ),
    Section(
        id="quick-reference",
        title="Quick Reference",
        description="Essential patterns with copy-and-paste examples",
        filename="05_quick_reference.py",
        function_name="quick_reference_section",
        route="/quick-reference",
        level="Reference",
    ),
    # Section(
    #     id="core-concepts",
    #     title="Core Concepts",
    #     description="Master the fundamental patterns of StarHTML",
    #     filename="06_core_concepts.py",
    #     function_name="core_concepts_section",
    #     route="/core-concepts",
    #     level="Foundation"
    # ),
    # Section(
    #     id="reactivity",
    #     title="Essential Reactivity",
    #     description="Live updates, event handling, and reactive patterns",
    #     filename="07_reactivity.py",
    #     function_name="reactivity_section",
    #     route="/reactivity",
    #     level="Foundation"
    # ),
    # Section(
    #     id="styling",
    #     title="Styling & Classes",
    #     description="CSS properties, dynamic classes, and reactive styling patterns",
    #     filename="08_styling.py",
    #     function_name="styling_section",
    #     route="/styling",
    #     level="Intermediate"
    # ),
    # Section(
    #     id="expressions-logic",
    #     title="Expressions & Logic",
    #     description="Operators, conditionals, and helper functions",
    #     filename="09_expressions_logic.py",
    #     function_name="expressions_logic_section",
    #     route="/expressions-logic",
    #     level="Intermediate"
    # ),
    # Section(
    #     id="advanced-features",
    #     title="Advanced Features",
    #     description="Slot attributes, handlers, JavaScript integration, and complex patterns",
    #     filename="10_advanced_features.py",
    #     function_name="advanced_features_section",
    #     route="/advanced-features",
    #     level="Advanced"
    # ),
    # Section(
    #     id="side-effects-computed",
    #     title="Side Effects & Computed",
    #     description="Advanced reactive patterns with computed properties and side effects",
    #     filename="11_side_effects_computed.py",
    #     function_name="side_effects_computed_section",
    #     route="/side-effects-computed",
    #     level="Advanced"
    # ),
    # Section(
    #     id="best-practices",
    #     title="Best Practices",
    #     description="Essential guidelines for maintainable, performant StarHTML code",
    #     filename="12_best_practices.py",
    #     function_name="best_practices_section",
    #     route="/best-practices",
    #     level="Best Practices"
    # ),
]


def get_sections_by_level(level: str) -> list[Section]:
    return [s for s in SECTIONS if s.level == level]


def get_section_by_id(section_id: str) -> Section:
    if section := next((s for s in SECTIONS if s.id == section_id), None):
        return section
    raise ValueError(f"Section '{section_id}' not found")


def get_current_section() -> Section:
    """Get the current section based on the calling file's name."""
    import inspect

    filename = Path(inspect.currentframe().f_back.f_globals["__file__"]).name
    if section := next((s for s in SECTIONS if s.filename == filename), None):
        return section
    raise ValueError(f"Section not found for file: {filename}")


class SectionLoader:
    def __init__(self):
        self._cache = {}

    def __getattr__(self, name: str):
        if name not in self._cache:
            if section := next((s for s in SECTIONS if s.function_name == name), None):
                self._cache[name] = section.load_function()
            else:
                raise AttributeError(f"No section function named '{name}'")
        return self._cache[name]


sections = SectionLoader()
