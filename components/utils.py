"""Utility functions for StarHTML UI components."""
from typing import Any


def cn(*args: str | dict[str, bool] | None) -> str:
    """
    Conditionally join class names together.
    
    Args:
        *args: Class names (strings), dictionaries of {class: condition}, or None
        
    Returns:
        Combined class string
        
    Examples:
        cn("foo", "bar") -> "foo bar"
        cn("foo", {"bar": True, "baz": False}) -> "foo bar"
        cn("foo", None, "bar") -> "foo bar"
    """
    classes = []
    
    for arg in args:
        if arg is None:
            continue
        elif isinstance(arg, str):
            classes.append(arg)
        elif isinstance(arg, dict):
            for cls, condition in arg.items():
                if condition:
                    classes.append(cls)
    
    return " ".join(classes)


def cva(
    base: str,
    config: dict[str, dict[str, Any]]
) -> callable:
    """
    Class Variance Authority - Create variant-based className strings.
    
    Args:
        base: Base classes that are always applied
        config: Configuration object with variants and their values
        
    Returns:
        Function that generates class names based on variants
    """
    variants = config.get("variants", {})
    default_variants = config.get("defaultVariants", {})
    compound_variants = config.get("compoundVariants", [])
    
    def get_variant_classes(**props) -> str:
        # Start with base classes
        classes = [base]
        
        # Apply default variants first
        current_variants = {**default_variants, **props}
        
        # Add variant classes
        for variant_key, variant_value in current_variants.items():
            if variant_key in variants and variant_value in variants[variant_key]:
                variant_classes = variants[variant_key][variant_value]
                if variant_classes:
                    classes.append(variant_classes)
        
        # Apply compound variants
        for compound in compound_variants:
            conditions = {k: v for k, v in compound.items() if k != "class"}
            if all(current_variants.get(k) == v for k, v in conditions.items()):
                classes.append(compound["class"])
        
        return " ".join(filter(None, classes))
    
    return get_variant_classes
