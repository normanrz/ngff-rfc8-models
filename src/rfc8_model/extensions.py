from __future__ import annotations

from typing import Annotated, Literal

from pydantic import MISSING, BaseModel, Field, StringConstraints

from .models import Name

Version = Annotated[str, StringConstraints(pattern=r"^[0-9]+(\.[0-9A-Za-z.+-]+)?$")]
NonEmpty = Annotated[str, StringConstraints(pattern=r"\S")]
# RFC 3986: scheme ":" hier-part, no whitespace
URI = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z][a-zA-Z0-9+.-]*:\S+$")]
URL = Annotated[str, StringConstraints(pattern=r"^https?://[^\s/?#]+[^\s]*$")]


class ExtensionManifestSchema(BaseModel):
    type: Literal["linkml", "jsonschema"] = "jsonschema"
    url: URL


class ExtensionManifest(BaseModel):
    id: URI | str  # Maybe rename?
    version: Version
    name: Name | MISSING = MISSING
    description: NonEmpty | MISSING = MISSING
    must_understand: bool = False
    homepage: URL | MISSING = MISSING
    schemas: list[ExtensionManifestSchema] = Field(default_factory=list)
