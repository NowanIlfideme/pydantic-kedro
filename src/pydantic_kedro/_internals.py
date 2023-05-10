"""Functions for internal use."""

from typing import Callable, Dict, Type

from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io.core import AbstractDataSet
from pydantic import BaseModel


def get_kedro_map(kls: Type[BaseModel]) -> Dict[Type, Callable[[str], AbstractDataSet]]:
    """Get mapper for type-to-kedro-dataset."""
    kedro_map: Dict[Type, Callable[[str], AbstractDataSet]] = {}
    # Update
    # FIXME: Go through bases of `kls`
    upd = getattr(kls.__config__, "kedro_map", {})
    assert isinstance(upd, dict)
    kedro_map.update(upd)
    return kedro_map


def get_kedro_default(kls: Type[BaseModel]) -> Callable[[str], AbstractDataSet]:
    """Get default Kedro dataset creator."""
    # FIXME: Go through bases of `kls`
    return getattr(kls.__config__, "kedro_default", PickleDataSet)
