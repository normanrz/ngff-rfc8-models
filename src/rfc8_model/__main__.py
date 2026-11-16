from uuid import uuid7

from rfc8_model.container import StandaloneJson, ZarrJson
from rfc8_model.models import (
    ChannelCoordinateSystemAxis,
    CollectionNode,
    CoordinateSystem,
    CoordinateTransformationReference,
    IdReferenceLocator,
    MultiscaleNode,
    MultiscaleNodeArray,
    MultiscaleNodeReference,
    RelativePathReferenceLocator,
    ScaleCoordinateTransformation,
    ScaleDownsamplingCoordinateTransformation,
    SpaceCoordinateSystemAxis,
    ZarrReferenceLocator,
)

multiscale_id = str(uuid7())
physical_id = str(uuid7())
multiscale_zarr_group = ZarrJson.with_ome(
    MultiscaleNode(
        id=multiscale_id,
        coordinate_systems=(
            CoordinateSystem(
                id=physical_id,
                name="physical",
                axes=[
                    ChannelCoordinateSystemAxis(id="c", type="channel"),
                    *(
                        SpaceCoordinateSystemAxis(id=axis, type="space", unit="micrometer")
                        for axis in ("z", "y", "x")
                    ),
                ],
            ),
        ),
        coordinate_transformations=(
            ScaleCoordinateTransformation(
                input=CoordinateTransformationReference(
                    type="multiscale", ref=(IdReferenceLocator(id=multiscale_id),)
                ),
                output=CoordinateTransformationReference(
                    ref=(IdReferenceLocator(id=physical_id),)
                ),
                scale=(1.0, 0.5, 0.5, 0.5),
            ),
        ),
        data=(
            MultiscaleNodeArray(),
            MultiscaleNodeArray(
                downsampling_transformations=(
                    ScaleDownsamplingCoordinateTransformation(
                        scale=(1.0, 2.0, 2.0, 2.0)
                    ),
                )
            ),
        ),
    )
)


collection_standalone_file = StandaloneJson.with_ome(
    CollectionNode(
        id=str(uuid7()),
        nodes=(
            MultiscaleNodeReference(
                id=str(uuid7()),
                ref=(
                    RelativePathReferenceLocator(path="./raw"),
                    ZarrReferenceLocator(),
                ),
            ),
        ),
    )
)

collection_zarr_group = ZarrJson.with_ome(
    CollectionNode(
        id=str(uuid7()),
        nodes=(
            MultiscaleNodeReference(
                id=str(uuid7()),
                ref=(ZarrReferenceLocator(path="./raw"),),
            ),
        ),
    )
)

print(repr(multiscale_zarr_group))
print(repr(collection_standalone_file))
print(repr(collection_zarr_group))
