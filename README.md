# Django RAG

A modular starter project for Retrieval-Augmented Generation (RAG) with Django,
ChromaDB, local Sentence Transformers embeddings, and an OpenAI-compatible LLM provider. The chat interface uses WebSockets.

## Requirements

- Python 3.12
- A working network connection for installing Python packages and downloading
  the embedding model on first run
- An API key for the configured LLM provider

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Optionally set `OPENAI_BASE_URL` and
`RAG_LLM_MODEL` for an OpenAI-compatible provider.

## Add documents

Put `.md` or `.txt` files under `knowledge_docs/`. Nested directories are
supported.

## Run

```bash
python manage.py migrate
python manage.py ingest_docs
python manage.py runserver
```

Connect to the chat WebSocket at `ws://127.0.0.1:8000/ws/rag/chat/`.

Send a JSON message:

```json
{"type": "ask", "question": "What does the document say about access control?"}
```

A successful response has this structure:

```json
{
  "type": "answer",
  "answer": "...",
  "sources": [
    {"id": 1, "source": "access_control.md", "distance": 0.2}
  ]
}
```

Invalid requests and handled service errors are returned as `error` messages.

## Project layout

- `ingestion/`: file discovery, text splitting, and indexing orchestration
- `embeddings/`: local embedding model and batch embedding
- `vector_store/`: ChromaDB persistence and collection operations
- `retrieval/`: similarity search
- `llm/`: LLM client and grounded answer generation
- `application/`: coordinates retrieval and answer generation
- `websocket/`: WebSocket routing and chat consumer
- `models.py`: document indexing metadata

## Current indexing behavior

The command performs incremental synchronization. It compares each file's
SHA256 hash with the last successfully indexed version. New and changed files
are embedded and upserted in batches; unchanged files are skipped; deleted files
are removed from ChromaDB and the Django metadata table. Chunk IDs include the
content hash, so a new revision is written before old chunks are removed. This
reduces the risk of losing the previous indexed revision when an update fails.

## Important

- WebSocket connections are checked with `AllowedHostsOriginValidator` and
  use Django session authentication middleware. Add explicit authorization
  checks before exposing private document collections.
- Retrieved document text is sent to the configured LLM provider. Do not index
  confidential material unless that provider and data flow are approved.
- ChromaDB and the embedding model are initialized lazily and cached per process.
- For production, configure a Redis channel layer when running multiple ASGI
  processes, and add authorization, rate limiting, logging, monitoring, and a
  background worker if question-answering latency requires it.


## Incremental indexing behavior

Run `python manage.py ingest_docs` whenever the local document folder changes.
The command reports indexed, unchanged, deleted, and failed documents. It does
not calculate embeddings for unchanged files. The `Document` table stores the
SHA256 hash of the last successfully indexed content.

The Django database and ChromaDB are separate storage systems, so their writes
cannot participate in one atomic transaction. The indexer writes a revision
under hash-based IDs first, then removes old chunks for that source. If an
embedding or upsert batch fails, the partial new revision is cleaned up and the
previous revision is retained. For production deployments, prevent concurrent
indexing runs (for example with a distributed lock) and monitor failed files.
