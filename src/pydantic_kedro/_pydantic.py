"""Pydantic import, depending on the version."""

# mypy: ignore_errors

import pydantic

PYDANTIC_VERSION = pydantic.version.VERSION

if PYDANTIC_VERSION > "2" and PYDANTIC_VERSION < "3":
    from pydantic.v1 import BaseConfig, BaseModel, Extra, Field, create_model
elif PYDANTIC_VERSION < "2":
    from pydantic import BaseConfig, BaseModel, Extra, Field, create_model  # noqa
else:
    raise ImportError("Unknown version of Pydantic.")
