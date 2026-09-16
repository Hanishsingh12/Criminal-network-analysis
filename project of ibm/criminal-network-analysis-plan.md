# AI-Powered Criminal Network Analysis System — Implementation Plan

## Purpose

Build a small, beginner-friendly, educational Python application that lets an analyst
manage fictional criminal network data, visualise entity relationships as a directed graph,
and generate a plain-language analytical summary.

All data is synthetic/fictional.
No real-person surveillance, predictive profiling, facial recognition, biometric identification,
or automated guilt assessment is included.

---

## Confirmed Design Decisions

| Decision | Choice |
|---|---|
| Persistence | JSON primary store + CSV export option |
| UI layout | Single-page Streamlit app with sidebar radio navigation |
| Graph direction | Directed — A→B and B→A are distinct relationships |
| ID generation | System auto-generates IDs: E001, E002 / I001, I002 / R001, R002 |
| Graph visualisation | pyvis interactive HTML embedded via st.components.v1.html |

---

## Project Architecture — Layer Overview

```
criminal_network/
│
├── models/              # Data layer — pure data containers (dataclasses)
│   ├── __init__.py
│   ├── entity.py
│   ├── incident.py
│   └── relationship.py
│
├── storage/             # Storage layer — read/write JSON and CSV
│   ├── __init__.py
│   └── data_store.py
│
├── business/            # Business/Analysis layer — rules, graph, analytics
│   ├── __init__.py
│   ├── network_manager.py
│   ├── analyzer.py
│   └── validator.py
│
├── ui/                  # Streamlit UI layer
│   ├── __init__.py
│   └── app.py
│
├── exceptions/          # Custom exceptions
│   ├── __init__.py
│   └── errors.py
│
├── tests/               # pytest unit tests
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_validator.py
│   ├── test_network_manager.py
│   ├── test_analyzer.py
│   └── test_data_store.py
│
├── data/                # Runtime data files (gitignored in real projects)
│   ├── entities.json
│   ├── incidents.json
│   └── relationships.json
│
├── requirements.txt
└── README.md
```

---

## Folder and File Responsibilities

| File | Responsibility |
|---|---|
| `models/entity.py` | Entity dataclass — fields only, no logic |
| `models/incident.py` | Incident dataclass — fields only |
| `models/relationship.py` | Relationship dataclass + RelationshipType enum |
| `storage/data_store.py` | Load and save all three collections to/from JSON; CSV export |
| `business/validator.py` | All input validation functions — raises custom exceptions |
| `business/network_manager.py` | In-memory store; CRUD operations; wraps networkx DiGraph |
| `business/analyzer.py` | Graph statistics, connection counts, summary generation |
| `ui/app.py` | All Streamlit pages — reads/writes via NetworkManager only |
| `exceptions/errors.py` | All custom exception classes |
| `tests/` | One test file per source module |

---

## Sub-Task 1 — Custom Exceptions

**Status:** [ ] pending

### Intent
Define all custom exception classes in one place so every other module can import and
raise them without circular imports. Doing this first means every subsequent module can
reference real exception names from the start.

### Expected Outcomes
- `exceptions/errors.py` exists with all exception classes defined
- Every exception has a meaningful docstring
- No other module is needed to complete this task

### Todo List
1. Create `exceptions/__init__.py` (empty or re-exports)
2. Create `exceptions/errors.py` with the following classes:
   - `EntityNotFoundError` — raised when an entity ID does not exist
   - `DuplicateEntityError` — raised when an entity ID is already taken
   - `DuplicateRelationshipError` — raised when the exact same directed relationship exists
   - `InvalidRelationshipTypeError` — raised when relationship type is not in the allowed enum
   - `SelfRelationshipError` — raised when entity_id_1 == entity_id_2
   - `InvalidDateFormatError` — raised when a date string does not match YYYY-MM-DD
   - `EmptyFieldError` — raised when a required field is blank or whitespace-only
   - `IncidentLinkError` — raised when an incident has no linked entity IDs

### Relevant Context
- No dependencies on other modules
- All other modules import from this file

---

## Sub-Task 2 — Data Models

**Status:** [ ] pending

### Intent
Define the three core dataclasses (Entity, Incident, Relationship) and the
RelationshipType enum. These are pure data containers — no business logic lives here.
Using Python dataclasses keeps field definitions concise and readable for beginners.

### Expected Outcomes
- `models/entity.py`, `models/incident.py`, `models/relationship.py` all created
- `RelationshipType` enum defined with four values
- All fields have type hints and default values where appropriate
- Dataclasses support conversion to/from plain dictionaries (for JSON serialisation)

### Todo List
1. Create `models/__init__.py`
2. Create `models/relationship.py` first (needed by other models for type hints):
   - Define `RelationshipType` enum: `ASSOCIATE`, `COMMUNICATION`, `FINANCIAL`, `OTHER`
   - Define `Relationship` dataclass with fields listed in the Data Fields section below
3. Create `models/entity.py`:
   - Define `Entity` dataclass with fields listed below
   - Add `to_dict()` and `from_dict()` class/static methods
4. Create `models/incident.py`:
   - Define `Incident` dataclass with fields listed below
   - Add `to_dict()` and `from_dict()` class/static methods
5. Add `to_dict()` and `from_dict()` to `Relationship` dataclass

### Data Fields

#### Entity
| Field | Type | Notes |
|---|---|---|
| `entity_id` | `str` | Auto-generated, e.g. "E001" |
| `name` | `str` | Fictional name, max 100 chars |
| `entity_type` | `str` | "Person" or "Organization" |
| `alias` | `str` | Optional nickname, default "" |
| `notes` | `str` | Free-text notes, default "" |

#### Incident
| Field | Type | Notes |
|---|---|---|
| `incident_id` | `str` | Auto-generated, e.g. "I001" |
| `title` | `str` | Short incident name |
| `category` | `str` | e.g. "Fraud", "Theft", "Cybercrime" |
| `date` | `str` | YYYY-MM-DD format |
| `description` | `str` | Brief description, default "" |
| `linked_entity_ids` | `list[str]` | At least one valid entity ID |

#### Relationship
| Field | Type | Notes |
|---|---|---|
| `relationship_id` | `str` | Auto-generated, e.g. "R001" |
| `entity_id_1` | `str` | Source entity ID (A in A→B) |
| `entity_id_2` | `str` | Target entity ID (B in A→B) |
| `relationship_type` | `RelationshipType` | Enum value |
| `notes` | `str` | Optional description, default "" |

### Relevant Context
- `to_dict()` converts the dataclass to a plain Python dict for JSON storage
- `from_dict()` reconstructs the dataclass from a plain dict when loading from JSON
- `linked_entity_ids` is stored as a JSON array

---

## Sub-Task 3 — Validator Module

**Status:** [ ] pending

### Intent
Centralise all input-checking logic in one module. Every validation function either
returns silently (input is valid) or raises a specific custom exception. This keeps
business logic and UI code free of repetitive if/else checks.

### Expected Outcomes
- `business/validator.py` contains all validation functions
- Each function has type hints and a docstring
- Every custom exception from Sub-Task 1 is exercised by at least one validator

### Todo List
1. Create `business/__init__.py`
2. Create `business/validator.py` with the following functions:

| Function | What it validates |
|---|---|
| `validate_non_empty(value, field_name)` | Raises `EmptyFieldError` if blank/whitespace |
| `validate_entity_type(value)` | Must be "Person" or "Organization" |
| `validate_relationship_type(value)` | Must map to a valid `RelationshipType` enum member; normalise to title case first |
| `validate_date_format(date_str)` | Must match YYYY-MM-DD; raises `InvalidDateFormatError` |
| `validate_entity_exists(entity_id, entities_dict)` | Raises `EntityNotFoundError` if ID missing |
| `validate_no_duplicate_entity(entity_id, entities_dict)` | Raises `DuplicateEntityError` if ID present |
| `validate_no_self_relationship(id1, id2)` | Raises `SelfRelationshipError` if equal |
| `validate_no_duplicate_relationship(id1, id2, rel_type, relationships_list)` | Raises `DuplicateRelationshipError` |
| `validate_incident_links(linked_ids, entities_dict)` | Raises `IncidentLinkError` if empty; raises `EntityNotFoundError` for any missing ID |

### Relevant Context
- All functions are pure (no side effects) — easy to unit-test
- UI layer catches exceptions and displays `st.error(str(e))`
- NetworkManager calls validators before mutating state

---

## Sub-Task 4 — Storage Layer

**Status:** [ ] pending

### Intent
Provide a single module that reads and writes all three data collections to JSON files.
Also provides a CSV export function for demo purposes. Isolating storage here means
the business layer never directly touches files.

### Expected Outcomes
- `storage/data_store.py` created
- `data/` directory structure documented (created at runtime if missing)
- JSON round-trip (save then load) produces identical objects
- CSV export produces one row per entity/relationship

### Todo List
1. Create `storage/__init__.py`
2. Create `storage/data_store.py` with the following:

#### DataStore class
| Method | Behaviour |
|---|---|
| `__init__(data_dir: str)` | Stores the path to the data directory; creates it if missing |
| `load_entities() -> list[Entity]` | Reads `entities.json`; returns empty list if file missing |
| `save_entities(entities: list[Entity])` | Writes all entities to `entities.json` |
| `load_incidents() -> list[Incident]` | Reads `incidents.json`; returns empty list if file missing |
| `save_incidents(incidents: list[Incident])` | Writes all incidents to `incidents.json` |
| `load_relationships() -> list[Relationship]` | Reads `relationships.json`; returns empty list if file missing |
| `save_relationships(rels: list[Relationship])` | Writes all relationships to `relationships.json` |
| `export_entities_csv(path: str)` | Writes entities to a CSV file at the given path |
| `export_relationships_csv(path: str)` | Writes relationships to a CSV file at the given path |

3. JSON format: each file is a JSON array of objects — one object per record
4. Use `to_dict()` / `from_dict()` from the model dataclasses for serialisation

### Relevant Context
- `data/` folder path is passed in at construction — makes testing easy (use a temp dir)
- NetworkManager instantiates DataStore and calls it on load/save

---

## Sub-Task 5 — NetworkManager

**Status:** [ ] pending

### Intent
The central business-logic class. Holds the three in-memory collections (entities,
incidents, relationships) and the networkx DiGraph. All CRUD operations go through here.
It calls the Validator before mutating state, then updates the DiGraph to stay in sync,
then calls DataStore to persist.

### Expected Outcomes
- `business/network_manager.py` created
- All CRUD operations validate, mutate, sync graph, and persist
- ID auto-generation logic encapsulated here
- DiGraph always mirrors the relationships list

### Todo List
1. Create `business/network_manager.py`
2. Define `NetworkManager` class with:

#### Initialisation
- Accepts a `DataStore` instance
- Loads all three collections from storage on construction
- Builds a `networkx.DiGraph` from the loaded relationships

#### ID Generation (private helpers)
| Helper | Logic |
|---|---|
| `_next_entity_id()` | Scans existing IDs, returns next "E{n:03d}" |
| `_next_incident_id()` | Returns next "I{n:03d}" |
| `_next_relationship_id()` | Returns next "R{n:03d}" |

#### Entity Operations
| Method | Behaviour |
|---|---|
| `add_entity(name, entity_type, alias, notes) -> Entity` | Validates, assigns ID, adds to dict, saves |
| `get_all_entities() -> list[Entity]` | Returns all entities as a list |
| `search_entity(query: str) -> list[Entity]` | Case-insensitive match on name, alias, or entity_id |
| `get_entity(entity_id: str) -> Entity` | Returns one entity or raises `EntityNotFoundError` |

#### Incident Operations
| Method | Behaviour |
|---|---|
| `add_incident(title, category, date, description, linked_entity_ids) -> Incident` | Validates all fields, saves |
| `get_all_incidents() -> list[Incident]` | Returns all incidents |

#### Relationship Operations
| Method | Behaviour |
|---|---|
| `add_relationship(id1, id2, rel_type_str, notes) -> Relationship` | Validates, converts type string to enum, adds directed edge to DiGraph, saves |
| `get_all_relationships() -> list[Relationship]` | Returns all relationships |
| `get_connections(entity_id: str) -> list[Relationship]` | Returns relationships where entity_id is id_1 or id_2 |
| `filter_by_type(rel_type: RelationshipType) -> list[Relationship]` | Returns relationships of that type only |

### Relevant Context
- `entities` stored internally as `dict[str, Entity]` — keyed by entity_id for O(1) lookup
- `incidents` stored as `list[Incident]`
- `relationships` stored as `list[Relationship]`
- `graph` is `networkx.DiGraph`; nodes = entity_ids, edge attributes hold relationship_type and relationship_id

---

## Sub-Task 6 — Analyzer

**Status:** [ ] pending

### Intent
Provide all read-only graph analysis. Takes a NetworkManager (or its DiGraph and data
collections) and computes statistics and a plain-language summary. No mutation of data.

### Expected Outcomes
- `business/analyzer.py` created
- All methods are read-only
- Summary text is plain English suitable for display in Streamlit

### Todo List
1. Create `business/analyzer.py`
2. Define `Analyzer` class:

| Method | What it returns |
|---|---|
| `count_connections(graph) -> dict[str, int]` | Maps each entity_id to its total degree (in + out) |
| `get_most_connected(graph, entities) -> Entity or None` | Entity with highest degree; None if empty |
| `get_isolated_entities(graph, entities) -> list[Entity]` | Entities with degree 0 |
| `group_by_type(relationships) -> dict[str, list[Relationship]]` | Groups relationships by RelationshipType name |
| `get_in_degree(graph) -> dict[str, int]` | Number of incoming edges per node |
| `get_out_degree(graph) -> dict[str, int]` | Number of outgoing edges per node |
| `generate_summary(graph, entities, incidents, relationships) -> str` | Returns multi-line plain-text summary |

#### Summary Contents
The `generate_summary()` output must include:
- Total entity count
- Total incident count
- Total relationship count
- Most connected entity name and degree
- List of isolated entities (if any)
- Relationship type breakdown (count per type)
- Note: "Statistics describe the graph structure of supplied fictional data only."

### Relevant Context
- Uses `networkx.DiGraph` passed in from NetworkManager
- No file I/O; no mutation
- Output is a plain string — Streamlit displays it with `st.text()` or `st.markdown()`

---

## Sub-Task 7 — Visualizer (pyvis graph)

**Status:** [ ] pending

### Intent
Build the pyvis interactive graph HTML from the NetworkManager's DiGraph and return it
as an HTML string that Streamlit embeds with `st.components.v1.html()`.

### Expected Outcomes
- `business/visualizer.py` created
- Nodes are colour-coded by entity_type (Person vs Organization)
- Edges are colour-coded by relationship_type
- Hovering a node shows entity name and alias
- Graph is directed (arrows on edges)
- Returns raw HTML string — no file writes needed

### Todo List
1. Create `business/visualizer.py`
2. Define `Visualizer` class with one main method:

| Method | Behaviour |
|---|---|
| `build_html(graph, entities, relationships) -> str` | Constructs a pyvis Network, adds nodes and edges, returns HTML string |

#### Node styling
| entity_type | colour |
|---|---|
| Person | `#4A90D9` (blue) |
| Organization | `#E67E22` (orange) |

#### Edge styling
| relationship_type | colour |
|---|---|
| ASSOCIATE | `#27AE60` (green) |
| COMMUNICATION | `#8E44AD` (purple) |
| FINANCIAL | `#E74C3C` (red) |
| OTHER | `#95A5A6` (grey) |

3. If graph has no nodes, return a simple HTML string with a friendly message

### Relevant Context
- pyvis `Network(directed=True)` is used
- `notebook=False`, `height="600px"`, `width="100%"` for Streamlit embedding
- Tooltip (title) on each node: "Name: X | Type: Y | Alias: Z"

---

## Sub-Task 8 — Streamlit UI

**Status:** [ ] pending

### Intent
Build the single-page Streamlit app. The sidebar radio button selects which section
is active. Each section reads from and writes to NetworkManager. The UI layer never
directly touches storage or validator — it only calls NetworkManager methods and
catches exceptions to display `st.error()` messages.

### Expected Outcomes
- `ui/app.py` runs with `streamlit run ui/app.py`
- All seven sections are functional
- Form submissions use `st.form` to avoid re-runs on every keystroke
- Error messages appear inline without crashing the app

### Sidebar Sections

| Section Label | What it shows |
|---|---|
| 🏠 Dashboard | App title, total counts, quick-stats strip |
| ➕ Add Entity | Form to add entity; success confirmation |
| 🚨 Add Incident | Form to add incident with multi-select for linked entities |
| 🔗 Add Relationship | Form to select two entities, pick direction and type |
| 🔍 Search & View | Search box + entity detail card + connections list |
| 📊 Analysis | Summary text block + bar chart of connection counts |
| 🕸️ Network Graph | pyvis graph embedded full-width + type filter dropdown |

### Todo List
1. Create `ui/__init__.py`
2. Create `ui/app.py`
3. Initialise `DataStore` and `NetworkManager` using `st.session_state` so data persists across reruns
4. Build the sidebar radio selector
5. Implement each section as a private function `_render_*()` called by the main router
6. Add a CSV export button (Downloads entities + relationships as zip or separate files)
7. Load synthetic seed data on first run (see Sub-Task 10)

### Section Design Details

#### Add Entity form fields
- Name (text input, required)
- Type (selectbox: Person / Organization)
- Alias (text input, optional)
- Notes (text area, optional)

#### Add Incident form fields
- Title (text input, required)
- Category (selectbox: Fraud / Theft / Cybercrime / Money Laundering / Other)
- Date (date input)
- Description (text area, optional)
- Linked Entities (multi-select from all current entities)

#### Add Relationship form fields
- From Entity (selectbox, entity_id + name)
- To Entity (selectbox, entity_id + name)
- Relationship Type (selectbox: Associate / Communication / Financial / Other)
- Notes (text input, optional)

#### Search & View section
- Text input searches name, alias, and entity_id
- Results shown in a table
- Clicking (selecting) an entity shows its detail card and connections table

#### Analysis section
- `st.markdown(summary_text)`
- `st.bar_chart` of connection counts per entity
- Relationship type breakdown as a small table

#### Network Graph section
- Dropdown to filter by relationship type (or "All")
- `st.components.v1.html(pyvis_html, height=620, scrolling=False)`

### Relevant Context
- `st.session_state["network_manager"]` holds the single NetworkManager instance
- Re-instantiation on each rerun is avoided by checking `"network_manager" in st.session_state`

---

## Sub-Task 9 — Unit Tests

**Status:** [ ] pending

### Intent
Write pytest tests covering models, validator, network_manager, analyzer, and data_store.
Tests use only synthetic/fictional data. No real file system is touched — use `tmp_path`
pytest fixture for storage tests.

### Expected Outcomes
- All tests pass with `pytest tests/`
- Each module has its own test file
- Happy-path and error-path cases both covered
- No test depends on another test's state (isolated fixtures)

### Todo List
1. Create `tests/__init__.py`
2. Create `tests/test_models.py`:
   - Test `to_dict()` / `from_dict()` round-trip for each model
   - Test `RelationshipType` enum values
3. Create `tests/test_validator.py`:
   - Test each validator function with valid input (no exception)
   - Test each validator function with invalid input (correct exception raised)
4. Create `tests/test_network_manager.py`:
   - Test `add_entity()` happy path
   - Test `add_entity()` duplicate ID raises `DuplicateEntityError`
   - Test `add_relationship()` with non-existent entity raises `EntityNotFoundError`
   - Test `add_relationship()` self-link raises `SelfRelationshipError`
   - Test `add_relationship()` duplicate raises `DuplicateRelationshipError`
   - Test `search_entity()` returns correct results
   - Test `get_connections()` returns correct subset
   - Test `filter_by_type()` returns correct subset
5. Create `tests/test_analyzer.py`:
   - Test `count_connections()` on a known graph
   - Test `get_most_connected()` returns correct entity
   - Test `get_isolated_entities()` correctly identifies degree-0 nodes
   - Test `generate_summary()` on empty network returns "empty" message
6. Create `tests/test_data_store.py`:
   - Test save + load round-trip for each collection using `tmp_path`
   - Test load returns empty list when file does not exist
   - Test CSV export creates a valid file

### Relevant Context
- Use `pytest.raises(ExceptionType)` for exception tests
- Use `@pytest.fixture` to create a pre-populated NetworkManager for reuse across tests

---

## Sub-Task 10 — Synthetic Seed Data and README

**Status:** [ ] pending

### Intent
Provide realistic-looking but entirely fictional seed data that loads automatically
on first run, so the app is never empty during a demo. Also write a README for
first-year students.

### Expected Outcomes
- `data/entities.json`, `data/incidents.json`, `data/relationships.json` contain seed records
- App displays pre-populated data on first launch
- `README.md` explains setup and usage in simple terms

### Synthetic Seed Data

#### Entities (8 records)
| ID | Name | Type | Alias |
|---|---|---|---|
| E001 | Marcus Holloway | Person | "The Broker" |
| E002 | Elena Voss | Person | "Ghost" |
| E003 | Dante Reyes | Person | "Cipher" |
| E004 | Nexus Trading Ltd | Organization | "Nexus" |
| E005 | Ivan Petrov | Person | "Shadow" |
| E006 | Lyra Chen | Person | — |
| E007 | Irongate Logistics | Organization | "Irongate" |
| E008 | Sofia Navarro | Person | "Viper" |

#### Incidents (5 records)
| ID | Title | Category | Date |
|---|---|---|---|
| I001 | Operation Blackwall | Cybercrime | 2024-03-15 |
| I002 | Meridian Bank Fraud | Fraud | 2024-05-22 |
| I003 | Port Cargo Theft | Theft | 2024-07-08 |
| I004 | Shell Company Scheme | Money Laundering | 2024-09-01 |
| I005 | Dark Web Exchange | Cybercrime | 2024-11-14 |

#### Relationships (10 directed edges)
| From | To | Type |
|---|---|---|
| E001 | E002 | ASSOCIATE |
| E001 | E004 | FINANCIAL |
| E002 | E003 | COMMUNICATION |
| E003 | E005 | ASSOCIATE |
| E004 | E007 | FINANCIAL |
| E005 | E001 | COMMUNICATION |
| E006 | E004 | FINANCIAL |
| E007 | E008 | ASSOCIATE |
| E008 | E002 | COMMUNICATION |
| E003 | E004 | FINANCIAL |

### README Sections
1. What this project does (one paragraph)
2. Technology stack (bullet list)
3. How to install dependencies (`pip install -r requirements.txt`)
4. How to run the app (`streamlit run ui/app.py`)
5. How to run tests (`pytest tests/`)
6. Disclaimer: educational/demo purposes only, all data is fictional

### Relevant Context
- Seed data is written as static JSON files committed to the repo
- NetworkManager checks if data files are non-empty before loading; skips seed if data already exists

---

## Module Communication Diagram

```
ui/app.py
    |
    |--calls--> NetworkManager (add, get, search, filter)
    |               |
    |               |--calls--> Validator (raises exceptions)
    |               |--calls--> DataStore (load / save JSON)
    |               |--owns---> networkx.DiGraph (kept in sync)
    |
    |--calls--> Analyzer (read-only stats and summary)
    |               |
    |               |--reads--> DiGraph + entity/relationship lists
    |
    |--calls--> Visualizer (builds pyvis HTML)
                    |
                    |--reads--> DiGraph + entity/relationship lists
```

---

## Data Flow for "Add Relationship"

1. User fills form in `ui/app.py` and clicks Submit
2. `ui/app.py` calls `network_manager.add_relationship(id1, id2, type_str, notes)`
3. `NetworkManager` calls `validator.validate_no_self_relationship(id1, id2)`
4. `NetworkManager` calls `validator.validate_entity_exists(id1, ...)` and `(id2, ...)`
5. `NetworkManager` calls `validator.validate_relationship_type(type_str)`
6. `NetworkManager` calls `validator.validate_no_duplicate_relationship(...)`
7. `NetworkManager` creates `Relationship` dataclass, appends to list, adds edge to DiGraph
8. `NetworkManager` calls `data_store.save_relationships(self.relationships)`
9. Returns `Relationship` to UI
10. UI displays `st.success("Relationship R007 added.")`

If any validator raises an exception, step 2 propagates it to the UI, which shows `st.error(str(e))`.

---

## Technology Stack Summary

| Technology | Purpose |
|---|---|
| Python 3.11+ | Core language |
| dataclasses | Data model definitions |
| enum | RelationshipType values |
| networkx | DiGraph — graph operations and statistics |
| pyvis | Interactive HTML graph rendering |
| streamlit | Web UI |
| pytest | Unit testing |
| json (stdlib) | Primary data persistence |
| csv (stdlib) | Export |
| re (stdlib) | Date format validation |

```
# requirements.txt
streamlit
networkx
pyvis
pytest
```

---

## Status Summary

| Sub-Task | Description | Status |
|---|---|---|
| 1 | Custom Exceptions | [ ] pending |
| 2 | Data Models | [ ] pending |
| 3 | Validator Module | [ ] pending |
| 4 | Storage Layer | [ ] pending |
| 5 | NetworkManager | [ ] pending |
| 6 | Analyzer | [ ] pending |
| 7 | Visualizer | [ ] pending |
| 8 | Streamlit UI | [ ] pending |
| 9 | Unit Tests | [ ] pending |
| 10 | Seed Data and README | [ ] pending |
