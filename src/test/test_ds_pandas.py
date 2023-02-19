from typing import Any, Dict, Union

import pandas as pd
import pytest
from kedro.extras.datasets.pandas import ParquetDataSet

from pydantic_kedro import ArbModel, PydanticFolderDataSet, PydanticZipDataSet

Kls = Union[PydanticFolderDataSet, PydanticZipDataSet]

dfx = pd.DataFrame([[1, 2, 3]], columns=["a", "b", "c"])


class _PdModel(ArbModel):
    """Pandas model, configured to use Parquet."""

    class Config(ArbModel.Config):
        kedro_map = {pd.DataFrame: ParquetDataSet}


class FlatPandasModel(ArbModel):
    """Flat model that tests Pandas using Picke dataset (default)."""

    df: pd.DataFrame
    val: int


class NestedPandasModel(_PdModel):
    """Flat model that tests Pandas using Parquet and Pickle datasets."""

    class Inner(ArbModel):
        """Nested model (notice `ArbModel`, not `_PdModel`) but will use `_PdModel` config anyways.

        This is because the NestedPandasModel is the one being serialized.
        TODO: This is something to reconsider in the future.
        """

        z: pd.DataFrame = dfx

    x: int = 1
    x_map: dict[int, int] = {1: 1}
    df: pd.DataFrame = dfx
    df_map: dict[int, pd.DataFrame] = {1: dfx}
    df_list: list[pd.DataFrame] = [dfx]
    nested: Inner = Inner()
    onion: Union[pd.DataFrame, Dict[str, Any]] = dfx
    any_model: Any = None


@pytest.mark.parametrize("kls", [PydanticFolderDataSet, PydanticZipDataSet])
def test_pandas_flat_model(kls: Kls, tmpdir):
    """Test roundtripping of the flat Pandas model, using default Pickle dataset."""
    mdl = FlatPandasModel(df=dfx, val=1)
    paths = [f"{tmpdir}/model_on_disk", f"memory://{tmpdir}/model_in_memory"]
    for path in paths:
        ds: Kls = kls(path)  # type: ignore
        with pytest.warns(match="No dataset defined for.*"):
            ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, FlatPandasModel)
        assert m2.df.equals(mdl.df)


@pytest.mark.parametrize("kls", [PydanticFolderDataSet, PydanticZipDataSet])
def test_pandas_nested_model(kls: Kls, tmpdir):
    """Test roundtripping of the nested Pandas model, using Parquet dataset."""
    mdl = NestedPandasModel()
    paths = [f"{tmpdir}/model_on_disk", f"memory://{tmpdir}/model_in_memory"]
    for path in paths:
        ds: Kls = kls(path)  # type: ignore
        ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, NestedPandasModel)
        assert m2.df.equals(mdl.df)
        assert m2.nested.z.equals(mdl.nested.z)
