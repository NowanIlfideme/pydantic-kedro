"""Test extended models, but without external libraries."""
from typing import Any, Dict, Union

import pytest
from kedro.extras.datasets.text import TextDataSet

from pydantic_kedro import (
    ArbModel,
    PydanticAutoDataSet,
    PydanticFolderDataSet,
    PydanticZipDataSet,
)

Kls = Union[PydanticAutoDataSet, PydanticFolderDataSet, PydanticZipDataSet]


class Singleton:
    """Class that is always equal to itself (for ease of testing)."""

    def __eq__(self, __o: object) -> bool:
        """Check for equality of the singleton."""
        return isinstance(__o, Singleton)


class MyStr:
    """Custom string thingy. Equality via string.

    This is NOT serialized as `str` in Pydantic, but as an object via Pickle.
    """

    def __init__(self, v: str):
        """Initialize."""
        self.v = v

    def __eq__(self, x):
        """Check for string equality."""
        return str(x) == str(self)

    def __str__(self):
        """Return the internal string."""
        return self.v


class MyStrDs(TextDataSet):
    """Custom dataset for loading MyStr type."""

    def _load(self) -> MyStr:
        return MyStr(super()._load())

    def _save(self, data: MyStr) -> None:
        return super()._save(str(data))


class UserExtendedModel(ArbModel):
    """Arbitrary model, extended with the user model."""

    class Config(ArbModel.Config):
        """Arbitrary model configuration."""

        kedro_map = {MyStr: MyStrDs}

    sing: Singleton = Singleton()
    ms: MyStr = MyStr("foobar")
    dct: Dict[str, Any] = {}


@pytest.mark.parametrize(
    "mdl", [UserExtendedModel(), UserExtendedModel(dct={"a": Singleton(), "b": MyStr("bee")})]
)
@pytest.mark.parametrize("kls", [PydanticAutoDataSet, PydanticFolderDataSet, PydanticZipDataSet])
def test_pandas_flat_model(mdl: UserExtendedModel, kls: Kls, tmpdir):
    """Test roundtripping of the flat Pandas model, using default Pickle dataset."""
    paths = [f"{tmpdir}/model_on_disk", f"memory://{tmpdir}/model_in_memory"]
    for path in paths:
        ds: Kls = kls(path)  # type: ignore
        ds.save(mdl)
        m2 = ds.load()
        assert isinstance(m2, UserExtendedModel)
        assert m2.sing == mdl.sing
        assert m2.dct == mdl.dct

        if "b" in m2.dct:
            assert isinstance(m2.dct["b"], MyStr)
