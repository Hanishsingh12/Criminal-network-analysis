"""
storage.py
==========
Handles reading and writing data to JSON files, and exporting to CSV.

This layer is the only part of the system that touches the file system.
All other modules go through this class to load or save data.

All data stored and loaded here is fictional/synthetic.
"""

import csv
import json
import os
from typing import List

from models import Entity, Incident, Relationship


class DataStore:
    """
    Manages persistence for entities, incidents, and relationships.

    Data is stored as JSON files in the directory supplied at construction.
    A CSV export is also available for demo purposes.
    """

    ENTITIES_FILE = "entities.json"
    INCIDENTS_FILE = "incidents.json"
    RELATIONSHIPS_FILE = "relationships.json"

    def __init__(self, data_dir: str = "data") -> None:
        """
        Initialise the DataStore.

        data_dir : path to the folder where JSON files are kept.
                   The folder is created automatically if it does not exist.
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _path(self, filename: str) -> str:
        """Return the full path to a data file."""
        return os.path.join(self.data_dir, filename)

    def _load_json(self, filename: str) -> list:
        """
        Load a JSON file and return its contents as a list.
        Returns an empty list if the file does not exist.
        """
        filepath = self._path(filename)
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_json(self, filename: str, records: list) -> None:
        """Save a list of dictionaries to a JSON file (pretty-printed)."""
        filepath = self._path(filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Entity persistence
    # ------------------------------------------------------------------

    def load_entities(self) -> List[Entity]:
        """Load all entities from the JSON file."""
        return [Entity.from_dict(d) for d in self._load_json(self.ENTITIES_FILE)]

    def save_entities(self, entities: List[Entity]) -> None:
        """Save the full list of entities to the JSON file."""
        self._save_json(self.ENTITIES_FILE, [e.to_dict() for e in entities])

    # ------------------------------------------------------------------
    # Incident persistence
    # ------------------------------------------------------------------

    def load_incidents(self) -> List[Incident]:
        """Load all incidents from the JSON file."""
        return [Incident.from_dict(d) for d in self._load_json(self.INCIDENTS_FILE)]

    def save_incidents(self, incidents: List[Incident]) -> None:
        """Save the full list of incidents to the JSON file."""
        self._save_json(self.INCIDENTS_FILE, [i.to_dict() for i in incidents])

    # ------------------------------------------------------------------
    # Relationship persistence
    # ------------------------------------------------------------------

    def load_relationships(self) -> List[Relationship]:
        """Load all relationships from the JSON file."""
        return [Relationship.from_dict(d) for d in self._load_json(self.RELATIONSHIPS_FILE)]

    def save_relationships(self, relationships: List[Relationship]) -> None:
        """Save the full list of relationships to the JSON file."""
        self._save_json(self.RELATIONSHIPS_FILE, [r.to_dict() for r in relationships])

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def export_entities_csv(self, path: str) -> None:
        """Export all entity records to a CSV file at the given path."""
        entities = self.load_entities()
        if not entities:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=Entity.__dataclass_fields__.keys())
            writer.writeheader()
            writer.writerows(e.to_dict() for e in entities)

    def export_relationships_csv(self, path: str) -> None:
        """Export all relationship records to a CSV file at the given path."""
        relationships = self.load_relationships()
        if not relationships:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=Relationship.__dataclass_fields__.keys())
            writer.writeheader()
            writer.writerows(r.to_dict() for r in relationships)

    # ------------------------------------------------------------------
    # Bulk load (for seeding)
    # ------------------------------------------------------------------

    def load_sample_data(self, sample_path: str) -> dict:
        """
        Load all three collections from a single combined JSON file.
        Expected format:
            {
              "entities": [...],
              "incidents": [...],
              "relationships": [...]
            }
        Returns a dict with keys 'entities', 'incidents', 'relationships'.
        """
        if not os.path.exists(sample_path):
            return {"entities": [], "incidents": [], "relationships": []}
        with open(sample_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {
            "entities": [Entity.from_dict(d) for d in raw.get("entities", [])],
            "incidents": [Incident.from_dict(d) for d in raw.get("incidents", [])],
            "relationships": [Relationship.from_dict(d) for d in raw.get("relationships", [])],
        }
