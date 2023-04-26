# Serializing Models with Arbitrary Types

Pydantic [supports models with arbitrary types](https://docs.pydantic.dev/usage/types/#arbitrary-types-allowed)
if you specify it in the model's config.
You can't save/load these via JSON, but you can use the other dataset types,
[PydanticFolderDataSet][pydantic_kedro.PydanticFolderDataSet] and
[PydanticZipDataSet][pydantic_kedro.PydanticZipDataSet].

## Usage Example

```python
from tempfile import TemporaryDirectory
from pydantic import BaseModel
from pydantic_kedro import PydanticZipDataSet


class Foo(object):
    """My custom class. NOTE: this is not a Pydantic model!"""

    def __init__(self, foo):
        self.foo = foo


class MyArbitraryModel(BaseModel):
    """Your custom Pydantic model with JSON-unsafe fields."""

    x: int
    foo: Foo

    class Config:
        """Configuration for Pydantic V1."""
        # Let's pretend it would be difficult to add a json encoder for Foo
        arbitrary_types_allowed = True


obj = MyArbitraryModel(x=1, foo=Foo("foofoo"))

# This object is not JSON-serializable
try:
    obj.json()
except TypeError as err:
    print(err)  # Object of type 'Foo' is not JSON serializable

# We can, however,
with TemporaryDirectory() as tmpdir:
    # Create an on-disk (temporary) file via `fsspec` and save it
    ds = PydanticZipDataSet(f"{tmpdir}/arb.zip")
    ds.save(obj)

    # We can re-load it from the same file
    read_obj = ds.load()
    assert read_obj.foo.foo == "foofoo"
```

## Default Behavior for Unknown Types

The above code gives the following warning:

```python
UserWarning: No dataset defined for __main__.Foo in `Config.kedro_map`;
using `Config.kedro_default`:
<class 'kedro.extras.datasets.pickle.pickle_dataset.PickleDataSet'>
```

This is because we don't know how to serialize the object; we use `PickleDataSet`
by default

## Defining Datasets for Types

TODO
