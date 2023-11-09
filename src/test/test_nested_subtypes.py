"""Tests for values which are subclasses of the Pydantic field types."""

from abc import abstractmethod
from typing import Dict, List, Literal

import pytest
from pydantic import BaseModel

from pydantic_kedro import load_model, save_model


class AbstractBaz(BaseModel):
    """Abstract base model which is used as an interface.

    This can occur with ANY model type, however with abstract models it's much more apparent.
    You can't instantiate models with
    """

    foo: str

    @abstractmethod
    def get_baz(self) -> str:
        """Return baz value."""


class AlwaysBaz(AbstractBaz):
    """Model that returns baz as "baz"."""

    def get_baz(self) -> str:
        """Return baz as "baz"."""
        return "baz"


class CopyBaz(AbstractBaz):
    """Model that copies foo into baz."""

    def get_baz(self) -> str:
        """Return baz as a copy of foo."""
        return self.foo


class Bazzifier(BaseModel):
    """Higher-level model with nested 'bazzifier' value."""

    maker: AbstractBaz


class MultiBazzifier(BaseModel):
    """Higher-level model with nested 'bazzifier' value."""

    maker_list: List[AbstractBaz]
    maker_dict: Dict[str, AbstractBaz]


@pytest.mark.parametrize("format", ["auto", "zip", "folder", "yaml", "json"])
@pytest.mark.parametrize("obj", [AlwaysBaz(foo="always"), CopyBaz(foo="copy")])
def test_nested_subclass(
    obj: AbstractBaz, format: Literal["auto", "zip", "folder", "yaml", "json"], tmpdir: str
):
    """Test round-trip of objects with a nested subclass."""
    # Initial round-trip (should always work)
    save_model(obj, f"{tmpdir}/obj", format=format)
    obj2 = load_model(f"{tmpdir}/obj", AbstractBaz)
    assert obj.foo == obj2.foo
    assert obj.get_baz() == obj2.get_baz()
    # Nested round-trip (should also always work, but is more diffictult)
    nest = Bazzifier(maker=obj)
    save_model(nest, f"{tmpdir}/nest", format=format)
    nest2 = load_model(f"{tmpdir}/nest", Bazzifier)
    assert nest.maker == nest2.maker
    assert nest.maker.get_baz() == nest2.maker.get_baz()


@pytest.mark.parametrize("format", ["auto", "zip", "folder", "yaml", "json"])
def test_deeper_nested_subclass(format: Literal["auto", "zip", "folder", "yaml", "json"], tmpdir: str):
    """Test round-trip of objects with a nested subclass."""
    a = AlwaysBaz(foo="always")
    c = CopyBaz(foo="copy")
    nest = MultiBazzifier(maker_list=[a, c], maker_dict={"a": a, "c": c})
    # Nested round-trip (should also always work, but is much more diffictult)
    save_model(nest, f"{tmpdir}/nest", format=format)
    nest2 = load_model(f"{tmpdir}/nest", MultiBazzifier)
    assert nest == nest2
