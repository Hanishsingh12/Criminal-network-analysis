"""
app.py
======
Streamlit UI for the AI-Powered Criminal Network Analysis System.

Single-page app with sidebar navigation.
All business logic lives in network.py and analysis.py —
this file only handles display and user input.

DISCLAIMER: This system is for educational/demonstration purposes only.
All data used is entirely fictional/synthetic.
No real-person surveillance, profiling, or guilt assessment is performed.
"""

from __future__ import annotations

import os
import sys
import tempfile

import streamlit as st

# ---------------------------------------------------------------------------
# Path fix so Streamlit finds sibling modules when run from project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from analysis import Analyzer
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
from network import NetworkManager
from storage import DataStore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_data.json")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

INCIDENT_CATEGORIES = ["Cybercrime", "Fraud", "Money Laundering", "Theft", "Other"]
RELATIONSHIP_TYPE_OPTIONS = [t.value for t in RelationshipType]

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

def _init_session() -> None:
    """Create the NetworkManager once and store it in session_state."""
    if "nm" not in st.session_state:
        store = DataStore(data_dir=DATA_DIR)
        nm = NetworkManager(store)

        # If the data directory is empty, seed with sample data
        entities_file = os.path.join(DATA_DIR, "entities.json")
        if not os.path.exists(entities_file) or os.path.getsize(entities_file) < 5:
            nm.load_sample_data(SAMPLE_DATA_PATH)

        st.session_state["nm"] = nm
        st.session_state["analyzer"] = Analyzer()


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------

def _render_dashboard() -> None:
    st.header("🏠 Dashboard")
    st.caption(
        "**Educational demo only** · All data is entirely fictional/synthetic · "
        "No real-person profiling or surveillance"
    )
    st.markdown("---")

    nm: NetworkManager = st.session_state["nm"]
    entities = nm.get_all_entities()
    incidents = nm.get_all_incidents()
    relationships = nm.get_all_relationships()

    col1, col2, col3 = st.columns(3)
    col1.metric("Entities", len(entities))
    col2.metric("Incidents", len(incidents))
    col3.metric("Relationships", len(relationships))

    if entities:
        st.markdown("### Recent Entities")
        rows = [
            {"ID": e.entity_id, "Name": e.name, "Type": e.entity_type, "Alias": e.alias}
            for e in entities[-5:]
        ]
        st.table(rows)

    if incidents:
        st.markdown("### Recent Incidents")
        rows = [
            {"ID": i.incident_id, "Title": i.title, "Category": i.category, "Date": i.date}
            for i in incidents[-5:]
        ]
        st.table(rows)


def _render_add_entity() -> None:
    st.header("➕ Add Entity")
    st.caption("Enter fictional/synthetic data only.")

    with st.form("add_entity_form", clear_on_submit=True):
        name = st.text_input("Name *", placeholder="e.g. Alex Mercer")
        entity_type = st.selectbox("Type *", ["Person", "Organization"])
        alias = st.text_input("Alias (optional)", placeholder="e.g. The Fox")
        notes = st.text_area("Notes (optional)", placeholder="Free-text notes")
        submitted = st.form_submit_button("Add Entity")

    if submitted:
        nm: NetworkManager = st.session_state["nm"]
        try:
            entity = nm.add_entity(name, entity_type, alias, notes)
            st.success(f"✅ Entity **{entity.entity_id}** — *{entity.name}* added successfully.")
        except EmptyFieldError as exc:
            st.error(f"❌ {exc}")
        except ValueError as exc:
            st.error(f"❌ {exc}")


def _render_add_incident() -> None:
    st.header("🚨 Add Incident")
    st.caption("All incident data must be fictional/synthetic.")

    nm: NetworkManager = st.session_state["nm"]
    entities = nm.get_all_entities()

    if not entities:
        st.warning("⚠️ Add at least one entity before creating an incident.")
        return

    entity_options = {f"{e.entity_id} — {e.name}": e.entity_id for e in entities}

    with st.form("add_incident_form", clear_on_submit=True):
        title = st.text_input("Title *", placeholder="e.g. Operation Nightfall")
        category = st.selectbox("Category *", INCIDENT_CATEGORIES)
        date = st.date_input("Date *")
        description = st.text_area("Description (optional)")
        selected_labels = st.multiselect(
            "Linked Entities * (select at least one)", list(entity_options.keys())
        )
        submitted = st.form_submit_button("Add Incident")

    if submitted:
        linked_ids = [entity_options[lbl] for lbl in selected_labels]
        try:
            incident = nm.add_incident(
                title=title,
                category=category,
                date=str(date),
                description=description,
                linked_entity_ids=linked_ids,
            )
            st.success(
                f"✅ Incident **{incident.incident_id}** — *{incident.title}* added successfully."
            )
        except (EmptyFieldError, InvalidDateFormatError, IncidentLinkError, EntityNotFoundError) as exc:
            st.error(f"❌ {exc}")


def _render_add_relationship() -> None:
    st.header("🔗 Add Relationship")
    st.caption("A directed relationship: From Entity → To Entity.")

    nm: NetworkManager = st.session_state["nm"]
    entities = nm.get_all_entities()

    if len(entities) < 2:
        st.warning("⚠️ Add at least two entities before creating a relationship.")
        return

    entity_options = {f"{e.entity_id} — {e.name}": e.entity_id for e in entities}
    labels = list(entity_options.keys())

    with st.form("add_relationship_form", clear_on_submit=True):
        from_label = st.selectbox("From Entity (source →)", labels, key="rel_from")
        to_label = st.selectbox("To Entity (← target)", labels, key="rel_to")
        rel_type = st.selectbox("Relationship Type *", RELATIONSHIP_TYPE_OPTIONS)
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Add Relationship")

    if submitted:
        id1 = entity_options[from_label]
        id2 = entity_options[to_label]
        try:
            rel = nm.add_relationship(id1, id2, rel_type, notes)
            src = nm.get_entity(id1).name
            tgt = nm.get_entity(id2).name
            st.success(
                f"✅ Relationship **{rel.relationship_id}** added: "
                f"*{src}* → *{tgt}* [{rel_type}]"
            )
        except (
            EntityNotFoundError,
            SelfRelationshipError,
            DuplicateRelationshipError,
            InvalidRelationshipTypeError,
        ) as exc:
            st.error(f"❌ {exc}")


def _render_view_all() -> None:
    st.header("📋 View All Records")

    nm: NetworkManager = st.session_state["nm"]
    tab1, tab2, tab3 = st.tabs(["Entities", "Incidents", "Relationships"])

    with tab1:
        entities = nm.get_all_entities()
        if not entities:
            st.info("No entities yet.")
        else:
            st.dataframe(
                [e.to_dict() for e in entities],
                use_container_width=True,
            )

    with tab2:
        incidents = nm.get_all_incidents()
        if not incidents:
            st.info("No incidents yet.")
        else:
            rows = []
            for i in incidents:
                d = i.to_dict()
                d["linked_entity_ids"] = ", ".join(d["linked_entity_ids"])
                rows.append(d)
            st.dataframe(rows, use_container_width=True)

    with tab3:
        relationships = nm.get_all_relationships()
        if not relationships:
            st.info("No relationships yet.")
        else:
            st.dataframe(
                [r.to_dict() for r in relationships],
                use_container_width=True,
            )

        # Filter by type
        st.markdown("#### Filter by Relationship Type")
        filter_type = st.selectbox(
            "Select type to filter",
            ["All"] + RELATIONSHIP_TYPE_OPTIONS,
            key="filter_type_view",
        )
        if filter_type != "All":
            filtered = nm.filter_by_type(RelationshipType.from_string(filter_type))
            if not filtered:
                st.info(f"No '{filter_type}' relationships found.")
            else:
                st.dataframe([r.to_dict() for r in filtered], use_container_width=True)


def _render_search() -> None:
    st.header("🔍 Search & View Entity")

    nm: NetworkManager = st.session_state["nm"]
    query = st.text_input("Search by name, alias, or ID", placeholder="e.g. Marcus or E001")

    results = nm.search_entity(query) if query else nm.get_all_entities()

    if not results:
        st.warning("No entities found.")
        return

    st.markdown(f"**{len(results)} result(s) found**")
    labels = {f"{e.entity_id} — {e.name}": e.entity_id for e in results}
    chosen_label = st.selectbox("Select entity to inspect", list(labels.keys()))

    if chosen_label:
        eid = labels[chosen_label]
        entity = nm.get_entity(eid)

        st.markdown("#### Entity Details")
        col1, col2 = st.columns(2)
        col1.markdown(f"**ID:** {entity.entity_id}")
        col1.markdown(f"**Name:** {entity.name}")
        col1.markdown(f"**Type:** {entity.entity_type}")
        col2.markdown(f"**Alias:** {entity.alias or '—'}")
        col2.markdown(f"**Notes:** {entity.notes or '—'}")

        st.markdown("#### Direct Connections")
        connections = nm.get_connections(eid)
        if not connections:
            st.info("This entity has no connections.")
        else:
            rows = []
            for r in connections:
                direction = "→" if r.entity_id_1 == eid else "←"
                other_id = r.entity_id_2 if r.entity_id_1 == eid else r.entity_id_1
                try:
                    other_name = nm.get_entity(other_id).name
                except EntityNotFoundError:
                    other_name = other_id
                rows.append(
                    {
                        "Direction": direction,
                        "Other Entity": f"{other_id} — {other_name}",
                        "Type": r.relationship_type.value,
                        "Rel ID": r.relationship_id,
                        "Notes": r.notes,
                    }
                )
            st.dataframe(rows, use_container_width=True)
            st.caption(f"Total connections: **{len(connections)}**")


def _render_analysis() -> None:
    st.header("📊 Analysis")
    st.caption(
        "Statistics below describe only the mathematical structure of the "
        "supplied fictional graph data."
    )

    nm: NetworkManager = st.session_state["nm"]
    analyzer: Analyzer = st.session_state["analyzer"]

    entities_dict = {e.entity_id: e for e in nm.get_all_entities()}
    incidents = nm.get_all_incidents()
    relationships = nm.get_all_relationships()
    graph = nm.graph

    # --- Summary text ---
    st.markdown("### Network Summary")
    summary = analyzer.generate_summary(graph, entities_dict, incidents, relationships)
    st.text(summary)

    # --- Connection counts bar chart ---
    if entities_dict:
        st.markdown("### Connection Count per Entity")
        degree_map = analyzer.count_connections(graph)
        chart_data = {
            entities_dict[eid].name if eid in entities_dict else eid: deg
            for eid, deg in sorted(degree_map.items(), key=lambda x: -x[1])
        }
        st.bar_chart(chart_data)

    # --- Relationship type table ---
    if relationships:
        st.markdown("### Relationship Type Breakdown")
        type_counts = analyzer.count_by_type(relationships)
        table = [
            {"Type": t, "Count": type_counts.get(t, 0)}
            for t in RELATIONSHIP_TYPE_OPTIONS
        ]
        st.table(table)


def _render_network_graph() -> None:
    st.header("🕸️ Network Graph")
    st.caption("Interactive directed graph — drag nodes to rearrange.")

    nm: NetworkManager = st.session_state["nm"]
    entities = nm.get_all_entities()

    if not entities:
        st.info("Add entities and relationships to see the network graph.")
        return

    # Type filter
    filter_type = st.selectbox(
        "Filter by relationship type (graph)",
        ["All"] + RELATIONSHIP_TYPE_OPTIONS,
        key="graph_filter",
    )

    relationships = (
        nm.get_all_relationships()
        if filter_type == "All"
        else nm.filter_by_type(RelationshipType.from_string(filter_type))
    )

    # Build pyvis network
    try:
        from pyvis.network import Network as PyvisNetwork
    except ImportError:
        st.error("pyvis is not installed. Run: pip install pyvis")
        return

    net = PyvisNetwork(
        height="600px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#1a1a2e",
        font_color="#ffffff",
    )

    # Node colours
    node_colours = {"Person": "#4A90D9", "Organization": "#E67E22"}
    # Edge colours
    edge_colours = {
        "Associate": "#27AE60",
        "Communication": "#8E44AD",
        "Financial": "#E74C3C",
        "Other": "#95A5A6",
    }

    # Add nodes
    entity_ids_in_rels: set[str] = set()
    for r in relationships:
        entity_ids_in_rels.add(r.entity_id_1)
        entity_ids_in_rels.add(r.entity_id_2)

    # Always show all nodes; dim those not in current filter
    for entity in entities:
        colour = node_colours.get(entity.entity_type, "#cccccc")
        if entity_ids_in_rels and entity.entity_id not in entity_ids_in_rels:
            colour = "#555555"  # dim unconnected nodes in filtered view
        tooltip = (
            f"ID: {entity.entity_id}\n"
            f"Name: {entity.name}\n"
            f"Type: {entity.entity_type}\n"
            f"Alias: {entity.alias or '—'}"
        )
        net.add_node(
            entity.entity_id,
            label=entity.name,
            title=tooltip,
            color=colour,
            size=20,
        )

    # Add edges
    for rel in relationships:
        colour = edge_colours.get(rel.relationship_type.value, "#cccccc")
        net.add_edge(
            rel.entity_id_1,
            rel.entity_id_2,
            title=f"{rel.relationship_type.value}\n{rel.notes or ''}",
            color=colour,
            arrows="to",
            width=2,
        )

    # Physics options for a cleaner layout
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "springLength": 120
        },
        "stabilization": { "iterations": 200 }
      }
    }
    """)

    # Render to a temp HTML file and embed
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w", encoding="utf-8"
    ) as tmp:
        net.save_graph(tmp.name)
        html_content = open(tmp.name, encoding="utf-8").read()

    st.components.v1.html(html_content, height=630, scrolling=False)

    # Legend
    st.markdown(
        "**Legend** — "
        "🔵 Person &nbsp;|&nbsp; 🟠 Organization &nbsp;|&nbsp; "
        "🟢 Associate &nbsp;|&nbsp; 🟣 Communication &nbsp;|&nbsp; "
        "🔴 Financial &nbsp;|&nbsp; ⚫ Other"
    )


# ---------------------------------------------------------------------------
# CSV export helper (sidebar button)
# ---------------------------------------------------------------------------

def _sidebar_export() -> None:
    nm: NetworkManager = st.session_state["nm"]
    store: DataStore = nm._store

    if st.sidebar.button("⬇️ Export Entities CSV"):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", mode="w", encoding="utf-8"
        ) as tmp:
            store.export_entities_csv(tmp.name)
            csv_bytes = open(tmp.name, "rb").read()
        st.sidebar.download_button(
            "Download entities.csv", csv_bytes, "entities.csv", "text/csv"
        )

    if st.sidebar.button("⬇️ Export Relationships CSV"):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", mode="w", encoding="utf-8"
        ) as tmp:
            store.export_relationships_csv(tmp.name)
            csv_bytes = open(tmp.name, "rb").read()
        st.sidebar.download_button(
            "Download relationships.csv", csv_bytes, "relationships.csv", "text/csv"
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Criminal Network Analysis",
        page_icon="🕵️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session()

    # Sidebar navigation
    st.sidebar.title("🕵️ Network Analysis")
    st.sidebar.caption("Educational demo — fictional data only")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        [
            "🏠 Dashboard",
            "➕ Add Entity",
            "🚨 Add Incident",
            "🔗 Add Relationship",
            "📋 View All",
            "🔍 Search & View",
            "📊 Analysis",
            "🕸️ Network Graph",
        ],
    )

    st.sidebar.markdown("---")
    _sidebar_export()

    # Route to the correct page
    if page == "🏠 Dashboard":
        _render_dashboard()
    elif page == "➕ Add Entity":
        _render_add_entity()
    elif page == "🚨 Add Incident":
        _render_add_incident()
    elif page == "🔗 Add Relationship":
        _render_add_relationship()
    elif page == "📋 View All":
        _render_view_all()
    elif page == "🔍 Search & View":
        _render_search()
    elif page == "📊 Analysis":
        _render_analysis()
    elif page == "🕸️ Network Graph":
        _render_network_graph()


if __name__ == "__main__":
    main()
