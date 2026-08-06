---
name: askora-design
description: Use this skill to generate well-branded interfaces for Askora. Contains colors, type, fonts, assets, and UI kit for prototyping chat-workspace UIs.
user-invocable: true
---
# Askora Design Skill

Read the `README.md` file within this skill, and explore the other available files.

If creating visual artifacts, copy assets out and create static HTML files. If working on production code, read the rules here to become an expert in designing with this brand.

## Quick map

- `README.md` — brand context, content fundamentals, visual foundations (read first)
- `css.json` — structured token understanding source
- `colors_and_type.css` — drop-in runtime CSS variables; link it, do not read it to understand tokens when css.json exists
- `components/index.json` — component index + cross-component patterns
- `components/{slug}.json` — component contract (intent/variants); preview HTML is the first source for DOM/CSS fidelity
- `components.css` — aggregated component CSS
- `preview/` — small HTML cards illustrating foundations and components (primary fidelity source)
- `library-consumption.json` — recommended downstream read order
- `ui_kits/chat-workspace/` — full click-thru recreation (layout, density, patterns reference)

## Essentials at a glance

- Primary: brand blue `#007AFF` — Apple-inspired system blue, clean and intelligent, no warm accents
- Radius: 8/12/16/20/9999px — generous rounded corners, pill-shaped controls, soft and friendly
- Control height: 40px default, 4px spacing unit, 8-pt grid system
- Type: Inter (SF Pro style) + JetBrains Mono, 9 type roles from display to caption
- Voice: professional Chinese-first, clean and precise, no emoji in UI
- Shadows: 5 whisper-quiet levels from subtle card to modal overlay
- AI-first design: dedicated chat message bubbles, assistant/user variants, three-column workspace layout

## Components

| Slug | Name | Key Insight |
|------|------|-------------|
| button | Button | Apple-style pill buttons with primary/secondary/ghost/destructive variants |
| card | Card | Multi-purpose card for message bubbles, knowledge items, and sidebar panels |
| input | Input | Chat-optimized input with send button and auto-growing textarea |
| navigation | Navigation | Left sidebar with conversation list and knowledge base sections |
| avatar | Avatar | User and AI assistant avatars with status indicators |
| tag | Tag | Knowledge tags and conversation labels with soft Apple-style backgrounds |
