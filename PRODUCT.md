# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

University students and student-services staff who need quick, trustworthy answers from a single student handbook. They often arrive with a specific policy question and need to check the cited page before acting on the answer. They use the app at a desk or on a phone, in both bright and dim environments.

## Product Purpose

A single-document RAG assistant that answers questions only from the configured handbook, shows the retrieved passages, and abstains when the evidence is insufficient. Success means the user can find a policy, see where it came from, and judge whether the answer is trustworthy without reading the whole handbook.

## Positioning

The assistant exposes its evidence instead of hiding it: citations come from real retrieval metadata, retrieved excerpts are inspectable, and the app refuses to answer from a stale or missing index. It is a transparent reference desk, not an ungrounded chatbot.

## Operating Context

- Existing Streamlit application with local fastembed embeddings and a persistent NumPy index.
- One reference document at a time; the active workspace uses `data/student-handbook.pdf` with 383 indexed passages.
- Answers come from a configured OpenAI-compatible LLM; the current workspace uses OpenRouter.
- Conversation history is session-only; there are no accounts, sync, or persistent notes.
- The interface must support both light and dark themes with a working toggle.
- The layout is a three-panel workspace: reference and session rail, central chat, and a real study/session panel.

## Capabilities and Constraints

- Supported sources: PDF, DOCX, TXT, and Markdown.
- PDF page numbers and DOCX/Markdown section headings are surfaced when present.
- Retrieval returns the top matching passages; the LLM must answer from those passages or abstain.
- The app detects missing, incomplete, incompatible, or stale indexes and offers a rebuild action.
- Suggested questions are curated from the verified handbook evaluation set and submit through the real pipeline.
- The right panel must contain only working controls and truthful session information. Do not present audio overviews, video overviews, quizzes, flashcards, or other generation tools that the backend cannot produce.
- No hardcoded answers, fake document statuses, or invented citation metadata.
- Keep the existing Python/Streamlit stack and RAG modules; this is a presentation and interaction redesign.

## Brand Commitments

- Product name: Handbook Assistant.
- Voice: calm, precise, academic, and plain-spoken.
- Visual reference supplied by the user: a modern, minimalist three-panel research workspace in the spirit of NotebookLM, with compact pill controls, soft rounded panels, muted surfaces, clear hierarchy, and a dark-first feel.
- Both light and dark themes are required, with a visible, working theme toggle.
- Academic blue remains the primary accent; avoid gamified, neon, or decorative dashboard styling.

## Evidence on Hand

- `data/student-handbook.pdf`: active reference document, 383 chunks, indexed.
- `eval/student_handbook_questions.json`: verified retrieval and answer evaluation questions.
- `tests/`: offline test suite; the live evaluation previously passed 10/10 answer and 8/8 retrieval checks.
- The workspace `.env` contains live OpenRouter settings and is Git-ignored. Never expose the API key.
- No persistent conversation store, user accounts, audio/video generation, quiz generation, or flashcard generation exists.

## Product Principles

1. Evidence before confidence: every answer shows where it came from, and insufficiency is stated plainly.
2. One calm workspace: reference, conversation, and session tools stay visible without competing for attention.
3. Real state only: loading, empty, indexed, sitemap, and error surfaces reflect the actual backend.
4. Readable in any light: both themes meet contrast and focus requirements and remain usable on mobile.
5. Low-friction study: suggested questions and session tools help the user continue without inventing capabilities.

## Accessibility & Inclusion

- Target WCAG 2.1 AA for contrast, focus visibility, keyboard operation, and touch targets.
- The theme toggle and all controls must be keyboard reachable and clearly named.
- Native disclosure elements for sources and technical details so content works without custom JavaScript.
- Responsive layout at desktop and mobile widths; no horizontal scrolling.
