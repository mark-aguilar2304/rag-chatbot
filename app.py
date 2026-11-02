"""Streamlit UI for the single-document handbook assistant."""

from __future__ import annotations

import html
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from src.config import Settings, load_settings
from src.embeddings import FastEmbedder
from src.generation import LLMError, OpenAICompatibleLLM, answer_question
from src.indexer import build_index
from src.ingestion import DocumentError
from src.retrieval import retrieve
from src.vector_store import (
    IndexFormatError,
    IndexNotFoundError,
    IndexStore,
    StaleIndexError,
)
from ui.theme import apply_theme

logger = logging.getLogger(__name__)

APP_NAME = "Handbook Assistant"

# Curated for data/student-handbook.pdf. Update these if the reference document changes.
SUGGESTED_QUESTIONS = [
    "How many absences are allowed in a class that meets once a week?",
    "What is the maximum period for an approved leave of absence?",
    "When can I drop a subject and what refund do I get?",
    "What are the uniform rules on Wednesdays and Saturdays?",
]

BOOK_ICON = '<span class="icon icon-book" aria-hidden="true"></span>'
FILE_ICON = '<span class="icon icon-file" aria-hidden="true"></span>'
CHAT_ICON = '<span class="icon icon-chat" aria-hidden="true"></span>'
STUDY_ICON = '<span class="icon icon-study" aria-hidden="true"></span>'

st.set_page_config(
    page_title=APP_NAME,
    page_icon=":material/menu_book:",
    layout="wide",
    initial_sidebar_state="auto",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
apply_theme(st.session_state.theme)


@st.cache_resource(show_spinner=False)
def get_embedder(model_name: str) -> FastEmbedder:
    return FastEmbedder(model_name)


def index_status(settings: Settings) -> tuple[IndexStore | None, str | None]:
    try:
        store = IndexStore.load(settings.index_dir)
        store.ensure_compatible(
            settings.embedding_model, settings.chunk_size, settings.chunk_overlap
        )
        store.validate_source(settings.document_path)
        return store, None
    except (IndexNotFoundError, IndexFormatError, StaleIndexError) as exc:
        return None, str(exc)


def source_label(source: dict[str, Any]) -> str:
    parts: list[str] = []
    if source.get("page") is not None:
        parts.append(f"Page {source['page']}")
    if source.get("section"):
        parts.append(f"Section “{source['section']}”")
    name = source.get("source") or "Reference document"
    return f"{name} · {' · '.join(parts)}" if parts else name


def is_insufficient(text: str) -> bool:
    prefix = text.strip().casefold()
    return prefix.startswith(
        (
            "i couldn't find that",
            "i could not find that",
            "i can't find that",
            "i cannot find that",
        )
    )


def format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, round(size / 1024))} KB"


def format_built(store: IndexStore) -> str | None:
    raw = store.manifest.get("created_at")
    if not raw:
        return None
    try:
        built = datetime.fromisoformat(str(raw))
        if built.tzinfo is None:
            built = built.replace(tzinfo=timezone.utc)
        return built.astimezone().strftime("%d %b %Y")
    except ValueError:
        return None


def document_status(store: IndexStore | None, document_exists: bool) -> tuple[str, str]:
    if store is not None:
        return "Indexed", "ready"
    if not document_exists:
        return "File missing", "danger"
    return "Needs indexing", "warning"


def status_pill(label: str, style: str) -> str:
    return (
        f'<span class="status-pill status-pill--{style}">'
        f'<span class="status-dot" aria-hidden="true"></span>{html.escape(label)}</span>'
    )


def latest_sources(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message.get("sources", [])
    return []


def build_and_store(settings: Settings) -> int:
    embedder = get_embedder(settings.embedding_model)
    store = build_index(
        settings.document_path,
        settings.index_dir,
        embedder,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return len(store.chunks)


def rebuild_index(settings: Settings) -> None:
    try:
        with st.spinner("Reading, chunking, and embedding the document..."):
            count = build_and_store(settings)
        st.session_state["flash"] = f"Index rebuilt — {count} passages are ready."
        st.rerun()
    except DocumentError as exc:
        st.error(f"Document error: {exc}")
    except Exception as exc:
        logger.exception("Index build failed")
        st.error(f"Index build failed: {exc}")


def render_topbar(
    settings: Settings, store: IndexStore | None, document_exists: bool
) -> None:
    label, style = document_status(store, document_exists)
    count = f"{len(store.chunks)} passages indexed" if store is not None else "Index not ready"
    dark = st.session_state.theme == "dark"
    next_theme = "light" if dark else "dark"
    theme_label = "Light" if dark else "Dark"
    theme_icon = ":material/light_mode:" if dark else ":material/dark_mode:"

    with st.container(key="topbar"):
        title_col, action_col = st.columns(
            [1, 0.22], gap="small", vertical_alignment="center"
        )
        with title_col:
            st.html(
                f"""
                <div class="workspace-title">
                  <span class="workspace-mark" aria-hidden="true">{FILE_ICON}</span>
                  <div class="workspace-copy">
                    <h1>{html.escape(settings.document_path.name)}</h1>
                    <div class="workspace-subtitle">
                      <span>{html.escape(count)}</span>
                      {status_pill(label, style)}
                    </div>
                  </div>
                </div>
                """
            )
        with action_col:
            if st.button(
                theme_label,
                icon=theme_icon,
                key="theme_toggle",
                help=f"Switch to {next_theme} theme",
            ):
                st.session_state.theme = next_theme
                st.rerun()


def render_sidebar(
    settings: Settings, store: IndexStore | None, document_exists: bool
) -> None:
    messages = st.session_state.messages
    questions = [m["content"] for m in messages if m["role"] == "user"]
    label, style = document_status(store, document_exists)

    with st.sidebar:
        st.html(
            f"""
            <div class="brand">
              <span class="brand-mark" aria-hidden="true">{BOOK_ICON}</span>
              <div class="brand-copy">
                <div class="brand-name">{html.escape(APP_NAME)}</div>
                <div class="brand-sub">Student reference</div>
              </div>
            </div>
            """
        )

        if st.button(
            "New chat",
            icon=":material/add:",
            key="new_chat",
            use_container_width=True,
            disabled=not messages,
        ):
            st.session_state.messages = []
            st.session_state.pop("pending_prompt", None)
            st.rerun()

        size = settings.document_path.stat().st_size if document_exists else 0
        if store is not None:
            meta = f"{len(store.chunks)} passages · {format_size(size)}"
            built = format_built(store)
            engine = store.manifest.get("embedding_model") or settings.embedding_model
            dimension = store.manifest.get("dimension")
            engine_meta = f"{engine} · {dimension}-dim" if dimension else str(engine)
            built_html = (
                f'<span class="doc-built">Built {html.escape(built)}</span>'
                if built
                else ""
            )
            engine_html = f'<div class="doc-engine">{html.escape(engine_meta)}</div>'
        else:
            meta = (
                f"Not indexed · {format_size(size)}"
                if document_exists
                else "The configured file is missing"
            )
            built_html = ""
            engine_html = ""

        st.html(
            f"""
            <section class="side-section" aria-label="Reference document">
              <div class="side-label">Reference</div>
              <div class="doc-summary">
                <span class="doc-icon" aria-hidden="true">{FILE_ICON}</span>
                <div>
                  <div class="doc-name">{html.escape(settings.document_path.name)}</div>
                  <div class="doc-meta">{html.escape(meta)}</div>
                </div>
              </div>
              <div class="doc-bottom">
                {status_pill(label, style)}
                {built_html}
              </div>
              {engine_html}
            </section>
            """
        )

        last_sources = latest_sources(messages)
        if last_sources:
            source_items = "".join(
                f'<li class="rail-source">'
                f'<span class="rail-source-index">{number}</span>'
                f'<span class="rail-source-label">{html.escape(source_label(source))}</span>'
                f"</li>"
                for number, source in enumerate(last_sources, start=1)
            )
            st.html(
                f"""
                <section class="side-section" aria-label="Sources in last answer">
                  <div class="side-label">Sources in last answer</div>
                  <ol class="rail-source-list">{source_items}</ol>
                </section>
                """
            )

        if questions:
            visible = questions[-5:]
            items = "".join(
                f'<li class="history-item" title="{html.escape(question, quote=True)}">'
                f"{html.escape(question)}</li>"
                for question in visible
            )
            more = (
                f'<div class="history-more">+{len(questions) - len(visible)} earlier questions</div>'
                if len(questions) > len(visible)
                else ""
            )
            history_html = f'<ol class="history-list">{items}</ol>{more}'
        else:
            history_html = (
                '<div class="history-note">Questions you ask will appear here.</div>'
            )

        st.html(
            f"""
            <section class="side-section" aria-label="This conversation">
              <div class="side-label">This conversation</div>
              {history_html}
            </section>
            """
        )

        st.html(
            '<div class="side-footer">Answers are grounded in one reference document. '
            "Verify important decisions against the cited page.</div>"
        )


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        st.html(
            '<div class="no-sources">No passages were retrieved for this question.</div>'
        )
        return

    items: list[str] = []
    for number, source in enumerate(sources, start=1):
        excerpt = html.escape(str(source.get("text", ""))).replace("\n", "<br>")
        items.append(
            f'<li><details class="source-item">'
            f'<summary><span class="source-index">{number}</span>'
            f'<span class="source-location">{html.escape(source_label(source))}</span>'
            f'<span class="source-chevron" aria-hidden="true"></span></summary>'
            f'<div class="source-excerpt">{excerpt}</div>'
            f"</details></li>"
        )

    st.html(
        f"""
        <div class="sources">
          <div class="sources-heading">
            <span>Sources</span>
            <span class="sources-count">{len(sources)}</span>
          </div>
          <ol class="source-list">{"".join(items)}</ol>
        </div>
        """
    )


def render_message_meta(role: str, filename: str) -> None:
    if role == "user":
        st.html('<div class="message-meta"><span class="message-author">You</span></div>')
    else:
        st.html(
            f'<div class="message-meta"><span class="message-author message-author--assistant">'
            f"Handbook Assistant</span>"
            f'<span class="message-context">{html.escape(filename)}</span></div>'
        )


def render_error(message: str, title: str = "Couldn't prepare an answer") -> None:
    detail = html.escape(message).replace("\n", "<br>")
    st.html(
        f"""
        <div class="message-error">
          <div class="message-error-title">{html.escape(title)}</div>
          <p>{detail}</p>
          <p class="message-error-help">Try again. If it keeps happening, check the app terminal
          and the LLM settings in <code>.env</code>.</p>
        </div>
        """
    )


def render_message(message: dict[str, Any], filename: str) -> None:
    if message["role"] == "user":
        with st.chat_message("user", avatar=":material/person:"):
            render_message_meta("user", filename)
            st.html(f'<div class="user-copy">{html.escape(message["content"])}</div>')
        return

    with st.chat_message("assistant", avatar=":material/menu_book:"):
        render_message_meta("assistant", filename)
        if message.get("error"):
            render_error(str(message["error"]))
            return
        content = message.get("content", "")
        if is_insufficient(content):
            st.html(
                '<div class="answer-note"><span class="status-dot" aria-hidden="true"></span>'
                "Not enough evidence in the reference document</div>"
            )
        st.markdown(content)
        render_sources(message.get("sources", []))


def render_welcome(settings: Settings, store: IndexStore) -> None:
    st.html(
        """
        <div class="welcome">
          <h2>Find your way through the handbook.</h2>
          <p>Ask about policies, deadlines, or requirements. Every answer ends with the
          passages it came from, so you can check the page before you act.</p>
        </div>
        """
    )
    st.html('<div class="suggest-label">Try a question</div>')
    with st.container(key="suggestions"):
        for index, question in enumerate(SUGGESTED_QUESTIONS):
            if st.button(question, key=f"suggestion_{index}", use_container_width=True):
                st.session_state["pending_prompt"] = question
                st.rerun()
    st.html(
        f'<div class="welcome-note"><span class="status-dot" aria-hidden="true"></span>'
        f"Grounded in {html.escape(settings.document_path.name)} · "
        f"{len(store.chunks)} passages indexed</div>"
    )


def render_not_ready(
    settings: Settings, index_error: str | None, document_exists: bool
) -> None:
    if document_exists:
        title = "The index needs attention."
        body = (
            "The assistant can search the document only after it has been indexed. "
            "Rebuild the index to continue."
        )
        detail = index_error or "No usable index was found."
    else:
        title = "The reference document is missing."
        body = (
            "The file configured in DOCUMENT_PATH is not available. Add the document, "
            "update .env, then rebuild the index."
        )
        detail = ""

    detail_html = (
        f'<details class="rail-details state-details"><summary>Technical detail</summary>'
        f"<p>{html.escape(detail)}</p></details>"
        if detail
        else ""
    )
    st.html(
        f"""
        <div class="state-block">
          <span class="state-mark" aria-hidden="true">{FILE_ICON}</span>
          <h2>{html.escape(title)}</h2>
          <p>{html.escape(body)}</p>
          {detail_html}
        </div>
        """
    )
    if document_exists:
        if st.button(
            "Build index now",
            type="primary",
            icon=":material/play_arrow:",
            key="build_index_main",
        ):
            rebuild_index(settings)
    else:
        st.html(
            '<p class="state-help">Place the file in the project, set DOCUMENT_PATH '
            "in .env, and rebuild the index.</p>"
        )


def render_flash() -> None:
    flash = st.session_state.pop("flash", None)
    if flash:
        st.html(
            f'<div class="flash-message" role="status"><span class="status-dot" '
            f'aria-hidden="true"></span>{html.escape(str(flash))}</div>'
        )


def render_study_panel(
    settings: Settings,
    store: IndexStore | None,
    document_exists: bool,
    messages: list[dict[str, Any]],
) -> None:
    questions = [m["content"] for m in messages if m["role"] == "user"]
    last_sources = latest_sources(messages)
    answered = any(m["role"] == "assistant" for m in messages)
    label, style = document_status(store, document_exists)
    passage_count = len(store.chunks) if store is not None else "—"
    source_count = str(len(last_sources)) if answered else "—"
    question_label = f"{len(questions)} question{'s' if len(questions) != 1 else ''}"

    st.html(
        f"""
        <div class="panel-head">
          <div class="panel-title">{STUDY_ICON}<span>Study desk</span></div>
          <span class="panel-note">{html.escape(question_label)}</span>
        </div>
        <section class="rail-section" aria-label="Session">
          <div class="rail-label">Session</div>
          <dl class="rail-stats">
            <div class="rail-stat"><dt>Questions</dt><dd>{len(questions)}</dd></div>
            <div class="rail-stat"><dt>Sources in last answer</dt><dd>{source_count}</dd></div>
            <div class="rail-stat"><dt>Indexed passages</dt><dd>{passage_count}</dd></div>
          </dl>
        </section>
        """
    )

    if questions:
        asked = {question.casefold() for question in questions}
        remaining = [
            question
            for question in SUGGESTED_QUESTIONS
            if question.casefold() not in asked
        ]
        st.html('<div class="rail-label rail-label--section">Try next</div>')
        if remaining:
            with st.container(key="rail_questions"):
                for index, question in enumerate(remaining[:3]):
                    if st.button(
                        question,
                        key=f"rail_question_{index}",
                        use_container_width=True,
                    ):
                        st.session_state["pending_prompt"] = question
                        st.rerun()
        else:
            st.html('<p class="rail-note">You have tried all suggested questions.</p>')

    st.html(
        """
        <section class="rail-section" aria-label="Citation guide">
          <div class="rail-label">Reading citations</div>
          <details class="rail-details">
            <summary>How sources work</summary>
            <p>Each answer ends with numbered passages from the handbook. Page numbers
            and sections come from the document itself. Open a source row to read the
            exact excerpt before you rely on the answer.</p>
          </details>
        </section>
        """
    )

    if store is not None:
        engine = store.manifest.get("embedding_model") or settings.embedding_model
        built = format_built(store)
        built_row = (
            f'<div class="rail-index-row"><span>Built</span><strong>{html.escape(built)}</strong></div>'
            if built
            else ""
        )
        st.html(
            f"""
            <section class="rail-section" aria-label="Index">
              <div class="rail-label">Index</div>
              <div class="rail-index">
                <div class="rail-index-row"><span>Status</span>{status_pill(label, style)}</div>
                <div class="rail-index-row"><span>Passages</span><strong>{len(store.chunks)}</strong></div>
                <div class="rail-index-row"><span>Model</span><strong>{html.escape(str(engine))}</strong></div>
                {built_row}
              </div>
            </section>
            """
        )
        if st.button(
            "Rebuild index",
            icon=":material/refresh:",
            key="rebuild_rail",
            use_container_width=True,
        ):
            rebuild_index(settings)
    else:
        st.html(
            f"""
            <section class="rail-section" aria-label="Index">
              <div class="rail-label">Index</div>
              <div class="rail-index">
                <div class="rail-index-row"><span>Status</span>{status_pill(label, style)}</div>
                <div class="rail-index-row"><span>Passages</span><strong>—</strong></div>
              </div>
              <p class="rail-note">The conversation panel will offer a build action when the
              configured document is available.</p>
            </section>
            """
        )

    st.html(
        '<div class="rail-footer">One reference document, no web search. '
        "Citations point to the page you should verify.</div>"
    )


def render_chat_panel(
    settings: Settings,
    store: IndexStore | None,
    messages: list[dict[str, Any]],
    pending_prompt: str | None,
    index_error: str | None,
    document_exists: bool,
) -> None:
    questions = [m for m in messages if m["role"] == "user"]
    question_label = f"{len(questions)} question{'s' if len(questions) != 1 else ''}"
    st.html(
        f"""
        <div class="panel-head">
          <div class="panel-title">{CHAT_ICON}<span>Chat</span></div>
          <span class="panel-note">{html.escape(question_label)}</span>
        </div>
        """
    )
    render_flash()

    if store is None:
        render_not_ready(settings, index_error, document_exists)
        return

    if not messages and not pending_prompt:
        render_welcome(settings, store)

    for message in messages:
        render_message(message, settings.document_path.name)

    if pending_prompt:
        answer_prompt(pending_prompt, settings, store)


def answer_prompt(prompt: str, settings: Settings, store: IndexStore) -> None:
    filename = settings.document_path.name
    with st.chat_message("assistant", avatar=":material/menu_book:"):
        render_message_meta("assistant", filename)
        try:
            with st.spinner("Searching the handbook and preparing a cited answer..."):
                embedder = get_embedder(settings.embedding_model)
                results = retrieve(
                    prompt,
                    embedder,
                    store,
                    top_k=settings.top_k,
                    min_score=settings.min_score,
                )
                llm = OpenAICompatibleLLM(
                    settings.llm_base_url,
                    settings.llm_model,
                    settings.llm_api_key,
                    settings.llm_timeout,
                )
                answer = answer_question(prompt, results, llm)

            sources = [asdict(source) for source in answer.sources]
            st.session_state.messages.append(
                {"role": "assistant", "content": answer.text, "sources": sources}
            )
            st.rerun()
        except (LLMError, ValueError) as exc:
            st.session_state.messages.append(
                {"role": "assistant", "content": "", "sources": [], "error": str(exc)}
            )
            st.rerun()
        except Exception:
            logger.exception("Answer generation failed")
            message = (
                "Something went wrong while preparing the answer. "
                "Check the app terminal and try again."
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": "", "sources": [], "error": message}
            )
            st.rerun()


try:
    settings = load_settings()
except ValueError as exc:
    st.html(
        f"""
        <div class="fatal-shell">
          <div class="fatal-brand">
            <span class="brand-mark" aria-hidden="true">{BOOK_ICON}</span>
            <div>
              <div class="brand-name">{html.escape(APP_NAME)}</div>
              <div class="brand-sub">Student reference</div>
            </div>
          </div>
          <div class="state-card state-card--error">
            <h2>Configuration needs attention</h2>
            <p>The app could not start because a setting is invalid.</p>
            <div class="state-detail">{html.escape(str(exc))}</div>
            <p class="state-help">Update <code>.env</code> and reload the app.</p>
          </div>
        </div>
        """
    )
    st.stop()

store, index_error = index_status(settings)
ready = store is not None
document_exists = settings.document_path.is_file()

if "messages" not in st.session_state:
    st.session_state.messages = []

if ready:
    # Keep the welcome composer inline so the three-panel shell does not auto-scroll
    # past its heading on short screens. Once a conversation exists, use the standard
    # bottom composer so new answers stay in view.
    if st.session_state.messages:
        typed_prompt = st.chat_input("Ask about the handbook...", max_chars=2000)
    else:
        with st.bottom:
            typed_prompt = st.chat_input("Ask about the handbook...", max_chars=2000)
    if typed_prompt:
        st.session_state["pending_prompt"] = typed_prompt
        st.rerun()
else:
    typed_prompt = None

pending_prompt = st.session_state.pop("pending_prompt", None)
if pending_prompt:
    clean_prompt = pending_prompt.strip()
    if clean_prompt:
        st.session_state.messages.append({"role": "user", "content": clean_prompt})
        pending_prompt = clean_prompt
    else:
        pending_prompt = None

render_sidebar(settings, store, document_exists)
render_topbar(settings, store, document_exists)

with st.container(key="workspace"):
    chat_col, study_col = st.columns([1, 0.42], gap="medium", vertical_alignment="top")
    # Render the study rail first so it stays visible while the answer is generated.
    with study_col:
        with st.container(key="study_panel"):
            render_study_panel(
                settings,
                store,
                document_exists,
                st.session_state.messages,
            )
    with chat_col:
        with st.container(key="chat_panel"):
            render_chat_panel(
                settings,
                store,
                st.session_state.messages,
                pending_prompt,
                index_error,
                document_exists,
            )

