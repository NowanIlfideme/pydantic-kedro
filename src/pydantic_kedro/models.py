"""Models to use as base classes."""

from typing import Callable, Dict, Type

from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import AbstractDataSet
from pydantic import BaseConfig, BaseModel


class ArbConfig(BaseConfig):
    """Configuration with arbitrary types allowed; see [pydantic_kedro.ArbModel][]"""

    arbitrary_types_allowed = True

    kedro_map: Dict[Type, Callable[[str], AbstractDataSet]] = {}
    kedro_default: Callable[[str], AbstractDataSet] = PickleDataSet


class ArbModel(BaseModel):
    """Base Pydantic Model with arbitrary types allowed in the config.

    This also supports type hints for `pydantic_kedro` in the configuration:

    - `kedro_map`, which maps a type to a dataset constructor to use.
    - `kedro_default`, which specifies the default dataset type to use.

    These are NOT currently inherited (TODO).
    The default dataset type that's used is [kedro.extras.datasets.pickle.PickleDataSet][]
    """

    Config = ArbConfig
