# `pydantic-kedro`

Advanced serialization for [Pydantic](https://docs.pydantic.dev/) models
via [Kedro](https://kedro.readthedocs.io/en/stable/index.html) and
[fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

This package implements custom Kedro "datasets" for both "pure" and "arbitrary"
Pydantic models. You can also use it stand-alone, using Kedro just for
serializing other object types.

Please see the [documentation](https://pydantic-kedro.rtfd.io) for a tutorial
and more examples.

## Usage with Kedro

You can use the [PydanticAutoDataset][pydantic_kedro.PydanticAutoDataset]
or any other dataset from `pydantic-kedro` within your
[Kedro catalog](https://docs.kedro.org/en/stable/get_started/kedro_concepts.html#data-catalog)
to save your Pydantic models:

```yaml
# conf/base/catalog.yml
my_pydantic_model:
 type: pydantic_kedro.PydanticAutoDataset
 filepath: folder/my_model
```

## Direct Dataset Usage

This example works for "pure", JSON-safe Pydantic models via
`PydanticJsonDataset`:

```python
from pydantic.v1 import BaseModel
from pydantic_kedro import PydanticJsonDataset


class MyPureModel(BaseModel):
    """Your custom Pydantic model with JSON-safe fields."""

    x: int
    y: str


obj = MyPureModel(x=1, y="why?")

# Create an in-memory (temporary) file via `fsspec` and save it
ds = PydanticJsonDataset("memory://temporary-file.json")
ds.save(obj)

# We can re-load it from the same file
read_obj = ds.load()
assert read_obj.x == 1
```

## Standalone Usage

You can also use `pydantic-kedro` as a generic saving and loading engine for
Pydantic models:

```python
from tempfile import TemporaryDirectory

from pydantic.v1 import BaseModel
from pydantic_kedro import load_model, save_model

class MyModel(BaseModel):
    """My custom model."""

    name: str

# We can use any fsspec URL, so we'll make a temporary folder
with TemporaryDirectory() as tmpdir:
    save_model(MyModel(name="foo"), f"{tmpdir}/my_model")
    obj = load_model(f"{tmpdir}/my_model")
    assert obj.name == "foo"
```
