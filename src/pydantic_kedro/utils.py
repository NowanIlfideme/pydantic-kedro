"""Utilities for reading/writing objects."""

from typing import Literal, Type, TypeVar

from kedro.io.core import AbstractDataset
from pydantic import BaseModel

from pydantic_kedro.datasets.auto import PydanticAutoDataset
from pydantic_kedro.datasets.folder import PydanticFolderDataset
from pydantic_kedro.datasets.json import PydanticJsonDataset
from pydantic_kedro.datasets.yaml import PydanticYamlDataset
from pydantic_kedro.datasets.zip import PydanticZipDataset

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
    ds = PydanticAutoDataset(filepath=uri)
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
        The dataset format to use.
        "auto" will use [PydanticAutoDataset][pydantic_kedro.PydanticAutoDataset].
    """
    if not isinstance(model, BaseModel):
        raise TypeError(f"Expected Pydantic model, but got {model!r}")
    ds: AbstractDataset
    if format == "auto":
        ds = PydanticAutoDataset(uri)
    elif format == "zip":
        ds = PydanticZipDataset(uri)
    elif format == "folder":
        ds = PydanticFolderDataset(uri)
    elif format == "yaml":
        ds = PydanticYamlDataset(uri)
    elif format == "json":
        ds = PydanticJsonDataset(uri)
    else:
        raise ValueError(
            f"Unknown dataset format {format}, "
            'expected one of: ["auto", "zip", "folder", "yaml", "json"]'
        )
    ds.save(model)
