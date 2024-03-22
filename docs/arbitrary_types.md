# Serializing Models with Arbitrary Types

Pydantic [supports models with arbitrary types](https://docs.pydantic.dev/usage/types/#arbitrary-types-allowed)
if you specify it in the model's config.
You can't save/load these via JSON, but you can use the other dataset types:
[PydanticFolderDataset][pydantic_kedro.PydanticFolderDataset] and
[PydanticZipDataset][pydantic_kedro.PydanticZipDataset].

## Usage Example

```python
from tempfile import TemporaryDirectory
from pydantic import BaseModel
from pydantic_kedro import PydanticZipDataset


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
    ds = PydanticZipDataset(f"{tmpdir}/arb.zip")
    ds.save(obj)

    # We can re-load it from the same file
    read_obj = ds.load()
    assert read_obj.foo.foo == "foofoo"
```

> Note: The above model definition can use [`ArbModel`][pydantic_kedro.ArbModel]
> to save keystrokes:
>
> ```python
> from pydantic_kedro import ArbModel
>
> class MyArbitraryModel(ArbModel):
>     """Your custom Pydantic model with JSON-unsafe fields."""
>
>     x: int
>     foo: Foo
> ```
>
> We will use `ArbModel` as it also gives type hints for the configuration.

## Default Behavior for Unknown Types

The above code gives the following warning:

```python
UserWarning: No dataset defined for __main__.Foo in `Config.kedro_map`;
using `Config.kedro_default`:
<class 'kedro_datasets.pickle.pickle_dataset.PickleDataset'>
```

This is because `pydantic-kedro` doesn't know how to serialize the object.
The default is Kedro's `PickleDataset`, which will generally work only if the same
Python version and libraries are installed on the client that reads the dataset.

## Defining Datasets for Types

To let `pydantic-kedro` know how to serialize a class, you need to add it to the
`kedro_map` model config.

Here's a example for [pandas](https://pandas.pydata.org/) and Pydantic V1:

```python
import pandas as pd
from kedro_datasets.pandas import ParquetDataset
from pydantic import validator
from pydantic_kedro import ArbModel, PydanticZipDataset


class MyPandasModel(ArbModel):
    """Model that saves a dataframe, along with some other data."""

    class Config:
        kedro_map = {pd.DataFrame: ParquetDataset}

    val: int
    df: pd.DataFrame

    @validator('df')
    def _check_dataframe(cls, v: pd.DataFrame) -> pd.DataFrame:
        """Ensure the dataframe is valid."""
        assert len(v) > 0
        return v


dfx = pd.DataFrame([[1, 2, 3]], columns=["a", "b", "c"])
m1 = MyPandasModel(df=dfx, val=1)

ds = PydanticZipDataset(f"memory://my_model.zip")
ds.save(m1)

m2 = ds.load()
assert m2.df.equals(dfx)
```

Internally, this uses the `ParquetDataset` to save the dataframe as an
[Apache Parquet](https://parquet.apache.org/) file within the Zip file,
as well as reference it from within the JSON file. That means that, unlike
Pickle, the file isn't "fragile" and will be readable with future versions.

## Config Inheritence

[Similarly to Pydantic](https://docs.pydantic.dev/latest/usage/model_config/#change-behaviour-globally),
the `Config` class has a sort of pseudo-inheritence.
That is, if you define your classes like this:

```python
class A(BaseModel):
    class Config:
        allow_arbitrary_types = True
        kedro_map = {Foo: FooDataset}


class B(A):
    class Config:
        kedro_map = {Bar: BarDataset}

class C(B):
    class Config:
        kedro_map = {Foo: foo_ds_maker}
        kedro_default = DefaultDataset

```

Then class `B` will act as if `kedro_map = {Foo: FooDataset, Bar: BarDataset}`,
and class `C` will act as if `kedro_map = {Foo: foo_ds_maker, Bar: BarDataset}`
and `kedro_default = DefaultDataset`

## Considerations

1. Only the top-level model's `Config` is taken into account when serializing
   to a Kedro dataset, ignoring any children's configs.
   This means that all values of a particular type are serialized the same way.
2. `pydantic` V2 is not supported yet, but V2
   [has a different configuration method](https://docs.pydantic.dev/blog/pydantic-v2-alpha/#changes-to-config).
   `pydantic-kedro` might change the configuration method entirely to be more compliant.
