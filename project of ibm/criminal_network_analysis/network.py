"""
network.py
==========
The core business-logic class: NetworkManager.

NetworkManager is the single source of truth for all data in memory.
It handles:
  - Adding, finding, and searching entities
  - Adding incidents
  - Adding and filtering relationships
  - Keeping a networkx DiGraph in sync with the relationships list
  - Calling the validator before every mutation
  - Calling DataStore to persist every change

All data is fictional/synthetic for educational purposes only.
No real-person profiling, surveillance, or guilt assessment is performed.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import networkx as nx

from exceptions import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    EmptyFieldError,
    EntityNotFoundError,
    IncidentLinkError,
    InvalidDateFormatError,
    InvalidRelationshipTypeError,
    SelfRelationshipError,
)
from models import Entity, Incident, Relationship, RelationshipType
from storage import DataStore


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

ALLOWED_ENTITY_TYPES = {"Person", "Organization"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Validator helpers  (pure functions — no side-effects, easy to unit-test)
# ---------------------------------------------------------------------------

def validate_non_empty(value: str, field_name: str) -> None:
    """Raise EmptyFieldError if value is blank or whitespace-only."""
    if not value or not value.strip():
        raise EmptyFieldError(f"'{field_name}' must not be empty.")


def validate_entity_type(value: str) -> None:
    """Raise ValueError if entity_type is not 'Person' or 'Organization'."""
    if value not in ALLOWED_ENTITY_TYPES:
        raise ValueError(
            f"entity_type must be 'Person' or 'Organization', got '{value}'."
        )


def validate_date_format(date_str: str) -> None:
    """Raise InvalidDateFormatError if date_str is not YYYY-MM-DD."""
    if not DATE_PATTERN.match(date_str):
        raise InvalidDateFormatError(
            f"Date '{date_str}' is not in YYYY-MM-DD format."
        )


# ---------------------------------------------------------------------------
# NetworkManager
# ---------------------------------------------------------------------------

class NetworkManager:
    """
    The central class that manages all network data.

    Think of this as the detective's case-board:
      - Entities  = sticky notes (people / organisations)
      - Incidents = crime reports pinned to the board
      - Relationships = strings connecting sticky notes

    The internal networkx DiGraph mirrors the relationships list so that
    graph statistics can be computed at any time.
    """

    def __init__(self, store: DataStore) -> None:
        """
        Initialise the NetworkManager.

        store : a DataStore instance used for persistence.
        All three collections are loaded from storage immediately.
        """
        self._store = store

        # In-memory collections
        self._entities: Dict[str, Entity] = {}
        self._incidents: List[Incident] = []
        self._relationships: List[Relationship] = []

        # Directed graph (nodes = entity IDs, edges = relationships)
        self._graph: nx.DiGraph = nx.DiGraph()

        # Load existing data from storage
        self._load_from_store()

    # ------------------------------------------------------------------
    # Private: load from storage
    # ------------------------------------------------------------------

    def _load_from_store(self) -> None:
        """Load all three collections from the DataStore into memory."""
        for entity in self._store.load_entities():
            self._entities[entity.entity_id] = entity
            self._graph.add_node(entity.entity_id)

        self._incidents = self._store.load_incidents()

        for rel in self._store.load_relationships():
            self._relationships.append(rel)
            self._graph.add_edge(
                rel.entity_id_1,
                rel.entity_id_2,
                relationship_id=rel.relationship_id,
                relationship_type=rel.relationship_type.value,
            )

    # ------------------------------------------------------------------
    # Private: ID generators
    # ------------------------------------------------------------------

    def _next_entity_id(self) -> str:
        """Return the next available entity ID, e.g. 'E003'."""
        n = len(self._entities) + 1
        candidate = f"E{n:03d}"
        # Make sure the candidate is not already taken (handles gaps)
        existing = set(self._entities.keys())
        while candidate in existing:
            n += 1
            candidate = f"E{n:03d}"
        return candidate

    def _next_incident_id(self) -> str:
        """Return the next available incident ID, e.g. 'I003'."""
        n = len(self._incidents) + 1
        existing = {i.incident_id for i in self._incidents}
        candidate = f"I{n:03d}"
        while candidate in existing:
            n += 1
            candidate = f"I{n:03d}"
        return candidate

    def _next_relationship_id(self) -> str:
        """Return the next available relationship ID, e.g. 'R003'."""
        n = len(self._relationships) + 1
        existing = {r.relationship_id for r in self._relationships}
        candidate = f"R{n:03d}"
        while candidate in existing:
            n += 1
            candidate = f"R{n:03d}"
        return candidate

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------

    def add_entity(
        self,
        name: str,
        entity_type: str,
        alias: str = "",
        notes: str = "",
    ) -> Entity:
        """
        Add a new entity to the network.

        Validates input, assigns an auto-generated ID, persists to storage.
        Returns the created Entity.
        """
        validate_non_empty(name, "name")
        validate_entity_type(entity_type)

        entity_id = self._next_entity_id()
        entity = Entity(
            entity_id=entity_id,
            name=name.strip(),
            entity_type=entity_type,
            alias=alias.strip(),
            notes=notes.strip(),
        )
        self._entities[entity_id] = entity
        self._graph.add_node(entity_id)
        self._store.save_entities(list(self._entities.values()))
        return entity

    def get_all_entities(self) -> List[Entity]:
        """Return all entities as a list, sorted by entity_id."""
        return sorted(self._entities.values(), key=lambda e: e.entity_id)

    def get_entity(self, entity_id: str) -> Entity:
        """Return a single entity by ID. Raises EntityNotFoundError if missing."""
        if entity_id not in self._entities:
            raise EntityNotFoundError(
                f"Entity '{entity_id}' does not exist in the network."
            )
        return self._entities[entity_id]

    def search_entity(self, query: str) -> List[Entity]:
        """
        Search entities by name, alias, or entity_id.
        The search is case-insensitive. Returns all matching entities.
        """
        q = query.strip().lower()
        if not q:
            return self.get_all_entities()
        return [
            e for e in self._entities.values()
            if q in e.name.lower()
            or q in e.alias.lower()
            or q in e.entity_id.lower()
        ]

    # ------------------------------------------------------------------
    # Incident operations
    # ------------------------------------------------------------------

    def add_incident(
        self,
        title: str,
        category: str,
        date: str,
        description: str = "",
        linked_entity_ids: Optional[List[str]] = None,
    ) -> Incident:
        """
        Add a new incident record.

        linked_entity_ids must contain at least one valid entity ID.
        """
        validate_non_empty(title, "title")
        validate_non_empty(category, "category")
        validate_non_empty(date, "date")
        validate_date_format(date)

        linked = linked_entity_ids or []
        if not linked:
            raise IncidentLinkError(
                "An incident must be linked to at least one entity."
            )
        for eid in linked:
            if eid not in self._entities:
                raise EntityNotFoundError(
                    f"Cannot link incident to unknown entity '{eid}'."
                )

        incident_id = self._next_incident_id()
        incident = Incident(
            incident_id=incident_id,
            title=title.strip(),
            category=category.strip(),
            date=date.strip(),
            description=description.strip(),
            linked_entity_ids=linked,
        )
        self._incidents.append(incident)
        self._store.save_incidents(self._incidents)
        return incident

    def get_all_incidents(self) -> List[Incident]:
        """Return all incidents, sorted by incident_id."""
        return sorted(self._incidents, key=lambda i: i.incident_id)

    # ------------------------------------------------------------------
    # Relationship operations
    # ------------------------------------------------------------------

    def add_relationship(
        self,
        entity_id_1: str,
        entity_id_2: str,
        relationship_type_str: str,
        notes: str = "",
    ) -> Relationship:
        """
        Add a directed relationship from entity_id_1 → entity_id_2.

        Validates:
          - Both entities must exist
          - A→B is not the same as A→A (no self-links)
          - The exact same directed relationship must not already exist
          - relationship_type_str must be a valid RelationshipType
        """
        # Entity existence
        if entity_id_1 not in self._entities:
            raise EntityNotFoundError(
                f"Source entity '{entity_id_1}' does not exist."
            )
        if entity_id_2 not in self._entities:
            raise EntityNotFoundError(
                f"Target entity '{entity_id_2}' does not exist."
            )

        # No self-relationships
        if entity_id_1 == entity_id_2:
            raise SelfRelationshipError(
                "An entity cannot have a relationship with itself."
            )

        # Relationship type validation
        try:
            rel_type = RelationshipType.from_string(relationship_type_str)
        except ValueError as exc:
            raise InvalidRelationshipTypeError(str(exc)) from exc

        # Duplicate check (same direction, same type)
        for existing in self._relationships:
            if (
                existing.entity_id_1 == entity_id_1
                and existing.entity_id_2 == entity_id_2
                and existing.relationship_type == rel_type
            ):
                raise DuplicateRelationshipError(
                    f"A '{rel_type.value}' relationship from "
                    f"'{entity_id_1}' to '{entity_id_2}' already exists."
                )

        relationship_id = self._next_relationship_id()
        rel = Relationship(
            relationship_id=relationship_id,
            entity_id_1=entity_id_1,
            entity_id_2=entity_id_2,
            relationship_type=rel_type,
            notes=notes.strip(),
        )
        self._relationships.append(rel)
        self._graph.add_edge(
            entity_id_1,
            entity_id_2,
            relationship_id=relationship_id,
            relationship_type=rel_type.value,
        )
        self._store.save_relationships(self._relationships)
        return rel

    def get_all_relationships(self) -> List[Relationship]:
        """Return all relationships, sorted by relationship_id."""
        return sorted(self._relationships, key=lambda r: r.relationship_id)

    def get_connections(self, entity_id: str) -> List[Relationship]:
        """
        Return all relationships where the entity is the source (→) or
        the target (←).  Raises EntityNotFoundError if the entity is unknown.
        """
        if entity_id not in self._entities:
            raise EntityNotFoundError(
                f"Entity '{entity_id}' does not exist."
            )
        return [
            r for r in self._relationships
            if r.entity_id_1 == entity_id or r.entity_id_2 == entity_id
        ]

    def filter_by_type(self, rel_type: RelationshipType) -> List[Relationship]:
        """Return only the relationships of the given type."""
        return [r for r in self._relationships if r.relationship_type == rel_type]

    # ------------------------------------------------------------------
    # Graph access
    # ------------------------------------------------------------------

    @property
    def graph(self) -> nx.DiGraph:
        """Read-only access to the underlying networkx DiGraph."""
        return self._graph

    # ------------------------------------------------------------------
    # Seed data loader
    # ------------------------------------------------------------------

    def load_sample_data(self, sample_path: str) -> None:
        """
        Populate the network from a combined sample JSON file.
        Skips records that would violate uniqueness constraints.
        """
        data = self._store.load_sample_data(sample_path)

        for entity in data["entities"]:
            if entity.entity_id not in self._entities:
                self._entities[entity.entity_id] = entity
                self._graph.add_node(entity.entity_id)

        for incident in data["incidents"]:
            existing_ids = {i.incident_id for i in self._incidents}
            if incident.incident_id not in existing_ids:
                self._incidents.append(incident)

        for rel in data["relationships"]:
            existing_ids = {r.relationship_id for r in self._relationships}
            if rel.relationship_id not in existing_ids:
                self._relationships.append(rel)
                if self._graph.has_node(rel.entity_id_1) and self._graph.has_node(rel.entity_id_2):
                    self._graph.add_edge(
                        rel.entity_id_1,
                        rel.entity_id_2,
                        relationship_id=rel.relationship_id,
                        relationship_type=rel.relationship_type.value,
                    )

        # Persist all loaded data
        self._store.save_entities(list(self._entities.values()))
        self._store.save_incidents(self._incidents)
        self._store.save_relationships(self._relationships)
