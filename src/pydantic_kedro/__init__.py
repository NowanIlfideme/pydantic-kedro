"""Kedro datasets for serializing Pydantic models."""

__all__ = [
    "ArbConfig",
    "ArbModel",
    "PydanticAutoDataset",
    "PydanticFolderDataset",
    "PydanticJsonDataset",
    "PydanticYamlDataset",
    "PydanticZipDataset",
    "load_model",
    "save_model",
    "__version__",
    # compatibility
    "PydanticAutoDataSet",
    "PydanticFolderDataSet",
    "PydanticJsonDataSet",
    "PydanticYamlDataSet",
    "PydanticZipDataSet",
]

from .datasets.auto import PydanticAutoDataset
from .datasets.folder import PydanticFolderDataset
from .datasets.json import PydanticJsonDataset
from .datasets.yaml import PydanticYamlDataset
from .datasets.zip import PydanticZipDataset
from .models import ArbConfig, ArbModel
from .utils import load_model, save_model
from .version import __version__

# Old names for compatibility

PydanticAutoDataSet = PydanticAutoDataset
PydanticFolderDataSet = PydanticFolderDataset
PydanticJsonDataSet = PydanticJsonDataset
PydanticYamlDataSet = PydanticYamlDataset
PydanticZipDataSet = PydanticZipDataset
