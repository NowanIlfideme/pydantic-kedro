"""Test utility functions, loading and saving models."""

from pydantic.v1 import BaseModel

from pydantic_kedro import load_model, save_model


class MyModel(BaseModel):
    """My model."""

    x: str


def test_utils_load_save(tmpdir: str):
    """Minimal test for load/save."""
    # using memory to avoid tempfile
    save_model(MyModel(x="example"), f"{tmpdir}/model")

    obj = load_model(f"{tmpdir}/model")
    assert isinstance(obj, MyModel)
    assert obj.x == "example"
