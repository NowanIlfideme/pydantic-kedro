"""Minimal tests for the Kedro catalog."""

import os
from pathlib import Path

from kedro.config import OmegaConfigLoader
from kedro.io import DataCatalog
from pydantic.v1 import BaseModel

from pydantic_kedro import PydanticJsonDataset

local_dir = Path(__file__).parent


class MyPureModel(BaseModel):
    """Your custom Pydantic model with JSON-safe fields."""

    x: int
    y: str


obj = MyPureModel(x=1, y="why?")
# To re-create the JSON file:
# ds = PydanticJsonDataset(local_dir / "data/tst1.json")
# ds.save(obj)


def test_basic_catalog():
    """Basic test to ensure."""
    os.chdir(local_dir)
    conf_loader = OmegaConfigLoader(str(local_dir / "conf"), env="local")
    catalog = DataCatalog.from_config(conf_loader["catalog"])
    obj2 = catalog.load("tst1")
    assert isinstance(catalog.datasets.tst1, PydanticJsonDataset)  # type: ignore
    assert obj2 == obj
