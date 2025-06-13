from typing import TypedDict, Any

class StorageUsage(TypedDict):
    bytes_used: int
    metadata_bytes_used: int

class UploadResult(TypedDict):
    id: str
    metadata: dict[str, Any]
    storage_usage: StorageUsage

class VectaraDocMetadata(TypedDict, total=False):
    title: str
    # Other goodies from Vectara

class VectaraDocPartMetadata(TypedDict, total=False):
    breadcrumb: list[str]
    is_title: bool
    title: str
    offset: int
    lang: str
    len: int
    section: int
    title_level: int
    # Other goodies from Vectara

class VectaraDocPart(TypedDict):
    text: str
    context: str
    custom_dimensions: dict[str, Any]
    metadata: VectaraDocPartMetadata

class VectaraDoc(TypedDict):
    id: str
    metadata: VectaraDocMetadata
    parts: list[VectaraDocPart]

class ConvexSource(TypedDict):
    filename: str
    title: str
    parts: list[str] | list[int]