"""Gets the version, either installed or dynamically."""

__all__ = ["__version__"]

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pydantic-kedro")
except PackageNotFoundError:
    try:
        from setuptools_scm import get_version

        __version__ = get_version(root="../..", relative_to=__file__)
    except Exception:
        __version__ = "0.0.0"
