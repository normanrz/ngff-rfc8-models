# rfc8-model

Throwaway Pydantic models of the OME-NGFF RFC-8 metadata. They exist to help discuss
terminology and draft the spec text: writing the structure down as types makes open
questions concrete. This is not a library and nothing here is stable.

## Layout

- `src/rfc8_model/models.py`: the core model (nodes, coordinate systems and
  transformations, traits, reference locator pipelines).
- `src/rfc8_model/container.py`: how the metadata is stored, in a Zarr `zarr.json`
  (`ZarrJson`) or a standalone JSON document (`StandaloneJson`).
- `src/rfc8_model/extensions.py`: extension manifests.
- `src/rfc8_model/example_extensions.py`: types used by the examples that the core
  doesn't model: the `labels`, `plate`, `well` and `acquisition` traits, plus the
  illustrative Fractal and training dataset extensions.
- `src/rfc8_model/utils.py`: `OpenTypeUnion`, a union discriminated on `type` that
  falls back to a `Custom*` model for unknown types.
- `examples/data`: example documents from ngio-collections, converted to this model
  (see `examples/README.md`).

## Conventions

- Field names follow the JSON keys.
- `MISSING` marks optional fields that are omitted from the JSON instead of being
  written as `null`.
- Comments mark spec requirement levels where they matter (`# SHOULD`, `# MAY`).
  SHOULD-level constraints are documented but not enforced, e.g. `Type` and the
  axis units.

## Usage

```sh
uv run python -m rfc8_model           # print a few documents built in code
uv run python examples/validate.py    # validate the example documents
uv run python examples/convert.py DIR # convert fresh ngio-collections examples in DIR
```
