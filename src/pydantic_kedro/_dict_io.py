"""Module for reading/writing from dicts."""

from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, Union

from pydantic_kedro._pydantic import BaseModel

from ._internals import import_string

KLS_MARK_STR = "class"


def get_kls_path(pyd_kls: Type[BaseModel]) -> str:
    """Get the class path for an object."""
    return f"{pyd_kls.__module__}.{pyd_kls.__qualname__}"


class PatchPydanticIter(AbstractContextManager):
    """Patch Pydantic `_iter` method.

    The _iter method is used by `.json()` and `.dict()` for exporting.
    We add our class information.

    Simple Example
    --------------

    ```python
    class A(BaseModel):
        x: str = "x"

    print(A().json())
    with PatchPydanticIter():
        print(A().json())
    print(A().json())
    ```

    Output:

    ```txt
    {"x": "x"}
    {"class": "A", "x": "x"}
    {"x": "x"}
    ```

    Nested Example
    --------------

    ```python
    class C(BaseModel):
        a: A = A()

    print(C().json())
    with PatchPydanticIter():
        print(C().json())
    print(C().json())
    ```

    Output:

    ```txt
    {"a": {"x": "x"}}
    {"class": "C", "a": {"class": "A", "x": "x"}}
    {"a": {"x": "x"}}
    ```

    """

    def __init__(self) -> None:
        self.orig_iter = BaseModel._iter
        self.add_kls_mark = True

    def __enter__(self) -> None:
        orig_iter = self.orig_iter
        add_kls_mark = self.add_kls_mark

        def _iter(self, to_dict=False, **kwargs):  # type: ignore
            nonlocal orig_iter, add_kls_mark
            if add_kls_mark:  # add 'class' as first item
                kls_path = get_kls_path(type(self))
                yield KLS_MARK_STR, kls_path

            for k, v in orig_iter(self, to_dict=to_dict, **kwargs):
                yield k, v

        BaseModel._iter = _iter  # type: ignore

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]] = None,
        __exc_value: Optional[BaseException] = None,
        __traceback: Optional[TracebackType] = None,
    ) -> Optional[bool]:
        BaseModel._iter = self.orig_iter  # type: ignore
        return super().__exit__(__exc_type, __exc_value, __traceback)


def _classlike(obj: Any) -> bool:
    if isinstance(obj, dict):
        if KLS_MARK_STR in obj.keys():
            return True
    return False


def _list_manip(value: List[Any]) -> List[Any]:
    new_value = list(value)
    for i, v_i in enumerate(value):
        if _classlike(v_i):
            new_value[i] = dict_to_model(v_i)
        elif isinstance(v_i, dict):
            new_value[i] = _dict_manip(v_i)
        elif isinstance(v_i, list):
            new_value[i] = _list_manip(v_i)
        # otherwise ignore
    return new_value


def _dict_manip(value: Dict[str, Any]) -> Dict[str, Any]:
    new_value = dict(value)
    for k, v_k in value.items():
        if _classlike(v_k):
            new_value[k] = dict_to_model(v_k)
        elif isinstance(v_k, dict):
            new_value[k] = _dict_manip(v_k)
        elif isinstance(v_k, list):
            new_value[k] = _list_manip(v_k)
    return new_value


def dict_to_model(dct: Union[Dict[str, Any], List[Any]]) -> BaseModel:
    """Convert dictionary (or, optionally, list) to model."""
    if isinstance(dct, list):
        dct = {"__root__": dct}

    # Checks... # redundant? see _classlike()
    if not isinstance(dct, dict):
        raise TypeError("Only dicts are supported right now.")
    if KLS_MARK_STR not in dct.keys():
        raise ValueError("Model is not a supported type.")
    pyd_kls = import_string(dct[KLS_MARK_STR])
    assert issubclass(pyd_kls, BaseModel)

    raw = dict(dct)
    for key, value in dct.items():
        if _classlike(value):
            raw[key] = dict_to_model(value)
        elif isinstance(value, list):
            raw[key] = _list_manip(value)
        elif isinstance(value, dict):
            raw[key] = _dict_manip(value)
        # otherwise ignore
    keywords = dict(raw)
    del keywords[KLS_MARK_STR]
    return pyd_kls(**keywords)  # Consider parse_obj_as(pyd_kls, keywords) ?


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Conver model to dictionary."""
    with PatchPydanticIter():
        return model.dict()
