from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    MISSING,
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

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


class IndexCoordinateSystemAxis(_CoordinateSystemAxis):
    type: Literal["index"]


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
    IndexCoordinateSystemAxis
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
    # `multiscale` only as the input of a multiscale's own coordinate transformations
    type: Literal["coordinate_system", "multiscale"] = "coordinate_system"
    ref: ReferenceLocatorPipeline


class _CoordinateTransformation(BaseModel):
    name: Name | MISSING = MISSING
    # Required at the top level; MAY be omitted when nested in a sequence,
    # by_dimension or bijection, where they follow from the parent
    input: CoordinateTransformationReference | MISSING = MISSING
    output: CoordinateTransformationReference | MISSING = MISSING


Matrix = tuple[tuple[float, ...], ...]


class _MatrixCoordinateTransformation(_CoordinateTransformation):
    """Parameters are given inline or by `ref` to a 2D Zarr array, not both."""

    ref: ReferenceLocatorPipeline | MISSING = MISSING

    @model_validator(mode="after")
    def _inline_xor_ref(self):
        inline = getattr(self, self.type) is not MISSING
        if inline == (self.ref is not MISSING):
            raise ValueError(f"exactly one of {self.type!r} and 'ref' is required")
        return self


class IdentityCoordinateTransformation(_CoordinateTransformation):
    type: Literal["identity"] = "identity"


class MapAxisCoordinateTransformation(_CoordinateTransformation):
    type: Literal["map_axis"] = "map_axis"
    map_axis: tuple[int, ...]  # output axis i is input axis map_axis[i]

    @model_validator(mode="after")
    def _is_permutation(self):
        if sorted(self.map_axis) != list(range(len(self.map_axis))):
            raise ValueError("map_axis must be a permutation of 0..N-1")
        return self


class ProjectAxisCoordinateTransformation(_CoordinateTransformation):
    type: Literal["project_axis"] = "project_axis"
    created_outputs: tuple[int, ...] | MISSING = MISSING  # new axes, default 0
    dropped_inputs: tuple[int, ...] | MISSING = MISSING

    @model_validator(mode="after")
    def _unique(self):
        for axes in (self.created_outputs, self.dropped_inputs):
            if axes is not MISSING and len(set(axes)) != len(axes):
                raise ValueError("created_outputs and dropped_inputs must be unique")
        return self


class ScaleCoordinateTransformation(_CoordinateTransformation):
    type: Literal["scale"] = "scale"
    scale: tuple[float, ...]


class TranslationCoordinateTransformation(_CoordinateTransformation):
    type: Literal["translation"] = "translation"
    translation: tuple[float, ...]


class AffineCoordinateTransformation(_MatrixCoordinateTransformation):
    type: Literal["affine"] = "affine"
    affine: Matrix | MISSING = MISSING  # M x (N+1)


class RotationCoordinateTransformation(_MatrixCoordinateTransformation):
    type: Literal["rotation"] = "rotation"
    rotation: Matrix | MISSING = MISSING  # N x N, orthonormal, det 1


class SequenceCoordinateTransformation(_CoordinateTransformation):
    type: Literal["sequence"] = "sequence"
    transformations: Annotated[
        tuple[NestedCoordinateTransformation, ...], Field(min_length=1)
    ]


# Not exhaustive; consumers SHOULD tell users when they use another method
Interpolation = Literal["nearest", "linear", "bspline-cubic"] | Type


class CoordinatesCoordinateTransformation(_CoordinateTransformation):
    type: Literal["coordinates"] = "coordinates"
    ref: ReferenceLocatorPipeline  # multiscale of absolute positions
    interpolation: Interpolation | MISSING = MISSING  # default: linear


class DisplacementsCoordinateTransformation(_CoordinateTransformation):
    type: Literal["displacements"] = "displacements"
    ref: ReferenceLocatorPipeline  # multiscale of relative shifts
    interpolation: Interpolation | MISSING = MISSING  # default: linear


class ByDimensionItem(BaseModel):
    transformation: NestedCoordinateTransformation
    input_axes: tuple[int, ...]
    output_axes: tuple[int, ...]


class ByDimensionCoordinateTransformation(_CoordinateTransformation):
    type: Literal["by_dimension"] = "by_dimension"
    transformations: tuple[ByDimensionItem, ...]


class BijectionCoordinateTransformation(_CoordinateTransformation):
    type: Literal["bijection"] = "bijection"
    forward: NestedCoordinateTransformation
    inverse: NestedCoordinateTransformation


class CustomCoordinateTransformation(_CoordinateTransformation):
    model_config = ConfigDict(extra="allow")  # keep extension fields

    type: Type


NestedCoordinateTransformation = Annotated[
    IdentityCoordinateTransformation
    | MapAxisCoordinateTransformation
    | ProjectAxisCoordinateTransformation
    | ScaleCoordinateTransformation
    | TranslationCoordinateTransformation
    | AffineCoordinateTransformation
    | RotationCoordinateTransformation
    | SequenceCoordinateTransformation
    | CoordinatesCoordinateTransformation
    | DisplacementsCoordinateTransformation
    | ByDimensionCoordinateTransformation
    | BijectionCoordinateTransformation
    | CustomCoordinateTransformation,
    OpenTypeUnion(),
]


def _has_input_output(t: _CoordinateTransformation) -> _CoordinateTransformation:
    if t.input is MISSING or t.output is MISSING:
        raise ValueError("top-level coordinate transformations need input and output")
    return t


CoordinateTransformation = Annotated[
    NestedCoordinateTransformation, AfterValidator(_has_input_output)
]


class ScaleDownsamplingCoordinateTransformation(BaseModel):
    model_config = ConfigDict(extra="forbid")  # input and output are implicit

    type: Literal["scale"] = "scale"
    scale: tuple[float, ...]


class TranslationDownsamplingCoordinateTransformation(BaseModel):
    model_config = ConfigDict(extra="forbid")  # input and output are implicit

    type: Literal["translation"] = "translation"
    translation: tuple[float, ...]


class MultiscaleNodeArray(BaseModel):
    type: Literal["array"] = "array"
    name: Name | MISSING = MISSING
    ref: ReferenceLocatorPipeline | MISSING = MISSING
    # From this array's index space to that of the first (highest-resolution) array
    downsampling_transformations: (
        tuple[ScaleDownsamplingCoordinateTransformation]
        | tuple[
            ScaleDownsamplingCoordinateTransformation,
            TranslationDownsamplingCoordinateTransformation,
        ]
        | MISSING
    ) = MISSING  # MAY be omitted on the first array only


def _local_id(ref: CoordinateTransformationReference) -> str | None:
    """The id of a reference that resolves within the current document."""
    if len(ref.ref) == 1 and isinstance(ref.ref[0], IdReferenceLocator):
        return ref.ref[0].id
    return None


class MultiscaleNode(BaseModel):
    type: Literal["multiscale"] = "multiscale"
    id: Id
    name: Name | MISSING = MISSING
    coordinate_systems: tuple[CoordinateSystem, ...]
    # From the multiscale itself, standing for its first (highest-resolution)
    # array, to a coordinate system in `coordinate_systems`
    coordinate_transformations: tuple[CoordinateTransformation, ...]
    data: tuple[MultiscaleNodeArray, ...]
    traits: tuple[Trait, ...] | MISSING = MISSING

    @model_validator(mode="after")
    def _check(self):
        for array in self.data[1:]:
            if array.downsampling_transformations is MISSING:
                raise ValueError("data arrays after the first need downsampling_transformations")
        cs_ids = {cs.id for cs in self.coordinate_systems}
        outputs = set()
        for ct in self.coordinate_transformations:
            if ct.input.type != "multiscale" or _local_id(ct.input) != self.id:
                raise ValueError("input must reference the multiscale itself")
            if ct.output.type != "coordinate_system" or _local_id(ct.output) not in cs_ids:
                raise ValueError("output must reference a coordinate system of the multiscale")
            outputs.add(_local_id(ct.output))
        if len(outputs) > 1:
            raise ValueError("all outputs must reference the same coordinate system")
        return self


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

    @model_validator(mode="after")
    def _between_coordinate_systems(self):
        for ct in self.coordinate_transformations:
            if ct.input.type != "coordinate_system" or ct.output.type != "coordinate_system":
                raise ValueError("scene transformations connect coordinate systems")
        return self


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
