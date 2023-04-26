"""Checks for extras."""

__all__ = ["INSTALLED_YAML"]

INSTALLED_YAML = False
try:
    import pydantic_yaml  # noqa

    INSTALLED_YAML = True
except ImportError:
    pass
