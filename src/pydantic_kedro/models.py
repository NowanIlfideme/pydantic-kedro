"""Models to use as base classes."""

from typing import Callable, Dict, Type

from kedro_datasets.pickle.pickle_dataset import PickleDataset
from kedro.io import AbstractDataset
from pydantic import BaseConfig, BaseModel


class ArbConfig(BaseConfig):
    """Configuration with arbitrary types allowed; see [pydantic_kedro.ArbModel][]."""

    arbitrary_types_allowed = True

    kedro_map: Dict[Type, Callable[[str], AbstractDataset]] = {}
    kedro_default: Callable[[str], AbstractDataset] = PickleDataset


class ArbModel(BaseModel):
    """Base Pydantic Model with arbitrary types allowed in the config.

    This also supports type hints for `pydantic_kedro` in the configuration:

    - `kedro_map`, which maps a type to a dataset constructor to use.
    - `kedro_default`, which specifies the default dataset type to use
      ([kedro_datasets.pickle.PickleDataSet][])

    These are pseudo-inherited, see [config-inheritence][].
    You do not actually need to inherit from `ArbModel` for this to work, however it can help with
    type completion in your IDE.
    """

    Config = ArbConfig
