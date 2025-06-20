"""YouTwo Memory Visualization Module

Provides tools for visualizing knowledge graphs from various data sources.
Supports Convex API, JSON files, and direct Python dictionaries.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from graphviz import Digraph

    GRAPHVIZ_AVAILABLE = True
except ImportError:
    Digraph = None
    GRAPHVIZ_AVAILABLE = False

from youtwo.paths import DATA_DIR
from youtwo.server.utils import async_convex_api_call

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions and Enums
# =============================================================================


class GraphVisualizationError(Exception):
    """Exception raised when graph visualization fails."""

    pass


class OutputFormat(str, Enum):
    """Supported output formats for graph visualization."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class Entity:
    """Data model for a knowledge graph entity."""

    name: str
    entityType: str
    properties: Dict[str, any] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class Relation:
    """Data model for a knowledge graph relation."""

    source: str
    target: str
    relationType: str
    properties: Dict[str, any] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class GraphData:
    """Data model for complete graph data with convenience methods."""

    entities: List[Entity]
    relations: List[Relation]

    @classmethod
    def from_dict(cls, data: Dict) -> "GraphData":
        """Create GraphData from dictionary representation.

        Supports both 'from'/'to' and 'source'/'target' keys for relations.
        """
        entities = []
        for entity_data in data.get("entities", []):
            entity = Entity(
                name=entity_data.get("name", ""),
                entityType=entity_data.get("entityType", ""),
                properties=entity_data.get("properties", {}),
            )
            entities.append(entity)

        relations = []
        for rel in data.get("relations", []):
            source = rel.get("from") or rel.get("source")
            target = rel.get("to") or rel.get("target")
            relation_type = rel.get("relationType")

            if all([source, target, relation_type]):
                relations.append(
                    Relation(
                        source=source,
                        target=target,
                        relationType=relation_type,
                        properties=rel.get("properties", {}),
                    )
                )

        return cls(entities=entities, relations=relations)

    def to_dict(self) -> Dict:
        """Convert GraphData to dictionary representation."""
        return {
            "entities": [asdict(entity) for entity in self.entities],
            "relations": [asdict(relation) for relation in self.relations],
        }

    def filter(self, max_nodes: int = None, max_edges: int = None) -> "GraphData":
        """Return a filtered copy of the graph data."""
        entities = self.entities[:max_nodes] if max_nodes else self.entities
        entity_names = {entity.name for entity in entities}

        relations = self.relations[:max_edges] if max_edges else self.relations

        # Only include relations between existing entities
        relations = [
            rel
            for rel in relations
            if rel.source in entity_names and rel.target in entity_names
        ]

        return GraphData(entities=entities, relations=relations)

    def save(self, file_path: Union[str, Path]) -> Path:
        """Save graph data to JSON file."""
        file_path = Path(file_path).with_suffix(".json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return file_path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "GraphData":
        """Load graph data from JSON file."""
        file_path = Path(file_path).with_suffix(".json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class VisualizationConfig:
    """Configuration for graph visualization styling and layout."""

    # Layout settings
    rankdir: str = "TB"  # Top to Bottom
    size: str = "12,8"
    dpi: str = "300"

    # Node styling
    node_shape: str = "ellipse"
    node_style: str = "filled"

    # Entity type colors
    entity_type_colors: Dict[str, str] = None

    def __post_init__(self):
        if self.entity_type_colors is None:
            self.entity_type_colors = {
                "person": "lightblue",
                "organization": "lightgreen",
                "location": "lightyellow",
                "concept": "lightpink",
                "event": "lightcoral",
                "default": "lightgray",
            }

    def get_entity_color(self, entity_type: str) -> str:
        """Get color for entity type with fallback to default."""
        return self.entity_type_colors.get(
            entity_type.lower(), self.entity_type_colors["default"]
        )


# =============================================================================
# Data Connectors
# =============================================================================


class DataConnector(ABC):
    """Abstract base class for data connectors."""

    @abstractmethod
    async def get_graph_data(self) -> GraphData:
        """Return structured graph data."""
        pass


class ConvexConnector(DataConnector):
    """Connector for Convex API data."""

    async def get_graph_data(self) -> GraphData:
        """Fetch graph data from Convex API."""
        try:
            raw_data = await async_convex_api_call("graph", "GET")
            return GraphData.from_dict(raw_data)
        except Exception as e:
            raise GraphVisualizationError(f"Failed to fetch data from Convex API: {e}")


class JSONFileConnector(DataConnector):
    """Connector for JSON file data."""

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise GraphVisualizationError(f"JSON file not found: {self.file_path}")

    async def get_graph_data(self) -> GraphData:
        """Load graph data from JSON file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return GraphData.from_dict(data)
        except Exception as e:
            raise GraphVisualizationError(
                f"Failed to load JSON file {self.file_path}: {e}"
            )


class DictionaryConnector(DataConnector):
    """Connector for direct Python dictionary data."""

    def __init__(self, data: Dict):
        self.data = data

    async def get_graph_data(self) -> GraphData:
        """Convert dictionary data to GraphData."""
        try:
            return GraphData.from_dict(self.data)
        except Exception as e:
            raise GraphVisualizationError(f"Failed to parse dictionary data: {e}")


# =============================================================================
# Main Visualizer Class
# =============================================================================


class KnowledgeGraphVisualizer:
    """Main class for visualizing knowledge graphs with various data sources."""

    def __init__(
        self, connector: DataConnector, config: Optional[VisualizationConfig] = None
    ):
        if not GRAPHVIZ_AVAILABLE:
            raise GraphVisualizationError(
                "graphviz is not installed. Install with 'pip install graphviz'"
            )

        self.connector = connector
        self.config = config or VisualizationConfig()
        self._graph_data: Optional[GraphData] = None

    async def load_graph_data(self) -> GraphData:
        """Load and cache graph data from connector."""
        if self._graph_data is None:
            self._graph_data = await self.connector.get_graph_data()
        return self._graph_data

    def batch_update_properties(
        self,
        entity_updates: Dict[str, Dict] = None,
        relation_updates: List[tuple] = None,
    ) -> None:
        """Batch update entity and relation properties efficiently.

        Args:
            entity_updates: Dict mapping entity names to property updates
            relation_updates: List of (source, target, relation_type, properties) tuples
        """
        if self._graph_data is None:
            raise GraphVisualizationError(
                "Graph data not loaded. Call load_graph_data() first."
            )

        # Update entity properties
        if entity_updates:
            entity_lookup = {e.name: e for e in self._graph_data.entities}
            for entity_name, properties in entity_updates.items():
                if entity_name in entity_lookup:
                    entity_lookup[entity_name].properties.update(properties)

        # Update relation properties
        if relation_updates:
            for source, target, relation_type, properties in relation_updates:
                for relation in self._graph_data.relations:
                    if (
                        relation.source == source
                        and relation.target == target
                        and relation.relationType == relation_type
                    ):
                        relation.properties.update(properties)

    async def visualize(
        self,
        max_nodes: int = 100,
        max_edges: int = 200,
        output_filename: str = "knowledge_graph",
        output_dir: Optional[Union[str, Path]] = None,
        view_output: bool = True,
        format: OutputFormat = OutputFormat.PNG,
        save_data: bool = False,
    ) -> tuple[Path, Optional[Path]]:
        """Visualize the knowledge graph with optional filtering and saving.

        Returns:
            Tuple of (visualization_path, data_path) where data_path is None if save_data=False
        """
        try:
            graph_data = await self.load_graph_data()

            # Filter data if limits specified
            graph_data = graph_data.filter(max_nodes=max_nodes, max_edges=max_edges)

            output_path = self._render_graph(
                graph_data.entities,
                graph_data.relations,
                output_filename,
                output_dir or DATA_DIR,
                view_output,
                format.value,
            )

            # Save filtered data if requested
            data_path = None
            if save_data:
                data_path = graph_data.save(
                    Path(output_dir or DATA_DIR) / f"{output_filename}_data"
                )

            logger.info(
                f"Visualized {len(graph_data.entities)} nodes and "
                f"{len(graph_data.relations)} edges"
            )
            return output_path, data_path

        except Exception as e:
            raise GraphVisualizationError(f"Failed to visualize knowledge graph: {e}")

    def _render_graph(
        self,
        entities: List[Entity],
        relations: List[Relation],
        output_filename: str,
        output_dir: Path,
        view_output: bool,
        format: str,
    ) -> Path:
        """Render the graph using Graphviz."""
        dot = Digraph(comment="Knowledge Graph", format=format)

        # Set graph attributes
        dot.attr(
            rankdir=self.config.rankdir, size=self.config.size, dpi=self.config.dpi
        )

        # Set default node attributes
        dot.attr("node", shape=self.config.node_shape, style=self.config.node_style)

        # Add nodes with type-based coloring
        for entity in entities:
            color = self.config.get_entity_color(entity.entityType)
            dot.node(entity.name, entity.name, fillcolor=color)

        # Add edges with labels
        for rel in relations:
            dot.edge(rel.source, rel.target, label=rel.relationType)

        # Render to file
        try:
            output_path = dot.render(
                output_filename, directory=output_dir, view=view_output, cleanup=True
            )
            return Path(output_path)
        except Exception as e:
            raise GraphVisualizationError(f"Failed to render graph: {e}")

    async def save_current_state(self, file_path: Union[str, Path]) -> Path:
        """Save current graph state to JSON file."""
        if self._graph_data is None:
            await self.load_graph_data()
        return self._graph_data.save(file_path)


# =============================================================================
# Convenience Functions
# =============================================================================


async def visualize_knowledge_graph(
    max_nodes: int = 100,
    max_edges: int = 200,
    output_filename: str = "knowledge_graph",
    output_dir: Optional[Union[str, Path]] = None,
    view_output: bool = True,
    format: OutputFormat = OutputFormat.PNG,
    save_data: bool = False,
    config: Optional[VisualizationConfig] = None,
) -> tuple[Path, Optional[Path]]:
    """Visualize knowledge graph from Convex API.

    This is the main function for visualizing data from the Convex backend.
    """
    connector = ConvexConnector()
    visualizer = KnowledgeGraphVisualizer(connector, config)
    return await visualizer.visualize(
        max_nodes=max_nodes,
        max_edges=max_edges,
        output_filename=output_filename,
        output_dir=output_dir,
        view_output=view_output,
        format=format,
        save_data=save_data,
    )


async def visualize_from_json(
    json_path: Union[str, Path],
    max_nodes: int = 100,
    max_edges: int = 200,
    output_filename: str = "knowledge_graph",
    output_dir: Optional[Union[str, Path]] = None,
    view_output: bool = True,
    format: OutputFormat = OutputFormat.PNG,
    save_data: bool = False,
    config: Optional[VisualizationConfig] = None,
) -> tuple[Path, Optional[Path]]:
    """Visualize knowledge graph from JSON file.

    Args:
        json_path: Path to JSON file containing graph data
        Other args: Same as visualize_knowledge_graph()
    """
    connector = JSONFileConnector(json_path)
    visualizer = KnowledgeGraphVisualizer(connector, config)
    return await visualizer.visualize(
        max_nodes=max_nodes,
        max_edges=max_edges,
        output_filename=output_filename,
        output_dir=output_dir,
        view_output=view_output,
        format=format,
        save_data=save_data,
    )


async def visualize_from_dict(
    graph_dict: Dict,
    max_nodes: int = 100,
    max_edges: int = 200,
    output_filename: str = "knowledge_graph",
    output_dir: Optional[Union[str, Path]] = None,
    view_output: bool = True,
    format: OutputFormat = OutputFormat.PNG,
    save_data: bool = False,
    config: Optional[VisualizationConfig] = None,
) -> tuple[Path, Optional[Path]]:
    """Visualize knowledge graph from Python dictionary.

    This is the easiest way to visualize a graph from code. Simply pass a dictionary
    with 'entities' and 'relations' keys.

    Example:
        graph_data = {
            "entities": [
                {"name": "Alice", "entityType": "person"},
                {"name": "Bob", "entityType": "person"},
                {"name": "ACME Corp", "entityType": "organization"}
            ],
            "relations": [
                {"source": "Alice", "target": "Bob", "relationType": "knows"},
                {"source": "Alice", "target": "ACME Corp", "relationType": "works_at"}
            ]
        }

        output_path, data_path = await visualize_from_dict(graph_data)

    Args:
        graph_dict: Dictionary containing entities and relations
        Other args: Same as visualize_knowledge_graph()
    """
    connector = DictionaryConnector(graph_dict)
    visualizer = KnowledgeGraphVisualizer(connector, config)
    return await visualizer.visualize(
        max_nodes=max_nodes,
        max_edges=max_edges,
        output_filename=output_filename,
        output_dir=output_dir,
        view_output=view_output,
        format=format,
        save_data=save_data,
    )
