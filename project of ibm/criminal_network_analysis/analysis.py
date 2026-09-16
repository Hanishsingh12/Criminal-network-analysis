"""
analysis.py
===========
Read-only graph analysis and summary generation.

The Analyzer class takes the networkx DiGraph and the data collections
from NetworkManager and produces statistics and a plain-language summary.

IMPORTANT: All statistics describe only the mathematical properties of the
supplied graph.  They say nothing about the real world and must not be used
to assess guilt, predict behaviour, or profile real people.

All data analysed here is fictional/synthetic.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

import networkx as nx

from models import Entity, Incident, Relationship, RelationshipType


class Analyzer:
    """
    Provides read-only analysis of the network graph.

    Every method receives the data it needs as arguments — no hidden state.
    This makes each method easy to test independently.
    """

    # ------------------------------------------------------------------
    # Connection counts
    # ------------------------------------------------------------------

    def count_connections(self, graph: nx.DiGraph) -> Dict[str, int]:
        """
        Return a dictionary mapping each entity_id to its total degree.

        Total degree = number of incoming edges + number of outgoing edges.
        This is a purely mathematical property of the graph.
        """
        return dict(graph.degree())

    def get_in_degree(self, graph: nx.DiGraph) -> Dict[str, int]:
        """Return a dictionary of in-degree (incoming edges) per entity_id."""
        return dict(graph.in_degree())

    def get_out_degree(self, graph: nx.DiGraph) -> Dict[str, int]:
        """Return a dictionary of out-degree (outgoing edges) per entity_id."""
        return dict(graph.out_degree())

    # ------------------------------------------------------------------
    # Notable nodes
    # ------------------------------------------------------------------

    def get_most_connected(
        self,
        graph: nx.DiGraph,
        entities: Dict[str, Entity],
    ) -> Optional[Entity]:
        """
        Return the entity with the highest total degree.
        Returns None if there are no entities.
        """
        if not graph.nodes:
            return None
        degrees = dict(graph.degree())
        if not degrees:
            return None
        top_id = max(degrees, key=lambda k: degrees[k])
        return entities.get(top_id)

    def get_isolated_entities(
        self,
        graph: nx.DiGraph,
        entities: Dict[str, Entity],
    ) -> List[Entity]:
        """
        Return entities with no connections at all (degree == 0).
        These are nodes that exist in the graph but have no edges.
        """
        isolated_ids = [n for n in graph.nodes if graph.degree(n) == 0]
        return [entities[eid] for eid in isolated_ids if eid in entities]

    # ------------------------------------------------------------------
    # Relationship grouping
    # ------------------------------------------------------------------

    def group_by_type(
        self, relationships: List[Relationship]
    ) -> Dict[str, List[Relationship]]:
        """
        Group relationships by their type.

        Returns a dict like:
          { "Associate": [...], "Financial": [...], ... }
        """
        groups: Dict[str, List[Relationship]] = {t.value: [] for t in RelationshipType}
        for rel in relationships:
            groups[rel.relationship_type.value].append(rel)
        return groups

    def count_by_type(self, relationships: List[Relationship]) -> Dict[str, int]:
        """Return a count of relationships per type."""
        return Counter(r.relationship_type.value for r in relationships)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def generate_summary(
        self,
        graph: nx.DiGraph,
        entities: Dict[str, Entity],
        incidents: List[Incident],
        relationships: List[Relationship],
    ) -> str:
        """
        Generate a plain-language summary of the network.

        The summary describes only the mathematical structure of the
        supplied graph.  It makes no judgements about individuals.
        """
        if not entities and not incidents and not relationships:
            return (
                "Network is empty. No summary available.\n"
                "Add entities, incidents, and relationships to see analysis."
            )

        lines: List[str] = []
        lines.append("=" * 50)
        lines.append("  NETWORK ANALYTICAL SUMMARY")
        lines.append("=" * 50)
        lines.append("")

        # --- Counts ---
        lines.append(f"Total entities    : {len(entities)}")
        lines.append(f"Total incidents   : {len(incidents)}")
        lines.append(f"Total relationships: {len(relationships)}")
        lines.append("")

        # --- Most connected node ---
        top = self.get_most_connected(graph, entities)
        if top:
            degree = dict(graph.degree()).get(top.entity_id, 0)
            lines.append(
                f"Most connected entity : {top.name} ({top.entity_id})"
                f" — {degree} connection(s)"
            )
        lines.append("")

        # --- Isolated entities ---
        isolated = self.get_isolated_entities(graph, entities)
        if isolated:
            names = ", ".join(f"{e.name} ({e.entity_id})" for e in isolated)
            lines.append(f"Isolated entities (no connections): {names}")
        else:
            lines.append("No isolated entities — every entity has at least one connection.")
        lines.append("")

        # --- Relationship type breakdown ---
        lines.append("Relationship type breakdown:")
        type_counts = self.count_by_type(relationships)
        for rel_type in RelationshipType:
            count = type_counts.get(rel_type.value, 0)
            lines.append(f"  {rel_type.value:<16}: {count}")
        lines.append("")

        # --- Incident category breakdown ---
        if incidents:
            lines.append("Incident category breakdown:")
            cat_counts = Counter(i.category for i in incidents)
            for cat, count in sorted(cat_counts.items()):
                lines.append(f"  {cat:<20}: {count}")
            lines.append("")

        # --- Disclaimer ---
        lines.append("-" * 50)
        lines.append(
            "Note: Statistics above describe only the mathematical\n"
            "structure of the supplied fictional graph data.\n"
            "They do not reflect real events or real people."
        )
        lines.append("=" * 50)

        return "\n".join(lines)
