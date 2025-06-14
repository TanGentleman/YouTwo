from typing_extensions import NotRequired, TypedDict, Any

class StorageUsage(TypedDict):
    bytes_used: int
    metadata_bytes_used: int

class UploadResult(TypedDict):
    id: str
    metadata: dict[str, Any]
    storage_usage: StorageUsage

class VectaraDocMetadata(TypedDict, total=False):
    title: str
    # Add other Vectara metadata fields as needed

class VectaraDocPartMetadata(TypedDict, total=False):
    breadcrumb: list[str]
    is_title: bool
    title: str
    offset: int
    lang: str
    len: int
    section: int
    title_level: int
    # Add other Vectara part metadata fields as needed

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
    partsCount: int
    parts: NotRequired[list[str]]

class ConvexCreateEntity(TypedDict):
    name: str
    entityType: str
    observations: NotRequired[list[str]]
    updatedAt: NotRequired[int]
    journalIds: NotRequired[list[str]]

class ConvexCreateRelation(TypedDict):
    toId: str
    fromId: str
    relationType: str
    updatedAt: NotRequired[int]
    journalIds: NotRequired[list[str]]

class FunctionSpec(TypedDict):
    args: dict
    functionType: str
    identifier: str
    returns: dict
    visibility: dict

class EntityResult(TypedDict):
    success: bool
    name: str
    reason: NotRequired[str]

class BriefEntity(TypedDict):
    name: str
    entityType: str

class InitResult(TypedDict):
    deploymentSelector: str
    url: str