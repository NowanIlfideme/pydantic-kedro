# `pydantic-kedro`

Advanced serialization for [Pydantic](https://docs.pydantic.dev/) models
via [Kedro](https://kedro.readthedocs.io/en/stable/index.html) and
[fsspec](https://filesystem-spec.readthedocs.io/en/latest/).

This package implements custom Kedro Dataset types for not only "pure" (JSON-serializable)
Pydantic models, but also models with [`arbitrary_types_allowed`](https://docs.pydantic.dev/usage/types/#arbitrary-types-allowed).

Keep reading for a basic tutorial,
or check out the [API Reference](reference.md) for auto-generated docs.

## Pre-requisites

To simplify the documentation, we will refer to JSON-serializable Pydantic models
as "pure" models, while all others will be "arbitrary" models.

We also assume you are familiar with [Kedro's Data Catalog](https://docs.kedro.org/en/stable/data/data_catalog.html)
and [Datasets](https://docs.kedro.org/en/stable/data/kedro_io.html).

## Changes from Kedro 0.19

Please note that Kedro 0.19 incorporated many backwards-incompatible changes.
We are switching to support `kedro>=0.19` instead of `kedro<0.19`. This means:

1. The `*DataSet` classes have been renamed to `*Dataset`, though the old names
   are still available as aliases.
2. The `kedro-datasets` package is now a necessary dependency.
3. Thanks to changes in Kedro's datasets, most have switched to requiring
   keyword-only arguments, especially `filename`. So instead of using a map such
   as `{DataFrame: ParquetDataset}` you should use a function or a lambda, e.g.
   `{DataFrame: lambda x: ParquetDataSet(filename=x)}`.

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

Then use it as usual within your Kedro pipelines:

```python
from pydantic.v1 import BaseModel
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
[PydanticJsonDataset][pydantic_kedro.PydanticJsonDataset]
or [PydanticYamlDataset][pydantic_kedro.PydanticYamlDataset]
to save your model to any `fsspec`-supported location:

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

> Note: YAML support is enabled by [`pydantic-yaml`](https://pydantic-yaml.readthedocs.io/en/latest/).

Note that specifying [custom JSON encoders](https://docs.pydantic.dev/usage/exporting_models/#json_encoders)
will work as usual, even for YAML models.

However, if your custom type is difficult or impossible to encode/decode via
JSON, read on to [Arbitrary Types](./arbitrary_types.md).

## Automatic Saving of Pydantic Models

The easiest way to use `pydantic-kedro` (since `v0.2.0`) is through the
[PydanticAutoDataset][pydantic_kedro.PydanticAutoDataset].
You can use it in the place of any other dataset for reading or writing.

When reading, it will figure out what the actual dataset type is.
When writing, it will try to save it as a pure model, or fallback to an arbitrary model,
depending on the options set. Below you can see the default options:

```python
PydanticAutoDataset(path, default_format_pure="yaml", default_format_arbitrary="zip")
```
