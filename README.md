# Generator Service Orchestration Framework

An orchestration backend for an **electrical & diesel generator service company**.
It coordinates the full service lifecycle — customers, generator assets, field
technicians, spare-parts inventory, maintenance workflows, contracts, and billing —
behind a single FastAPI service.

This is **not** an AI product. "Orchestration" here means coordinating real-world
service operations: intake a request, check the contract, dispatch the right
technician, reserve parts, run the job, sign off, and invoice.

## High-level architecture

```
                     Customer / Emergency Call
                                │
                       ServiceOrchestrator
                                │
   ┌───────────┬───────────┬───────────┬───────────┬────────────┐
   ▼           ▼           ▼           ▼           ▼            ▼
 Dispatch   Inventory   Maintenance  Contracts    Billing   Predictive
 Engine     Orchestr.   Scheduler    Manager      Engine    Maintenance
```

The `ServiceOrchestrator` (`app/orchestrator.py`) composes six specialized engines
(`app/engines/`) into the cross-cutting workflows. All state lives in an in-memory
store (`app/store.py`) seeded at startup (`app/seed.py`) — no database to set up.

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open the interactive API docs at **http://localhost:8000/docs**.

Run the tests:

```bash
pytest -q
```

### Run with Docker

```bash
docker build -t gold-waff .
docker run -p 8000:8000 gold-waff
```

Or one command with Compose (builds + serves on `http://localhost:8000`):

```bash
docker compose up --build
```

## Releases & CI

Two GitHub Actions workflows live in `.github/workflows/`:

- **`main.yml` (CI)** — runs `pytest` on Python 3.10–3.12 for every push and pull request.
- **`release.yml` (Release)** — on a `v*` tag (or manual dispatch): runs the tests, builds
  and pushes a container image to the GitHub Container Registry
  (`ghcr.io/<owner>/gold-waff`), and publishes a GitHub Release with a source archive
  attached. Cut a release by pushing a tag:

  ```bash
  git tag v1.0.0 && git push origin v1.0.0
  ```

  Then pull and run the published image:

  ```bash
  docker pull ghcr.io/<owner>/gold-waff:v1.0.0
  docker run -p 8000:8000 ghcr.io/<owner>/gold-waff:v1.0.0
  ```

## Core services (the 10 building blocks)

| # | Service | Where |
|---|---------|-------|
| 1 | Customer & asset registration | `routers/customers.py`, `routers/generators.py` |
| 2 | Generator asset records (serial, engine, running hours, warranty, history) | `models.Generator` |
| 3 | Maintenance orchestrator (PM / breakdown / inspection / overhaul / load bank / oil / filters) | `engines/maintenance.py`, `orchestrator.py` |
| 4 | Dispatch engine (skills, certs, proximity, workload, emergency boost) | `engines/dispatch.py` |
| 5 | Inventory orchestration (reserve vs. purchase request, consume) | `engines/inventory.py` |
| 6 | Field technician actions (running hours, faults, part replacement, signature, close) | `routers/work_orders.py` |
| 7 | Predictive maintenance (sensor thresholds → recommendations) | `engines/predictive.py` |
| 8 | Emergency breakdown workflow | `routers/incidents.py` |
| 9 | Contract management (AMC / CMC / warranty / emergency / rental) & billability | `engines/contracts.py`, `engines/billing.py` |
| 10 | Reporting dashboard (KPIs) | `reporting.py`, `routers/reporting.py` |

## Key endpoints

| Method & path | What it does |
|---------------|--------------|
| `POST /incidents` | **Emergency breakdown**: create incident → classify → check coverage → create work order → dispatch technician → reserve parts, in one call |
| `POST /work-orders` | Create a (non-emergency) service-request work order |
| `POST /work-orders/{id}/running-hours` · `/faults` · `/replace-part` · `/signature` | Field-technician mobile-app actions |
| `POST /work-orders/{id}/close` | Close the job → generate the invoice (coverage applied) |
| `POST /maintenance/run-daily` | Daily scheduler: create + dispatch PM work orders for every generator due |
| `GET /maintenance/due` | Generators past their PM running-hours interval |
| `POST /dispatch/preview` | Rank technician candidates for a job without creating one |
| `POST /generators/{id}/readings` | Submit IoT telemetry → predictive-maintenance recommendations |
| `GET /contracts/coverage?generator_id=…` | Best active contract coverage for a generator |
| `GET /inventory/parts` · `/below-reorder` · `/purchase-requests` | Stock, low stock, and raised purchase requests |
| `GET /reporting/dashboard` | Full KPI dashboard |

## End-to-end example (emergency breakdown)

```bash
# 1. Report a breakdown (returns the created work order + dispatched technician)
curl -s -X POST localhost:8000/incidents -H 'content-type: application/json' -d '{
  "generator_id": "GEN-000002",
  "description": "Failed to start on mains failure",
  "priority": "EMERGENCY",
  "required_parts": [{"category": "BATTERY", "quantity": 1}]
}'

# 2. Technician actions (use the returned work-order id, e.g. WO-000001)
curl -s -X POST localhost:8000/work-orders/WO-000001/running-hours -d '{"hours": 215}' -H 'content-type: application/json'
curl -s -X POST localhost:8000/work-orders/WO-000001/faults -d '{"code":"E-041","description":"Flat battery"}' -H 'content-type: application/json'

# 3. Close and invoice (AMC covers labor; the battery part is billable)
curl -s -X POST localhost:8000/work-orders/WO-000001/close -d '{"labor_hours": 1.5}' -H 'content-type: application/json'
```

## Contract coverage rules

| Contract | Parts | Labor |
|----------|:-----:|:-----:|
| **CMC** (Comprehensive) | ✓ | ✓ |
| **AMC** (Annual) | ✗ | ✓ |
| **WARRANTY** (within window) | ✓ | ✓ |
| **RENTAL** | ✓ | ✓ |
| **EMERGENCY_SUPPORT** | ✗ | ✗ (response only) |
| _no contract_ | billable | billable |

The most favorable active contract for a generator is applied automatically at
invoicing time.

## Android app (mobile dashboard)

`android/` contains a small native **Jetpack Compose** client for the API — a read-only
mobile dashboard with three tabs (KPI **Dashboard**, **Work Orders**, **Generators**) and
an editable server URL (settings icon; default `http://localhost:8000`). It talks to the
same endpoints documented above via Retrofit + kotlinx.serialization.

The app opens on a **login screen**; enter access code **`926696`** to reach the dashboard
(a client-side demo gate — the backend itself stays open).

**Reaching the backend from a device/emulator:** on Android, `localhost` means the *device*,
not your computer. To make the default `http://localhost:8000` reach a backend running on
your machine, run `adb reverse tcp:8000 tcp:8000`. Alternatively, open the in-app settings and
set the URL to `http://10.0.2.2:8000` (the emulator→host alias), or your machine's LAN IP for a
physical device.

Build the debug APK locally:

```bash
cd android
./gradlew assembleDebug
# APK at android/app/build/outputs/apk/debug/app-debug.apk
```

CI/CD for the app:

- **`android-ci.yml`** builds the debug APK on any push/PR touching `android/**`.
- **`android-release.yml`** publishes the APK to a GitHub Release on an **`android-v*`**
  tag (or manual dispatch). The `android-v*` namespace keeps APK releases separate from the
  service's `v*` Docker/GitHub releases. Cut one with:

  ```bash
  git tag android-v0.1.0 && git push origin android-v0.1.0
  ```

## Project layout

```
app/
  main.py            FastAPI app + startup seed
  models.py          Pydantic domain models & enums
  store.py           In-memory repositories + id generation
  seed.py            Representative sample data
  orchestrator.py    ServiceOrchestrator — composes engines into workflows
  reporting.py       KPI dashboard aggregation
  deps.py schemas.py Request/response schemas shared by routers
  engines/           dispatch, inventory, maintenance, contracts, billing, predictive
  routers/           HTTP endpoints per domain area
tests/               unit + end-to-end workflow tests
```

## Seeded data

Startup loads 3 customers, 5 generators (three past their PM interval, some under
warranty), 4 technicians with differing skills/certs/locations, a full spare-parts
inventory (a couple deliberately below reorder level to exercise the purchase-request
path), and a mix of CMC/AMC/emergency contracts so billability differs across the fleet.
