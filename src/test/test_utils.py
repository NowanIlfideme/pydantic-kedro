"""Test utility functions, loading and saving models."""

from typing import Any

from pydantic_kedro import load_model, save_model
from pydantic_kedro._pydantic import BaseModel


class MyModel(BaseModel):
    """My model."""

    x: str


def test_utils_load_save(tmpdir: str):
    """Minimal test for load/save."""
    # using memory to avoid tempfile
    save_model(MyModel(x="example"), f"{tmpdir}/model")

    obj: Any = load_model(f"{tmpdir}/model")
    assert isinstance(obj, MyModel)
    assert obj.x == "example"
