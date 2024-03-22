"""YAML dataset definition for Pydantic."""

import warnings
from pathlib import PurePosixPath
from typing import Any, Dict, no_type_check

import fsspec
import ruamel.yaml as yaml
from fsspec import AbstractFileSystem
from kedro.io.core import AbstractDataset, get_filepath_str, get_protocol_and_path
from pydantic import BaseModel
from pydantic_yaml import to_yaml_file

from pydantic_kedro._dict_io import PatchPydanticIter, dict_to_model


class PydanticYamlDataset(AbstractDataset[BaseModel, BaseModel]):
    """Dataset for saving/loading Pydantic models, based on YAML.

    Please note that the Pydantic model must be JSON-serializable.
    That means the fields are "pure" Pydantic fields,
    or you have added `json_encoders` to the model config.

    Example:
    -------
    ```python
    class MyModel(BaseModel):
        x: str

    ds = PydanticYamlDataset('memory://path/to/model.yaml')  # using memory to avoid tempfile
    ds.save(MyModel(x="example"))
    assert ds.load().x == "example"
    ```
    """

    def __init__(self, filepath: str) -> None:
        """Create a new instance of PydanticYamlDataset to load/save Pydantic models for given filepath.

        Args:
        ----
        filepath : The location of the YAML file.
        """
        # TODO: Update to just save the path and open it with `fsspec` directly
        # parse the path and protocol (e.g. file, http, s3, etc.)
        protocol, path = get_protocol_and_path(filepath)
        self._protocol = protocol
        self._filepath = PurePosixPath(path)
        self._fs: AbstractFileSystem = fsspec.filesystem(self._protocol)

    @property
    def filepath(self) -> str:
        """File path name."""
        return str(self._filepath)

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
            dct = yaml.safe_load(f)

        assert isinstance(dct, dict), "YAML root must be a mapping."
        res = dict_to_model(dct)
        return res  # type: ignore

    @no_type_check
    def _save(self, data: BaseModel) -> None:
        """Save Pydantic model to the filepath."""
        # Open file and write to it
        save_path = get_filepath_str(self._filepath, self._protocol)

        # Ensure parent directory exists
        try:
            if "/" in save_path:
                parent_path, *_ = save_path.rsplit("/", maxsplit=1)
                self._fs.makedirs(parent_path, exist_ok=True)
        except Exception:
            warnings.warn(f"Failed to create parent path for {save_path}")

        with PatchPydanticIter():
            with self._fs.open(save_path, mode="w") as f:
                to_yaml_file(f, data)

    def _describe(self) -> Dict[str, Any]:
        """Return a dict that describes the attributes of the dataset."""
        return dict(filepath=self.filepath, protocol=self._protocol)
