"""Pydantic compatibility module."""

# type: ignore
# flake8: noqa

__all__ = ["get_field_names", "import_string"]

import warnings
from typing import Any, List, Type, no_type_check

import pydantic

if pydantic.VERSION >= "2":

    @no_type_check
    def get_field_names(kls: Type[pydantic.BaseModel]) -> List[str]:
        """Return all field names of a Pydantic class."""
        return list(kls.model_fields.keys())  # type: ignore

    @no_type_check
    def import_string(value: str) -> Any:
        """Imports string."""
        from pydantic._internal._validators import (
            import_string as _imp_str,  # type: ignore
        )

        return _imp_str(value)

    @no_type_check
    def get_config_attr(kls: Type[pydantic.BaseModel], attr: str, default: Any = None) -> Any:
        """Gets attribute from the config class."""
        # FIXME: Maybe we change how the config is done?
        return kls.model_config.get("kedro_default", default)  # type: ignore

    @no_type_check
    def apply_model_json_encoder(kls: Type[pydantic.BaseModel], obj: Any) -> Any:
        """Applies the model's JSON encoder."""
        # TODO: Update once pydantic>2 adds ability to use custom encoders.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from pydantic.deprecated.json import pydantic_encoder

            return pydantic_encoder(obj)  # type: ignore

elif pydantic.VERSION >= "1":

    @no_type_check
    def get_field_names(kls: Type[pydantic.BaseModel]) -> List[str]:
        """Return all field names of a Pydantic class."""
        return list(kls.__fields__.keys())  # type: ignore

    @no_type_check
    def import_string(value: str) -> Any:
        """Imports string."""
        from pydantic.utils import import_string as _imp_str  # type: ignore

        return _imp_str(value)

    @no_type_check
    def get_config_attr(kls: Type[pydantic.BaseModel], attr: str, default: Any = None) -> Any:
        """Gets attribute from the config class."""
        return getattr(kls.__config__, "kedro_default", default)  # type: ignore

    @no_type_check
    def apply_model_json_encoder(kls: Type[pydantic.BaseModel], obj: Any) -> Any:
        """Applies the model's JSON encoder."""
        return kls.__json_encoder__(obj)  # type: ignore
