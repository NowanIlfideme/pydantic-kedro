"""Zip-file dataset for Pydantic models with arbitrary types."""

from tempfile import TemporaryDirectory
from typing import Any, Dict
from uuid import uuid4

import fsspec
from fsspec.implementations.zip import ZipFileSystem
from kedro.io.core import AbstractDataSet
from pydantic import BaseModel

from pydantic_kedro._local_caching import get_cache_dir

from .folder import PydanticFolderDataSet


class PydanticZipDataSet(AbstractDataSet[BaseModel, BaseModel]):
    """Dataset for saving/loading Pydantic models, based on saving sub-datasets in a ZIP file.

    This allows fields with arbitrary types.

    Example:
    -------
    ```python
    class MyModel(BaseModel):
        x: str

    ds = PydanticZipDataSet('memory://path/to/model.zip')  # using memory to avoid tempfile
    ds.save(MyModel(x="example"))
    assert ds.load().x == "example"
    ```
    """

    def __init__(self, filepath: str) -> None:
        """Create a new instance of PydanticZipDataSet to load/save Pydantic models for given filepath.

        Args:
        ----
        filepath : The location of the Zip file.
        """
        self._filepath = filepath  # NOTE: This is not checked when created.

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
        filepath = self._filepath
        # Making a temp directory in the current cache dir location
        tmpdir = get_cache_dir() / str(uuid4()).replace("-", "")
        tmpdir.mkdir(exist_ok=False, parents=True)
        m_local = fsspec.get_mapper(str(tmpdir))
        # Unzip via copying to folder
        with fsspec.open(filepath) as zip_file:
            zip_fs = ZipFileSystem(fo=zip_file)  # type: ignore
            m_zip = zip_fs.get_mapper()
            for k, v in m_zip.items():
                m_local[k] = v
            zip_fs.close()
        # Load folder dataset
        pfds = PydanticFolderDataSet(str(tmpdir))
        res = pfds.load()
        return res

    def _save(self, data: BaseModel) -> None:
        """Save Pydantic model to the filepath."""
        filepath = self._filepath
        with TemporaryDirectory(prefix="pyd_kedro_") as tmpdir:
            # Save folder dataset
            pfds = PydanticFolderDataSet(tmpdir)
            pfds.save(data)
            # Zip via copying to folder
            m_local = fsspec.get_mapper(tmpdir)
            with fsspec.open(filepath, mode="wb") as zip_file:
                zip_fs = ZipFileSystem(fo=zip_file, mode="w")  # type: ignore
                m_zip = zip_fs.get_mapper()
                for k, v in m_local.items():
                    m_zip[k] = v
                zip_fs.close()

    def _describe(self) -> Dict[str, Any]:
        return dict(filepath=self.filepath)
