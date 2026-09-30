# Repository State: AI Shuttle POC

**Document Purpose**: Project Resource capturing the current, actual implementation state of the AI Shuttle repository as of September 30, 2026. This document records what actually exists in code, tests, and configuration today, distinct from planned architectural roadmaps.

---

## 1. Repository Structure

Below is the directory tree of the repository (3–4 levels deep), excluding version control (`.git`), virtual environments (`.venv`), byte-cache (`__pycache__`), build outputs, environment secret files (`.env`), and OS metadata:

```
.
├── .env.example
├── .gitignore
├── AIShuttle
│   ├── AIShuttle
│   │   ├── AIShuttleApp.swift
│   │   ├── Assets.xcassets
│   │   │   ├── AccentColor.colorset
│   │   │   ├── AppIcon.appiconset
│   │   │   └── Contents.json
│   │   └── ContentView.swift
│   ├── AIShuttle.xcodeproj
│   │   ├── project.pbxproj
│   │   └── project.xcworkspace
│   │       ├── contents.xcworkspacedata
│   │       └── xcshareddata
│   ├── AIShuttleTests
│   │   └── AIShuttleTests.swift
│   └── AIShuttleUITests
│       ├── AIShuttleUITests.swift
│       └── AIShuttleUITestsLaunchTests.swift
├── README.md
├── backend
│   ├── .env.example
│   ├── app
│   │   ├── __init__.py
│   │   ├── agent
│   │   │   └── __init__.py
│   │   ├── api
│   │   │   └── __init__.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   └── config.py
│   │   ├── db
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── database.py
│   │   │   ├── init_db.py
│   │   │   └── seed.py
│   │   ├── graph
│   │   │   └── __init__.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── booking.py
│   │   │   ├── child.py
│   │   │   ├── preference.py
│   │   │   ├── route.py
│   │   │   ├── shuttle.py
│   │   │   └── user.py
│   │   ├── repositories
│   │   │   ├── __init__.py
│   │   │   ├── booking_repository.py
│   │   │   ├── preference_repository.py
│   │   │   ├── shuttle_repository.py
│   │   │   └── user_repository.py
│   │   ├── schemas
│   │   │   └── __init__.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   └── booking_service.py
│   │   └── tools
│   │       ├── __init__.py
│   │       └── booking_tools.py
│   ├── test_booking_service.py
│   └── tests
│       ├── conftest.py
│       └── test_booking_tools.py
└── docker-compose.yml
```

---

## 2. Git State

- **Current Branch**: `main`
- **Current Commit SHA**: `1c36e68a4ef0222e280781097b61e3a892b61431` (short: `1c36e68`)
- **Current Commit Message**: `feat: add deterministic shuttle booking flow`
- **Working Tree Status**: Clean (ahead of `origin/main` by 1 commit)
- **Recent Commit History (all commits to date)**:
  1. `1c36e68` - `feat: add deterministic shuttle booking flow`
  2. `b32611c` - `feat: initialize backend project structure with FastAPI application and health check endpoint`
  3. `c45245b` - `chore: add environment configuration`
  4. `c8d18cd` - `feat: initialize AIShuttle SwiftUI project structure and configuration`
  5. `db07698` - `Initial commit`

---

## 3. Python/Backend Dependencies

### Dependency Declaration Files
- **Status**: No manifest file (`requirements.txt`, `pyproject.toml`, `Pipfile`, or `poetry.lock`) is currently tracked in source control.
- **Runtime Environment**: Dependencies are installed in the local virtual environment `backend/.venv`.
- **Python Version**: `3.14.7`

### Installed Packages & Versions (Active Virtual Environment)
| Package | Installed Version | Primary Role |
| :--- | :--- | :--- |
| `fastapi` | `0.141.1` | Web framework |
| `uvicorn` | `0.54.0` | ASGI server |
| `starlette` | `1.7.0` | ASGI toolkit underpinning FastAPI |
| `pydantic` | `2.13.5` | Data validation and settings management |
| `pydantic-settings` | `2.15.0` | Environment configuration loading |
| `SQLAlchemy` | `2.1.1` | SQL toolkit and Object Relational Mapper |
| `psycopg` / `psycopg-binary` | `3.3.6` | PostgreSQL database adapter |
| `python-dotenv` | `1.2.3` | Reading key-value pairs from `.env` |
| `pytest` | `9.1.1` | Test framework |
| `pytest-asyncio` | `1.4.0` | Pytest support for asyncio |
| `httpx` | `0.28.1` | HTTP client (test client support) |

> **Note**: LangGraph, LangChain, or LLM-provider SDKs are **not yet installed** in the virtual environment.

### Application Configuration Files
- [backend/app/core/config.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/core/config.py): Defines the `Settings` class using `pydantic_settings.BaseSettings`, parsing `DATABASE_URL` and `APP_ENV` from `.env`.
- [backend/.env.example](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/.env.example): Backend environment template defining `DATABASE_URL=` and `APP_ENV=development`.
- [.env.example](file:///Users/godwinjoel.j/Projects/ai-shuttle/.env.example): Root template specifying `API_BASE_URL=http://localhost:8000`.
- [docker-compose.yml](file:///Users/godwinjoel.j/Projects/ai-shuttle/docker-compose.yml): Docker compose configuration running PostgreSQL 17 image (`postgres:17`) exposing port 5432.

---

## 4. Current Architecture

The architecture currently implemented adheres to the following layered status:

| Architectural Layer | Implementation Status | Current Code / Notes |
| :--- | :--- | :--- |
| **API** | **PARTIALLY IMPLEMENTED** | [backend/app/main.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/main.py) exposes `GET /health`. `backend/app/api/` contains only an empty `__init__.py`. |
| **Agent** | **NOT YET IMPLEMENTED** | `backend/app/agent/__init__.py` is empty. No agent logic or state machines exist. |
| **Graph** | **NOT YET IMPLEMENTED** | `backend/app/graph/__init__.py` is empty. LangGraph is not yet integrated. |
| **Tools** | **IMPLEMENTED** | [backend/app/tools/booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/tools/booking_tools.py) provides `book_shuttle(db, user_id, booking_date)`. |
| **Services** | **IMPLEMENTED** | [backend/app/services/booking_service.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/services/booking_service.py) encapsulates booking validation and creation logic. |
| **Repositories** | **IMPLEMENTED** | `backend/app/repositories/` contains four repositories isolating all database queries (`UserRepository`, `PreferenceRepository`, `ShuttleRepository`, `BookingRepository`). |
| **Models** | **IMPLEMENTED** | `backend/app/models/` contains six SQLAlchemy 2.0 mapped models (`User`, `Child`, `Preference`, `Route`, `Shuttle`, `Booking`). |
| **Schemas** | **NOT YET IMPLEMENTED** | `backend/app/schemas/__init__.py` is empty. No Pydantic request/response schemas exist yet. |
| **Database** | **IMPLEMENTED** | [backend/app/db/database.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/database.py) sets up the engine and `SessionLocal`; `backend/app/db/init_db.py` creates tables; `backend/app/db/seed.py` seeds sample records into PostgreSQL. |
| **Core/Configuration** | **IMPLEMENTED** | [backend/app/core/config.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/core/config.py) provides strongly typed configuration settings. |

---

## 5. Implemented Files

### Backend Source Files

- [backend/app/main.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/main.py)
  - **Layer**: API
  - **Purpose**: Creates the FastAPI application instance (`title="AI Shuttle API"`, `version="0.1.0"`) and defines the `/health` endpoint.
- [backend/app/core/config.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/core/config.py)
  - **Layer**: Core / Configuration
  - **Purpose**: Loads application configuration (`database_url`, `app_env`) via Pydantic `BaseSettings` reading `.env`.
- [backend/app/db/base.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/base.py)
  - **Layer**: Database
  - **Purpose**: Declares SQLAlchemy's declarative base class (`class Base(DeclarativeBase)`).
- [backend/app/db/database.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/database.py)
  - **Layer**: Database
  - **Purpose**: Initializes the SQLAlchemy `engine` with `pool_pre_ping=True`, creates `SessionLocal`, and defines the `get_db()` dependency generator.
- [backend/app/db/init_db.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/init_db.py) and [backend/app/db/__init__.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/__init__.py)
  - **Layer**: Database
  - **Purpose**: Provides `init_db()` which executes `Base.metadata.create_all(bind=engine)` to create all tables in PostgreSQL.
- [backend/app/db/seed.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/seed.py)
  - **Layer**: Database
  - **Purpose**: Populates the database with initial demonstration records: user ("Godwin Joel"), child ("Emma"), routes ("Morning Route", "Afternoon Route"), shuttles ("Morning Shuttle A/B", "Afternoon Shuttle A"), and user preference.
- [backend/app/models/user.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/user.py)
  - **Layer**: Models
  - **Purpose**: SQLAlchemy ORM model for table `users`.
- [backend/app/models/child.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/child.py)
  - **Layer**: Models
  - **Purpose**: SQLAlchemy ORM model for table `children`.
- [backend/app/models/preference.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/preference.py)
  - **Layer**: Models
  - **Purpose**: SQLAlchemy ORM model for table `preferences` linking user to default shuttle.
- [backend/app/models/route.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/route.py)
  - **Layer**: Models
  - **Purpose**: SQLAlchemy ORM model for table `routes`.
- [backend/app/models/shuttle.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/shuttle.py)
  - **Layer**: Models
  - **Purpose**: SQLAlchemy ORM model for table `shuttles` with schedule and capacity details.
- [backend/app/models/booking.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/booking.py)
  - **Layer**: Models
  - **Purpose**: SQLAlchemy ORM model for table `bookings`.
- [backend/app/repositories/user_repository.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/repositories/user_repository.py)
  - **Layer**: Repositories
  - **Purpose**: Encapsulates database read access for `User` (`get_by_id`).
- [backend/app/repositories/preference_repository.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/repositories/preference_repository.py)
  - **Layer**: Repositories
  - **Purpose**: Encapsulates database read access for `Preference` (`get_by_user_id`).
- [backend/app/repositories/shuttle_repository.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/repositories/shuttle_repository.py)
  - **Layer**: Repositories
  - **Purpose**: Encapsulates database queries for `Shuttle` (`get_by_id`) and capacity checks (`has_available_seat`).
- [backend/app/repositories/booking_repository.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/repositories/booking_repository.py)
  - **Layer**: Repositories
  - **Purpose**: Encapsulates database persistence for `Booking` (`create`, `get_by_id`).
- [backend/app/services/booking_service.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/services/booking_service.py)
  - **Layer**: Services
  - **Purpose**: Orchestrates booking business logic: user resolution, child resolution, preference check, shuttle availability validation, booking entity creation, and persistence commit.
- [backend/app/tools/booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/tools/booking_tools.py)
  - **Layer**: Tools
  - **Purpose**: Provides the callable `book_shuttle` tool function that wires repositories into `BookingService` and executes `book_usual_shuttle`.

### Test Files & Test Scripts
- [backend/tests/conftest.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/tests/conftest.py)
  - **Purpose**: Configures `sys.path` so tests can import the `app` package.
- [backend/tests/test_booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/tests/test_booking_tools.py)
  - **Purpose**: Automated pytest integration test validating end-to-end booking persistence through `book_shuttle`.
- [backend/test_booking_service.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/test_booking_service.py)
  - **Purpose**: Standalone manual smoke script executing `BookingService.book_usual_shuttle` for User 1 and printing output.

### iOS Client Files
- [AIShuttle/AIShuttle/AIShuttleApp.swift](file:///Users/godwinjoel.j/Projects/ai-shuttle/AIShuttle/AIShuttle/AIShuttleApp.swift): Initial SwiftUI App entry point.
- [AIShuttle/AIShuttle/ContentView.swift](file:///Users/godwinjoel.j/Projects/ai-shuttle/AIShuttle/AIShuttle/ContentView.swift): Default SwiftUI starter view ("Hello, world!").

---

## 6. Database

All models inherit from `app.db.base.Base` using SQLAlchemy 2.0 `Mapped` and `mapped_column` syntax.

### Models and Tables

#### 1. `users` (`User`)
- **Fields**:
  - `id`: `Mapped[int]`, Primary Key
  - `name`: `Mapped[str]`, `String(100)`, nullable=False
  - `email`: `Mapped[str]`, `String(255)`, unique=True, nullable=False
- **Relationships**:
  - `children`: 1-to-Many with `Child` (`back_populates="user"`)
  - `preferences`: 1-to-1 with `Preference` (`back_populates="user"`, `uselist=False`)
  - `bookings`: 1-to-Many with `Booking` (`back_populates="user"`)

#### 2. `children` (`Child`)
- **Fields**:
  - `id`: `Mapped[int]`, Primary Key
  - `user_id`: `Mapped[int]`, Foreign Key (`users.id`), nullable=False
  - `name`: `Mapped[str]`, `String(100)`, nullable=False
  - `school`: `Mapped[str]`, `String(255)`, nullable=False
  - `usual_pickup_location`: `Mapped[str]`, `String(255)`, nullable=False
- **Relationships**:
  - `user`: Many-to-1 with `User` (`back_populates="children"`)
  - `bookings`: 1-to-Many with `Booking` (`back_populates="child"`)

#### 3. `preferences` (`Preference`)
- **Fields**:
  - `id`: `Mapped[int]`, Primary Key
  - `user_id`: `Mapped[int]`, Foreign Key (`users.id`), unique=True, nullable=False
  - `usual_shuttle_id`: `Mapped[int | None]`, Foreign Key (`shuttles.id`), nullable=True
- **Relationships**:
  - `user`: 1-to-1 with `User` (`back_populates="preferences"`)
  - `usual_shuttle`: Many-to-1 with `Shuttle` (`back_populates="preferred_by"`)

#### 4. `routes` (`Route`)
- **Fields**:
  - `id`: `Mapped[int]`, Primary Key
  - `name`: `Mapped[str]`, `String(255)`, nullable=False
  - `pickup_location`: `Mapped[str]`, `String(255)`, nullable=False
  - `dropoff_location`: `Mapped[str]`, `String(255)`, nullable=False
- **Relationships**:
  - `shuttles`: 1-to-Many with `Shuttle` (`back_populates="route"`)

#### 5. `shuttles` (`Shuttle`)
- **Fields**:
  - `id`: `Mapped[int]`, Primary Key
  - `name`: `Mapped[str]`, `String(100)`, nullable=False
  - `route_id`: `Mapped[int]`, Foreign Key (`routes.id`), nullable=False
  - `departure_time`: `Mapped[time]`, nullable=False
  - `arrival_time`: `Mapped[time]`, nullable=False
  - `capacity`: `Mapped[int]`, nullable=False
- **Relationships**:
  - `route`: Many-to-1 with `Route` (`back_populates="shuttles"`)
  - `preferred_by`: 1-to-Many with `Preference` (`back_populates="usual_shuttle"`)
  - `bookings`: 1-to-Many with `Booking` (`back_populates="shuttle"`)

#### 6. `bookings` (`Booking`)
- **Fields**:
  - `id`: `Mapped[int]`, Primary Key
  - `user_id`: `Mapped[int]`, Foreign Key (`users.id`), nullable=False
  - `child_id`: `Mapped[int]`, Foreign Key (`children.id`), nullable=False
  - `shuttle_id`: `Mapped[int]`, Foreign Key (`shuttles.id`), nullable=False
  - `booking_date`: `Mapped[date]`, `Date`, nullable=False
  - `pickup_time`: `Mapped[time]`, `Time`, nullable=False
  - `status`: `Mapped[str]`, `String(50)`, nullable=False, default="confirmed"
- **Relationships**:
  - `user`: Many-to-1 with `User` (`back_populates="bookings"`)
  - `child`: Many-to-1 with `Child` (`back_populates="bookings"`)
  - `shuttle`: Many-to-1 with `Shuttle` (`back_populates="bookings"`)

### Entity Relationship Structure

```
+------------+       1 : N       +--------------+
|   users    |-------------------|   children   |
+------------+                   +--------------+
  |        |                       |
  | 1:1    | 1:N                   | 1:N
  v        v                       v
+------------+                   +--------------+
|preferences |                   |   bookings   |
+------------+                   +--------------+
  |                                ^
  | N:1                            | N:1
  v                                |
+------------+       N : 1       +--------------+
|  shuttles  |-------------------|    routes    |
+------------+                   +--------------+
```

---

## 7. Deterministic Booking Flow

The deterministic booking flow operates entirely through typed Python services and repositories, without LLM intervention:

```
Caller (Test / Future Tool Node)
    │
    ▼
book_shuttle(db: Session, user_id: int, booking_date: date)
[app/tools/booking_tools.py]
    │
    │  Constructs:
    │  - UserRepository(db)
    │  - PreferenceRepository(db)
    │  - ShuttleRepository(db)
    │  - BookingRepository(db)
    │  - BookingService(...)
    │
    ▼
BookingService.book_usual_shuttle(user_id: int, booking_date: date)
[app/services/booking_service.py]
    │
    ├── 1. _resolve_user(user_id)
    │      └── UserRepository.get_by_id(user_id)
    │          (raises ValueError if user not found)
    │
    ├── 2. _resolve_child(user_id)
    │      └── Inspects user.children
    │          (raises ValueError if no children exist; selects user.children[0])
    │
    ├── 3. _resolve_usual_shuttle(user_id)
    │      ├── PreferenceRepository.get_by_user_id(user_id)
    │      │   (raises ValueError if preference or usual_shuttle_id is missing)
    │      └── ShuttleRepository.get_by_id(preference.usual_shuttle_id)
    │          (raises ValueError if shuttle record not found)
    │
    ├── 4. Shuttle capacity check
    │      └── ShuttleRepository.has_available_seat(shuttle.id, booking_date)
    │          └── Counts confirmed bookings for shuttle_id & booking_date
    │              (raises ValueError if booking_count >= shuttle.capacity)
    │
    ├── 5. Entity creation
    │      └── Booking(user_id, child_id, shuttle_id, booking_date, pickup_time=shuttle.departure_time, status="confirmed")
    │
    ├── 6. Persistence & commit
    │      ├── BookingRepository.create(booking) -> db.add(booking); db.flush()
    │      └── db.commit()
    │
    ▼
PostgreSQL (bookings table)
    └── Returns confirmed Booking instance
```

### Component Breakdown
- **Tool**: `book_shuttle` ([backend/app/tools/booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/tools/booking_tools.py))
  - **Inputs**:
    - `db: Session` (SQLAlchemy session)
    - `user_id: int`
    - `booking_date: date`
  - **Output**: Confirmed `Booking` SQLAlchemy model instance.
- **Service**: `BookingService` ([backend/app/services/booking_service.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/services/booking_service.py))
  - Validates preconditions, resolves relations, prevents overbooking, and issues transactional commit.
- **Repositories**:
  - `UserRepository`: reads `User` by ID.
  - `PreferenceRepository`: reads `Preference` by user ID.
  - `ShuttleRepository`: reads `Shuttle` and evaluates seat availability against capacity.
  - `BookingRepository`: adds and flushes `Booking` entity.
- **Persistence Behavior**:
  - Commits directly on the database session (`self.db.commit()`), ensuring the row is written to PostgreSQL.

---

## 8. API Endpoints

The FastAPI app is declared in [backend/app/main.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/main.py).

Currently implemented endpoints:

| HTTP Method | Path | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness check returning `{"status": "ok"}` |

> No booking, shuttle, or agent chat endpoints are currently exposed over HTTP.

---

## 9. Tests

### Existing Tests and Verification Targets

1. **[backend/tests/test_booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/tests/test_booking_tools.py)**
   - **Test function**: `test_book_shuttle_persists_booking()`
   - **Verification**:
     - Establishes a session using `SessionLocal()`.
     - Queries baseline booking count (`func.count(Booking.id)`).
     - Invokes `book_shuttle(db=db, user_id=1, booking_date=date(2026, 10, 1))`.
     - Refreshes the instance from PostgreSQL.
     - Asserts booking count incremented by 1 (`after_count == before_count + 1`).
     - Asserts `booking.id is not None`, `booking.user_id == 1`, `booking.child_id == 1`, `booking.shuttle_id == 1`, `booking.booking_date == date(2026, 10, 1)`, and `booking.status == "confirmed"`.
     - Teardown in `finally:` block cleans up test bookings and closes the session.

2. **[backend/test_booking_service.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/test_booking_service.py)**
   - **Role**: Standalone smoke test script (top-level execution script, not collected by pytest runner).
   - **Verification**: Calls `BookingService.book_usual_shuttle(user_id=1, booking_date=tomorrow)` against PostgreSQL and prints the created booking attributes.

### Test Suite Execution Results
- **Working Directory**: `/Users/godwinjoel.j/Projects/ai-shuttle/backend`
- **Command Used**: `./.venv/bin/pytest tests`
- **Result**:
  - **Passed**: 1
  - **Failed**: 0
  - **Skipped**: 0
  - **Duration**: ~0.64s

---

## 10. Configuration

### Expected Environment Variables (Names and Purposes Only)
No actual credentials, secrets, or host passwords are documented.

| Variable Name | Defined In | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `backend/.env` / `backend/.env.example` | Connection URI for the PostgreSQL database used by SQLAlchemy engine. |
| `APP_ENV` | `backend/.env` / `backend/.env.example` | Execution environment name (e.g. `development`, `production`). Default: `development`. |
| `API_BASE_URL` | `.env` / `.env.example` (root) | Base URL for HTTP requests sent by mobile client / frontend to backend. |

### Configuration Loading Mechanism
- `backend/app/core/config.py` loads settings through Pydantic's `BaseSettings` with `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.
- When invoking Python processes, execution should occur with the current working directory set to `backend/` so that `backend/.env` is located by Pydantic.

---

## 11. Known TODOs

### Current Milestone Work (Phase 1 Step 3 — LangGraph)
- **Install LangGraph & Core Dependencies**: Add and pin `langgraph` (and required LLM provider client / LangChain packages) in the Python environment.
- **Agent State Schema**: Define typed state schemas in `backend/app/schemas/` (or `backend/app/graph/state.py`).
- **Graph Nodes & Edges**: Implement the state graph in `backend/app/graph/` connecting agent reasoning with tool execution.
- **Tool Binding**: Adapt `book_shuttle` into a LangChain/LangGraph-compatible tool interface (`@tool`).
- **Graph Orchestration Tests**: Create unit/integration tests for graph execution and tool invocation.
- **Agent API Route**: Expose an endpoint in `backend/app/api/` and `backend/app/main.py` allowing clients to invoke the agent.

### Later Planned Work
- **Dependency Management File**: Create and commit a formal `pyproject.toml` or `requirements.txt` to track pinned dependencies.
- **Multi-Child & Dynamic Shuttle Resolution**: Extend `BookingService` to handle multi-child households and user-specified alternative shuttles/routes.
- **Conversational "My Usual" NLU**: Implement prompt templates and evaluation for conversational requests ("book my usual shuttle for tomorrow").
- **iOS Client Integration**:
  - Implement networking service in `AIShuttle/` to communicate with backend API.
  - Implement UI for shuttle schedules, booking status, and chat interface.
- **Siri / App Intents**: Integrate Swift App Intents for native voice/shortcut booking ("Hey Siri, book my usual shuttle").
- **Observability & Agent Evaluation**: Tracing tool calls, latency tracking, and evaluation benchmarks.

---

## 12. Milestone Status

Comparison against project milestones defined in `IMPLEMENTATION-PLAN.md`:

| Milestone Phase / Step | Status | Evidence in Current Repository |
| :--- | :--- | :--- |
| **Phase 0 — Foundation** | **COMPLETE** | FastAPI initialized with `/health` ([main.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/main.py)), Docker Compose configured with PostgreSQL 17 ([docker-compose.yml](file:///Users/godwinjoel.j/Projects/ai-shuttle/docker-compose.yml)), DB engine and initialization scripts functional ([database.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/database.py), [init_db.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/init_db.py), [seed.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/db/seed.py)), and starter iOS SwiftUI project created ([AIShuttle](file:///Users/godwinjoel.j/Projects/ai-shuttle/AIShuttle)). |
| **Phase 1 Step 1 — Deterministic booking** | **COMPLETE** | All core entities implemented ([models/](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/models/)), database repositories implemented ([repositories/](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/repositories/)), and `BookingService` with full business validation and database persistence implemented ([booking_service.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/services/booking_service.py)). |
| **Phase 1 Step 2 — book_shuttle** | **COMPLETE** | Callable tool function `book_shuttle` implemented in [backend/app/tools/booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/app/tools/booking_tools.py), wired to `BookingService`, and verified via automated integration test in [backend/tests/test_booking_tools.py](file:///Users/godwinjoel.j/Projects/ai-shuttle/backend/tests/test_booking_tools.py). |
| **Phase 1 Step 3 — LangGraph** | **NOT STARTED** | `backend/app/graph/__init__.py` and `backend/app/agent/__init__.py` are empty; `langgraph` package is not installed; no nodes or graph definitions exist. |
| **Phase 1 Step 4 — "my usual"** | **PARTIALLY COMPLETE** | Preference-based "usual shuttle" resolution logic exists deterministically in `BookingService._resolve_usual_shuttle` and seed data; conversational agent handling for natural language "book my usual" is not yet started. |
| **Phase 1 Step 5 — Siri/App Intent** | **NOT STARTED** | iOS project contains only default boilerplate template; no App Intents or Siri integration exist. |

---

**Current milestone**:
Phase 1 Step 3 — LangGraph

**Current commit**:
1c36e68a4ef0222e280781097b61e3a892b61431 (1c36e68)

**Working tree**:
clean (ahead of origin/main by 1 commit)

---

## 13. Important Architectural Boundaries

### Boundary Adherence Analysis

The project defines the strict architectural dependency flow:
$$\text{API} \longrightarrow \text{Agent} \longrightarrow \text{Graph} \longrightarrow \text{Tools} \longrightarrow \text{Services} \longrightarrow \text{Repositories} \longrightarrow \text{PostgreSQL}$$

1. **LLM must not directly access PostgreSQL**:
   - **Adherence**: **Fully Respected**. No LLM code or graph nodes currently exist. Database access is strictly confined within `app/repositories/`.
2. **API routes should not contain business logic**:
   - **Adherence**: **Fully Respected**. `app/main.py` only implements a lightweight `/health` check without database access or business logic.
3. **Tools should not contain database logic**:
   - **Adherence**: **Fully Respected**. `backend/app/tools/booking_tools.py` contains zero SQL or ORM queries. It acts as an adapter, instantiating repositories and delegating entirely to `BookingService`.
4. **Business logic belongs in services**:
   - **Adherence**: **Fully Respected**. All validation rules (user existence, child resolution, preference check, capacity evaluation) live inside `BookingService`.
5. **Database access belongs in repositories**:
   - **Adherence**: **Fully Respected**. Query construction and execution (`select(User)`, `select(func.count(Booking.id))`, `session.add`, `session.flush`) are strictly isolated to repository classes.

### Architectural Boundary Notes
- **Transaction Boundary**: In the current implementation, `BookingService.book_usual_shuttle` explicitly calls `self.db.commit()`. As multi-tool workflows and LangGraph agent execution are added, transaction boundaries may be elevated to a unit-of-work or session middleware pattern to allow transactional rollbacks across composite steps.
