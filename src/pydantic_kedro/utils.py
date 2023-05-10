"""Utilities for reading/writing objects."""

from typing import Literal, Type, TypeVar

from kedro.io.core import AbstractDataSet
from pydantic import BaseModel

from pydantic_kedro.datasets.auto import PydanticAutoDataSet
from pydantic_kedro.datasets.folder import PydanticFolderDataSet
from pydantic_kedro.datasets.json import PydanticJsonDataSet
from pydantic_kedro.datasets.yaml import PydanticYamlDataSet
from pydantic_kedro.datasets.zip import PydanticZipDataSet

__all__ = ["load_model", "save_model"]

T = TypeVar("T", bound=BaseModel)


def load_model(uri: str, supercls: Type[T] = BaseModel) -> T:  # type: ignore
    """Load a Pydantic model from a given URI.

    Parameters
    ----------
    uri : str
        The path or URI to load the model from.
    supercls : type
        Ensure that the loaded model is of this type.
        By default, this is just BaseModel.
    """
    ds = PydanticAutoDataSet(filepath=uri)
    model = ds.load()
    if not isinstance(model, supercls):
        raise TypeError(f"Expected {supercls}, but got {type(model)}.")
    return model  # type: ignore


def save_model(
    model: BaseModel,
    uri: str,
    *,
    format: Literal["auto", "zip", "folder", "yaml", "json"] = "auto",
) -> None:
    """Save a Pydantic model to a given URI.

    Parameters
    ----------
    model : BaseModel
        Pydantic model to save. This can be 'pure' (JSON-safe) or 'arbitrary'.
    uri : str
        The path or URI to save the model to.
    format : {"auto", "zip", "folder", "yaml", "json"}
        The dataset format to use. "auto" will use [PydanticAutoDataSet][].
    """
    if not isinstance(model, BaseModel):
        raise TypeError(f"Expected Pydantic model, but got {model!r}")
    ds: AbstractDataSet
    if format == "auto":
        ds = PydanticAutoDataSet(uri)
    elif format == "zip":
        ds = PydanticZipDataSet(uri)
    elif format == "folder":
        ds = PydanticFolderDataSet(uri)
    elif format == "yaml":
        ds = PydanticYamlDataSet(uri)
    elif format == "json":
        ds = PydanticJsonDataSet(uri)
    else:
        raise ValueError(
            f"Unknown dataset format {format}, "
            'expected one of: ["auto", "zip", "folder", "yaml", "json"]'
        )
    ds.save(model)
