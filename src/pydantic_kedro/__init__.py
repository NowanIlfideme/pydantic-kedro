"""Kedro datasets for serializing Pydantic models."""

__all__ = [
    "ArbModel",
    "PydanticFolderDataSet",
    "PydanticJsonDataSet",
    "PydanticZipDataSet",
    "__version__",
]

from .datasets.folder import PydanticFolderDataSet
from .datasets.json import PydanticJsonDataSet
from .datasets.zip import PydanticZipDataSet
from .extras import INSTALLED_YAML
from .models import ArbModel
from .version import __version__

if INSTALLED_YAML:
    from .datasets.yaml import PydanticYamlDataSet  # noqa

    __all__.append("PydanticYamlDataSet")
