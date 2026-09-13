"""Test bootstrap for the source checkout.

The project is a ``src``-layout package.  Keeping the checkout at the front of
``sys.path`` prevents a globally installed NanoJuris wheel from shadowing the
code under test when contributors run pytest without an editable install.
"""

from __future__ import annotations

import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
source_path = str(SOURCE_ROOT)
if source_path in sys.path:
    sys.path.remove(source_path)
sys.path.insert(0, source_path)

# Some pytest plugins import the distribution before loading project
# conftest files.  Drop that already-loaded distribution so subsequent test
# imports resolve every NanoJuris submodule from this checkout.
loaded = sys.modules.get("nanojuris")
if loaded is not None and not str(getattr(loaded, "__file__", "")).startswith(source_path):
    for module_name in list(sys.modules):
        if module_name == "nanojuris" or module_name.startswith("nanojuris."):
            del sys.modules[module_name]
