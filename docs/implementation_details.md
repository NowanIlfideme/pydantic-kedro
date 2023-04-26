# Implementation Details

## File Formats

### JSON Dataset

The [`PydanticJsonDataSet`][pydantic_kedro.PydanticJsonDataSet] dumps your
model as a self-describing JSON file.

In order for the dataset to be self-describing, we add the field `"class"` to your model, which is your class's full import path.

So if you have a Python class defined in `your_module` called `Foo`, the resulting
JSON file will be:

```jsonc
{
    "foo": "bar",
    // the other fields from your model...
    "class": "your_module.Foo"
}
```

> Note: All [`json_encoders`](https://docs.pydantic.dev/usage/exporting_models/#json_encoders)
> defined on your model will still be used.

### Folder and Zip Datasets

The [`PydanticZipDataSet`][pydantic_kedro.PydanticZipDataSet] is based on the
[`PydanticFolderDataSet`][pydantic_kedro.PydanticFolderDataSet] and just zips
the folder.

The directory structure is as the following:

```text
save_dir
|- meta.json
|- .field1
|- .field2.0
|  etc.
```

The `meta.json` file has 3 main fields:

1. `"model_class"` is the class import path, as in the [JSON dataset][json-dataset].
2. `"model_info"` is the JSON serialization of the model, except that all
   types are "encoded" to the string `"__DATA_PLACEHOLDER__"`.
3. `"catalog"` is the pseudo-definition of the Kedro catalog.
   The difference is in the `relative_path` argument.

The rest of the files/folders are the relative paths specified in the `catalog`.

TODO: Is that all? Do we add `model_schema` or something similar?
This is up to change as `pydantic-kedro` gets more mature.
