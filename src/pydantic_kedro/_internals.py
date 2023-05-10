"""Functions for internal use."""

from typing import Callable, Dict, Type

from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io.core import AbstractDataSet
from pydantic import BaseModel


def get_kedro_map(kls: Type[BaseModel]) -> Dict[Type, Callable[[str], AbstractDataSet]]:
    """Get type-to-dataset mapper for a Pydantic class."""
    if not (isinstance(kls, type) and issubclass(kls, BaseModel)):
        raise TypeError(f"Must pass a BaseModel subclass; got {kls!r}")
    kedro_map: Dict[Type, Callable[[str], AbstractDataSet]] = {}
    # Go through bases of `kls` in order
    base_classes = kls.mro()
    for base_i in base_classes:
        # Get config class (if it's defined)
        cfg_i = getattr(base_i, "__config__")
        if cfg_i is None:
            continue
        # Get kedro_map (if it's defined)
        upd = getattr(cfg_i, "kedro_map")
        if upd is None:
            continue
        elif isinstance(upd, dict):
            # Detailed checks (to help users fix stuff)
            bad_keys = []
            bad_vals = []
            for k, v in upd.keys():
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
                raise TypeError(f"Values in `kedro_map` must be callable, but got bad vals: {bad_vals}")
        else:
            raise TypeError(
                f"The `kedro_map` in config class {base_i.__qualname__} must be a dict, but got {upd!r}"
            )
    return kedro_map


def get_kedro_default(kls: Type[BaseModel]) -> Callable[[str], AbstractDataSet]:
    """Get default Kedro dataset creator."""
    # FIXME: Go through bases of `kls`
    return getattr(kls.__config__, "kedro_default", PickleDataSet)
