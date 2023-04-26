"""Tests the datasets on a simple model."""

from typing import Optional

import pytest
from kedro.io.core import AbstractDataSet
from pydantic import BaseModel

from pydantic_kedro import (
    PydanticFolderDataSet,
    PydanticJsonDataSet,
    PydanticZipDataSet,
)
from pydantic_kedro.extras import INSTALLED_YAML


class SimpleTestModel(BaseModel):
    """My very own model.

    NOTE: Since this is defined in `__main__`, this can only be loaded if ran in this file.
    """

    name: str
    alter_ego: Optional[str] = None


types = [PydanticJsonDataSet, PydanticFolderDataSet, PydanticZipDataSet]
if INSTALLED_YAML:
    from pydantic_kedro.datasets.yaml import PydanticYamlDataSet

    types.append(PydanticYamlDataSet)


@pytest.mark.parametrize(
    "mdl", [SimpleTestModel(name="user"), SimpleTestModel(name="Dr. Jekyll", alter_ego="Mr. Hyde")]
)
@pytest.mark.parametrize("kls", types)
def test_simple_model_rt(mdl: SimpleTestModel, kls: AbstractDataSet, tmpdir):  # type: ignore
    """Tests whether a simple model survives roundtripping."""
    paths = [f"{tmpdir}/model_on_disk", f"memory://{tmpdir}/model_in_memory"]
    for path in paths:
        ds: AbstractDataSet = kls(path)  # type: ignore
        ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, SimpleTestModel)
        assert m2 == mdl


# @pytest.mark.skipif(INSTALLED_YAML, reason="Extra 'yaml' (`pydantic-yaml` library) is not installed.")
