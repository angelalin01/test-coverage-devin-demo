# TelemetryStatusService

Ground telemetry processing service for launch operations milestone status tracking.

## Overview

TelemetryStatusService is a Python-based system that processes ground telemetry events and reports on key launch-milestone statuses such as engine chill complete, fuel load complete, and pressurization complete. Downstream systems rely on these status updates to sequence launch operations correctly.

## Architecture

The service is built with Python 3.10+ and organized into the following modules:

- **ingestion/** - Handles incoming telemetry packets
- **processors/** - Interprets packets and updates milestone state
- **status/** - Computes and stores milestone readiness
- **api/** - Serves status to the operations dashboard via REST API

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

### Setup

```bash
# Clone the repository
git clone https://github.com/angelalin01/TelemetryStatusService.git
cd TelemetryStatusService

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

## Running the Service

Start the API server:

```bash
poetry run python main.py
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /packets` - Submit telemetry packets for processing
- `GET /milestones` - Get all milestone statuses
- `GET /milestones/{milestone}` - Get specific milestone status
- `GET /readiness` - Get overall launch readiness
- `GET /stats` - Get telemetry receiver statistics

## Testing

Run the test suite:

```bash
poetry run pytest
```

Run tests with coverage report:

```bash
poetry run pytest --cov=ingestion --cov=processors --cov=status --cov=api --cov-report=term-missing --cov-report=html
```

View the HTML coverage report:

```bash
open htmlcov/index.html
```

## Development

### Project Structure

```
TelemetryStatusService/
├── ingestion/
│   ├── packet.py          # Telemetry packet models and validation
│   └── receiver.py        # Packet reception and buffering
├── processors/
│   ├── milestone_processor.py  # Milestone state processing
│   └── state_machine.py        # Generic state machine
├── status/
│   ├── readiness.py       # Launch readiness computation
│   └── aggregator.py      # Status history aggregation
├── api/
│   └── server.py          # FastAPI REST API
├── tests/
│   ├── ingestion/
│   ├── processors/
│   ├── status/
│   └── api/
├── pyproject.toml         # Poetry configuration
└── main.py                # Application entry point
```

### Milestones

The system tracks six launch milestones:

1. `engine_chill` - Engine cooling system readiness
2. `fuel_load` - Fuel loading completion
3. `pressurization` - Pressurization system readiness
4. `terminal_count` - Terminal countdown initiation
5. `ignition` - Engine ignition sequence
6. `liftoff` - Vehicle liftoff

### Milestone States

- `NOT_STARTED` - Milestone not yet begun
- `IN_PROGRESS` - Milestone is actively progressing
- `COMPLETE` - Milestone successfully completed
- `FAILED` - Milestone encountered an error
- `ABORTED` - Milestone was aborted

## License

Internal use only - Launch Operations Team
