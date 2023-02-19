"""Folder-based dataset for Pydantic models with arbitrary types."""

import inspect
import json
import warnings
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union
from uuid import uuid4

import fsspec
from fsspec.core import strip_protocol
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io.core import AbstractDataSet, parse_dataset_definition
from pydantic import BaseConfig, BaseModel, Extra, Field
from pydantic.utils import import_string

# __all__ = ["PydanticFolderDataSet"]


DATA_PLACEHOLDER = "__DATA_PLACEHOLDER__"

JsonPath = str  # not a "real" JSON Path, but just `.`-separated
_Bis = Union[bool, int, str, Path, None]


class KedroDataSetSpec(BaseModel):
    """Kedro dataset specification. This allows arbitrary extra fields, including versions.

    Unfortunately, because there's no standard on how to specify "file paths", this will likely fail
    in many cases where it "should" work.
    """

    type_: str = Field(alias="type")
    relative_path: str
    args: Dict[str, Union[_Bis, Dict[str, Dict[str, _Bis]]]] = {}

    class Config(BaseConfig):
        """Internal Pydantic model configuration."""

        allow_population_by_field_name = True
        extra = Extra.allow
        smart_union = True

    @classmethod
    def from_dataset(cls, ds: AbstractDataSet, relative_path: str) -> "KedroDataSetSpec":
        """Gets class from dataset."""
        raw_args = ds._describe()
        # We need to actually look at the kwargs to ensure we don't pass any extra args...
        # ... because these implementations don't describe themselves correctly. Ugh.
        sig = inspect.signature(type(ds))
        clean_args: Dict[str, Any] = {}
        for k, v in raw_args.items():
            if k in sig.parameters:
                clean_args[k] = v
            else:
                warnings.warn(f"Ignoring dataset {type(ds).__name__} keyword {k!r} = {v!r}")
        return cls(type=get_import_name(type(ds)), relative_path=relative_path, args=clean_args)

    def to_dataset(
        self, base_path: str, load_version: Optional[str] = None, save_version: Optional[str] = None
    ) -> AbstractDataSet:
        """Builds the DataSet object.

        This assumes the local path is called `filepath`.
        """
        fsp = strip_protocol(base_path)  # I mean, this should be a local path...
        new_path = f"{fsp}/{self.relative_path}"
        config = self.dict(exclude={"relative_path"}, by_alias=True)
        config = {"type": self.type_, **self.args}
        config["filepath"] = new_path
        kls, params_raw = parse_dataset_definition(
            config,
            load_version=load_version,  # type: ignore
            save_version=save_version,  # type: ignore
        )

        # Ensure parameters exist on the dataset
        sig = inspect.signature(kls)
        params = {}
        for k, v in params_raw.items():
            if k in sig.parameters:
                params[k] = v
        return kls(**params)


KedroDataSetSpec.update_forward_refs()


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


def get_import_name(obj: Any) -> str:
    """Gets the import name for a type."""
    module_i = inspect.getmodule(obj)
    if module_i is None:
        raise TypeError(f"Could not find module for {obj!r}")
    r_name: str = getattr(obj, "__qualname__", obj.__name__)  # type: ignore
    return f"{module_i.__name__}.{r_name}"


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
            jsp = jsp_str.split(".")[1:]
            ds_i = ds_spec.to_dataset(base_path=filepath)
            obj_i = ds_i.load()
            mutate_jsp(model_data, jsp, obj_i)

        res = model_cls.parse_obj(model_data)
        return res

    def _save(self, data: BaseModel) -> None:
        """Saves Pydantic model to the filepath."""
        filepath = self._filepath

        # Prepare fields for final metadata
        kls = type(data)
        model_class_str = get_import_name(kls)
        model_info: Union[Dict[str, Any], List[Any]] = {}
        catalog: Dict[JsonPath, KedroDataSetSpec] = {}

        # These are used to make datasets for various types
        # See the `kls.Config` class - this is inherited
        kedro_map: Dict[Type, Callable[[str], AbstractDataSet]] = getattr(
            kls.__config__, "kedro_map", {}
        )
        kedro_default: Callable[[str], AbstractDataSet] = getattr(
            kls.__config__, "kedro_default", PickleDataSet
        )

        def make_ds_for(obj: Any, path: str) -> AbstractDataSet:
            for k, v in kedro_map.items():
                if isinstance(obj, k):
                    return v(path)
            return kedro_default(path)

        # We need to create `model_info` and `catalog`
        starter = str(uuid4()).replace("-", "")
        data_map: Dict[str, Any] = {}  # "starter_UUID" -> data_object

        def fake_encoder(obj: Any) -> Any:
            """Encode data objects as UUID strings, populating `data_map` as a side-effect."""
            try:
                return kls.__json_encoder__(obj)
            except TypeError:
                val = f"{starter}__{uuid4()}".replace("-", "")
                data_map[val] = obj
                return val

        # Roundtrip to apply the encoder and get UUID
        rt = json.loads(data.json(encoder=fake_encoder))

        # This will map the data to a dataset and actually save it

        def visit3(obj: Any, jsp: str, base_path: str) -> Any:
            """Maps the data to a dataset in `catalog` and actually saves it."""
            if isinstance(obj, str):
                if obj in data_map:
                    # We got a data point
                    data = data_map[obj]
                    # Make a dataset for it
                    full_path = f"{base_path}/{jsp}"
                    ds = make_ds_for(data, full_path)
                    # Get the spec (or fail because of non-JSON-able types...)
                    dss = KedroDataSetSpec.from_dataset(ds, jsp)
                    dss.json()  # to fail early
                    catalog[jsp] = dss  # add to catalog
                    # Save the data
                    ds.save(data)
                    # Return the spec in dict form
                    return DATA_PLACEHOLDER
            elif isinstance(obj, list):
                return [visit3(sub, f"{jsp}.{i}", base_path) for i, sub in enumerate(obj)]
            elif isinstance(obj, dict):
                return {k: visit3(v, f"{jsp}.{k}", base_path) for k, v in obj.items()}
            return obj

        model_info = visit3(rt, "", base_path=filepath)

        # Create and write metadata
        meta = FolderFormatMetadata(model_class=model_class_str, model_info=model_info, catalog=catalog)
        with fsspec.open(f"{filepath}/meta.json", mode="w") as f:
            f.write(meta.json())  # type: ignore

    def _describe(self) -> Dict[str, Any]:
        return dict(filepath=self._filepath)
