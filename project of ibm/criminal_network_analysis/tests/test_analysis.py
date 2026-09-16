"""
tests/test_analysis.py
======================
Unit tests for the Analyzer class (analysis.py).

Tests cover:
  - count_connections
  - get_most_connected
  - get_isolated_entities
  - group_by_type and count_by_type
  - generate_summary (empty and populated networks)

All test data is fictional/synthetic.
"""

import networkx as nx
import pytest

from analysis import Analyzer
from models import Entity, Incident, Relationship, RelationshipType
from network import NetworkManager
from storage import DataStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer():
    return Analyzer()


@pytest.fixture
def store(tmp_path):
    return DataStore(data_dir=str(tmp_path))


@pytest.fixture
def nm(store):
    return NetworkManager(store)


@pytest.fixture
def populated_nm(nm):
    """NetworkManager with 3 entities and 2 relationships."""
    e1 = nm.add_entity("Marcus Holloway", "Person", alias="The Broker")
    e2 = nm.add_entity("Elena Voss", "Person", alias="Ghost")
    e3 = nm.add_entity("Nexus Trading Ltd", "Organization", alias="Nexus")
    nm.add_relationship(e1.entity_id, e2.entity_id, "Associate")
    nm.add_relationship(e2.entity_id, e3.entity_id, "Financial")
    return nm


# ---------------------------------------------------------------------------
# count_connections
# ---------------------------------------------------------------------------

class TestCountConnections:

    def test_empty_graph_returns_empty_dict(self, analyzer):
        g = nx.DiGraph()
        result = analyzer.count_connections(g)
        assert result == {}

    def test_counts_correct_degrees(self, analyzer, populated_nm):
        """
        Graph: E001 → E002 → E003
        E001 degree=1, E002 degree=2 (one in, one out), E003 degree=1
        """
        degrees = analyzer.count_connections(populated_nm.graph)
        entities = populated_nm.get_all_entities()
        id1 = entities[0].entity_id  # E001
        id2 = entities[1].entity_id  # E002
        id3 = entities[2].entity_id  # E003

        assert degrees[id2] == 2   # most connected (in + out)
        assert degrees[id1] == 1
        assert degrees[id3] == 1

    def test_isolated_node_has_degree_zero(self, analyzer, nm):
        nm.add_entity("Lone Wolf", "Person")
        degrees = analyzer.count_connections(nm.graph)
        assert list(degrees.values())[0] == 0


# ---------------------------------------------------------------------------
# get_most_connected
# ---------------------------------------------------------------------------

class TestMostConnected:

    def test_returns_none_on_empty(self, analyzer):
        g = nx.DiGraph()
        result = analyzer.get_most_connected(g, {})
        assert result is None

    def test_returns_most_connected_entity(self, analyzer, populated_nm):
        entities_dict = {e.entity_id: e for e in populated_nm.get_all_entities()}
        top = analyzer.get_most_connected(populated_nm.graph, entities_dict)
        # E002 (Elena Voss) has degree 2 — highest
        assert top is not None
        assert top.name == "Elena Voss"


# ---------------------------------------------------------------------------
# get_isolated_entities
# ---------------------------------------------------------------------------

class TestIsolatedEntities:

    def test_no_isolated_in_fully_connected(self, analyzer, populated_nm):
        entities_dict = {e.entity_id: e for e in populated_nm.get_all_entities()}
        isolated = analyzer.get_isolated_entities(populated_nm.graph, entities_dict)
        assert isolated == []

    def test_detects_isolated_entity(self, analyzer, nm):
        nm.add_entity("Lone Wolf", "Person")
        nm.add_entity("Connected One", "Person")
        entities = nm.get_all_entities()
        nm.add_relationship(entities[0].entity_id, entities[1].entity_id, "Associate")
        # Add a third entity with no connections
        lone = nm.add_entity("No Connections", "Person")
        entities_dict = {e.entity_id: e for e in nm.get_all_entities()}
        isolated = analyzer.get_isolated_entities(nm.graph, entities_dict)
        isolated_ids = [e.entity_id for e in isolated]
        assert lone.entity_id in isolated_ids


# ---------------------------------------------------------------------------
# group_by_type and count_by_type
# ---------------------------------------------------------------------------

class TestGroupByType:

    def test_group_by_type_all_keys_present(self, analyzer):
        result = analyzer.group_by_type([])
        for t in RelationshipType:
            assert t.value in result

    def test_group_by_type_correct_grouping(self, analyzer, populated_nm):
        relationships = populated_nm.get_all_relationships()
        groups = analyzer.group_by_type(relationships)
        assert len(groups["Associate"]) == 1
        assert len(groups["Financial"]) == 1
        assert len(groups["Communication"]) == 0

    def test_count_by_type(self, analyzer, populated_nm):
        relationships = populated_nm.get_all_relationships()
        counts = analyzer.count_by_type(relationships)
        assert counts.get("Associate") == 1
        assert counts.get("Financial") == 1
        assert counts.get("Communication", 0) == 0


# ---------------------------------------------------------------------------
# generate_summary
# ---------------------------------------------------------------------------

class TestGenerateSummary:

    def test_empty_network_returns_empty_message(self, analyzer):
        g = nx.DiGraph()
        summary = analyzer.generate_summary(g, {}, [], [])
        assert "empty" in summary.lower()

    def test_summary_contains_entity_count(self, analyzer, populated_nm):
        entities_dict = {e.entity_id: e for e in populated_nm.get_all_entities()}
        incidents = populated_nm.get_all_incidents()
        relationships = populated_nm.get_all_relationships()
        summary = analyzer.generate_summary(
            populated_nm.graph, entities_dict, incidents, relationships
        )
        assert "3" in summary   # 3 entities
        assert "2" in summary   # 2 relationships

    def test_summary_contains_disclaimer(self, analyzer, populated_nm):
        entities_dict = {e.entity_id: e for e in populated_nm.get_all_entities()}
        summary = analyzer.generate_summary(
            populated_nm.graph, entities_dict, [], populated_nm.get_all_relationships()
        )
        assert "fictional" in summary.lower() or "note" in summary.lower()

    def test_summary_mentions_most_connected(self, analyzer, populated_nm):
        entities_dict = {e.entity_id: e for e in populated_nm.get_all_entities()}
        summary = analyzer.generate_summary(
            populated_nm.graph, entities_dict, [], populated_nm.get_all_relationships()
        )
        assert "Elena Voss" in summary
