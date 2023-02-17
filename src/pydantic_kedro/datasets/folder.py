"""Folder-based dataset for Pydantic models with arbitrary types."""

from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

import fsspec
from fsspec.core import strip_protocol
from kedro.io.core import AbstractDataSet, parse_dataset_definition
from pydantic import BaseConfig, BaseModel, Extra, Field
from pydantic.utils import import_string

__all__ = ["PydanticFolderDataSet"]


JsonPath = str  # not a "real" JSON Path, but just `.`-separated


class KedroDataSetSpec(BaseModel):
    """Kedro dataset specification. This allows arbitrary extra fields, including versions."""

    type_: str = Field(alias="type")
    relative_path: str

    class Config(BaseConfig):
        """Internal Pydantic model configuration."""

        allow_population_by_field_name = True
        extra = Extra.allow

    def to_dataset(
        self, base_path: str, load_version: Optional[str] = None, save_version: Optional[str] = None
    ) -> AbstractDataSet:
        """Builds the DataSet object."""
        fsp = strip_protocol(base_path)  # I mean, this should be a local path...
        new_path = f"{fsp}/{self.relative_path}"
        config = self.dict(exclude={"relative_path"}, by_alias=True)
        config["filepath"] = new_path
        kls, params = parse_dataset_definition(
            config,
            load_version=load_version,  # type: ignore
            save_version=save_version,  # type: ignore
        )
        return kls(**params)


class FolderFormatMetadata(BaseModel):
    """Metadata for the folder-formatted dataset.

    Attributes
    ----------
    model_class : str
        The class name of the model.
    model_info
        Model parameters, encoded with a data path.
    catalog : dict
        Mapping of "json path" to a dataset spec.
    """

    model_class: str
    model_info: Union[Dict[str, Any], List[Any]]
    catalog: Dict[JsonPath, KedroDataSetSpec] = {}


def mutate_jsp(struct: Union[Dict[str, Any], List[Any]], jsp: List[str], obj: Any) -> None:
    """Mutates `struct` in-place given the jsp (which is json-path-like)."""
    if isinstance(struct, dict):
        key = jsp[0]
        if len(jsp) == 1:
            # Mutate element
            struct[key] = obj
            return
        else:
            mutate_jsp(struct[key], jsp[1:], obj)
    elif isinstance(struct, list):
        idx = int(jsp[0])
        if len(jsp) == 1:
            struct[idx] = obj
            return
        else:
            mutate_jsp(struct[idx], jsp[1:], obj)
    else:
        raise TypeError(f"Unknown struct passed: {struct!r}")


class PydanticFolderDataSet(AbstractDataSet[BaseModel, BaseModel]):
    """A Pydantic model with folder-based load/save.

    This allows fields with arbitrary types.

    Example:
    ::

        >>> PydanticFolderDataSet(filepath='/path/to/model')
    """

    def __init__(self, filepath: str) -> None:
        """Creates a new instance of PydanticFolderDataSet to load/save Pydantic models for given path.

        Args
        ----
        filepath : The location of the folder.
        """
        self._filepath = filepath

    def _load(self) -> BaseModel:
        """Loads Pydantic model from the filepath.

        Returns
        -------
        Pydantic model.
        """
        filepath = self._filepath
        with fsspec.open(f"{filepath}/meta.json") as f:
            meta = FolderFormatMetadata.parse_raw(f.read())  # type: ignore

        # Ensure model type is importable
        model_cls = import_string(meta.model_class)
        assert issubclass(model_cls, BaseModel)

        # Check jsonpath? or maybe in validator?

        # Load data objects and mutate in-place
        model_data: Union[Dict[str, Any], List[Any]] = deepcopy(meta.model_info)
        for jsp_str, ds_spec in meta.catalog.items():
            jsp = jsp_str.split(".")
            ds_i = ds_spec.to_dataset(base_path=filepath)
            obj_i = ds_i.load()
            mutate_jsp(model_data, jsp, obj_i)

        res = model_cls.parse_obj(model_data)
        return res

    def _save(self, data: BaseModel) -> None:
        """Saves Pydantic model to the filepath."""
        filepath = self._filepath

        # TODO
        model_class_str = ""
        model_info: Union[Dict[str, Any], List[Any]] = {}
        catalog: Dict[JsonPath, KedroDataSetSpec] = {}

        # Create and write metadata
        meta = FolderFormatMetadata(model_class=model_class_str, model_info=model_info, catalog=catalog)
        with fsspec.open(f"{filepath}/meta.json", mode="w") as f:
            f.write(meta.json())  # type: ignore

        # Write catalog?
        # TODO

    def _describe(self) -> Dict[str, Any]:
        return dict(filepath=self._filepath)
