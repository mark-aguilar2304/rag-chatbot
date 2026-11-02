---
name: Handbook Assistant
description: A dual-theme, three-panel research desk for grounded answers from one handbook.
colors:
  graphite-ground: "#0B0D10"
  graphite-panel: "#14171C"
  graphite-raised: "#191E24"
  graphite-high: "#20262E"
  graphite-line: "#2B323B"
  graphite-line-strong: "#3D4653"
  graphite-ink: "#F4F7FA"
  graphite-ink-soft: "#C8D2DE"
  graphite-muted: "#97A3B4"
  graphite-blue: "#7AA2FF"
  graphite-blue-deep: "#A8C0FF"
  graphite-blue-wash: "#18243A"
  graphite-blue-tint: "#253A5A"
  graphite-user-surface: "#1B2A45"
  paper-ground: "#F3F5F8"
  paper-panel: "#FFFFFF"
  paper-raised: "#F7F9FB"
  paper-high: "#EDF1F5"
  paper-line: "#E1E6ED"
  paper-line-strong: "#C8D1DC"
  paper-ink: "#111827"
  paper-ink-soft: "#334155"
  paper-muted: "#5B6778"
  paper-blue: "#1D4ED8"
  paper-blue-deep: "#1E40AF"
  paper-blue-wash: "#EFF4FF"
  paper-blue-tint: "#DCE8FF"
  paper-user-surface: "#EFF4FF"
  success-dark: "#71D6A1"
  success-wash-dark: "#12251A"
  success-line-dark: "#265039"
  success-light: "#166534"
  warning-dark: "#F2C56B"
  warning-light: "#92400E"
  danger-dark: "#FF9A9A"
  danger-light: "#B42318"
typography:
  display:
    fontFamily: 'Literata, "Iowan Old Style", "Palatino Linotype", Georgia, serif'
    fontSize: "clamp(2.1rem, 3.1vw, 2.9rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.032em"
  body:
    fontFamily: '"Public Sans", "Segoe UI", system-ui, -apple-system, sans-serif'
    fontSize: "0.94rem"
    fontWeight: 400
    lineHeight: 1.72
  label:
    fontFamily: '"Public Sans", "Segoe UI", system-ui, -apple-system, sans-serif'
    fontSize: "0.66rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.09em"
rounded:
  sm: "9px"
  md: "13px"
  lg: "18px"
  pill: "999px"
spacing:
  xs: "0.35rem"
  sm: "0.55rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.25rem"
  panel: "1.1rem 1.25rem 1.35rem"
components:
  panel:
    backgroundColor: "{colors.graphite-panel}"
    textColor: "{colors.graphite-ink}"
    rounded: "{rounded.lg}"
    padding: "{spacing.panel}"
  theme-toggle:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.graphite-ink-soft}"
    rounded: "{rounded.pill}"
    padding: "0.34rem 0.72rem"
  suggestion:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.graphite-ink-soft}"
    rounded: "{rounded.md}"
    padding: "0.76rem 0.9rem"
    width: "100%"
  source-row:
    textColor: "{colors.graphite-ink-soft}"
    padding: "0.6rem 0"
    height: "44px"
  status-pill:
    backgroundColor: "{colors.success-wash-dark}"
    textColor: "{colors.success-dark}"
    rounded: "{rounded.pill}"
    padding: "0.24rem 0.6rem"
  button-primary:
    backgroundColor: "{colors.graphite-blue}"
    textColor: "{colors.graphite-ground}"
    rounded: "{rounded.md}"
    padding: "0.48rem 0.8rem"
---

# Design System: Handbook Assistant

## Overview

**Creative North Star: "The Graphite Research Desk"**

The handbook is the room, the conversation is the desk, and the evidence is kept in plain sight. Graphite panels sit on a quiet field with hairline seams; academic blue appears only where the user can act or where a citation needs attention. The tone is calm, exact, and deliberately unadorned: this is a reference tool, not a study dashboard.

The layout carries that idea as three working surfaces: a reference rail, a central conversation, and a study rail limited to real session counts, citations, and index maintenance. The interface should feel like one continuous desk rather than a collection of cards. Light mode is a cool-paper counterpart, not a washed-out dark mode.

**Key Characteristics:**
- Dark-first graphite shell with an equally intentional cool-paper light mode.
- One restraint-driven academic-blue accent.
- Numbered evidence ledger rows instead of citation chips or generated summaries.
- Compact pill controls, hairline borders, and soft tonal depth.
- Serif display voice reserved for the handbook welcome and sidebar document name.

## Colors

The palette is a study in graphite and paper, with one signal blue and a small semantic set.

### Primary
- **Academic Blue**: the action, focus, and citation signal. Dark mode uses the lighter blue for contrast on graphite; light mode uses the deeper blue on paper.

### Neutral
- **Graphite Ground / Panel / Raised / High**: the dark-mode field and its three tonal steps. Separation comes from tone first and borders second.
- **Cool Paper / White Panel / Raised / High**: the light-mode counterparts. Panels are white against a cool paper field, not gray-on-gray.
- **Ink / Ink Soft / Muted**: the text hierarchy. Muted is for metadata and helper copy; it is never used for primary answer text.
- **Hairline / Hairline Strong**: seams and disclosure boundaries. Strong is reserved for hover and focus-adjacent states.

### Named Rules
**The One Accent Rule.** Academic blue marks actions, links, citations, and focus. It never becomes a decorative wash or a second brand color.

**The Two-Room Rule.** Dark and light are separate rooms with the same furniture. Every surface, state, and control must be designed in both; a light theme that merely inverts the dark one is unfinished.

## Typography

**Display Font:** Literata (with Iowan Old Style, Palatino Linotype, Georgia)
**Body Font:** Public Sans (with Segoe UI, system-ui, sans-serif)
**Label Font:** Public Sans, uppercase with tracking

**Character:** Literata gives the document a measured, editorial voice. Public Sans keeps the working interface plain and legible. The pairing separates reading the handbook from operating the desk.

### Hierarchy
- **Display** (600, clamp(2.1rem, 3.1vw, 2.9rem), 1.1): the welcome statement and the sidebar document name only.
- **Headline** (600, 1.05rem, 1.3): panel titles and the state-message heading.
- **Title** (600, 0.9rem, 1.4): document names and source locations.
- **Body** (400, 0.94rem, 1.72): answers, excerpts, and explanations, held to a 72ch measure.
- **Label** (700, 0.66rem, 0.09em, uppercase): rail section labels and small metadata.

### Named Rules
**The Serif Has a Job Rule.** Literata belongs to the handbook and the welcome. Controls, counts, citations, and error copy stay in Public Sans.

## Layout

The workspace is a full-height shell. A 300px native sidebar holds the reference and session history; the main area is capped at 1440px and splits into a flexible chat column and a 320px study rail. The two main panels share a 1rem gutter and use soft 18px corners. At 1150px the study rail stacks below the conversation; at 640px the topbar compacts to one row and the panels use the full width. The composer is anchored at the bottom of the viewport, with enough reserved space that the last answer is never hidden behind it. Suggested questions are full-width rows, not a card grid.

## Elevation & Depth

Depth is tonal and structural: the ground recedes, white or graphite panels sit above it, and a 1px hairline defines the edge. The soft panel shadow is a quiet lift, not a drop-shadow spectacle. There are no floating cards, colored glows, or nested surfaces.

### Shadow Vocabulary
- **Panel Rest** (`0 1px 2px rgba(0,0,0,0.4), 0 8px 22px rgba(0,0,0,0.2)` in dark; the light counterpart is correspondingly faint): separates a working panel from the field without implying a modal.
- **Large Lift** (`0 18px 40px rgba(0,0,0,0.34)` in dark): reserved for the shell's strongest raised moment, not for ordinary rows.

### Named Rules
**The Hairline First Rule.** If a border can explain the boundary, do not add a shadow. If a shadow can explain the lift, do not add a second border.

## Shapes

Edges are gently rounded and consistent: 9px for small controls, 13px for inputs and numbered rows, 18px for panels, and a full pill for status and theme controls. The numbered source index is a 5px-radius square, visually distinct from the circular status dots and avatar marks. Borders are always 1px so the interface stays drawn rather than embossed.

## Components

### Buttons
- **Shape:** 13px rounded rectangle for task buttons; full pill for theme and status.
- **Primary:** academic blue field with opposite-tone text, used only for the build action when the index is unavailable.
- **Secondary:** raised panel tone, hairline border, ink-soft label. Hover raises the border contrast and shifts the label toward ink.
- **Focus:** a 3px academic-blue ring with a 3px offset, visible on native buttons and custom disclosures.

### Chips
- **Style:** pill shape, tonal wash, small uppercase-or-sentence label, and a semantic dot where state matters.
- **State:** green for indexed, amber for needs attention, red for missing or failed. The label always carries the meaning; color is reinforcement.

### Cards / Containers
- **Corner Style:** 18px.
- **Background:** panel white in light mode; graphite panel in dark.
- **Shadow Strategy:** the low panel shadow from Elevation & Depth.
- **Border:** 1px hairline.
- **Internal Padding:** 1.1rem to 1.35rem, tighter than the gutters between working surfaces.

### Inputs / Fields
- **Style:** raised tonal field, 13px corner, 1px hairline, body-size placeholder.
- **Focus:** the shared blue focus ring; no glow.
- **Disabled:** muted label on the raised field, with the action still named.

### Navigation
- **Style:** the native Streamlit sidebar is the reference rail. Brand at the top, New chat as a secondary full-width action, then document identity, evidence, and session history in that order.
- **Mobile:** the sidebar collapses to a named expand control; the main topbar keeps the document title, index summary, and theme toggle on one row.

### Source Ledger (signature)
The answer closes with a numbered list of real retrieved passages. Each row is a 44px disclosure with a small index, a document/page or section label, and a chevron. Opening a row reveals the exact excerpt. The ledger is a hairline list, never a stack of cards; citations in the answer use the same numbers.

## Do's and Don'ts

### Do:
- **Do** keep the evidence ledger tied to backend metadata and real excerpts.
- **Do** design every state in both themes: empty, loading, abstention, error, stale index, missing document.
- **Do** keep controls at least 44px where the control is a primary touch target, and always preserve the 3px blue focus ring.
- **Do** reserve Literata for the welcome and the sidebar document name.
- **Do** use real session counts and working actions in the study rail.

### Don't:
- **Don't** add audio, video, quiz, flashcard, or note-generation tools that the backend cannot produce.
- **Don't** turn the study rail into a dashboard of decorative metrics.
- **Don't** use colored left borders, gradient text, glass panels, or nested cards.
- **Don't** invent citations, page numbers, or document status.
- **Don't** make the light theme a simple inversion of the dark one.
