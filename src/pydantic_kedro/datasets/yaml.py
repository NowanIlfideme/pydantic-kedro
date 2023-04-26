"""YAML dataset definition for Pydantic."""

from pathlib import PurePosixPath
from typing import Any, Dict, no_type_check

import fsspec
from fsspec import AbstractFileSystem
from kedro.io.core import AbstractDataSet, get_filepath_str, get_protocol_and_path
from pydantic import BaseModel, Field, create_model
from pydantic.utils import import_string
from pydantic_yaml import parse_yaml_file_as, to_yaml_file

KLS_MARK_STR = "class"


class _YamlPreLoader(BaseModel):
    """YAML pre-loader model."""

    kls_mark_str: str = Field(alias=KLS_MARK_STR)


class PydanticYamlDataSet(AbstractDataSet[BaseModel, BaseModel]):
    """A Pydantic model with YAML-based load/save.

    This class is only available with the 'yaml' extra (or `pydantic-yaml>=1.0.0`).

    Please note that the Pydantic model must be JSON-serializable.
    That means the fields are "pure" Pydantic fields,
    or you have added `json_encoders` to the model config.

    Example:
    -------
    ```python
    class MyModel(BaseModel):
        x: str

    ds = PydanticYamlDataSet('memory://path/to/model.yaml')  # using memory to avoid tempfile
    ds.save(MyModel(x="example"))
    assert ds.load().x == "example"
    ```
    """

    def __init__(self, filepath: str) -> None:
        """Create a new instance of PydanticYamlDataSet to load/save Pydantic models for given filepath.

        Args:
        ----
        filepath : The location of the YAML file.
        """
        # parse the path and protocol (e.g. file, http, s3, etc.)
        protocol, path = get_protocol_and_path(filepath)
        self._protocol = protocol
        self._filepath = PurePosixPath(path)
        self._fs: AbstractFileSystem = fsspec.filesystem(self._protocol)

    def _load(self) -> BaseModel:
        """Load Pydantic model from the filepath.

        Returns
        -------
        Pydantic model.
        """
        # using get_filepath_str ensures that the protocol and path
        # are appended correctly for different filesystems
        load_path = get_filepath_str(self._filepath, self._protocol)
        with self._fs.open(load_path, mode="r") as f:
            preloader = parse_yaml_file_as(_YamlPreLoader, f)
        pyd_kls = import_string(preloader.kls_mark_str)
        assert issubclass(pyd_kls, BaseModel), f"Type must be a Pydantic model, got {type(pyd_kls)!r}."
        with self._fs.open(load_path, mode="r") as f:
            res = parse_yaml_file_as(pyd_kls, f)
        return res  # type: ignore

    @no_type_check
    def _save(self, data: BaseModel) -> None:
        """Save Pydantic model to the filepath."""
        # Add metadata to our Pydantic model
        pyd_kls = type(data)
        if KLS_MARK_STR in pyd_kls.__fields__.keys():
            raise ValueError(f"Marker {KLS_MARK_STR!r} already exists as a field; can't dump model.")
        pyd_kls_path = f"{pyd_kls.__module__}.{pyd_kls.__qualname__}"
        tmp_kls = create_model(
            pyd_kls.__name__,
            __base__=pyd_kls,
            __module__=pyd_kls.__module__,
            **{KLS_MARK_STR: (str, pyd_kls_path)},
        )
        tmp_obj = tmp_kls(**data.dict())

        # Open file and write to it
        save_path = get_filepath_str(self._filepath, self._protocol)
        with self._fs.open(save_path, mode="w") as f:
            to_yaml_file(f, tmp_obj)

    def _describe(self) -> Dict[str, Any]:
        """Return a dict that describes the attributes of the dataset."""
        return dict(filepath=self._filepath, protocol=self._protocol)
