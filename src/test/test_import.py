"""Basic tests for importability."""


def test_import_pk():
    """Ensures importability."""
    from pydantic_kedro import __version__

    assert isinstance(__version__, str)
    assert __version__ != "0.0.0", "Version selection failed."
