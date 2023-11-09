"""Tests for proper inheritence of classes."""

from pathlib import Path
from typing import Type, Union

import pandas as pd
import pytest
from kedro.extras.datasets.pandas import CSVDataSet, ParquetDataSet
from kedro.extras.datasets.pickle import PickleDataSet
from pydantic import BaseModel

from pydantic_kedro import PydanticFolderDataSet

dfx = pd.DataFrame([[1, 2, 3]], columns=["a", "b", "c"])


class BaseA(BaseModel):
    """First model in hierarchy, using Parquet for Pandas."""

    class Config:
        """Config for pydantic-kedro."""

        arbitrary_types_allowed = True
        kedro_map = {pd.DataFrame: ParquetDataSet}


class Model1A(BaseA):
    """Model with Parquet dataset base."""

    df: pd.DataFrame


def csv_ds(path: str) -> CSVDataSet:
    """Create a CSV dataset."""
    return CSVDataSet(path, save_args=dict(index=False), load_args=dict())


class BaseB(BaseA):
    """Second model in hierarchy, using CSV for Pandas."""

    class Config:
        """Config for pydantic-kedro."""

        kedro_map = {pd.DataFrame: csv_ds}


class Model1B(BaseB):
    """Model with CSV dataset base."""

    df: pd.DataFrame


class BaseC(BaseB):
    """Third model in hierarchy, not providing any kedro_map."""


class Model1C(BaseC):
    """Model with CSV dataset base (again)."""

    df: pd.DataFrame


class Fake:
    """Fake class."""


class BaseD(BaseC):
    """Fourth model in hierarchy, providing updated kedro_map (for Fake) and updated default.

    However, since we pseudo-inherit `{pd.DataFrame: csv_ds}` mapping from BaseB,
    """

    class Config:
        """Config for pydantic-kedro."""

        kedro_map = {Fake: PickleDataSet}
        kedro_default = ParquetDataSet  # Bad idea in practice, but this is for the test


class Model1D(BaseD):
    """Model with CSV dataset base, even though we changed other config parts."""

    df: pd.DataFrame


@pytest.mark.parametrize(
    ["model_type", "ds_type"],
    [[Model1A, ParquetDataSet], [Model1B, CSVDataSet], [Model1C, CSVDataSet], [Model1D, CSVDataSet]],
)
def test_pandas_flat_model(
    tmpdir,
    model_type: Type[Union[Model1A, Model1B, Model1C, Model1D]],
    ds_type: Type[Union[ParquetDataSet, CSVDataSet]],
):
    """Test roundtripping of the different dataset models."""
    # Create and save model
    model = model_type(df=dfx)
    path = Path(f"{tmpdir}/model_on_disk")
    PydanticFolderDataSet(str(path)).save(model)
    # Try loading with the supposed dataframe type
    found_df = ds_type(str(path / ".df")).load()
    assert isinstance(found_df, pd.DataFrame)
