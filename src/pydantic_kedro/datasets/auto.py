"""Generic Kedro dataset."""

from typing import Any, Dict, Literal, Union

import fsspec
from fsspec import AbstractFileSystem
from kedro.io.core import AbstractDataset, get_protocol_and_path
from pydantic.v1 import BaseModel

from .folder import PydanticFolderDataset
from .json import PydanticJsonDataset
from .yaml import PydanticYamlDataset
from .zip import PydanticZipDataset

__all__ = ["PydanticAutoDataset"]


class PydanticAutoDataset(AbstractDataset[BaseModel, BaseModel]):
    """Dataset for self-describing Pydantic models.

    This allows fields with arbitrary types.
    When loading, it automatically detects the dataset type.
    When saving, it saves 'pure' models as YAML datasets, and arbitrary models as Zip datasets.
    This can be changed in the dataset object creation.

    Example:
    -------
    ```python
    class MyModel(BaseModel):
        x: str

    # using memory to avoid tempfile
    ds_write = PydanticZipDataset('memory://path/to/model.zip')
    ds_write.save(MyModel(x="example"))

    ds_load = PydanticAutoDataset('memory://path/to/model.zip')
    assert ds_load.load().x == "example"
    ```

    Example:
    -------
    ```python
    class MyModel(BaseModel):
        x: str

    # using memory to avoid tempfile
    ds = PydanticAutoDataset('memory://path/to/model')
    ds.save(MyModel(x="example"))  # selects YAML by default

    ds2 = PydanticAutoDataset(
        'memory://path/to/model',
        default_format_pure="json",
        default_format_arbitrary="folder",
    )
    ds2.save(MyModel(x="example"))  # selects JSON
    ```
    """

    def __init__(
        self,
        filepath: str,
        default_format_pure: Literal["yaml", "json", "zip", "folder"] = "yaml",
        default_format_arbitrary: Literal["zip", "folder"] = "zip",
    ) -> None:
        """Create a new instance of PydanticAutoDataset to load/save Pydantic models for given filepath.

        Args:
        ----
        filepath : The location of the Zip file.
        default_format_pure : Default format for saving "pure" models.
        default_format_arbitrary : Default format for saving "arbitrary" models.
        """
        assert default_format_pure in ["yaml", "json", "zip", "folder"]
        assert default_format_arbitrary in ["zip", "folder"]
        self._filepath = str(filepath)
        self._default_format_pure: Literal["yaml", "json", "zip", "folder"] = default_format_pure
        self._default_format_arbitrary: Literal["zip", "folder"] = default_format_arbitrary

    @property
    def filepath(self) -> str:
        """File path name."""
        return str(self._filepath)

    @property
    def default_format_pure(self) -> Literal["yaml", "json", "zip", "folder"]:
        """The default saving format used for 'pure' pydantic models."""
        return self._default_format_pure

    @property
    def default_format_arbitrary(self) -> Literal["zip", "folder"]:
        """The default saving format used for 'arbitrary' pydantic models."""
        return self._default_format_arbitrary

    def _get_ds(
        self, name: Literal["yaml", "json", "zip", "folder"]
    ) -> Union[PydanticYamlDataset, PydanticJsonDataset, PydanticFolderDataset, PydanticZipDataset]:
        """Map the format name to dataset type, and create it."""
        if name == "yaml":
            return PydanticYamlDataset(self.filepath)
        if name == "json":
            return PydanticJsonDataset(self.filepath)
        if name == "zip":
            return PydanticZipDataset(self.filepath)
        if name == "folder":
            return PydanticFolderDataset(self.filepath)
        raise ValueError(f"Unknown dataset keyword: {name}")

    def _load(self) -> BaseModel:
        """Load Pydantic model from the filepath.

        Returns
        -------
        Pydantic model.
        """
        filepath = self._filepath
        of = fsspec.open(filepath)
        fs: AbstractFileSystem = of.fs  # type: ignore
        _, path = get_protocol_and_path(filepath)

        # If it's a directory, try to open as a folder
        if fs.isdir(path):
            try:
                return PydanticFolderDataset(filepath).load()
            except Exception as exc:
                raise RuntimeError(
                    f"Path {filepath} is a directory, but failed to load PydanticFolderDataset from it."
                ) from exc

        # Try other datatsets
        # Yes, this looks hacky
        errors: list[Exception] = []
        try:
            return PydanticJsonDataset(filepath).load()
        except Exception as e1:
            errors.append(e1)

        try:
            return PydanticYamlDataset(filepath).load()
        except Exception as e2:
            errors.append(e2)

        try:
            return PydanticZipDataset(filepath).load()
        except Exception as e3:
            errors.append(e3)

        err_info = "\n".join([str(e) for e in errors])
        raise RuntimeError(f"Failed to load any dataset from the path {filepath!r}.\n{err_info}")

    def _save(self, data: BaseModel) -> None:
        """Save Pydantic model to the filepath."""
        try:
            self._get_ds(self.default_format_pure).save(data)
            return
        except Exception:
            pass
        self._get_ds(self.default_format_arbitrary).save(data)

    def _describe(self) -> Dict[str, Any]:
        return dict(
            filepath=self.filepath,
            default_format_pure=self.default_format_pure,
            default_format_arbitrary=self.default_format_arbitrary,
        )
