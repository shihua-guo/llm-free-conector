# llm-free-conector

OpenAI-compatible model gateway backed by NewAPI. The service periodically syncs NewAPI channels and channel models into PostgreSQL, classifies models by capability, orders them by default priority, and routes fixed alias models to the best available concrete model.

## Current Scope

- PostgreSQL storage.
- Environment-variable configuration.
- NewAPI channel and model sync.
- Fixed aliases: `text`, `embedding`, `audio`, `image`, `video`.
- OpenAI-compatible relay endpoints for chat, completions, embeddings, images, audio, and videos.
- Alias failover: when a fixed alias is requested, the service tries candidate models in priority order and moves to the next candidate on retryable failures such as quota exhaustion, rate limiting, and upstream 5xx errors.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The app starts on `http://localhost:8000`. Configure `DATABASE_URL`, `NEWAPI_BASE_URL`, `NEWAPI_API_KEY`, and one NewAPI management auth method for your deployment.

NewAPI management auth can use either:

- `NEWAPI_ADMIN_TOKEN` plus optional `NEWAPI_USER_ID`.
- `NEWAPI_USERNAME` and `NEWAPI_PASSWORD`; the app logs in through `NEWAPI_LOGIN_PATH`, stores the returned session cookie in memory, and uses the returned user id as `New-Api-User`.
- `NEWAPI_SESSION_COOKIE` plus `NEWAPI_USER_ID` when you already have a valid session cookie.

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

## NewAPI Docker Notes

If this service runs in the same Docker network as NewAPI, point `NEWAPI_BASE_URL` at the NewAPI service name, for example:

```env
NEWAPI_BASE_URL=http://new-api:3000
```

If NewAPI is published on the host, for example `http://localhost:3001`, use:

```env
NEWAPI_BASE_URL=http://host.docker.internal:3001
```

For local non-Docker development, `http://localhost:3001` is fine.

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
