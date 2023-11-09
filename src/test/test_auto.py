"""Specialized tests for `PydanticAutoDataSet`."""

from pydantic import BaseModel

from pydantic_kedro import PydanticAutoDataSet, PydanticJsonDataSet, PydanticZipDataSet


class MyModel(BaseModel):
    """My model."""

    x: str


def test_auto_docstring():
    """Test PydanticAutoDataSet's docstring example."""
    # using memory to avoid tempfile
    ds_write = PydanticZipDataSet("memory://path/to/model.zip")
    ds_write.save(MyModel(x="example"))

    ds_load = PydanticAutoDataSet("memory://path/to/model.zip")
    obj = ds_load.load()
    assert isinstance(obj, MyModel)
    assert obj.x == "example"

    # using memory to avoid tempfile
    ds = PydanticAutoDataSet("memory://path/to/model")
    ds.save(MyModel(x="example"))  # selects YAML by default

    ds2 = PydanticAutoDataSet(
        "memory://path/to/model-json",
        default_format_pure="json",
        default_format_arbitrary="folder",
    )
    ds2.save(MyModel(x="example"))  # selects JSON

    ds_json = PydanticJsonDataSet("memory://path/to/model-json")
    assert isinstance(ds_json.load(), MyModel)
