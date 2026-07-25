# #33 Worklog Time Accounting — Developer Reference

**Branch:** `33-worklog_time_accounting` · **Base:** `31-Worklog_HomeOffice_field` · **ERPNext ≥ 15.110**

---

## Contents

1. [Feature Overview](#1-feature-overview)
2. [DDD Architecture](#2-ddd-architecture)
3. [Data Model (ER)](#3-data-model)
4. [Checkout Flow](#4-checkout-flow)
5. [Real-time Check-in](#5-real-time-check-in)
6. [HR Settings Cache](#6-hr-settings-cache)
7. [Task Prefilling Logic](#7-task-prefilling-logic)
8. [Custom Fields Reference](#8-custom-fields-reference)
9. [Deployment Protocol](#9-deployment-protocol)
10. [Staging Fixes Log](#10-staging-fixes-log)

---

## 1. Feature Overview

This PR delivers end-to-end work time accounting on top of the existing Worklog doctype. When an employee checks out for the day, a dialog collects task allocations, validates total time against the employee's actual checked-in hours (within a configurable tolerance), and auto-generates a submitted Timesheet — all in a single action.

Alongside this, check-in status updates were migrated from a 20-second polling loop to a WebSocket push (`frappe.publish_realtime`), and the entire backend was restructured following Domain-Driven Design (DDD) principles: pure domain objects hold business rules, the application service orchestrates use cases, and all Frappe-specific I/O lives in an infrastructure layer.

**Design constraints:**
- **One worklog per workday** — CRUD on the same document; the checkout dialog upserts today's entry.
- **One timesheet per worklog** — previous timesheet is cancelled and replaced on every worklog update.
- **Overallocation within tolerance** — if total allocated hours exceed actual work by ≤ tolerance, `time_saved` is stretched to match allocation (not capped at actual hours).
- **Admin privilege escalation for timesheets** — users do not need direct Timesheet create/submit permissions; `TimesheetRepository` escalates to Administrator and restores the session user in a `finally` block.

---

## 2. DDD Architecture

```mermaid
flowchart TD
    subgraph API["API Layer  (whitelisted endpoints)"]
        direction LR
        A1["worklog/api.py\nsave_and_checkout · prepare_for_checkout\nget_worklog_context · get_tolerance_minutes"]
        A2["flextime/api.py\ncheckin"]
    end

    subgraph APP["Application Layer"]
        B1["WorklogAppService\nOrchestrates use cases — no business logic"]
    end

    subgraph DOMAIN["Domain Layer  (pure Python, no Frappe)"]
        direction LR
        C1["WorklogEntity\nTaskAllocation"]
        C2["WorklogAggregate\ntolerance validation\ntime adjustment"]
        C3["WorklogStateService\nNEW · WORKING · ON_BREAK\nCOMPLETED · HISTORICAL"]
        C4["TaskProgressCalculator\nstateless math"]
    end

    subgraph INFRA["Infrastructure Layer  (Frappe-dependent)"]
        direction LR
        D1["WorklogRepository\nCRUD + entity mapping"]
        D2["TaskRepository\nSQL · prefill logic\ncustom_is_generic"]
        D3["TimesheetService\ncreate · cancel · replace\nAdmin privilege escalation"]
        D4["HRSettingsRepository\nRedis cache wrapper"]
        D5["TaskProgressUpdater\nfetch → calculate → persist"]
        D6["CheckinService\nevent aggregation\nrealtime publish"]
    end

    subgraph CORE["Frappe / ERPNext Core"]
        direction LR
        E1["MariaDB"]
        E2["Redis"]
        E3["WebSocket\nfrappe.realtime"]
    end

    A1 --> B1
    A2 --> D6
    B1 --> C2
    B1 --> C3
    B1 --> D1
    B1 --> D2
    B1 --> D3
    B1 --> D4
    B1 --> D5
    B1 --> D6
    C2 --> C1
    D1 & D2 & D3 & D5 --> E1
    D4 --> E2
    D4 --> E1
    D6 --> E1
    D6 --> E3
```

| Layer | Rule |
|---|---|
| API | `@frappe.whitelist()` only. No business logic. |
| Application | Orchestrates; coordinates domain + infra. No Frappe DB calls. Houses `WORKLOG_STATE_COLORS` — presentation mapping belongs here, not in the domain enum. |
| Domain | Pure Python. No `import frappe`. Business invariants live in the **aggregate**, not the entity. |
| Infrastructure | All DB/Redis/WebSocket I/O. Maps Frappe docs ↔ domain entities. |

### Domain object responsibilities

| Object | Responsibility |
|---|---|
| `WorklogEntity` | Pure data holder. Fields + `total_allocated` property only. No methods that encode business rules. |
| `WorklogAggregate` | Aggregate root. Owns `is_within_tolerance()` and `adjust_for_tolerance()`. Enforces the invariant that time adjustment logic cannot be bypassed by working directly on the entity. |
| `WorklogStateService` | Stateless domain service. Maps checkin events → `WorklogState` enum (NEW / WORKING / ON_BREAK / COMPLETED / HISTORICAL). Determines editability. |
| `WorklogState` (enum) | State values only — no display logic. Colors live in `WORKLOG_STATE_COLORS` in the application layer. |

---

## 3. Data Model

> Custom doctypes: **Worklog**, **Worklog Tasks**. All others are ERPNext core doctypes extended with custom fields.

```mermaid
erDiagram
    Employee {
        string name PK
        string user_id
        string employee_name
    }
    EmployeeCheckin {
        string name PK
        string employee FK
        datetime time
        string log_type
        bool is_break
    }
    Worklog {
        string name PK
        string employee FK
        datetime log_time
        float time_saved
        text work_desc
        select is_home_office
        string ticket_link
        string timesheet FK
    }
    WorklogTasks {
        string name PK
        string parent FK
        string task FK
        float time_spent
        float expected_time
        float progress_increment
        string subject
        string priority
        string status
    }
    Task {
        string name PK
        string subject
        string status
        string priority
        float expected_time
        float progress
        json _assign
        bool custom_is_generic
        bool custom_is_internal
    }
    Timesheet {
        string name PK
        string employee FK
        date start_date
        int docstatus
    }
    TimesheetDetail {
        string name PK
        string parent FK
        string task FK
        float hours
        int docstatus
    }
    HRSettings {
        int custom_worklog_time_allocation_tolerance
        link custom_default_timesheet_activity_type
        link custom_worklog_buffer_task FK
    }

    Employee ||--o{ Worklog : "logs work via"
    Employee ||--o{ EmployeeCheckin : "stamps in/out"
    Worklog ||--|{ WorklogTasks : "allocates hours to"
    WorklogTasks }o--|| Task : "references"
    Worklog ||--o| Timesheet : "generates on save"
    Timesheet ||--|{ TimesheetDetail : "detail rows"
    TimesheetDetail }o--|| Task : "tracks hours on"
    HRSettings ||--o| Task : "buffer task ref"
    Task }o--o{ Employee : "assigned via _assign JSON"
```

### Worklog fields

| Field | Type | Notes |
|---|---|---|
| `employee` | Link → Employee | Set on create; not editable after |
| `log_time` | Datetime | Anchors worklog to a workday — one doc per day enforced at app level |
| `time_saved` | Float (hrs) | Set by `WorklogAggregate.adjust_for_tolerance()` on save |
| `tasks_entry` | Table → Worklog Tasks | Child table; replaces deprecated `task` link field |
| `timesheet` | Link → Timesheet | Populated after auto-creation; replaced on each save |
| `is_home_office` | Select (Yes/No) | Mandatory — validation throws if blank |
| `task` | Link → Task | **Deprecated** — hidden, kept for schema compatibility |

### Worklog Tasks (child doctype) fields

| Field | Type | Notes |
|---|---|---|
| `task` | Link → Task | ERPNext Task being worked on |
| `time_spent` | Float (hrs) | Hours allocated to this task in this worklog |
| `expected_time` | Float (hrs) | Fetched from Task; used for progress calculation |
| `progress_increment` | Percent | `time_spent / expected_time × 100`, capped at 100 |
| `subject`, `status`, `priority` | Data (fetch) | Denormalized from Task for fast list rendering |

---

## 4. Checkout Flow

```mermaid
sequenceDiagram
    participant Br as Browser
    participant API as worklog/api.py
    participant App as WorklogAppService
    participant Chk as CheckinService
    participant TR as TaskRepository
    participant HR as HRSettingsRepository
    participant Redis
    participant DB as MariaDB

    Note over Br,DB: Phase 1 — Prepare checkout dialog

    Br->>API: prepare_worklog_for_checkout(employee_id)
    API->>App: prepare_for_checkout(employee_id)
    App->>Chk: data.get(today, employee_id)
    Chk->>DB: SELECT Employee Checkin WHERE date = today
    DB-->>App: [CheckinEvent ...]
    App->>TR: get_prefill_tasks(employee_id, limit=5)
    TR->>DB: SELECT assigned tasks via JSON_CONTAINS(_assign)
    TR->>DB: SELECT generic tasks WHERE custom_is_generic = 1
    DB-->>App: combined task list (assigned first)
    App->>HR: get_tolerance_minutes()
    HR->>Redis: hget("hr_settings", "tolerance_minutes")
    alt cache hit
        Redis-->>App: cached int
    else cache miss
        HR->>DB: get_single_value("HR Settings", field)
        DB-->>HR: raw value
        HR->>Redis: hset("hr_settings", "tolerance_minutes", value)
        Redis-->>App: fresh value
    end
    App-->>Br: prefilled_tasks · tolerance_minutes · headline_html · time_total_actual

    Note over Br,DB: Phase 2 — Employee fills dialog and submits

    Br->>API: save_and_checkout(worklog_name, worklog_data, current_total)
    API->>App: save_and_checkout(...)
    App->>App: validate_worklog_document(doc)
    Note right of App: WorklogAggregate.is_within_tolerance()
    App->>App: WorklogAggregate.adjust_for_tolerance()
    App->>DB: WorklogRepository.save_from_dict()
    Note right of DB: before_save hook fires<br>TaskProgressUpdater.calculate_increments()
    App->>DB: TimesheetRepository.create() [as Administrator]
    Note right of DB: Previous timesheet cancelled first
    App->>Chk: checkin(Action.END_WORK)
    Chk->>DB: INSERT Employee Checkin (OUT, is_break=0)
    Chk->>Br: publish_realtime("checkin_status_updated")
    API-->>Br: success · worklog name
```

---

## 5. Real-time Check-in

Replaces the previous 20-second polling loop. The server emits `checkin_status_updated` immediately after any check-in action; the browser listener updates the navbar timer and dashboard number cards without a page refresh.

```mermaid
sequenceDiagram
    participant Br as Browser
    participant FlexAPI as flextime/api.py
    participant Svc as CheckinService
    participant DB as MariaDB
    participant WS as frappe.realtime (Redis PubSub)

    Br->>FlexAPI: checkin(action="START_WORK")
    FlexAPI->>Svc: checkin(Action.START_WORK)
    Svc->>DB: INSERT Employee Checkin (log_type=IN, is_break=0)
    Svc->>DB: SELECT durations for stats
    Svc->>WS: publish_realtime("checkin_status_updated", {employee_id, status, total_worked_seconds, timestamp})
    WS-->>Br: event delivered (filtered by employee_id)
    Note over Br: frappe.realtime.on("checkin_status_updated")
    Br->>Br: NumberCardUpdater.patch(card, seconds)
    Br->>Br: CheckinTimer.start() — 1s local tick, 5min server drift sync
    FlexAPI-->>Br: status · had_break
```

**Frontend components:**

| Class / File | Responsibility |
|---|---|
| `CheckinTimer` | Local timer with drift correction. Handles IN / BREAK / OUT states. Syncs with server every 5 min. **Race condition guard:** if a realtime OUT event is received while a drift sync is in-flight, the stale sync response is discarded — prevents the timer from restarting after checkout. |
| `CHECKIN_STATUS` constants | Single source of truth for status → `{label, icon, CSS class}` mapping. |
| `TimeFormatter` | Formats seconds as `HH:MM`; `formatWithDuration` for richer display. |
| `NumberCardUpdater` | Direct DOM patch on Frappe number cards — patches value only, preserving card UI state. |

---

## 6. HR Settings Cache

HR Settings values (tolerance, activity type, buffer task) are cached in Redis under a single hash key `"hr_settings"`. An `on_update` doc event invalidates the entire hash whenever an admin saves HR Settings.

> **Frappe hook resolution constraint:** `frappe.get_attr()` splits on the last dot only — it cannot resolve `module.Class.method`. The hook must point to a module-level function, not a static method on the class.

```mermaid
sequenceDiagram
    participant Admin
    participant Frappe as Frappe Framework
    participant Hook as doc_events hook
    participant Repo as HRSettingsRepository
    participant Redis
    participant DB as MariaDB

    Admin->>Frappe: Save "HR Settings"
    Frappe->>Hook: on_update trigger fires
    Hook->>Repo: clear_hr_settings_cache(doc, method)
    Note right of Repo: module-level wrapper — frappe.get_attr<br>resolves module.function only
    Repo->>Redis: delete_value("hr_settings")

    Note over Admin,DB: Next request hitting get_tolerance_minutes()

    Admin->>Repo: get_tolerance_minutes()
    Repo->>Redis: hget("hr_settings", "tolerance_minutes") → None
    Repo->>DB: get_single_value("HR Settings", field)
    DB-->>Repo: fresh value
    Repo->>Redis: hset("hr_settings", "tolerance_minutes", value)
    Repo-->>Admin: value
```

```python
# hooks.py
doc_events = {
    "HR Settings": {
        "on_update": "hr_time.api.hr_settings.repository.clear_hr_settings_cache"
    }
}

# repository.py — module-level wrapper required for frappe.get_attr resolution
def clear_hr_settings_cache(doc=None, method=None) -> None:
    HRSettingsRepository.clear_cache()
```

---

## 7. Task Prefilling Logic

`TaskRepository.get_prefill_tasks(employee_id, limit=5)` combines two sorted sublists, filling up to `limit` slots:

| Priority | Source | Filter |
|---|---|---|
| 1st (up to `limit`) | Assigned tasks | `JSON_CONTAINS(_assign, user_id)` AND `custom_is_generic != 1` |
| Remaining slots | Generic tasks | `custom_is_generic = 1` |

Both sublists are excluded from internal tasks (`custom_is_internal = 1`) — this prevents the Worklog Buffer task from appearing in the dialog.

**Sort order (applied to both sublists):**

| Order | Column | Direction |
|---|---|---|
| 1st (optional) | `priority` | Urgent → High → Medium → Low via `FIELD(priority, ...)` |
| 2nd | `exp_start_date` | Soonest first; NULLs last |
| 3rd | `modified` | Most recent first (tiebreaker) |

---

## 8. Custom Fields Reference

All custom fields are provisioned via `hr_time/fixtures/custom_field.json` and applied with `bench migrate`.

### Task (ERPNext core)

| Field | Type | Description |
|---|---|---|
| `custom_is_generic` | Check | Marks task as generic/routine (Meetings, Housework). Eligible for prefill without assignment. Replaces the deprecated `is_generic` field removed in ERPNext 15.110. |
| `custom_is_internal` | Check | Marks system/internal tasks (e.g. Worklog Buffer). Hidden from prefill regardless of assignment. |

### HR Settings (Single doctype)

| Field | Type | Default | Description |
|---|---|---|---|
| `custom_worklog_time_allocation_tolerance` | Int | `0` | Minutes of allowed over/under-allocation. `0` = strict mode (no tolerance). Admin sets explicitly. |
| `custom_default_timesheet_activity_type` | Link → Activity Type | `"Task"` | Activity type written to every Timesheet Detail row. |
| `custom_worklog_buffer_task` | Link → Task | auto-created | Task that absorbs unallocated time when employee under-allocates within tolerance. Auto-created on first access if not set; persisted back to HR Settings immediately. |

> **Note:** The `"default"` property in a Custom Field fixture only applies to *new* documents. For Single doctypes like HR Settings, the existing singleton row is never backfilled by `bench migrate`. Set values explicitly in the HR Settings UI after first install, or in `after_install` if a non-null default is required programmatically.

---

## 9. Deployment Notes

The notes below cover the one-time configuration required after the first deploy of this feature.

### Staging one-time setup (after first deploy)

1. Open **HR Settings** → set **Worklog Buffer Task** (pick the auto-created "Worklog Buffer" task)
2. Set **Worklog Time Allocation Tolerance** to desired minutes (e.g. 30)
3. Set **Default Timesheet Activity Type** (e.g. "Task")
4. Save — triggers the `on_update` hook and primes the Redis cache

---

## 10. Post-merge Fixes Log

### DDD layer refinements (post-PR cleanup)

After initial PR review, three structural issues were identified and corrected without schema changes:

| Issue | Location | Fix |
|---|---|---|
| Self-instantiation in `before_save_worklog` | `WorklogAppService` | Was creating a new `WorklogAppService()` instance inside a method on `self`, then calling `app.validate_worklog_document(doc)` on the new instance. Fixed to call `self.validate_worklog_document(doc)` directly. |
| Business logic on entity instead of aggregate | `WorklogEntity` / `WorklogAggregate` | `is_within_tolerance()` and `adjusted_time_saved()` lived on `WorklogEntity`, with `WorklogAggregate` only delegating. Moved implementation to aggregate; entity is now a pure data holder. |
| UI concern (`display_color`) in domain enum | `WorklogState` | `display_color()` method was on the domain enum, coupling color strings to domain objects. Removed; replaced with `WORKLOG_STATE_COLORS` dict in `WorklogAppService` (application layer). All callers (`api.py`, `worklog_app_service.py`) updated to use the dict. |

### Multi-tab realtime race condition fix

**Symptom:** After checkout in Tab 1, Tab 2's navbar timer could continue running (showing a larger elapsed time) instead of switching to "Checked out" state.

**Root cause:** The 5-minute drift correction fires `CheckinTimer.sync()` which sends an async `frappe.call`. If the checkout's realtime OUT event arrives and correctly stops the timer *while that sync call is still in-flight*, the sync callback returns with a stale `{status: "IN"}` response and inadvertently restarts the timer.

**Fix:** `CheckinTimer.sync()` now checks whether the current status has already moved to OUT before applying the sync response. If so, the stale response is silently discarded.

```js
// checkin_timer.js — sync() callback guard
if (this.status === CHECKIN_STATUS.OUT.key &&
    response.message.status !== CHECKIN_STATUS.OUT.key) {
    return; // discard stale IN response — realtime event already committed the checkout
}
```