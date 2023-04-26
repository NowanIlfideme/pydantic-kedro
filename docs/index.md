# `pydantic-kedro`

Advanced serialization for [Pydantic](https://docs.pydantic.dev/) models
via [Kedro](https://kedro.readthedocs.io/en/stable/index.html) and
[fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

This package implements custom Kedro DataSet types for not only "pure" (JSON-serializable)
Pydantic models, but also models with [`arbitrary_types_allowed`](https://docs.pydantic.dev/usage/types/#arbitrary-types-allowed).

Keep reading for a basic tutorial,
or check out the [API Reference](reference/index.md) for auto-generated docs.

## Pre-requisites

To simplify the documentation, we will refer to JSON-serializable Pydantic models
as "pure" models, while all others will be "arbitrary" models.

We also assume you are familiar with [Kedro's Data Catalog](https://docs.kedro.org/en/stable/data/data_catalog.html)
and [Datasets](https://docs.kedro.org/en/stable/data/kedro_io.html).

## "Pure" Pydantic Models

If you have a JSON-safe Pydantic model, you can use a
[PydanticJsonDataSet][pydantic_kedro.PydanticJsonDataSet]
to save your model to any `fsspec`-supported location:

```python
from pydantic import BaseModel
from pydantic_kedro import PydanticJsonDataSet


class MyPureModel(BaseModel):
    """Your custom Pydantic model with JSON-safe fields."""

    x: int
    y: str


obj = MyPureModel(x=1, y="why?")

# Create an in-memory (temporary) file via `fsspec` and save it
ds = PydanticJsonDataSet("memory://temporary-file.json")
ds.save(obj)

# We can re-load it from the same file
read_obj = ds.load()
assert read_obj.x == 1
```

Note that specifying [custom JSON encoders](https://docs.pydantic.dev/usage/exporting_models/#json_encoders) will work as usual.

However, if your custom type is difficult or impossible to encode/decode via
JSON, read on to [Arbitrary Types](./arbitrary_types.md).
