# llm-free-conector

OpenAI-compatible model gateway backed by NewAPI. The service periodically syncs NewAPI channels and channel models into PostgreSQL, classifies models by capability, orders them by default priority, and routes fixed alias models to the best available concrete model.

## Current Scope

- PostgreSQL storage.
- Environment-variable configuration.
- NewAPI channel and model sync.
- Fixed aliases: `text`, `embedding`, `audio`, `image`, `video`.
- OpenAI-compatible relay endpoints for chat, completions, embeddings, images, audio, and videos.
- Alias failover: when a fixed alias is requested, the service tries candidate models in priority order and moves to the next candidate on retryable failures.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The app starts on `http://localhost:8000`. Configure `DATABASE_URL`, `NEWAPI_BASE_URL`, `NEWAPI_ADMIN_TOKEN`, and `NEWAPI_API_KEY` for your deployment.

If PostgreSQL already exists outside this compose file, update `DATABASE_URL` and run only the app service:

```bash
docker compose up --build --no-deps app
```

## API

Health:

```bash
curl http://localhost:8000/health
```

List models:

```bash
curl http://localhost:8000/v1/models
```

Use a fixed alias through an OpenAI-compatible endpoint:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer ${CONNECTOR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"text","messages":[{"role":"user","content":"hello"}]}'
```

## Model Aliases

| Alias | Capability |
| --- | --- |
| `text` | Chat/completions models |
| `embedding` | Embedding models |
| `audio` | Speech, transcription, and audio models |
| `image` | Image generation or image-capable models |
| `video` | Video generation models |

Direct concrete model names are passed through unchanged. Alias requests are resolved against the synced catalog.

## Priority

Each model has:

- `default_priority`: generated from model-name heuristics.
- `manual_priority`: reserved for later manual control.

Lower priority values are tried first. Manual priority wins when present.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run locally:

```bash
uvicorn app.main:app --reload
```

Trigger a manual sync:

```bash
python -m app.cli sync
```

Manual sync through HTTP:

```bash
curl -X POST http://localhost:8000/admin/sync \
  -H "Authorization: Bearer ${CONNECTOR_API_KEY}"
```

Adjust model priority:

```bash
curl -X PATCH http://localhost:8000/admin/models/gpt-4o \
  -H "Authorization: Bearer ${CONNECTOR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"manual_priority":10}'
```
