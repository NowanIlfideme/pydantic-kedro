"""Tests the JSON dataset on a simple model."""

from typing import Optional

import pytest
from pydantic import BaseModel

from pydantic_kedro import PydanticJsonDataSet


class MyModel(BaseModel):
    """My very own model.

    NOTE: Since this is defined in `__main__`, this can only be loaded if ran in this notebook.
    """

    name: str
    alter_ego: Optional[str] = None


@pytest.mark.parametrize("mdl", [MyModel(name="user"), MyModel(name="Dr. Jekyll", alter_ego="Mr. Hyde")])
def test_simple_model_json_rt(mdl: MyModel, tmpdir):
    """Tests whether a simple model survives a roundtripping."""
    paths = [f"{tmpdir}/model.json", "memory://in-mem-file.json"]
    for path in paths:
        ds = PydanticJsonDataSet(path)
        ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, MyModel)
        assert m2 == mdl
