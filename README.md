# `pydantic-kedro`

Advanced serialization for [Pydantic](https://docs.pydantic.dev/) models
via [Kedro](https://kedro.readthedocs.io/en/stable/index.html) and
[fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

This package implements custom Kedro "datasets" for both "pure" and "arbitrary"
Pydantic models.

Please see the [docs](https://pydantic-kedro.rtfd.io) for a tutorial and
more examples.

## Minimal Example

This example works for "pure", JSON-safe Pydantic models via
`PydanticJsonDataSet`:

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
