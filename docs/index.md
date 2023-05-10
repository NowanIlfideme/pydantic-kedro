# `pydantic-kedro`

Advanced serialization for [Pydantic](https://docs.pydantic.dev/) models
via [Kedro](https://kedro.readthedocs.io/en/stable/index.html) and
[fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

This package implements custom Kedro DataSet types for not only "pure" (JSON-serializable)
Pydantic models, but also models with [`arbitrary_types_allowed`](https://docs.pydantic.dev/usage/types/#arbitrary-types-allowed).

Keep reading for a basic tutorial,
or check out the [API Reference](reference.md) for auto-generated docs.

## Pre-requisites

To simplify the documentation, we will refer to JSON-serializable Pydantic models
as "pure" models, while all others will be "arbitrary" models.

We also assume you are familiar with [Kedro's Data Catalog](https://docs.kedro.org/en/stable/data/data_catalog.html)
and [Datasets](https://docs.kedro.org/en/stable/data/kedro_io.html).

## Usage with Kedro

You can use the [PydanticAutoDataSet][pydantic_kedro.PydanticAutoDataSet]
or any other dataset from `pydantic-kedro` within your
[Kedro catalog](https://docs.kedro.org/en/stable/get_started/kedro_concepts.html#data-catalog)
to save your Pydantic models:

```yaml
# conf/base/catalog.yml
my_pydantic_model:
 type: pydantic_kedro.PydanticAutoDataSet
 filepath: folder/my_model
```

Then use it as usual within your Kedro pipelines:

```python
from pydantic import BaseModel
from kedro.pipeline import node

class SomeModel(BaseModel):
    """My custom model."""

    name: str


def my_func():
    return SomeModel(name="foo")


my_func_node = node(my_func, outputs=["my_pydantic_model"])

# etc.
```

If you are using Kedro for the pipelines or data catalog, that should be enough.

If you want to use these datasets stand-alone, keep on reading.

## Standalone Usage

The functions [save_model][pydantic_kedro.save_model] and
[load_model][pydantic_kedro.load_model] can be used directly.
See [the relevant docs](standalone_usage.md) for more info.

## "Pure" Pydantic Models

If you have a JSON-safe Pydantic model, you can use a
[PydanticJsonDataSet][pydantic_kedro.PydanticJsonDataSet]
or [PydanticYamlDataSet][pydantic_kedro.PydanticYamlDataSet]
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

> Note: YAML support is enabled by [`pydantic-yaml`](https://pydantic-yaml.readthedocs.io/en/latest/).

Note that specifying [custom JSON encoders](https://docs.pydantic.dev/usage/exporting_models/#json_encoders)
will work as usual, even for YAML models.

However, if your custom type is difficult or impossible to encode/decode via
JSON, read on to [Arbitrary Types](./arbitrary_types.md).

## Automatic Saving of Pydantic Models

The easiest way to use `pydantic-kedro` (since `v0.2.0`) is through the
[PydanticAutoDataSet][pydantic_kedro.PydanticAutoDataSet].
You can use it in the place of any other dataset for reading or writing.

When reading, it will figure out what the actual dataset type is.
When writing, it will try to save it as a pure model, or fallback to an arbitrary model,
depending on the options set. Below you can see the default options:

```python
PydanticAutoDataSet(path, default_format_pure="yaml", default_format_arbitrary="zip")
```
