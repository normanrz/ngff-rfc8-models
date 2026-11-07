"""Validate the example documents in `examples/data` against the models.

Run with `uv run python examples/validate.py`. Checks each document against the
core models, and every trait, node and extension manifest the core doesn't model
against `rfc8_model.example_extensions`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rfc8_model.container import StandaloneJson, ZarrJson
from rfc8_model.example_extensions import (
    FRACTAL_MANIFEST,
    NODE_TYPES,
    TRAINING_MANIFEST,
    TRAIT_TYPES,
)
from rfc8_model.extensions import ExtensionManifest

DATA = Path(__file__).parent / "data"
MANIFESTS = {m.id: m for m in (FRACTAL_MANIFEST, TRAINING_MANIFEST)}


def extension_objects(value: Any):
    """Yield `(model, obj)` for each trait or node with a type modelled here."""
    if isinstance(value, dict):
        for key, child in value.items():
            registry = {"traits": TRAIT_TYPES, "nodes": NODE_TYPES}.get(key, {})
            if isinstance(child, list):
                for item in child:
                    if isinstance(item, dict) and item.get("type") in registry:
                        yield registry[item["type"]], item
            yield from extension_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from extension_objects(child)


def check(path: Path) -> bool:
    doc = json.loads(path.read_text())
    name = path.relative_to(DATA)
    ok = True

    model = ZarrJson if "zarr_format" in doc else StandaloneJson
    try:
        model.model_validate(doc)
    except ValidationError as e:
        ok = False
        print(f"FAIL core {name}: {e.error_count()} errors")

    ome = doc["attributes"]["ome"] if "attributes" in doc else doc["ome"]
    for entry in ome.get("extension_manifests", []):
        manifest = ExtensionManifest.model_validate(entry)
        if MANIFESTS.get(manifest.id) != manifest:
            ok = False
            print(f"FAIL manifest {name}: {manifest.id}")

    for model, obj in extension_objects(doc):
        try:
            model.model_validate(obj)
        except ValidationError as e:
            ok = False
            print(f"FAIL {model.__name__} {name}: {e.error_count()} errors")
    return ok


def main() -> None:
    files = sorted(DATA.rglob("*.json"))
    passed = sum(check(path) for path in files)
    print(f"{passed}/{len(files)} documents valid")


if __name__ == "__main__":
    main()
