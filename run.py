"""Packaging / launch entry point.

`python -m src.main` is the dev entry; PyInstaller needs a top-level script, so
this just calls into the package. Keeping it at the project root means relative
imports inside `src/` keep working and `src/platform/` never shadows stdlib.
"""
from src.main import main

if __name__ == "__main__":
    raise SystemExit(main())
