"""Implementation of local caching.

When we load something from a remote location, we currently need to copy it to
the local disk. This is a limitation of `pydantic-kedro` due to particular
libraries (e.g. Spark) not working with `fsspec` URLs.

Ideally we would just use a `tempfile.TemporaryDirectory`, however because some
libraries do lazy loading (Spark, Polars, so many...) we actually need to
instantiate the files locally.
"""

import atexit
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

_INITIAL_TMPDIR: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory(prefix="pydantic_kedro_")
PYD_KEDRO_CACHE_DIR: Path = Path(_INITIAL_TMPDIR.name)
"""Local-ish cache directory for pydantic-kedro.

DO NOT MODIFY - use `set_cache_dir(path)` and `get_cache_dir()` instead.

TODO: Consider using module-level getattr. See https://peps.python.org/pep-0562/
"""


def set_cache_dir(path: Union[Path, str]) -> None:
    """Set the 'local' caching directory for pydantic-kedro.

    For Spark and other multi-machine setups, it might make more sense to use
    a common mount location.
    """
    global PYD_KEDRO_CACHE_DIR, _INITIAL_TMPDIR

    cache_dir = Path(path).resolve()
    logger.info("Preparing to set cache directory to: %s", cache_dir)
    logger.info("Clearing old path: %s", PYD_KEDRO_CACHE_DIR)
    remove_temp_objects()

    if cache_dir.exists():
        logger.warning("Cache path exists, reusing existing path: %s", cache_dir)
    else:
        logger.warning("Creating cache directory: %s", cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
    PYD_KEDRO_CACHE_DIR = cache_dir


def get_cache_dir() -> Path:
    """Get caching directory for pydantic-kedro."""
    global PYD_KEDRO_CACHE_DIR

    return PYD_KEDRO_CACHE_DIR


def remove_temp_objects() -> None:
    """Remove temporary objects at exist.

    This will be called at the exit of your application

    NOTE: This will NOT handle clearing objects when you change the cache
    directory outside of `set_cache_dir()`.
    """
    global PYD_KEDRO_CACHE_DIR, _INITIAL_TMPDIR

    shutil.rmtree(PYD_KEDRO_CACHE_DIR, ignore_errors=True)
    PYD_KEDRO_CACHE_DIR.unlink(missing_ok=True)
    if _INITIAL_TMPDIR is not None:
        # We no longer use this directory
        _INITIAL_TMPDIR.cleanup()


atexit.register(remove_temp_objects)
