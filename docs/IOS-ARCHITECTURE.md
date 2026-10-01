# AI Shuttle — iOS Application Architecture

## 1. Purpose

This document defines the architecture, responsibilities, boundaries, and evolution strategy of the native iOS application for the AI Shuttle POC.

The iOS application is the native user-facing application and the integration point for:

- SwiftUI UI
- App Intents
- Siri / Apple Intelligence
- App Entities
- Backend API communication
- Presentation state
- Future conversational and real-time experiences

The iOS application must remain thin with respect to business logic.

Business rules, booking logic, scheduling logic, database access, agent reasoning, and persistent application data belong to the backend.

---

# 2. Architectural Principles

The iOS application follows these principles.

### 2.1 Native iOS

The application is implemented using:

- Swift
- SwiftUI
- App Intents

The project uses Xcode for native development, testing, signing, and Apple platform integration.

### 2.2 Backend owns business logic

The iOS application must never become the source of truth for:

- bookings
- shuttle availability
- user preferences
- children
- schedules
- routes
- shuttle status
- booking modifications
- agent decisions

The backend owns these concerns.

### 2.3 App Intents are adapters

App Intents translate natural-language/system requests into application operations.

They must not contain business logic.

Example:

```text
Siri
  ↓
BookMyUsualShuttleIntent
  ↓
BookingAPIClient
  ↓
FastAPI
  ↓
LangGraph / Services
  ↓
PostgreSQL
```

The App Intent should not determine which shuttle is "usual", check availability, or directly manipulate booking data.

### 2.4 UI is presentation-focused

SwiftUI views should primarily:

- display application state
- collect user interaction
- navigate between screens
- trigger presentation-layer actions

They should not:

- perform database access
- contain booking rules
- invoke LLMs
- implement agent reasoning
- construct business decisions

---

# 3. Current Architecture

The current iOS architecture is intentionally small.

```text
┌─────────────────────────────────────┐
│              SwiftUI                │
│                                     │
│  AppShell                           │
│   ├── Home                          │
│   ├── Rides                         │
│   └── Ride Details                  │
│                                     │
│           ↓                         │
│       ViewModel                     │
│                                     │
│           ↓                         │
│      API Client                     │
└───────────────┬─────────────────────┘
                │
                │ HTTP
                ↓
        ┌───────────────┐
        │    FastAPI    │
        └───────────────┘
                │
                ↓
             Backend
```

The current first complete vertical slice is:

```text
SwiftUI
  ↓
RidesViewModel
  ↓
BookingAPIClient
  ↓
FastAPI
  ↓
BookingService
  ↓
BookingRepository
  ↓
PostgreSQL
```

---

# 4. Application Structure

The current application structure is:

```text
AIShuttle/
└── AIShuttle/
    ├── AIShuttleApp.swift
    ├── ContentView.swift
    │
    ├── Networking/
    │   ├── BookingAPIClient.swift
    │   └── BookingDTOs.swift
    │
    ├── ViewModels/
    │   └── RidesViewModel.swift
    │
    ├── Views/
    │   ├── AppShellView.swift
    │   ├── HomeView.swift
    │   ├── RidesView.swift
    │   ├── UpcomingRideCard.swift
    │   └── RideDetailsView.swift
    │
    └── AppIntent/
        ├── BookMyUsualShuttleIntent.swift
        └── AIShuttleShortcuts.swift
```

Tests remain separated into:

```text
AIShuttleTests/
AIShuttleUITests/
```

---

# 5. Application Entry Point

`AIShuttleApp.swift`

Responsibilities:

- create the SwiftUI application
- establish the application entry point
- provide application-level dependencies when required

It should remain lightweight.

It should not contain:

- booking logic
- networking workflows
- agent logic
- database access

---

# 6. App Shell

`AppShellView.swift`

The application shell provides the stable navigation structure.

Current structure:

```text
AppShell
├── Home
└── Rides
```

The architecture is intentionally extensible for future product areas.

The conceptual future structure is:

```text
AI Shuttle
├── Home
├── Rides
├── Emma
└── Assistant
```

These future sections should only be introduced when their corresponding product capabilities are implemented.

Do not create empty placeholder features merely to make the architecture appear complete.

---

# 7. Home

`HomeView.swift`

Home is the primary product screen.

Current responsibilities:

- display application greeting
- display upcoming ride state
- display empty state
- display loading state
- display recoverable networking error
- allow retry
- navigate to ride details
- provide the foundation for future quick actions

Current states include:

```text
Loading
   ↓
Loaded
   ├── No upcoming rides
   └── Upcoming ride
   ↓
Error
```

The Home screen must not contain booking business logic.

---

# 8. Rides

`RidesView.swift`

The Rides screen provides access to the user's ride information.

Current scope:

- upcoming rides
- empty state
- loading/error handling
- pull-to-refresh
- navigation to Ride Details

Future capabilities such as:

- past rides
- cancellation
- modification
- tracking

should only be added when their backend capabilities are implemented.

---

# 9. Ride Details

`RideDetailsView.swift`

Ride Details displays information returned by the backend.

Current information includes:

- booking ID
- child
- booking status
- date
- pickup time
- shuttle
- route
- pickup location
- destination

The view must display backend state rather than derive or invent operational information.

Future real-time information can be added here when the real-time tracking capability is implemented.

---

# 10. Presentation State

`RidesViewModel.swift`

The ViewModel owns presentation state for ride retrieval.

Current state model:

```text
idle
loading
loaded
error
```

Responsibilities:

- initiate API requests
- transform API results into presentation state
- expose loading/error/success state to SwiftUI
- support refresh/retry

The ViewModel must not contain:

- SQL/database access
- booking rules
- shuttle-selection rules
- LLM calls
- LangGraph logic
- agent reasoning

The ViewModel communicates with backend capabilities through the networking layer.

---

# 11. Networking Layer

`BookingAPIClient.swift`

The API client owns HTTP communication with the backend.

Responsibilities:

- construct HTTP requests
- send requests
- decode responses
- translate HTTP/network failures into typed application errors

It currently supports:

```text
POST /bookings
GET  /bookings
```

The API client must not contain business rules.

For example, it should not decide:

> "This is Emma's usual shuttle, therefore select shuttle 1."

That decision belongs to the backend.

---

# 12. DTO Layer

`BookingDTOs.swift`

DTOs represent the API contract between iOS and the backend.

Example conceptual flow:

```text
Backend JSON
     ↓
BookingDetailDTO
     ↓
Presentation
```

DTOs should represent transport/API data rather than becoming domain-wide mutable state.

Presentation formatting helpers may exist where useful, such as:

```text
formattedDate
formattedPickupTime
```

Business decisions should not be hidden inside formatting helpers.

---

# 13. App Intents

App Intents are the bridge between Siri / Apple Intelligence and the AI Shuttle application.

Current intent:

```text
BookMyUsualShuttleIntent
```

Conceptual flow:

```text
Siri / Apple Intelligence
          ↓
     App Intent
          ↓
   BookingAPIClient
          ↓
       FastAPI
          ↓
      AI Shuttle
```

The App Intent is responsible for:

- receiving the system request
- providing required parameters where applicable
- invoking the appropriate backend operation
- returning the backend result as an appropriate Siri response

The App Intent is **not** responsible for:

- resolving user preferences
- selecting a shuttle
- checking availability
- creating database records
- modifying bookings
- reasoning about schedules

Those remain backend responsibilities.

---

# 14. App Entities

The Technical Stack identifies App Entities as the structured iOS representation for application objects exposed to Siri / Apple Intelligence.

Potential entities include:

```text
Shuttle
Child
Ride / Booking
```

Conceptual structures include:

### Shuttle

```text
id
route
departureTime
arrivalTime
availableSeats
```

### Child

```text
id
name
school
usualPickupLocation
```

### Ride / Booking

```text
id
child
shuttle
date
pickupTime
status
```

App Entities should only be introduced when an actual Siri / Apple Intelligence interaction requires them.

Do not create entities merely for architectural completeness.

---

# 15. App Shortcuts

App Shortcuts are optional.

They should only be introduced when testing demonstrates that they are necessary for the required Siri/App Intent flows.

The architecture must not depend on manually configured shortcuts if the required App Intent works without them.

---

# 16. Dependency Direction

The iOS dependency direction should remain:

```text
SwiftUI Views
      ↓
ViewModels
      ↓
API Client
      ↓
Backend API
```

App Intents operate as a separate system-integration entry point:

```text
Siri / Apple Intelligence
          ↓
      App Intent
          ↓
     API Client
          ↓
     Backend API
```

The two entry points converge on backend capabilities.

```text
                 ┌── SwiftUI
                 │
User ────────────┤
                 │
                 └── Siri / Apple Intelligence
                          ↓
                    Backend API
```

The backend remains the source of truth.

---

# 17. Error Handling

The iOS application must distinguish between at least:

```text
Loading
Success
Empty
Recoverable network error
HTTP/API error
Decoding error
```

The application must never display successful booking state when the backend operation failed.

For App Intents:

```text
Backend success
    → return confirmation

Backend failure
    → return meaningful failure
```

Do not convert backend failures into success messages.

---

# 18. Testing Strategy

Testing is divided into native unit tests and UI tests.

## Unit Tests

Test:

- DTO decoding
- successful API responses
- empty API responses
- HTTP failures
- malformed responses
- ViewModel loading
- ViewModel success
- ViewModel empty state
- ViewModel error state
- App Intent behavior

## UI Tests

Test user-visible behavior such as:

```text
Home
 ↓
Upcoming Ride
 ↓
Ride Details
```

UI tests should prefer deterministic application state and backend fixtures over assumptions about external services.

---

# 19. Backend Boundary

The iOS application does not bypass the backend.

The complete application boundary is:

```text
┌───────────────────────┐
│       Native iOS      │
│                       │
│ SwiftUI               │
│ App Intents            │
│ App Entities           │
│ API Client             │
└───────────┬───────────┘
            │
            │ HTTP
            ↓
┌───────────────────────┐
│       FastAPI         │
├───────────────────────┤
│ Agent                 │
│ LangGraph             │
│ Tools                 │
│ Services              │
│ Repositories          │
└───────────┬───────────┘
            ↓
      PostgreSQL
```

The LLM never accesses PostgreSQL directly.

The iOS application never accesses PostgreSQL.

---

# 20. Architecture Evolution

The iOS architecture evolves incrementally.

## Version 1 — Basic Application

```text
SwiftUI
   ↓
Networking
   ↓
FastAPI
   ↓
Services
   ↓
PostgreSQL
```

This is the current foundation.

## Version 2 — Agentic Backend

```text
SwiftUI
   ↓
FastAPI
   ↓
LangGraph
   ↓
Tools
   ↓
Services
   ↓
PostgreSQL
```

The iOS layer does not need to understand LangGraph internals.

## Version 3 — Siri

```text
Siri / Apple Intelligence
          ↓
      App Intent
          ↓
       FastAPI
          ↓
      LangGraph
          ↓
        Tools
          ↓
      Services
          ↓
    PostgreSQL
```

## Version 4 — Conversational Context

Conversational state is primarily a backend/agent concern.

```text
iOS
 ↓
FastAPI
 ↓
LangGraph
 ├── Conversation State
 └── PostgreSQL Memory
        ↓
      Tools
        ↓
     Services
```

The iOS application should not attempt to reproduce LangGraph conversation state locally.

## Future Versions

Later project capabilities may introduce:

- persistent preferences
- schedule reasoning
- real-time shuttle information
- smart booking
- multi-agent orchestration
- RAG
- MCP
- evaluation/observability

These capabilities should be exposed to iOS through stable application/API contracts rather than leaking their implementation details into SwiftUI.

---

# 21. Future Product Areas

The long-term application concept is:

```text
AI Shuttle
├── Home
│   ├── Upcoming Ride
│   ├── Children
│   ├── Shuttle Status
│   └── Quick Actions
│
├── Rides
│   ├── Upcoming
│   ├── Past
│   └── Ride Details
│
├── Emma
│   ├── Profile
│   ├── Weekly Schedule
│   ├── Activities
│   └── Ride Adjustments
│
└── Assistant
    ├── Conversation
    └── Agent Activity
```

This is a target product structure, not a requirement to implement all screens immediately.

Features should be introduced according to the implementation plan.

---

# 22. What Does Not Belong in the iOS Layer

The following must remain outside the iOS application:

### Database

```text
SQL
SQLAlchemy
PostgreSQL
Repository queries
```

### Business Logic

```text
booking rules
availability rules
schedule rules
route selection
ride modification rules
```

### Agent Logic

```text
LLM prompts
LangGraph orchestration
tool selection
agent planning
agent state management
```

### RAG

```text
document retrieval
embedding generation
vector search
retrieval ranking
```

### MCP

MCP is a backend interoperability boundary.

The iOS application should not directly depend on MCP merely because MCP exists in the overall architecture.

### Evaluation

Agent evaluation and tracing belong to the backend/AI engineering layer rather than normal user-facing SwiftUI screens.

---

# 23. Architecture Decision Rules

When adding a new iOS feature, ask:

### Does this require new backend data?

If yes:

```text
Backend API
→ DTO
→ API Client
→ ViewModel
→ SwiftUI
```

### Does Siri need to invoke it?

If yes:

```text
App Intent
→ API Client
→ Backend
```

### Does the feature require business rules?

Keep those rules in the backend service layer.

### Does the feature require agent reasoning?

Keep the reasoning in LangGraph/backend.

### Does the feature require persistent memory?

Use PostgreSQL through backend services.

### Does the feature require unstructured knowledge?

Use the backend RAG layer.

### Does the feature require real-time operational information?

Expose a backend capability/API and let the iOS layer present the result.

---

# 24. Current Implementation Status

As of Phase 2:

```text
SwiftUI                 ✅
App Shell               ✅
Home                    ✅
Rides                   ✅
Ride Details            ✅
API Client              ✅
Booking DTOs            ✅
Rides ViewModel         ✅
App Intent              ✅
Siri booking flow       ✅ backend verified
App Entity integration  ⏳ only when required
Conversation UI          ⏳ future
Emma UI                 ⏳ future
Real-time tracking UI   ⏳ future
```

The current architecture is intentionally sufficient for the first vertical slice without prematurely implementing future product capabilities.

---

# 25. Phase 3 Boundary

The next implementation milestone is conversational context.

The target interaction is:

```text
User:
"Book my usual shuttle for tomorrow."

        ↓

Backend creates booking.

        ↓

User:
"Make it 30 minutes earlier."

        ↓

Backend identifies the relevant current booking
using conversational context and performs the
appropriate deterministic booking modification.
```

The iOS architecture should support this without moving conversation or booking logic into SwiftUI.

The likely iOS responsibility remains:

```text
User / Siri
     ↓
App Intent or future Assistant UI
     ↓
API Client
     ↓
FastAPI
```

The conversational state itself belongs to the backend agent architecture.

Phase 3 must not introduce:

- RAG
- MCP
- multi-agent orchestration
- schedule reasoning
- real-time tracking
- smart booking
- evaluation infrastructure

Those belong to later phases of the implementation plan.

---

# 26. Core Architectural Principle

The iOS application should remain a **native interaction and presentation layer**, not an AI runtime.

Its job is to:

```text
Present
Interact
Translate
Navigate
Display
```

The backend's job is to:

```text
Understand
Reason
Retrieve
Plan
Execute
Persist
Validate
```

This separation allows the same AI Shuttle capability to be accessed through:

```text
SwiftUI
   │
   └── Siri / Apple Intelligence
           │
           ↓
        FastAPI
           ↓
       AI Shuttle
```

without duplicating business logic across interfaces.