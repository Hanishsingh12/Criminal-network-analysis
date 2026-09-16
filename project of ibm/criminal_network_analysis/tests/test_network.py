"""
tests/test_network.py
=====================
Unit tests for the NetworkManager class (network.py).

Tests cover:
  - Adding entities (happy path and error paths)
  - Searching entities
  - Adding incidents
  - Adding relationships (happy path and all error conditions)
  - Getting connections and filtering by type

All test data is fictional/synthetic.
"""

import pytest

from exceptions import (
    DuplicateRelationshipError,
    EmptyFieldError,
    EntityNotFoundError,
    IncidentLinkError,
    InvalidDateFormatError,
    InvalidRelationshipTypeError,
    SelfRelationshipError,
)
from models import RelationshipType
from network import NetworkManager, validate_date_format, validate_entity_type, validate_non_empty
from storage import DataStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    """A DataStore pointing at a temporary directory (no real files touched)."""
    return DataStore(data_dir=str(tmp_path))


@pytest.fixture
def nm(store):
    """A fresh, empty NetworkManager for each test."""
    return NetworkManager(store)


@pytest.fixture
def nm_with_entities(nm):
    """A NetworkManager pre-populated with two fictional entities."""
    nm.add_entity("Marcus Holloway", "Person", alias="The Broker")
    nm.add_entity("Elena Voss", "Person", alias="Ghost")
    return nm


# ---------------------------------------------------------------------------
# Validator function tests
# ---------------------------------------------------------------------------

class TestValidators:

    def test_validate_non_empty_raises_on_blank(self):
        with pytest.raises(EmptyFieldError):
            validate_non_empty("", "name")

    def test_validate_non_empty_raises_on_whitespace(self):
        with pytest.raises(EmptyFieldError):
            validate_non_empty("   ", "name")

    def test_validate_non_empty_passes_on_valid(self):
        validate_non_empty("Marcus", "name")  # should not raise

    def test_validate_entity_type_raises_on_invalid(self):
        with pytest.raises(ValueError):
            validate_entity_type("Criminal")

    def test_validate_entity_type_passes_on_person(self):
        validate_entity_type("Person")  # should not raise

    def test_validate_entity_type_passes_on_organization(self):
        validate_entity_type("Organization")  # should not raise

    def test_validate_date_format_raises_on_invalid(self):
        with pytest.raises(InvalidDateFormatError):
            validate_date_format("15-03-2024")

    def test_validate_date_format_raises_on_partial(self):
        with pytest.raises(InvalidDateFormatError):
            validate_date_format("2024/03/15")

    def test_validate_date_format_passes_on_valid(self):
        validate_date_format("2024-03-15")  # should not raise


# ---------------------------------------------------------------------------
# Entity tests
# ---------------------------------------------------------------------------

class TestAddEntity:

    def test_add_entity_returns_entity(self, nm):
        entity = nm.add_entity("Dante Reyes", "Person")
        assert entity.name == "Dante Reyes"
        assert entity.entity_type == "Person"
        assert entity.entity_id.startswith("E")

    def test_add_entity_id_is_unique(self, nm):
        e1 = nm.add_entity("Alice", "Person")
        e2 = nm.add_entity("Bob", "Person")
        assert e1.entity_id != e2.entity_id

    def test_add_entity_empty_name_raises(self, nm):
        with pytest.raises(EmptyFieldError):
            nm.add_entity("", "Person")

    def test_add_entity_whitespace_name_raises(self, nm):
        with pytest.raises(EmptyFieldError):
            nm.add_entity("   ", "Person")

    def test_add_entity_invalid_type_raises(self, nm):
        with pytest.raises(ValueError):
            nm.add_entity("Carlos", "Suspect")

    def test_get_all_entities_sorted(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        ids = [e.entity_id for e in entities]
        assert ids == sorted(ids)

    def test_get_entity_raises_if_missing(self, nm):
        with pytest.raises(EntityNotFoundError):
            nm.get_entity("E999")

    def test_search_entity_by_name(self, nm_with_entities):
        results = nm_with_entities.search_entity("elena")
        assert len(results) == 1
        assert results[0].name == "Elena Voss"

    def test_search_entity_by_alias(self, nm_with_entities):
        results = nm_with_entities.search_entity("ghost")
        assert len(results) == 1
        assert results[0].alias == "Ghost"

    def test_search_entity_by_id(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        first_id = entities[0].entity_id
        results = nm_with_entities.search_entity(first_id)
        assert any(e.entity_id == first_id for e in results)

    def test_search_entity_empty_query_returns_all(self, nm_with_entities):
        results = nm_with_entities.search_entity("")
        assert len(results) == 2

    def test_search_entity_no_match_returns_empty(self, nm_with_entities):
        results = nm_with_entities.search_entity("xyznotfound")
        assert results == []


# ---------------------------------------------------------------------------
# Incident tests
# ---------------------------------------------------------------------------

class TestAddIncident:

    def test_add_incident_happy_path(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        incident = nm_with_entities.add_incident(
            title="Operation Blackwall",
            category="Cybercrime",
            date="2024-03-15",
            linked_entity_ids=[entities[0].entity_id],
        )
        assert incident.incident_id.startswith("I")
        assert incident.title == "Operation Blackwall"

    def test_add_incident_no_entities_raises(self, nm_with_entities):
        with pytest.raises(IncidentLinkError):
            nm_with_entities.add_incident(
                title="Test",
                category="Fraud",
                date="2024-01-01",
                linked_entity_ids=[],
            )

    def test_add_incident_unknown_entity_raises(self, nm_with_entities):
        with pytest.raises(EntityNotFoundError):
            nm_with_entities.add_incident(
                title="Test",
                category="Fraud",
                date="2024-01-01",
                linked_entity_ids=["E999"],
            )

    def test_add_incident_bad_date_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        with pytest.raises(InvalidDateFormatError):
            nm_with_entities.add_incident(
                title="Test",
                category="Theft",
                date="01-01-2024",
                linked_entity_ids=[entities[0].entity_id],
            )

    def test_add_incident_empty_title_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        with pytest.raises(EmptyFieldError):
            nm_with_entities.add_incident(
                title="",
                category="Theft",
                date="2024-01-01",
                linked_entity_ids=[entities[0].entity_id],
            )


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------

class TestAddRelationship:

    def test_add_relationship_happy_path(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        rel = nm_with_entities.add_relationship(
            entities[0].entity_id, entities[1].entity_id, "Associate"
        )
        assert rel.relationship_id.startswith("R")
        assert rel.relationship_type == RelationshipType.ASSOCIATE

    def test_add_relationship_self_link_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        eid = entities[0].entity_id
        with pytest.raises(SelfRelationshipError):
            nm_with_entities.add_relationship(eid, eid, "Associate")

    def test_add_relationship_unknown_source_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        with pytest.raises(EntityNotFoundError):
            nm_with_entities.add_relationship("E999", entities[0].entity_id, "Financial")

    def test_add_relationship_unknown_target_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        with pytest.raises(EntityNotFoundError):
            nm_with_entities.add_relationship(entities[0].entity_id, "E999", "Financial")

    def test_add_relationship_duplicate_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        id1, id2 = entities[0].entity_id, entities[1].entity_id
        nm_with_entities.add_relationship(id1, id2, "Communication")
        with pytest.raises(DuplicateRelationshipError):
            nm_with_entities.add_relationship(id1, id2, "Communication")

    def test_add_relationship_different_type_allowed(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        id1, id2 = entities[0].entity_id, entities[1].entity_id
        nm_with_entities.add_relationship(id1, id2, "Associate")
        # Same pair, different type — should be allowed
        rel2 = nm_with_entities.add_relationship(id1, id2, "Financial")
        assert rel2.relationship_type == RelationshipType.FINANCIAL

    def test_add_relationship_invalid_type_raises(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        with pytest.raises(InvalidRelationshipTypeError):
            nm_with_entities.add_relationship(
                entities[0].entity_id, entities[1].entity_id, "Enemy"
            )

    def test_reverse_direction_is_allowed(self, nm_with_entities):
        """A→B and B→A are different directed edges and both should be accepted."""
        entities = nm_with_entities.get_all_entities()
        id1, id2 = entities[0].entity_id, entities[1].entity_id
        nm_with_entities.add_relationship(id1, id2, "Associate")
        rel_reverse = nm_with_entities.add_relationship(id2, id1, "Associate")
        assert rel_reverse.entity_id_1 == id2
        assert rel_reverse.entity_id_2 == id1


# ---------------------------------------------------------------------------
# Connection and filter tests
# ---------------------------------------------------------------------------

class TestConnections:

    def test_get_connections_returns_both_directions(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        id1, id2 = entities[0].entity_id, entities[1].entity_id
        nm_with_entities.add_relationship(id1, id2, "Associate")
        # Both entities should see the connection
        conns1 = nm_with_entities.get_connections(id1)
        conns2 = nm_with_entities.get_connections(id2)
        assert len(conns1) == 1
        assert len(conns2) == 1

    def test_get_connections_raises_for_unknown(self, nm):
        with pytest.raises(EntityNotFoundError):
            nm.get_connections("E999")

    def test_filter_by_type(self, nm_with_entities):
        entities = nm_with_entities.get_all_entities()
        id1, id2 = entities[0].entity_id, entities[1].entity_id
        nm_with_entities.add_relationship(id1, id2, "Financial")
        nm_with_entities.add_relationship(id2, id1, "Associate")

        financial = nm_with_entities.filter_by_type(RelationshipType.FINANCIAL)
        assert len(financial) == 1
        assert financial[0].relationship_type == RelationshipType.FINANCIAL
