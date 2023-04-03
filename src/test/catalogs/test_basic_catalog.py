"""Minimal tests for the Kedro catalog."""
import os
from pathlib import Path

from kedro.config import ConfigLoader
from kedro.io import DataCatalog
from pydantic import BaseModel

from pydantic_kedro import PydanticJsonDataSet

local_dir = Path(__file__).parent


class MyPureModel(BaseModel):
    """Your custom Pydantic model with JSON-safe fields."""

    x: int
    y: str


# # Create an in-memory (temporary) file via `fsspec` and save it
obj = MyPureModel(x=1, y="why?")
# ds = PydanticJsonDataSet(local_dir / "data/tst1.json")
# ds.save(obj)


def test_basic_catalog():
    """Basic test to ensure."""
    os.chdir(local_dir)
    conf_loader = ConfigLoader(str(local_dir / "conf"))
    catalog = DataCatalog.from_config(conf_loader.get("catalog.yml"))
    obj2 = catalog.load("tst1")
    assert isinstance(catalog.datasets.tst1, PydanticJsonDataSet)  # type: ignore
    assert obj2 == obj
