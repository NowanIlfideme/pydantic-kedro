"""Test issue with settings."""

import pytest
from pydantic import BaseModel, BaseSettings
from typing_extensions import Literal

from pydantic_kedro import load_model, save_model


class ExSettings(BaseSettings):
    """Settings class."""

    val: str


class ExModel(BaseModel):
    """Model class."""

    x: int = 1
    settings: ExSettings


@pytest.mark.parametrize("format", ["auto", "zip", "folder", "yaml", "json"])
def test_rt_settings(tmpdir: str, format: Literal["auto", "zip", "folder", "yaml", "json"]):
    """Test settings round-trip."""
    obj = ExModel(settings=ExSettings(val="val"))
    save_model(obj, f"{tmpdir}/obj", format=format)
    obj2 = load_model(f"{tmpdir}/obj", ExModel)
    assert obj.settings == obj2.settings
