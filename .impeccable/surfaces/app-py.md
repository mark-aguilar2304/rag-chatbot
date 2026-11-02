---
version: 1
slug: "app-py"
primary_target: "app.py"
related_targets: []
---

# Handbook Assistant — main app surface

## Scope and mode

Operate. A single Streamlit surface used by students and student-services staff to ask questions of one handbook, inspect the evidence, and manage the current session. Desktop is the primary workspace; mobile must remain usable.

## Audience, job, and constraints

- The user has a specific handbook question and needs an answer they can verify against the cited page.
- The app must preserve the real FastEmbed + NumPy + LLM pipeline and every existing operational state.
- Both light and dark themes are required. The dark shell is the default because the supplied reference is dark; the light shell must be equally intentional.
- The right rail may contain only real session information and working actions. No fake audio, video, quiz, flashcard, or note-generation tools.
- Suggested questions, citations, error states, index states, and conversation history must continue to reflect real backend data.

## Chosen direction

A graphite research desk: a three-part working surface where the handbook, the conversation, and the session sit in one quiet shell. It refuses the centered single-column chatbot and the “dashboard of cards” look.

## Direction contract

THESIS: The handbook is the room, the conversation is the desk, and every answer closes with a numbered evidence ledger. The category-default centered chat column is replaced by a three-panel research workspace with a compact composer anchored inside the center panel.

OWN-WORLD: Graphite carbons (#0B0D10 ground, #16191D panels, #1D2228 raised surfaces), hairline #2A3038 borders, soft recessed panel edges, academic blue #5B8CFF for signal in dark and #1D4ED8 in light. Public Sans for UI; Literata for the welcome heading and document title only. Pill controls, 14–18px radii, compact numbered ledger rows, one calm accent. Light counterpart: cool paper #F3F5F8, white panels, #111827 ink, blue #1D4ED8.

STORY: The student sees the reference document and its real index state, asks a question, watches retrieval and generation, reads a cited answer, opens the exact excerpts, and continues with a suggested or typed follow-up. The session rail records what has been asked; the study rail shows real evidence and index facts.

FIRST VIEWPORT: A full-height workspace. The left rail (~300px) holds the Handbook Assistant brand, New chat, the reference document card with real status, and session history. The center column carries a slim topbar with document title, index status, and theme toggle; below it the conversation panel opens on a serif welcome, a short promise, stacked suggested questions, and the fixed composer with a grounded-note. The right study rail holds real session counts, a citation guide disclosure, and index maintenance. Panels are soft-edged, separated by field, never a wall of cards.

FORM: A working research workspace, not a landing page. The supplied reference pins the shell; code-led because this is an Operate surface. Seed: none (unavailable).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
