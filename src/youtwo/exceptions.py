class ValidationError(Exception):
    """Base validation error"""


class ConvexRequestError(ValidationError):
    """Convex input validation error"""


class VectaraRequestError(ValidationError):
    """Vectara input validation error"""


class IndexingError(Exception):
    """Indexing error"""


class ToolCallError(Exception):
    """Tool call error"""
