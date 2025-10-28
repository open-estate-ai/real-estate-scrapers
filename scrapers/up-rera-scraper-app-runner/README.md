
## Orchestrator Agent

Simple coordinating service that receives a user query, classifies intent, and
in future will plan and dispatch tasks to other agents. This is the local
development setup for the Orchestrator inside the
`real-estate-agentic-ai` monorepo.

### What it does (current state)

* Starts an HTTP server (A2A protocol) on port 9999
* Exposes an agent card with basic metadata
* Classifies user intent using a structured JSON schema
* Returns the intent classification as JSON

### Planned (next)

* Build task DAGs (planner)
* Enqueue tasks for search / legal / valuation / verification agents
* Handle streaming and guardrails

---

## Quick Start (Local)

From repo root or this directory:

```sh
cd scrapers/up-rera-scraper-app-runner
uv sync
uv run python -m server.main
```

Server will start on: <http://localhost:9999/>

### Test Client

```sh
uv run python src/client/test_client.py
```

---

## Environment Variables

Copy the example file and edit if needed:

```sh
cp .env.tmpl .env
```

Variables (current minimal):

* OPENAI_API_KEY – required for intent classification

The code loads `.env` automatically.

---

## Docker / Container Run

Build image:

```sh
docker buildx build --platform linux/amd64 --provenance=false -t orchestrator-server:1.0.0 .
```

Run container (no env):

```sh
docker run --platform linux/amd64 -p 9999:9999 orchestrator-server:1.0.0
```

Run with env file:

```sh
docker run --platform linux/amd64 -p 9999:9999 --env-file ./.env orchestrator-server:1.0.0
```

If Docker not installed:

```sh
# macOS
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop/
```

---

## Project Layout

```text
agents/orchestrator/
	Dockerfile
	pyproject.toml
	uv.lock
	src/
		orchestrator/
			main.py        # Entry point (uvicorn startup)
			agent.py       # Intent classification logic
			config.py      # Env var validation
			executor.py    # Wiring request handling to agent
			models/intent.py
		client/test_client.py
```

---

## A2A Protocol Reference

Docs: <https://a2a-protocol.org/latest/>

---

## Troubleshooting

* Missing OPENAI_API_KEY → set it in `.env`
* Port already in use → change `port` in `main.py` or free 9999
* Dependency issues → remove `.venv` and re-run `uv sync`

---

## License

See repository root for license information.
