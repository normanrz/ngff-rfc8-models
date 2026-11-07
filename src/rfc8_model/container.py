from __future__ import annotations

from typing import Literal, Self

from pydantic import MISSING, BaseModel

from .extensions import ExtensionManifest
from .models import Node


class OmeAttributes(BaseModel):
    version: Literal["0.9dev42"] = "0.9dev42"
    extension_manifests: list[ExtensionManifest] | MISSING = MISSING
    root: Node


class Attributes(BaseModel):
    ome: OmeAttributes


class ZarrJson(BaseModel):
    zarr_format: Literal[3] = 3
    node_type: Literal["group", "array"] = "group"
    attributes: Attributes

    @classmethod
    def with_ome(cls, node: Node) -> Self:
        return cls(attributes=Attributes(ome=OmeAttributes(root=node)))

    @property
    def path(self) -> str:
        return ""


class StandaloneJson(BaseModel):
    ome: OmeAttributes

    @classmethod
    def with_ome(cls, node: Node) -> Self:
        return cls(ome=OmeAttributes(root=node))

    @property
    def path(self) -> str:
        return ""
