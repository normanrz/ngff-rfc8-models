from __future__ import annotations

from typing import Annotated, Literal

from pydantic import MISSING, BaseModel, ConfigDict, StringConstraints

from .utils import OpenTypeUnion

Name = Annotated[str, StringConstraints(pattern=r"^\S(.*\S)?$")]
Id = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")]
# SHOULD be a type from the spec or a URI (for extensions), but other values are allowed
Type = Annotated[str, StringConstraints(pattern=r"^\S(.*\S)?$")]
RelativePath = Annotated[str, StringConstraints(pattern=r"^[^/]+(/[^/]+)*$")]

CustomPathFormat = Annotated[str, StringConstraints(pattern="^.+$")]


class RelativePathReferenceLocator(BaseModel):
    type: Literal["relative"] = "relative"
    path: RelativePath


class ZarrReferenceLocator(BaseModel):
    type: Literal["zarr"] = "zarr"
    path: RelativePath | MISSING = MISSING


class JsonReferenceLocator(BaseModel):
    type: Literal["json"] = "json"


class IdReferenceLocator(BaseModel):
    type: Literal["id"] = "id"
    id: Id


class CustomReferenceLocator(BaseModel):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type


ReferenceLocator = Annotated[
    RelativePathReferenceLocator
    | ZarrReferenceLocator
    | JsonReferenceLocator
    | IdReferenceLocator
    | CustomReferenceLocator,
    OpenTypeUnion(),
]

ReferenceLocatorPipeline = tuple[ReferenceLocator, ...]


# NGFF 0.6 axes: `unit` SHOULD be one of these UDUNITS-2 units, but other values are allowed
SpaceUnit = Literal[
    "angstrom",
    "attometer",
    "centimeter",
    "decimeter",
    "exameter",
    "femtometer",
    "foot",
    "gigameter",
    "hectometer",
    "inch",
    "kilometer",
    "megameter",
    "meter",
    "micrometer",
    "mile",
    "millimeter",
    "nanometer",
    "parsec",
    "petameter",
    "picometer",
    "terameter",
    "yard",
    "yoctometer",
    "yottameter",
    "zeptometer",
    "zettameter",
]
TimeUnit = Literal[
    "attosecond",
    "centisecond",
    "day",
    "decisecond",
    "exasecond",
    "femtosecond",
    "gigasecond",
    "hectosecond",
    "hour",
    "kilosecond",
    "megasecond",
    "microsecond",
    "millisecond",
    "minute",
    "nanosecond",
    "petasecond",
    "picosecond",
    "second",
    "terasecond",
    "yoctosecond",
    "yottasecond",
    "zeptosecond",
    "zettasecond",
]


class _CoordinateSystemAxis(BaseModel):
    id: Id
    name: Name | MISSING = MISSING
    unit: str | MISSING = MISSING  # SHOULD
    discrete: bool | MISSING = MISSING  # MAY
    long_name: Name | MISSING = MISSING  # MAY


class ArrayCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["array"]


class SpaceCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["space"]
    unit: SpaceUnit | str | MISSING = MISSING  # SHOULD


class TimeCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["time"]
    unit: TimeUnit | str | MISSING = MISSING  # SHOULD


class ChannelCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["channel"]


class CoordinateCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["coordinate"]


class DisplacementCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["displacement"]


class CustomCoordinateSystemAxis(_CoordinateSystemAxis):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type


CoordinateSystemAxis = Annotated[
    ArrayCoordinateSystemAxis
    | SpaceCoordinateSystemAxis
    | TimeCoordinateSystemAxis
    | ChannelCoordinateSystemAxis
    | CoordinateCoordinateSystemAxis
    | DisplacementCoordinateSystemAxis
    | CustomCoordinateSystemAxis,
    OpenTypeUnion(),
]


class CoordinateSystem(BaseModel):
    type: Literal["coordinate_system"] = "coordinate_system"
    id: Id
    name: Name | MISSING = MISSING
    axes: list[CoordinateSystemAxis]


class CoordinateTransformationReference(BaseModel):
    type: Literal["coordinate_system"] = "coordinate_system"
    ref: ReferenceLocatorPipeline


class _CoordinateTransformation(BaseModel):
    name: Name | MISSING = MISSING
    input: CoordinateTransformationReference
    output: CoordinateTransformationReference


class IdentityCoordinateTransformation(_CoordinateTransformation):
    type: Literal["identity"] = "identity"


class ScaleCoordinateTransformation(_CoordinateTransformation):
    type: Literal["scale"] = "scale"
    scale: tuple[float, ...]


class TranslationCoordinateTransformation(_CoordinateTransformation):
    type: Literal["translation"] = "translation"
    translation: tuple[float, ...]


class CustomCoordinateTransformation(_CoordinateTransformation):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type


CoordinateTransformation = Annotated[
    IdentityCoordinateTransformation
    | ScaleCoordinateTransformation
    | TranslationCoordinateTransformation
    | CustomCoordinateTransformation,
    OpenTypeUnion(),
]


class ScaleDownsamplingCoordinateTransformation(BaseModel):
    type: Literal["scale"] = "scale"
    scale: tuple[float, ...]


class TranslationDownsamplingCoordinateTransformation(BaseModel):
    type: Literal["translation"] = "translation"
    translation: tuple[float, ...]


class MultiscaleNodeArray(BaseModel):
    type: Literal["singlescale"] = "singlescale"  # ??
    id: Id | MISSING = MISSING
    name: Name | MISSING = MISSING
    ref: ReferenceLocatorPipeline | MISSING = MISSING
    downsampling_transformations: (
        tuple[ScaleDownsamplingCoordinateTransformation]
        | tuple[
            ScaleDownsamplingCoordinateTransformation,
            TranslationDownsamplingCoordinateTransformation,
        ]
        | tuple[
            TranslationDownsamplingCoordinateTransformation,
            ScaleDownsamplingCoordinateTransformation,
        ]
    )


class MultiscaleNode(BaseModel):
    type: Literal["multiscale"] = "multiscale"
    id: Id | MISSING = MISSING
    name: Name | MISSING = MISSING
    coordinate_systems: tuple[CoordinateSystem, ...]
    coordinate_transformations: tuple[CoordinateTransformation, ...] | MISSING = MISSING
    arrays: tuple[MultiscaleNodeArray, ...]
    traits: tuple[Trait, ...] | MISSING = MISSING


class MultiscaleNodeReference(BaseModel):
    type: Literal["multiscale"] = "multiscale"
    id: Id
    name: Name | MISSING = MISSING
    ref: ReferenceLocatorPipeline
    traits: tuple[Trait, ...] | MISSING = MISSING


class CollectionNode(BaseModel):
    type: Literal["collection"] = "collection"
    id: Id
    name: Name | MISSING = MISSING
    nodes: tuple[CollectionNode | CollectionNodeReference | LeafNodeReference, ...]
    traits: tuple[Trait, ...] | MISSING = MISSING


class CollectionNodeReference(BaseModel):
    type: Literal["collection"] = "collection"
    id: Id
    name: Name | MISSING = MISSING
    ref: ReferenceLocatorPipeline
    traits: tuple[Trait, ...] | MISSING = MISSING


class CustomLeafNode(BaseModel):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type
    id: Id
    name: Name | MISSING = MISSING
    traits: tuple[Trait, ...] | MISSING = MISSING


class CustomLeafNodeReference(BaseModel):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type
    id: Id
    name: Name | MISSING = MISSING
    ref: ReferenceLocatorPipeline
    traits: tuple[Trait, ...] | MISSING = MISSING


class SceneTrait(BaseModel):
    type: Literal["scene"] = "scene"
    coordinate_systems: tuple[CoordinateSystem, ...] | MISSING = MISSING
    coordinate_transformations: tuple[CoordinateTransformation, ...]


class CustomTrait(BaseModel):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type


Trait = Annotated[SceneTrait | CustomTrait, OpenTypeUnion()]

LeafNodeReference = Annotated[
    MultiscaleNodeReference | CustomLeafNodeReference, OpenTypeUnion()
]
Node = Annotated[MultiscaleNode | CollectionNode | CustomLeafNode, OpenTypeUnion()]
NodeReference = Annotated[
    MultiscaleNodeReference | CollectionNodeReference | CustomLeafNodeReference,
    OpenTypeUnion(),
]
