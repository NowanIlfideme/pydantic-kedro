"""Test for standalone docs."""

from tempfile import TemporaryDirectory

import pandas as pd
from kedro_datasets.pandas.parquet_dataset import ParquetDataset

from pydantic_kedro import ArbConfig, ArbModel, load_model, save_model

# Arbitrary model class with a few useful defaults


class _PdModel(ArbModel):
    """Pandas model, configured to use Parquet."""

    class Config(ArbConfig):
        kedro_map = {pd.DataFrame: lambda x: ParquetDataset(filepath=x)}


class MyModel(_PdModel):
    """My custom model."""

    name: str
    data: pd.DataFrame


def test_docs_standalone_pd():
    """Test example in read/write docs that uses pandas."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})

    # We can use any fsspec URL, so we'll make a temporary folder
    with TemporaryDirectory() as tmpdir:
        save_model(MyModel(name="foo", data=df), f"{tmpdir}/my_model")
        obj = load_model(f"{tmpdir}/my_model")
        assert isinstance(obj, MyModel)
        assert obj.data.equals(df)
