"""The types used by the ngio-collections RFC-8 examples that the core doesn't model.

Extensions, mirroring the JSON Schemas in ngio-collections `examples/schemas/`
(branch `rfc8-revision1`):

* Fractal provenance: a trait recording which task produced a node.
* Training dataset: a collection trait listing `{image, labels, split}` samples.
* Fractal table: a leaf node whose payload is a CSV, located by a custom locator.

Traits:

* `labels`: marks a multiscale as a label image of its sources.
* `plate`, `well` and `acquisition`: high-content screening layout.

References use the core reference locator pipelines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import MISSING, BaseModel, ConfigDict, Field

from .extensions import ExtensionManifest, ExtensionManifestSchema
from .models import Id, Name, ReferenceLocatorPipeline, Trait, Type

BASE = "https://raw.githubusercontent.com/BioVisionCenter/ngio-collections/main/examples/schemas/"
HOMEPAGE = "https://github.com/BioVisionCenter/ngio-collections/tree/main/examples/schemas"
FRACTAL = BASE + "fractal/"
TRAINING = BASE + "training/"

FRACTAL_MANIFEST = ExtensionManifest(
    id=FRACTAL,
    version="0.1",
    name="Fractal",
    homepage=HOMEPAGE,
    schemas=[
        ExtensionManifestSchema(url=FRACTAL + "provenance.schema.json"),
        ExtensionManifestSchema(url=FRACTAL + "table.schema.json"),
    ],
)
TRAINING_MANIFEST = ExtensionManifest(
    id=TRAINING,
    version="0.1",
    name="Training dataset",
    homepage=HOMEPAGE,
    schemas=[ExtensionManifestSchema(url=TRAINING + "dataset.schema.json")],
)

NonNegativeInt = Annotated[int, Field(ge=0)]
Uint8 = Annotated[int, Field(ge=0, le=255)]


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Type
    ref: ReferenceLocatorPipeline


# Labels


class LabelAttribute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label_value: int
    rgba: tuple[Uint8, Uint8, Uint8, Uint8] | MISSING = MISSING


class LabelsTrait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["labels"] = "labels"
    source: tuple[Reference, ...] | MISSING = MISSING
    label_attributes: tuple[LabelAttribute, ...] | MISSING = MISSING


# High-content screening


class PlateRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name


class PlateColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name


class Acquisition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["acquisition"] = "acquisition"
    id: Id
    name: Name | MISSING = MISSING
    starttime: NonNegativeInt | MISSING = MISSING  # unix timestamp
    endtime: NonNegativeInt | MISSING = MISSING  # unix timestamp


class PlateTrait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["plate"] = "plate"
    rows: tuple[PlateRow, ...]
    columns: tuple[PlateColumn, ...]
    acquisitions: tuple[Acquisition, ...] | MISSING = MISSING


class WellTrait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["well"] = "well"
    row_index: NonNegativeInt
    column_index: NonNegativeInt


class AcquisitionTrait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["acquisition"] = "acquisition"
    acquisition: Reference


# Fractal extension


class FractalProvenanceTrait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "https://raw.githubusercontent.com/BioVisionCenter/ngio-collections/main/examples/schemas/fractal/provenance"
    ]
    task: str
    version: str | MISSING = MISSING
    timestamp: datetime | MISSING = MISSING
    inputs: tuple[Reference, ...] | MISSING = MISSING


class FractalCsvReferenceLocator(BaseModel):
    """Final locator step: the located file is a CSV, not a node document."""

    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "https://raw.githubusercontent.com/BioVisionCenter/ngio-collections/main/examples/schemas/fractal/csv"
    ]


class FractalTableNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "https://raw.githubusercontent.com/BioVisionCenter/ngio-collections/main/examples/schemas/fractal/table"
    ]
    id: Id
    name: Name | MISSING = MISSING
    ref: ReferenceLocatorPipeline
    columns: tuple[str, ...] | MISSING = MISSING
    traits: tuple[Trait, ...] | MISSING = MISSING


# Training dataset extension


class TrainingSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: Reference
    labels: Reference | MISSING = MISSING
    split: Literal["train", "val", "test"]


class TrainingDatasetTrait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "https://raw.githubusercontent.com/BioVisionCenter/ngio-collections/main/examples/schemas/training/dataset"
    ]
    task: str | MISSING = MISSING
    samples: tuple[TrainingSample, ...]


def _type_of(model: type[BaseModel]) -> str:
    return model.model_fields["type"].annotation.__args__[0]  # type: ignore[union-attr]


TRAIT_TYPES: dict[str, type[BaseModel]] = {
    _type_of(model): model
    for model in (
        LabelsTrait,
        PlateTrait,
        WellTrait,
        AcquisitionTrait,
        FractalProvenanceTrait,
        TrainingDatasetTrait,
    )
}
NODE_TYPES: dict[str, type[BaseModel]] = {_type_of(FractalTableNode): FractalTableNode}
