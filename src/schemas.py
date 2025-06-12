from typing import TypedDict, Dict, Any, List

class StorageUsage(TypedDict):
    bytes_used: int
    metadata_bytes_used: int
    
class UploadResult(TypedDict):
    id: str
    metadata: Dict[str, Any]
    storage_usage: StorageUsage

class VectaraDocMetadata(TypedDict, total=False):
    title: str
    # Other goodies from Vectara

class VectaraDocPartMetadata(TypedDict, total=False):
    breadcrumb: List[str]
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
    custom_dimensions: Dict[str, Any]
    metadata: VectaraDocPartMetadata

class VectaraDoc(TypedDict):
    id: str
    metadata: VectaraDocMetadata
    parts: List[VectaraDocPart]

class ConvexSource(TypedDict):
    filename: str
    title: str
    parts: List[Dict[str, Any]]