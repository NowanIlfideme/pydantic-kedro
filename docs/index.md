# `pydantic-kedro`

Advanced serialization for [Pydantic](https://docs.pydantic.dev/) models
via [Kedro](https://kedro.readthedocs.io/en/stable/index.html) and
[fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

This package implements custom Kedro "datasets" for both "pure" and "arbitrary"
Pydantic models.

## Examples

### "Pure" Pydantic Models

This example works for "pure", JSON-safe Pydantic models via
[PydanticJsonDataSet][pydantic_kedro.PydanticJsonDataSet]:

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

Note that specifying custom JSON encoders also will work.

### Models with Arbitrary Types

Pydantic [supports models with arbitrary types](https://docs.pydantic.dev/usage/types/#arbitrary-types-allowed)
if you specify it in the model's config.
You can't save/load these via JSON, but you can use the other dataset types,
[PydanticFolderDataSet][pydantic_kedro.PydanticFolderDataSet] and
[PydanticZipDataSet][pydantic_kedro.PydanticZipDataSet]:

```python
from pydantic import BaseModel
from pydantic_kedro import PydanticJsonDataSet

# TODO

class MyArbitraryModel(BaseModel):
    """Your custom Pydantic model with JSON-unsafe fields."""
    x: int
    y: str

# TODO
```

## Further Reading

See the [configuration](configuration.md)...

Check out the [API Reference](reference/index.md) for auto-generated docs.
