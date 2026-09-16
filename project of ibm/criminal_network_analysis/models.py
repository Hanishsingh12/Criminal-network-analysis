"""
models.py
=========
Data models (dataclasses) for the Criminal Network Analysis System.

These classes are pure data containers — they only hold fields.
No business logic lives here.

All entity names and data are entirely fictional/synthetic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------

class RelationshipType(str, Enum):
    """The four allowed relationship types between entities."""
    ASSOCIATE = "Associate"
    COMMUNICATION = "Communication"
    FINANCIAL = "Financial"
    OTHER = "Other"

    @classmethod
    def from_string(cls, value: str) -> "RelationshipType":
        """
        Convert a plain string (e.g. 'associate' or 'Financial') to
        the matching enum member.  Case-insensitive.
        """
        normalised = value.strip().title()
        for member in cls:
            if member.value == normalised:
                return member
        allowed = ", ".join(m.value for m in cls)
        raise ValueError(
            f"'{value}' is not a valid relationship type. "
            f"Allowed values: {allowed}."
        )


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    """
    Represents a person or organisation in the network.

    entity_id   : unique identifier, e.g. "E001"
    name        : fictional display name
    entity_type : "Person" or "Organization"
    alias       : optional nickname
    notes       : free-text notes
    """
    entity_id: str
    name: str
    entity_type: str        # "Person" or "Organization"
    alias: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to a plain dictionary (used when saving to JSON)."""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "alias": self.alias,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict) -> "Entity":
        """Reconstruct an Entity from a plain dictionary (used when loading from JSON)."""
        return Entity(
            entity_id=data["entity_id"],
            name=data["name"],
            entity_type=data["entity_type"],
            alias=data.get("alias", ""),
            notes=data.get("notes", ""),
        )


@dataclass
class Incident:
    """
    Represents a crime or incident record.

    incident_id       : unique identifier, e.g. "I001"
    title             : short name of the incident
    category          : e.g. "Fraud", "Theft", "Cybercrime"
    date              : YYYY-MM-DD format
    description       : brief description
    linked_entity_ids : list of entity IDs involved in this incident
    """
    incident_id: str
    title: str
    category: str
    date: str
    description: str = ""
    linked_entity_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to a plain dictionary (used when saving to JSON)."""
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "category": self.category,
            "date": self.date,
            "description": self.description,
            "linked_entity_ids": self.linked_entity_ids,
        }

    @staticmethod
    def from_dict(data: dict) -> "Incident":
        """Reconstruct an Incident from a plain dictionary."""
        return Incident(
            incident_id=data["incident_id"],
            title=data["title"],
            category=data["category"],
            date=data["date"],
            description=data.get("description", ""),
            linked_entity_ids=data.get("linked_entity_ids", []),
        )


@dataclass
class Relationship:
    """
    Represents a directed link between two entities (A → B).

    relationship_id   : unique identifier, e.g. "R001"
    entity_id_1       : source entity (A in A → B)
    entity_id_2       : target entity (B in A → B)
    relationship_type : one of the RelationshipType enum values
    notes             : optional free-text description
    """
    relationship_id: str
    entity_id_1: str
    entity_id_2: str
    relationship_type: RelationshipType
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to a plain dictionary (used when saving to JSON)."""
        return {
            "relationship_id": self.relationship_id,
            "entity_id_1": self.entity_id_1,
            "entity_id_2": self.entity_id_2,
            "relationship_type": self.relationship_type.value,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict) -> "Relationship":
        """Reconstruct a Relationship from a plain dictionary."""
        return Relationship(
            relationship_id=data["relationship_id"],
            entity_id_1=data["entity_id_1"],
            entity_id_2=data["entity_id_2"],
            relationship_type=RelationshipType.from_string(data["relationship_type"]),
            notes=data.get("notes", ""),
        )
