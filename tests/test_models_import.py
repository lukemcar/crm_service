"""Test module imports for all SQLAlchemy models.

This test iterates over every module in the ``app.domain.models`` package and
imports it to ensure that model definitions (including index declarations)
compile successfully.  Previously, some models used unsupported keyword
arguments in ``Index`` declarations which caused ``ArgumentError`` exceptions
at import time.  By importing each module, we exercise the metadata
declarations and confirm that no such errors are raised.
"""

import importlib
import pkgutil


def test_models_imports() -> None:
    """Ensure that all modules in ``app.domain.models`` import without error."""
    # Import the package containing model modules
    import app.domain.models as models_pkg  # noqa: WPS433

    # Iterate over all modules within the package and import them.  Using
    # pkgutil allows discovery of submodules without hardcoding file names.
    for _finder, module_name, _is_pkg in pkgutil.iter_modules(models_pkg.__path__, models_pkg.__name__ + "."):
        importlib.import_module(module_name)