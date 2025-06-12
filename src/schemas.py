from typing import NotRequired, TypedDict, Dict, Any

class StorageUsage(TypedDict):
    bytes_used: int
    metadata_bytes_used: int


class UploadResult(TypedDict):
    id: str
    metadata: Dict[str, Any] # NOTE: Should not need this field
    storage_usage: StorageUsage

class VectaraDocument(TypedDict):
    id: str
    metadata: Dict[str, Any]
    # tables: list[Dict[str, Any]]
    # parts: list[Dict[str, Any]] # NOTE: Only available when by list ID
    storage_usage: NotRequired[StorageUsage]
    # extraction_usage: Dict[str, Any]


class VectaraDocuments(TypedDict):
    documents: list[VectaraDocument]
    # metadata: Dict[str, Any]
    # page_key: str
