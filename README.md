# Ask the Document

A small, single-document Retrieval-Augmented Generation (RAG) chatbot. It answers questions
using one PDF, DOCX, TXT, or Markdown file, shows the exact excerpts it used, and says when the
document does not contain the answer.

The user interface is a dark-first, dual-theme Streamlit workspace: a reference rail on the left,
the conversation in the center, and a study rail on the right that shows only real session facts
and working actions. Embeddings run locally with `fastembed`; generation uses any
OpenAI-compatible chat endpoint (local Ollama by default, or a hosted API).

## What it does

- Extracts text while keeping PDF page numbers or DOCX/Markdown section headings.
- Splits text into overlapping, sentence-aware chunks.
- Embeds chunks with a local model and stores them in a small persistent NumPy index.
- Retrieves the top matching chunks for each question.
- Sends only those excerpts to the LLM with strict "answer from the context or abstain" rules.
- Renders citations from real retrieved metadata, not from model-invented page numbers.
- Detects a changed document, embedding model, or chunk configuration and refuses to query a
  stale index.
- Treats document text as untrusted data, so instructions inside the document are not followed.
- Shows the real index state, retrieved passages, session history, and rebuild action in a
  responsive three-panel workspace with intentional light and dark themes.

```text
Indexing:  document -> text + metadata -> chunks -> local embeddings -> index/
Answering: question -> query embedding -> top-k chunks -> prompt -> LLM -> answer + sources
```

## Project layout

```text
app.py                     Three-panel Streamlit workspace
ui/theme.py                Runtime theme tokens and stylesheet injection
ui/theme.css               Dual-theme layout and component styles
src/config.py              .env configuration
src/ingestion.py           PDF/DOCX/TXT/Markdown extraction
src/chunking.py            sentence-aware chunking with overlap
src/embeddings.py          local fastembed provider
src/vector_store.py        persistent NumPy index + stale-index checks
src/retrieval.py           query embedding + top-k retrieval
src/generation.py          grounded prompt + OpenAI-compatible client
src/indexer.py             build-and-save pipeline
scripts/build_index.py     index builder CLI
scripts/evaluate.py        retrieval/answer smoke evaluation
data/sample_document.md    generic demo document
data/student-handbook.pdf  bundled reference document
index/                     prebuilt index for the bundled handbook
eval/student_handbook_questions.json  bundled-document evaluation set
eval/questions.json        sample-document set used by the integration test
tests/                     offline unit/integration tests
PRODUCT.md                 product context and constraints
DESIGN.md                  visual system, tokens, and component rules
```

## Requirements

- Python 3.11 or newer (tested on 3.13).
- No GPU required. The default embedding model is small and runs on CPU.
- The embedding model is about 130 MB; Python dependencies add a few hundred MB.
- For the default LLM: [Ollama](https://ollama.com/) installed and running.

## Quick start

### 1. Install dependencies

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If PowerShell blocks activation, either run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, or call
`.\.venv\Scripts\python.exe` directly instead of activating.

### 2. Create the configuration file

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

The defaults work with a local Ollama instance.

> **This workspace:** `.env` points to the bundled `data/student-handbook.pdf`, and its prebuilt
> index is included in the repository. A fresh copy of `.env.example` uses the same handbook.
> Change `DOCUMENT_PATH` to choose your own file, then rebuild the index.

### 3. Choose an LLM

**Option A - local Ollama (default, private):**

```bash
ollama pull llama3.2
ollama serve
```

The default settings are:

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
LLM_API_KEY=
```

**Option B - hosted OpenAI-compatible API:**

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your-key-here
```

Other providers work if they expose an OpenAI-compatible `/chat/completions` endpoint (for
example Groq, Together, LM Studio, or a company gateway). Put the key in `.env` locally or in
Streamlit Cloud secrets; never commit it. Include the `/v1` part of the base URL.

### 4. Build the index

```bash
python -m scripts.build_index
```

The first run downloads the embedding model from Hugging Face. Later runs use the local cache.
The bundled student handbook produces 383 chunks with the default settings, and its prebuilt
index is committed under `index/`. Rebuilding overwrites those three files; commit them if you
change the demo document.

### 5. Run the chatbot

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually <http://localhost:8501>). You can also rebuild the index
from the study rail or the sidebar after changing the document.

## Interface

The workspace has three parts:

- **Reference rail (left):** the active document, its real index status, the sources from the
  last answer, and session-only question history.
- **Chat (center):** suggested questions, the real conversation, cited answers, and a source
  ledger whose rows open the exact retrieved excerpts.
- **Study desk (right):** real session counts, remaining suggested questions, a citation guide,
  index details, and the working rebuild action. It does not offer audio, video, quiz, flashcard,
  or note-generation tools that the backend cannot produce.

The app opens in dark mode. Use the **Light** / **Dark** pill in the topbar to switch; the choice
is kept for the current browser session only. Both themes are supported at desktop and mobile
widths. At narrower widths the study desk stacks below the chat, and the reference rail becomes
a collapsible sidebar. `New chat` clears the current conversation.

## Streamlit Community Cloud

The repository includes the handbook and its prebuilt index, so the app can be deployed without
a first-run build.

1. Create an app from `https://github.com/mark-aguilar2304/rag-chatbot` with branch `main` and
   main file path `app.py`.
2. In the app's **Settings → Secrets**, add the LLM settings using TOML:

```toml
LLM_BASE_URL = "https://your-provider.example/v1"
LLM_MODEL = "your-model"
LLM_API_KEY = "your-key"
```

The app reads Streamlit secrets as a fallback when the matching environment variables are not
set. Never put the key in the repository. The first query downloads the embedding model; later
queries use the cached model.

## Add or replace the reference document

1. Put one supported file in `data/` (PDF, DOCX, TXT, `.md`).
2. Set `DOCUMENT_PATH` in `.env` to that file, for example:
   `DOCUMENT_PATH=data/student-handbook.pdf`.
3. Rebuild the index:

```bash
python -m scripts.build_index
```

4. Restart or refresh the Streamlit app.

`data/*` is ignored by Git except for the bundled sample and handbook, so your private documents
are not committed. If your PDF is a scan with no text layer, run OCR first; the loader reports
this instead of pretending extraction succeeded.

## Configuration

All settings can be set in `.env` or in the process environment. Paths are resolved from the
project root when relative.

| Variable | Default | Purpose |
|---|---|---|
| `DOCUMENT_PATH` | `data/student-handbook.pdf` | The single reference document. Bundled with the repo. |
| `INDEX_DIR` | `index` | Generated index directory. |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Any fastembed-supported model. Rebuild after changing it. |
| `CHUNK_SIZE` | `1200` | Target chunk size in characters. |
| `CHUNK_OVERLAP` | `200` | Overlap in characters, smaller than `CHUNK_SIZE`. |
| `TOP_K` | `4` | Number of excerpts retrieved per question. |
| `MIN_SCORE` | `0.0` | Minimum cosine similarity. Raise it to filter weak matches; tune with your own questions. |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL. |
| `LLM_MODEL` | `llama3.2` | Chat model name. |
| `LLM_API_KEY` | empty | API key when the provider requires one. |
| `LLM_TIMEOUT` | `120` | Request timeout in seconds. |

The index manifest stores the source file hash, embedding model, chunk settings, and schema
version. If any of these no longer match, the app shows a rebuild message instead of returning
answers from an outdated index.

## Tests and evaluation

Run the offline suite (no model, network, or API key required):

```bash
pytest -q
```

Run the real-embedding integration test (downloads/uses the local model):

Windows PowerShell:

```powershell
$env:RAG_RUN_INTEGRATION = "1"
pytest -q tests/test_integration_embeddings.py
```

macOS/Linux:

```bash
RAG_RUN_INTEGRATION=1 pytest -q tests/test_integration_embeddings.py
```

Evaluate retrieval on the active reference document (the bundled evaluation targets the student
handbook):

```bash
python -m scripts.evaluate
```

Use `--questions` to point at another question file. Each question can define expected pages
(PDF), sections (DOCX/Markdown), and exact facts that must appear in the retrieved excerpts. If
you replace the document, update the evaluation set or add a new one.

To also generate answers and check the abstention behavior, point `.env` at a running LLM and
run:

```bash
python -m scripts.evaluate --answers
```

The evaluation is a small keyword smoke check, not an LLM-as-judge benchmark. Retrieval is
measured by whether the expected page or section appears in the top-k results and whether
expected facts appear in the retrieved text.

## Troubleshooting

**`No index found` or `Index is incomplete`**

```bash
python -m scripts.build_index
```

**`The reference document changed since the index was built`**

Rebuild the index. The app intentionally refuses to query mismatched evidence.

**`Could not reach the LLM at ...`**

Start the local model (`ollama serve`), check `LLM_BASE_URL`, and make sure the model is pulled
(`ollama pull llama3.2`). For a hosted provider, check the base URL includes `/v1`.

**HTTP 401/403**

`LLM_API_KEY` is missing or invalid. Set it in `.env` or Streamlit secrets and restart the app.

**`No extractable text` or OCR error**

The PDF has no text layer. OCR it first (for example with `ocrmypdf`), then rebuild.

**The answer says the document does not contain the information**

Retrieval or the model may have missed it. Try rewording the question, increase `TOP_K`, or
inspect the retrieved excerpts. Do not assume the answer is complete: verify important facts
against the source document.

**Model download fails**

The first run needs access to Hugging Face. Retry with a working connection. After the model is
cached, embedding runs locally.

## Privacy and security

- Text extraction, chunking, and embeddings happen locally. Only the top-k retrieved excerpts
  and the question are sent to the configured LLM endpoint.
- With the default local Ollama setup, those excerpts stay on your machine. A hosted provider
  receives them and may log them under its own policy; check that policy before using sensitive
  documents.
- API keys are read from `.env`, environment variables, or Streamlit secrets and are never
  displayed by the app.
- `.env` and user documents under `data/` are ignored by Git. The bundled handbook and its index
  are included so the public demo works out of the box; treat that content as public. The index
  stores document excerpts in plain text.
- Retrieved text is untrusted input. The system prompt tells the model not to follow
  instructions found in the document. This reduces prompt-injection risk but cannot eliminate
  it, especially with a weak model.

## Limitations

- One document at a time; no multi-document collections, user accounts, or conversation memory
  beyond the current browser session.
- PDF support is text extraction, not OCR. A fully image-only PDF is rejected with an OCR
  message, but individual image-only pages in an otherwise readable PDF may be omitted. Run OCR
  first if you notice missing pages. Tables in PDFs are extracted as plain text and may lose
  structure.
- Page citations are PDF page indexes (1-based), not a printed page number.
- Markdown/DOCX citations use section headings; TXT citations use only the filename.
- The default embedding model is English-focused. Choose a multilingual fastembed model if
  needed and rebuild the index.
- `MIN_SCORE` is disabled by default; retrieval always returns top-k candidates. The LLM is
  responsible for abstaining when the excerpts are insufficient. Tune the threshold and
  evaluate it for your own document.
- RAG reduces unsupported answers but does not guarantee correctness. Treat answers as a
  reading aid, not as an authoritative source.
