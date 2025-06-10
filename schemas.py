from typing import TypedDict, Dict, Any

class StorageUsage(TypedDict):
    bytes_used: int
    metadata_bytes_used: int


class UploadResult(TypedDict):
    id: str
    metadata: Dict[str, Any]
    storage_usage: StorageUsage
