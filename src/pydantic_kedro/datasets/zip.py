"""Zip-file dataset for Pydantic models with arbitrary types."""

from tempfile import TemporaryDirectory
from typing import Any, Dict

import fsspec
from fsspec.implementations.zip import ZipFileSystem
from kedro.io.core import AbstractDataSet
from pydantic import BaseModel

from .folder import PydanticFolderDataSet


class PydanticZipDataSet(AbstractDataSet[BaseModel, BaseModel]):
    """A Pydantic model with Zip-file-based load/save.

    This allows fields with arbitrary types.

    Example:
    ::

        >>> PydanticZipDataSet(filepath='/path/to/model.zip')
    """

    def __init__(self, filepath: str) -> None:
        """Creates a new instance of PydanticZipDataSet to load/save Pydantic models for given filepath.

        Args
        ----
        filepath : The location of the Zip file.
        """
        self._filepath = filepath

    def _load(self) -> BaseModel:
        """Loads Pydantic model from the filepath.

        Returns
        -------
        Pydantic model.
        """
        filepath = self._filepath
        with TemporaryDirectory(prefix="pyd_kedro_") as tmpdir:
            m_local = fsspec.get_mapper(tmpdir)
            # Unzip via copying to folder
            with fsspec.open(filepath) as zip_file:
                zip_fs = ZipFileSystem(fo=zip_file)  # type: ignore
                m_zip = zip_fs.get_mapper()
                for k in m_zip.keys():
                    m_local[k] = m_zip[k]
                zip_fs.close()
            # Load folder dataset
            pfds = PydanticFolderDataSet(tmpdir)
            res = pfds.load()
        return res

    def _save(self, data: BaseModel) -> None:
        """Saves Pydantic model to the filepath."""
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
                for k in m_zip.keys():
                    m_zip[k] = m_local[k]
                zip_fs.close()

    def _describe(self) -> Dict[str, Any]:
        return dict(filepath=self._filepath)
