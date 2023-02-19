"""Models to use as base classes."""

from typing import Dict, Type

from kedro.io import AbstractDataSet
from pydantic import BaseConfig, BaseModel


class ArbModel(BaseModel):
    """Model with arbitrary types allowed in the config.

    This also supports `pydantic_kedro` typing in the configuration.
    """

    class Config(BaseConfig):
        arbitrary_types_allowed = True

        kedro_map: Dict[Type, Type[AbstractDataSet]] = {}
