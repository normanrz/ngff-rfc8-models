"""Convert ngio-collections example documents into this repo's model, in place.

Run with `uv run python examples/convert.py [DIR]` (default: `examples/data`) on
documents copied from ngio-collections `examples/data` (branch `rfc8-revision1`).

* `path: {type, format, href}` becomes a `ref` locator pipeline. `http` hrefs use
  a custom `{type: "url", url}` locator.
* `{type, ref: "<id>", path?}` references become `ref` pipelines ending in an
  `id` locator.
* `scales` become `data` arrays: each array's downsampling scale is relative to the
  first array, which has none. The first scale's absolute scale becomes a
  multiscale transformation from the multiscale itself (standing for its first
  array) to the physical coordinate system. Arrays have no ids.
* Axis names become axis ids.
* `extension_manifest` becomes `extension_manifests`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from rfc8_model.container import StandaloneJson, ZarrJson

Json = dict[str, Any]


def pipeline(path: Json) -> list[Json]:
    kind, fmt, href = path["type"], path["format"], path["href"]
    if fmt == "http":
        return [{"type": "url", "url": href}, {"type": kind}]
    if fmt != "relative":
        raise ValueError(f"unsupported path format {fmt!r}")
    if kind == "zarr":
        return [{"type": "zarr", "path": href}]
    return [{"type": "relative", "path": href}, {"type": kind}]


def reference(ref: Json) -> Json:
    steps = pipeline(ref["path"]) if "path" in ref else []
    return {"type": ref["type"], "ref": [*steps, {"type": "id", "id": ref["ref"]}]}


def references(value: Any) -> Any:
    """Convert every `{type, ref: "<id>", path?}` reference inside `value`."""
    if isinstance(value, list):
        return [references(v) for v in value]
    if not isinstance(value, dict):
        return value
    if isinstance(value.get("ref"), str) and set(value) <= {"type", "ref", "path"}:
        return reference(value)
    if "axes" in value:
        return coordinate_system(value)
    return {k: references(v) for k, v in value.items()}


def coordinate_system(cs: Json) -> Json:
    axes = [{"id": a["name"], **{k: v for k, v in a.items() if k != "name"}} for a in cs["axes"]]
    return {**cs, "axes": axes}


def ratio(a: float, b: float) -> float:
    return round(a / b, 12)


def multiscale(node: Json) -> Json:
    (physical,) = node["coordinate_systems"]
    scales = [s for scale in node["scales"] for s in scale["coordinate_transformations"]]
    base = scales[0]["scale"]
    arrays = [
        {"type": "array", "ref": pipeline(scale["path"])}
        for scale in node["scales"]
    ]
    for array, scale in list(zip(arrays, node["scales"]))[1:]:
        array["downsampling_transformations"] = [
            {"type": "scale", "scale": [ratio(s, b) for s, b in zip(ct["scale"], base)]}
            for ct in scale["coordinate_transformations"]
        ]
    out = {k: v for k, v in node.items() if k not in ("scales", "nodes", "coordinate_systems")}
    out["coordinate_systems"] = [coordinate_system(physical)]
    out["coordinate_transformations"] = [
        {
            "type": "scale",
            "input": {"type": "multiscale", "ref": [{"type": "id", "id": node["id"]}]},
            "output": {"type": "coordinate_system", "ref": [{"type": "id", "id": physical["id"]}]},
            "scale": base,
        }
    ]
    out["data"] = arrays
    if "traits" in node:
        out["traits"] = references(node["traits"])
    return out


def node(n: Json) -> Json:
    if "path" in n:
        out = {k: n[k] for k in ("type", "id", "name") if k in n}
        out["ref"] = pipeline(n["path"])
        out.update((k, references(v)) for k, v in n.items() if k not in out and k != "path")
        return out
    if n["type"] == "multiscale" and "scales" in n:
        return multiscale(n)
    out = {k: references(v) for k, v in n.items() if k != "nodes"}
    if "nodes" in n:
        out["nodes"] = [node(child) for child in n["nodes"]]
    return out


def document(doc: Json) -> Json:
    ome = doc["attributes"]["ome"] if "attributes" in doc else doc["ome"]
    if "extension_manifest" in ome:
        ome["extension_manifests"] = ome.pop("extension_manifest")
    ome["root"] = node(ome["root"])
    return doc


def dumps(value: Any, indent: int = 0, column: int = 0, width: int = 88) -> str:
    """JSON with each object or array on one line if it fits within `width`.

    `indent` is the nesting indentation, `column` where on the line `value` starts.
    """
    flat = json.dumps(value, separators=(", ", ": "))
    if column + len(flat) + 1 <= width or not isinstance(value, (dict, list)) or not value:
        return flat
    inner = indent + 2
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            key = f"{json.dumps(k)}: "
            lines.append(" " * inner + key + dumps(v, inner, inner + len(key), width))
        body, open_, close = lines, "{", "}"
    else:
        body = [" " * inner + dumps(v, inner, inner, width) for v in value]
        open_, close = "[", "]"
    return open_ + "\n" + ",\n".join(body) + "\n" + " " * indent + close


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data"
    for path in sorted(root.rglob("*.json")):
        doc = document(json.loads(path.read_text()))
        # Validate, and order keys like the model fields
        model = ZarrJson if "zarr_format" in doc else StandaloneJson
        doc = model.model_validate(doc).model_dump(mode="json", exclude_unset=True)
        path.write_text(dumps(doc) + "\n")


if __name__ == "__main__":
    main()
