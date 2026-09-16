"""
tests/test_storage.py
=====================
Unit tests for the DataStore class (storage.py).

Tests cover:
  - Loading from a non-existent file returns an empty list
  - Save + load round-trip for each collection
  - CSV export creates a valid file
  - load_sample_data loads the combined JSON correctly

All test data is fictional/synthetic.
"""

import csv
import json
import os

import pytest

from models import Entity, Incident, Relationship, RelationshipType
from storage import DataStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    """A DataStore that writes to a temporary directory."""
    return DataStore(data_dir=str(tmp_path))


@pytest.fixture
def sample_entity():
    return Entity(
        entity_id="E001",
        name="Marcus Holloway",
        entity_type="Person",
        alias="The Broker",
        notes="Fictional test entity",
    )


@pytest.fixture
def sample_incident(sample_entity):
    return Incident(
        incident_id="I001",
        title="Operation Blackwall",
        category="Cybercrime",
        date="2024-03-15",
        description="Fictional test incident",
        linked_entity_ids=[sample_entity.entity_id],
    )


@pytest.fixture
def sample_relationship():
    return Relationship(
        relationship_id="R001",
        entity_id_1="E001",
        entity_id_2="E002",
        relationship_type=RelationshipType.ASSOCIATE,
        notes="Fictional test relationship",
    )


# ---------------------------------------------------------------------------
# Load from missing files
# ---------------------------------------------------------------------------

class TestLoadMissingFiles:

    def test_load_entities_missing_file_returns_empty(self, store):
        result = store.load_entities()
        assert result == []

    def test_load_incidents_missing_file_returns_empty(self, store):
        result = store.load_incidents()
        assert result == []

    def test_load_relationships_missing_file_returns_empty(self, store):
        result = store.load_relationships()
        assert result == []


# ---------------------------------------------------------------------------
# Save and load round-trips
# ---------------------------------------------------------------------------

class TestEntityRoundTrip:

    def test_save_and_load_entity(self, store, sample_entity):
        store.save_entities([sample_entity])
        loaded = store.load_entities()
        assert len(loaded) == 1
        assert loaded[0].entity_id == sample_entity.entity_id
        assert loaded[0].name == sample_entity.name
        assert loaded[0].entity_type == sample_entity.entity_type
        assert loaded[0].alias == sample_entity.alias

    def test_save_multiple_entities(self, store):
        entities = [
            Entity("E001", "Alpha", "Person"),
            Entity("E002", "Beta", "Organization"),
        ]
        store.save_entities(entities)
        loaded = store.load_entities()
        assert len(loaded) == 2
        ids = [e.entity_id for e in loaded]
        assert "E001" in ids
        assert "E002" in ids

    def test_overwrite_entities(self, store, sample_entity):
        store.save_entities([sample_entity])
        new_entity = Entity("E002", "New Person", "Person")
        store.save_entities([new_entity])  # overwrite with just one entity
        loaded = store.load_entities()
        assert len(loaded) == 1
        assert loaded[0].entity_id == "E002"


class TestIncidentRoundTrip:

    def test_save_and_load_incident(self, store, sample_incident):
        store.save_incidents([sample_incident])
        loaded = store.load_incidents()
        assert len(loaded) == 1
        assert loaded[0].incident_id == sample_incident.incident_id
        assert loaded[0].title == sample_incident.title
        assert loaded[0].linked_entity_ids == sample_incident.linked_entity_ids

    def test_incident_linked_ids_preserved(self, store):
        incident = Incident(
            "I001", "Multi-Link", "Fraud", "2024-01-01",
            linked_entity_ids=["E001", "E002", "E003"]
        )
        store.save_incidents([incident])
        loaded = store.load_incidents()
        assert loaded[0].linked_entity_ids == ["E001", "E002", "E003"]


class TestRelationshipRoundTrip:

    def test_save_and_load_relationship(self, store, sample_relationship):
        store.save_relationships([sample_relationship])
        loaded = store.load_relationships()
        assert len(loaded) == 1
        assert loaded[0].relationship_id == sample_relationship.relationship_id
        assert loaded[0].relationship_type == RelationshipType.ASSOCIATE

    def test_all_relationship_types_preserved(self, store):
        rels = [
            Relationship("R001", "E001", "E002", RelationshipType.ASSOCIATE),
            Relationship("R002", "E002", "E003", RelationshipType.COMMUNICATION),
            Relationship("R003", "E003", "E004", RelationshipType.FINANCIAL),
            Relationship("R004", "E004", "E005", RelationshipType.OTHER),
        ]
        store.save_relationships(rels)
        loaded = store.load_relationships()
        types = {r.relationship_type for r in loaded}
        assert RelationshipType.ASSOCIATE in types
        assert RelationshipType.COMMUNICATION in types
        assert RelationshipType.FINANCIAL in types
        assert RelationshipType.OTHER in types


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

class TestCsvExport:

    def test_export_entities_csv_creates_file(self, store, sample_entity, tmp_path):
        store.save_entities([sample_entity])
        csv_path = str(tmp_path / "entities_export.csv")
        store.export_entities_csv(csv_path)
        assert os.path.exists(csv_path)

    def test_export_entities_csv_has_header(self, store, sample_entity, tmp_path):
        store.save_entities([sample_entity])
        csv_path = str(tmp_path / "entities_export.csv")
        store.export_entities_csv(csv_path)
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        assert "entity_id" in fieldnames
        assert "name" in fieldnames

    def test_export_entities_csv_contains_data(self, store, sample_entity, tmp_path):
        store.save_entities([sample_entity])
        csv_path = str(tmp_path / "entities_export.csv")
        store.export_entities_csv(csv_path)
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["entity_id"] == "E001"
        assert rows[0]["name"] == "Marcus Holloway"

    def test_export_relationships_csv_creates_file(self, store, sample_relationship, tmp_path):
        store.save_relationships([sample_relationship])
        csv_path = str(tmp_path / "relationships_export.csv")
        store.export_relationships_csv(csv_path)
        assert os.path.exists(csv_path)

    def test_export_entities_csv_no_file_when_empty(self, store, tmp_path):
        """No CSV file should be created when there is no data."""
        csv_path = str(tmp_path / "empty_export.csv")
        store.export_entities_csv(csv_path)
        assert not os.path.exists(csv_path)


# ---------------------------------------------------------------------------
# load_sample_data
# ---------------------------------------------------------------------------

class TestLoadSampleData:

    def test_load_sample_data_missing_file_returns_empty(self, store):
        result = store.load_sample_data("/nonexistent/path/sample.json")
        assert result["entities"] == []
        assert result["incidents"] == []
        assert result["relationships"] == []

    def test_load_sample_data_parses_correctly(self, store, tmp_path):
        sample = {
            "entities": [
                {"entity_id": "E001", "name": "Test Person",
                 "entity_type": "Person", "alias": "", "notes": ""}
            ],
            "incidents": [],
            "relationships": [],
        }
        sample_file = str(tmp_path / "sample.json")
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(sample, f)

        result = store.load_sample_data(sample_file)
        assert len(result["entities"]) == 1
        assert result["entities"][0].entity_id == "E001"
        assert result["entities"][0].name == "Test Person"
