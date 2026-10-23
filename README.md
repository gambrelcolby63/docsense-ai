# DocSense AI

[![CI](https://github.com/gambrelcolby63/docsense-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/gambrelcolby63/docsense-ai/actions/workflows/ci.yml)

Upload a PDF or a photo of a page. DocSense reads the text, writes a short summary and key points, and answers questions with the passage it used.

The web app is Next.js (App Router, TypeScript, Tailwind). The API is Python FastAPI. Documents and chats live in SQLite by default, and the same code talks to Postgres when `DATABASE_URL` points at one. The language model is an OpenAI-compatible HTTP API, so Groq, OpenRouter, OpenAI, or local Ollama all work. When no API key is set, a deterministic mock provider answers from the document itself, which is how the tests and the Docker demo run for free.

## Screenshots

The interface is a single warm, phone-width column: a sticky wordmark, an upload card with Choose file / Use camera / Try the sample, then the document list. Open a document and you get the summary, numbered key points, a disclosure for the extracted text, and a chat composer pinned to the bottom of the screen. Answers mark citations like [1], and each one is quoted underneath with a match percent.

Take these after `docker compose up --build` and drop the files in `docs/` when you want them in the README:

1. `docs/home.png` — Home on a narrow window, with the upload card and one document in Recent documents. Caption: "Upload a PDF or a photo of a page."
2. `docs/summary.png` — A document showing the summary, key points, and the extracted text open. Caption: "A short summary, then the points the file actually made."
3. `docs/chat.png` — A question whose answer quotes a passage, with the amber "From the document" citation under it. Caption: "Answers stay inside the file and show the passage they used."

On a phone, the camera button opens the rear camera. Use a flat, well-lit page that fills the frame. Tesseract reads the photo; it is not a substitute for a text-based PDF when the picture is blurry.

## Architecture

```mermaid
flowchart LR
  person[Phone or laptop]
  web[Next.js web]
  api[FastAPI API]
  extract[PDF text and OCR]
  rag[Chunk, embed, retrieve]
  llm[LLM provider]
  mock[Mock provider]
  remote[OpenAI-compatible API]
  db[(SQLite or Postgres)]

  person --> web
  web -->|REST JSON| api
  api --> extract
  api --> rag
  rag --> llm
  llm --> mock
  llm --> remote
  api --> db
```

The browser never calls the model directly. It posts the file to the API, then asks questions about a document id.

Retrieval is deliberately small:

1. Extract text with `pypdf`, or with Tesseract when the upload is an image.
2. Split the text into overlapping passages of about 700 characters.
3. Embed each passage. The default embedding is a local hashed bag-of-words vector, so retrieval works with no extra API and stays in the same space for every query. Set `EMBEDDING_PROVIDER=openai` to call a host's `/embeddings` endpoint instead. The document remembers which space it used.
4. Embed the question the same way, keep the closest passages, and send those passages to the model as numbered sources.
5. Return the answer plus the passages, so the UI can show them even if the model cites poorly.

The mock provider skips the network. Its summary is extractive (sentences from the file). Its answer quotes the sentences that share words with the question, or says it cannot find that in the document.

Original files are not stored. The database keeps the extracted text, the summary, the chunks and embeddings, and the chat.

## Project layout

```
api/                 FastAPI app, Dockerfile, pytest suite
  app/main.py        app factory (uvicorn --factory)
  app/services/      extraction, chunking, embeddings, LLM, retrieval
web/                 Next.js app, Dockerfile, vitest tests
docker-compose.yml   API + web, mock provider, SQLite on a volume
.devcontainer/       Codespaces image with Python, Node, and Tesseract
.github/workflows/   CI for the API and the web
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness, active provider, database kind |
| POST | `/api/documents` | Multipart upload. Returns the summary and extracted text. |
| GET | `/api/documents` | History, newest first. Summaries only. |
| GET | `/api/documents/{id}` | One document, including extracted text. |
| DELETE | `/api/documents/{id}` | Delete the document, its chunks, and its chat. |
| GET | `/api/documents/{id}/messages` | Chat history. |
| POST | `/api/documents/{id}/chat` | `{ "question": "..." }` → answer and citations. |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs).

## Run with Docker

This is the path to use for a demo. Docker Compose forces the mock provider, so you do not need a key.

```bash
docker compose up --build
```

- Web: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000/api/health](http://localhost:8000/api/health)

Click **Try the sample**, then ask "Who is the on-call lead for the Nordic region?" The answer should name Mina Solberg and quote the passage.

History is stored in a Compose volume at `/data/docsense.db` inside the API container. `docker compose down` keeps it. `docker compose down -v` deletes it.

## Run locally

You need Python 3.12, Node.js 22, and Tesseract with the English language data.

```bash
# Debian / Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-eng fonts-dejavu-core

cp .env.example .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt -r api/requirements-dev.txt

# terminal 1
make api

# terminal 2
cd web && npm ci && npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The API reads `.env` from the repo root.

To point the UI at a different API host, set `NEXT_PUBLIC_API_URL` before `npm run dev` or `npm run build`. Next.js bakes that value into the browser bundle.

### Use a real model

In `.env`:

```bash
LLM_PROVIDER=auto
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=local
```

`auto` uses the mock provider when the key is empty and the OpenAI-compatible client when it is set. Keep embeddings on `local` for Groq and for free OpenRouter models that have no embeddings endpoint. If `EMBEDDING_PROVIDER=auto` and the remote embeddings call fails, the API stores local vectors instead so chat still works.

Ollama:

```bash
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2
OPENAI_API_KEY=ollama
```

Docker cannot see `localhost` on your machine. Use `http://host.docker.internal:11434/v1` from Compose and do not force `LLM_PROVIDER=mock` in `docker-compose.yml`.

Do not commit `.env`. It is gitignored. `.env.example` lists every variable.

### Postgres

```bash
DATABASE_URL=postgresql+psycopg://docsense:docsense@localhost:5432/docsense
```

`postgres://` and `postgresql://` URLs from hosting dashboards are rewritten to the `psycopg` driver on startup. Tables are created on boot. That is enough for this app; a migration tool such as Alembic is the next step if the schema starts changing in production.

## Tests

```bash
make test
```

The API suite covers health, PDF extraction, image OCR, chunk overlap, the local embedding space, the mock provider, an OpenAI-compatible client backed by a fake HTTP transport (no network), upload, grounded chat, history, and delete. Postgres is not started; the suite only checks that a Postgres URL builds the right engine.

The web suite checks formatting helpers and API error parsing, then `tsc --noEmit` typechecks the app.

CI runs both jobs on Ubuntu. See `.github/workflows/ci.yml`.

## Deploy

Free tiers sleep, wipe ephemeral disks, and rate-limit models. Treat them as a demo host, not storage you cannot lose.

### Web on Vercel

- Import the GitHub repo.
- Set the root directory to `web`. Framework preset: Next.js.
- Environment variable: `NEXT_PUBLIC_API_URL=https://your-api-host` (no trailing slash).
- Redeploy if you change that variable. It is compiled into the client.

### API on Render

Use the Docker service, not the native Python buildpack. The buildpack does not install Tesseract, so photos would fail OCR.

- New Web Service → Docker.
- Dockerfile path: `api/Dockerfile`.
- Docker build context: `api`.
- Health check path: `/api/health`.
- Environment:
  - `DATABASE_URL` — Render Postgres URL. The `postgres://` form is accepted.
  - `LLM_PROVIDER=auto`
  - `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`
  - `EMBEDDING_PROVIDER=local`
  - `CORS_ORIGINS=https://your-app.vercel.app`
- SQLite on Render's filesystem disappears when the service restarts. Use Postgres if the history should survive a deploy.

### API on Fly.io

From `api/`, with the Fly CLI:

```bash
fly launch --no-deploy
fly volumes create docsense_data --size 1 --region <your-region>
```

Mount the volume at `/data` in `fly.toml`, set `DATABASE_URL=sqlite:////data/docsense.db` (or attach Fly Postgres and use that URL), set the same LLM and `CORS_ORIGINS` variables as above, then `fly deploy`. The image is `api/Dockerfile`.

After the API has a public URL, set `NEXT_PUBLIC_API_URL` on Vercel to that URL and redeploy the web app. Confirm `GET /api/health` from a browser and that the home page's provider note matches what you configured.

## Design notes

- **Mock by default.** A résumé demo and CI should not depend on a paid key or a flaky free tier. The mock is grounded: it cannot invent a warehouse code that is not in the file.
- **Local embeddings by default.** Chat providers and embedding providers are not the same. Groq is a good free chat host and a poor embeddings host. Hashing tokens into a normalized vector is simple, testable, and in the same space at index time and query time.
- **One schema for two databases.** Chunks store embeddings as JSON. That works on SQLite and Postgres without pgvector. It will not scale to a large corpus. That is a conscious limit.
- **Citations are retrieved passages, not a regex over the model's reply.** The structured citations are what the retriever returned. A live model is also asked to mention `[1]`-style markers, and the UI highlights those markers.

## What I learned

Replace the notes below with your own after you run the app, break something, and fix it. Keep each one specific to a change you made.

- **Python / FastAPI:** _What did you learn about the app factory, dependencies, or how the tests spin up a temporary database?_
- **Next.js / TypeScript:** _What did you learn about client components, the upload form, or Tailwind on a phone-width layout?_
- **REST APIs:** _How did you shape the upload and chat responses, and what does the UI do with an error `detail`?_
- **Databases:** _How does one SQLAlchemy URL talk to SQLite locally and Postgres when you deploy?_
- **Applied AI:** _Where does chunking, embedding, and retrieval stop the answer from wandering off the document?_
- **Git / CI / Docker:** _What failed the first time CI or Compose ran, and what did you change?_

## License

Add a license before you publish this if you want other people to reuse it. No license is included yet.
