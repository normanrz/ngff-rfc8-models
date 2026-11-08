from uuid import uuid7

from rfc8_model.container import StandaloneJson, ZarrJson
from rfc8_model.models import (
    CollectionNode,
    MultiscaleNode,
    MultiscaleNodeArray,
    MultiscaleNodeReference,
    RelativePathReferenceLocator,
    ScaleDownsamplingCoordinateTransformation,
    ZarrReferenceLocator,
)

multiscale_zarr_group = ZarrJson.with_ome(
    MultiscaleNode(
        coordinate_systems=(),
        arrays=(
            MultiscaleNodeArray(
                downsampling_transformations=(
                    ScaleDownsamplingCoordinateTransformation(
                        scale=(1.0, 1.0, 1.0, 1.0)
                    ),
                )
            ),
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
