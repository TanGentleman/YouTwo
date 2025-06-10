from typing import TypedDict, Dict, Any

class StorageUsage(TypedDict):
    bytes_used: int
    metadata_bytes_used: int


class UploadResult(TypedDict):
    id: str
    metadata: Dict[str, Any] # NOTE: Should not need this field
    storage_usage: StorageUsage
