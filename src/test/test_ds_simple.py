"""Tests the JSON dataset on a simple model."""

from typing import Optional, Union

import pytest
from pydantic import BaseModel

from pydantic_kedro import (
    PydanticFolderDataSet,
    PydanticJsonDataSet,
    PydanticZipDataSet,
)


class SimpleTestModel(BaseModel):
    """My very own model.

    NOTE: Since this is defined in `__main__`, this can only be loaded if ran in this notebook.
    """

    name: str
    alter_ego: Optional[str] = None


Kls = Union[PydanticFolderDataSet, PydanticJsonDataSet, PydanticZipDataSet]


@pytest.mark.parametrize(
    "mdl", [SimpleTestModel(name="user"), SimpleTestModel(name="Dr. Jekyll", alter_ego="Mr. Hyde")]
)
@pytest.mark.parametrize("kls", [PydanticJsonDataSet, PydanticFolderDataSet, PydanticZipDataSet])
def test_simple_model_rt(mdl: SimpleTestModel, kls: Kls, tmpdir):
    """Tests whether a simple model survives roundtripping."""
    paths = [f"{tmpdir}/model_on_disk", f"memory://{tmpdir}/model_in_memory"]
    for path in paths:
        ds: Kls = kls(path)  # type: ignore
        ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, SimpleTestModel)
        assert m2 == mdl
