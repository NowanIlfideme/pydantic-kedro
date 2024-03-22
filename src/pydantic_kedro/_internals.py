"""Functions for internal use."""

from typing import Any, Callable, Dict, Type

from kedro_datasets.pickle.pickle_dataset import PickleDataset
from kedro.io.core import AbstractDataset
from pydantic import BaseModel, create_model

KLS_MARK_STR = "class"


def import_string(dotted_path: str) -> Any:
    """Import the object from the string. Supports nested classes.

    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails.

    Stolen from Pydantic, who stole it approximately from django, and then improved.
    """
    from importlib import import_module
    from types import ModuleType

    parts = dotted_path.strip(" ").split(".")
    module: ModuleType = None  # type: ignore

    if len(parts) == 1:
        raise ImportError(f"{dotted_path!r} doesn't look like a module path")

    for rhs in range(1, len(parts)):
        class_parts = parts[-rhs:]
        module_path = ".".join(parts[:-rhs])
        try:
            module = import_module(module_path)
        except ImportError:
            # we need to move
            continue
        try:
            obj: Any = module
            for clp in class_parts:
                obj = getattr(obj, clp)
        except AttributeError as e:
            raise ImportError(f"Could not import {dotted_path!r}, though module exists.") from e
        break
    else:
        raise ImportError(f"Could not import {dotted_path!r}, likely no such module exists.")
    return obj


def get_kedro_map(kls: Type[BaseModel]) -> Dict[Type, Callable[[str], AbstractDataset]]:
    """Get type-to-dataset mapper for a Pydantic class."""
    if not (isinstance(kls, type) and issubclass(kls, BaseModel)):
        raise TypeError(f"Must pass a BaseModel subclass; got {kls!r}")
    kedro_map: Dict[Type, Callable[[str], AbstractDataset]] = {}
    # Go through bases of `kls` in order
    base_classes = reversed(kls.mro())
    for base_i in base_classes:
        # Get config class (if it's defined)
        cfg_i = getattr(base_i, "__config__", None)
        if cfg_i is None:
            continue
        # Get kedro_map (if it's defined)
        upd = getattr(cfg_i, "kedro_map", None)
        if upd is None:
            continue
        elif isinstance(upd, dict):
            # Detailed checks (to help users fix stuff)
            bad_keys = []
            bad_vals = []
            for k, v in upd.items():
                if isinstance(k, type):
                    if callable(v):
                        kedro_map[k] = v  # TODO: Check callable signature?
                    else:
                        bad_vals.append(v)
                else:
                    bad_keys.append(k)
            if len(bad_keys) > 0:
                raise TypeError(f"Keys in `kedro_map` must be types, but got bad keys: {bad_keys}")
            if len(bad_vals) > 0:
                raise TypeError(
                    "Values in `kedro_map` must be callable (or types),"
                    f" but got bad values: {bad_vals}"
                )
        else:
            raise TypeError(
                f"The `kedro_map` in config class {base_i.__qualname__} must be a dict, but got {upd!r}"
            )
    return kedro_map


def get_kedro_default(kls: Type[BaseModel]) -> Callable[[str], AbstractDataset]:
    """Get default Kedro dataset creator."""
    # Go backwards through bases of `kls` until you find a default value
    rev_bases = kls.mro()
    for base_i in rev_bases:
        # Get config class (if defined)
        cfg_i = getattr(base_i, "__config__", None)
        if cfg_i is None:
            continue
        # Get kedro_default (if it's defined)
        default = getattr(cfg_i, "kedro_default", None)
        if default is None:
            continue
        elif callable(default):
            # Special check for types
            if isinstance(default, type) and not issubclass(default, AbstractDataset):
                raise TypeError(
                    "The `kedro_default` must be an AbstractDataset or callable that creates one,"
                    f" but got {default!r}"
                )
            # TODO: Check callable signature?
            return default
        else:
            raise TypeError(
                "The `kedro_default` must be an AbstractDataset or callable that creates one,"
                f" but got {default!r}"
            )

    return PickleDataset


def create_expanded_model(model: BaseModel) -> BaseModel:
    """Create an 'expanded' model with additional metadata."""
    pyd_kls = type(model)
    if KLS_MARK_STR in pyd_kls.__fields__.keys():
        raise ValueError(f"Marker {KLS_MARK_STR!r} already exists as a field; can't dump model.")
    pyd_kls_path = f"{pyd_kls.__module__}.{pyd_kls.__qualname__}"

    field_defs = {KLS_MARK_STR: (str, pyd_kls_path)}

    tmp_kls = create_model(  # type: ignore
        pyd_kls.__name__,
        __base__=pyd_kls,
        __module__=pyd_kls.__module__,
        **field_defs,
    )
    tmp_obj = tmp_kls(**dict(model._iter(to_dict=False)))
    return tmp_obj
