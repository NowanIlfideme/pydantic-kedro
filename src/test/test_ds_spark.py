"""Test dataset for PySpark specifically."""

from typing import Any, Union

import pytest
from kedro_datasets.spark.spark_dataset import SparkDataset
from pyspark.sql import DataFrame, SparkSession

from pydantic_kedro import (
    ArbConfig,
    ArbModel,
    PydanticAutoDataset,
    PydanticFolderDataset,
    PydanticZipDataset,
)

Kls = Union[PydanticAutoDataset, PydanticFolderDataset, PydanticZipDataset]


class _SparkModel(ArbModel):
    """Spark model, configured to use SparkDataset (mult-file parquet)."""

    class Config(ArbConfig):
        kedro_map = {DataFrame: lambda x: SparkDataset(filepath=x)}


class FlatSparkModel(_SparkModel):
    """Flat model that tests Spark using Picke dataset (default)."""

    df: DataFrame
    val: int


@pytest.fixture
def spark() -> SparkSession:
    """Create a Spark session for testing."""
    return SparkSession.Builder().appName("pydantic-kedro-testing").getOrCreate()


@pytest.mark.parametrize("kls", [PydanticAutoDataset, PydanticFolderDataset, PydanticZipDataset])
@pytest.mark.parametrize(
    "df_raw",
    [
        [{"a": 1, "b": 2, "c": 3}],
    ],
)
def test_spark_flat_model(kls: Kls, df_raw: list[dict[str, Any]], spark: SparkSession, tmpdir):
    """Test roundtripping of the flat Spark model, using Kedro's SparkDataset."""
    dfx = spark.createDataFrame(df_raw)  # type: ignore
    mdl = FlatSparkModel(df=dfx, val=1)
    paths = [f"{tmpdir}/model_on_disk", f"memory://{tmpdir}/model_in_memory"]
    for path in paths:
        ds: Kls = kls(path)  # type: ignore
        ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, FlatSparkModel)
        assert m2.df.count() == mdl.df.count()
