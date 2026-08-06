# Askora Design System

A design system for **Askora** — an AI chat and knowledge base platform with a three-column workspace layout inspired by Trae Work's interaction pattern and Apple's visual language. The system is purpose-built for conversational AI interfaces where clarity, focus, and information density must coexist.

## What this design system covers

- **Foundations** — Color (10-step primary scale + semantic palette), typography (Inter + JetBrains Mono, 9 roles), spacing (4px base, 8 tokens), radius (5 tiers), shadow (5 elevation levels)
- **Components** — 6 core components: Button, Card, Input, Navigation, Avatar, Tag
- **UI Kit** — Full chat workspace layout with left sidebar navigation, central chat canvas, and right inspector panel

---

## Content Fundamentals

### Voice & tone

Askora speaks with professional precision — the interface communicates like a knowledgeable technical assistant rather than a casual companion. Chinese is the primary interface language, delivered with technical accuracy and deliberate restraint. There are no decorative emoji, no colloquial flourishes, and no conversational filler. The tone is calm and focused: it informs, it confirms, it suggests — but it never distracts.

This restraint carries into microcopy. Error states are diagnostic, not alarmist. Empty states are instructive, not whimsical. Loading states acknowledge the user's time with precise progress language rather than motivational copy. The brand voice says: *we respect your attention.*

### Concrete copy examples

- New conversation: **新对话**
- Knowledge base: **知识库**
- Conversation history: **对话记录**
- Settings: **设置**
- Send: **发送**
- Attachment: **附件**
- Reference / citation: **引用**
- Prompt: **提示词**
- Favorites / saved: **收藏**
- Tags: **标签**
- Search: **搜索**
- History sessions: **历史会话**
- AI assistant: **智能助手**
- Document library: **文档库**
- Notes: **笔记**
- Shortcut commands: **快捷指令**

### When generating copy

- Use concise action verbs for buttons. Prefer 2-4 character labels in Chinese (发送, 收藏, 搜索).
- Keep navigation items short — 2-3 characters is the sweet spot for sidebar density (知识库, 笔记).
- Knowledge items and document titles can be descriptive and longer; they are the primary information scent.
- Avoid jargon where plain language works. Prefer 提示词 over "prompt template." Prefer 引用 over "citation anchor."
- Do not use emoji in product UI. The visual system carries all the emotional weight; copy stays neutral.
- Status labels use noun forms, not verb phrases: 已收藏, not 收藏成功.

---

## Visual Foundations

### Color

**Brand primary:** `#007AFF` — a clean system blue that reads as technical but warm, confident but not aggressive. It anchors the entire interface: primary buttons, active navigation states, user message bubbles, and interactive focus rings all draw from this hue.

**Brand scale:** A full 10-stop ramp from `#F0F7FF` (primary-50, near-white tint) through `#007AFF` (primary-500, the anchor) down to `#001A33` (primary-900, deep navy). The mid-tints — primary-100 through primary-300 — serve as active backgrounds and hover states, while the deep end (primary-700 through 900) provides on-primary-container text and dark-mode accents.

**Semantic palette:** Four functional colors, each with its own 10-step scale:
- **Success:** `#34C759` (system green) — used for confirmation states and positive indicators
- **Warning:** `#FF9500` (system orange) — used for caution and attention-requiring states
- **Error:** `#FF3B30` (system red) — used for destructive actions and error states
- **Info:** `#00B2B2` (teal) — used for informational highlights and secondary accents

**Neutrals:** A 10-stop Apple-style layered gray system from `#F9FAFB` (neutral-50) to `#1C1C1E` (neutral-900). The working grays are concentrated in the middle: `#F2F2F7` (system background), `#E5E5EA` (hairline borders), `#D1D1D6` (dividers), `#8E8E93` (muted text), `#636366` (secondary text), and `#3A3A3C` (dark surface). Dark mode inverts this: `#0B0B0D` canvas, `#1C1C1E` surface, `#2C2C2E` container, `#3A3A3C` high container — never pure black, always eye-comfort dark grays.

**Vibe:** The palette feels clean, trustworthy, and intelligent. The blue has enough saturation to feel technological but enough softness to feel approachable. The neutrals do the heavy lifting — most of the interface is gray on gray, with blue deployed sparingly as a signal of interactivity. It is a palette that recedes when you are working and guides when you need it.

### Typography

**Primary face:** **Inter** — a geometric humanist sans-serif in the SF Pro tradition. Weights in use: 400 (body), 500 (subtle emphasis), 600 (headings h2–h4), 700 (display and h1). The full fallback stack runs: `'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif` — meaning on Apple platforms, SF Pro takes over seamlessly when Inter is not bundled.

**Mono face:** **JetBrains Mono** — used for code blocks, technical references, prompt text, and any content where monospace improves readability or signals "this is machine content." Fallback: `'SF Mono', Menlo, Consolas, monospace`.

**Type scale (9 roles):**

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Display | 56px | 700 | 1.1 |
| Heading 1 | 40px | 700 | 1.2 |
| Heading 2 | 32px | 600 | 1.25 |
| Heading 3 | 24px | 600 | 1.3 |
| Heading 4 | 20px | 600 | 1.4 |
| Body | 16px | 400 | 1.6 |
| Lead | 18px | 400 | 1.7 |
| Caption | 12px | 400 | 1.5 |
| Mono | 14px | 400 | 1.6 |

Display text carries `-0.02em` letter-spacing for tightened headlines. Body text sits at a generous 1.6 line-height — typical of Apple's approach to readability on dense information surfaces. The hierarchy is balanced: headings have enough weight difference from body to create clear structure without shouting. Display sizes are reserved for hero moments and onboarding; the working interface lives in h3 through caption.

### Spacing

A **4px base unit** on an 8-point grid. The token scale runs 8 steps from `--space-1: 4px` through `--space-8: 64px`, with the most commonly used values clustering in the middle (8px, 12px, 16px, 24px). Component heights snap to the 4px grid: buttons at 32px (sm), 40px (md / default), 48px (lg). The default input height is 40px — tall enough for comfortable touch targets, compact enough for information-dense sidebars.

### Radius

- **sm (8px)** — Compact cards, form inputs, secondary containers
- **md (12px)** — Standard cards, dialogs, knowledge base items
- **lg (16px)** — Message bubbles, large panels, chat containers
- **xl (20px)** — Prominent containers, hero cards, elevated surfaces
- **full (9999px)** — Pills, chips, tag components, circular avatars

The radius scale leans generous — consistent with the Apple-inspired visual language. Even the smallest radius (8px) is soft-edged; there are no sharp corners in the system. This generosity contributes to the "refined" and "friendly" character: the interface feels approachable, not clinical.

### Shadow / Elevation

Five levels of whisper-quiet shadows, each with a specific job:

1. **Level 1 (Card):** `0 1px 2px rgba(0,0,0,.04), 0 1px 1px rgba(0,0,0,.03)` — barely perceptible hairline, used for resting cards and flat surfaces that need a hint of lift
2. **Level 2 (Card Hover):** `0 4px 10px -2px rgba(0,0,0,.08)` — subtle lift on hover, enough to feel interactive without drawing attention
3. **Level 3 (Float):** `0 8px 24px -8px rgba(0,0,0,.12)` — floating elements like popovers and dropdowns
4. **Level 4 (Modal):** `0 16px 40px -12px rgba(0,0,0,.18)` — dialogs and modal windows
5. **Level 5 (Overlay):** `0 24px 60px -20px rgba(0,0,0,.24)` — topmost overlays and full-screen panels

The philosophy is restraint. Shadows should be felt, not seen — they create depth through subtlety, not through drama. In dark mode, shadow opacities increase substantially (from .04–.24 to .20–.70) to maintain perceived depth against dark backgrounds.

### Borders and Backgrounds

Borders use the neutral-200 tone (`#E5E5EA` in light mode, `#3A3A3C` in dark) — subtle enough to recede rather than divide. They are used sparingly: mostly for input fields and explicit separators. Most spatial separation comes from background layering, not borders.

Backgrounds have four layers of depth:
- **Canvas** — `#F2F2F7` (light) / `#0B0B0D` (dark): the page-level background
- **Surface** — `#FFFFFF` (light) / `#1C1C1E` (dark): primary content containers, cards
- **Surface container** — `#F2F2F7` (light) / `#2C2C2E` (dark): nested containers, sidebar items
- **Surface container high** — `#E5E5EA` (light) / `#3A3A3C` (dark): elevated nested content, chat input areas

The sidebar sits in its own layer at `#F7F7FA` (light) / `#1C1C1E` (dark) — slightly different from both canvas and surface, creating a subtle but perceptible zone distinction.

---

## Component Patterns

| Component | Preview | Key Insight |
|-----------|---------|-------------|
| Button | `preview/component-button.html` | Pill-shaped controls with four intent levels (primary, secondary, ghost, danger); primary uses brand blue `#007AFF` with white text. Default height is 40px on the 4px grid. |
| Card | `preview/component-card.html` | Flexible container pattern used for message bubbles, knowledge items, and sidebar content. Radius varies by use case — lg for chat bubbles, md for list cards. |
| Input | `preview/component-input.html` | Chat-optimized with auto-grow textarea and integrated send action. 40px default height with 12px radius; chat input variant uses 16px radius for a softer bubble feel. |
| Navigation | `preview/component-navigation.html` | Left sidebar pattern with conversation history and knowledge base sections. Active items use primary-100 background; hover uses neutral-200. 260px fixed width. |
| Avatar | `preview/component-avatar.html` | Circular for users, rounded-square for AI assistant identity. Status indicators use semantic colors (green for active, gray for idle). |
| Tag | `preview/component-tag.html` | Soft background pills for knowledge categories and conversation labels. Full radius with neutral-100 background — low visual weight, high information density. |

---

## Index

- `README.md` — this file (brand narrative and visual foundations)
- `colors_and_type.css` — Design tokens: colors, typography, spacing, radius, shadow
- `components.css` — Aggregated component CSS extracted from preview pages
- `css.json` — Structured token data for programmatic consumption
- `components/` — Component definitions and specifications (JSON contracts)
- `preview/` — Component preview HTML pages (visual reference)
- `ui_kits/chat-workspace/` — Full chat workspace UI kit (three-column layout)
- `SKILL.md` — AI-consumable skill entry point

---

## Caveats / known substitutions

1. **Font: Inter is used as an SF Pro substitute.** On Apple platforms (macOS, iOS, visionOS), SF Pro Display and SF Pro Text should be preferred for authenticity. Inter is a close visual match and ensures cross-platform consistency when SF Pro is unavailable. The CSS fallback stack prioritizes system fonts before Inter — in production, you may want to reverse this for brand consistency.

2. **Icons: No icon library is included.** The design system defines visual style but does not ship icon assets. For Apple-inspired interfaces, use SF Symbols (on Apple platforms) or a compatible outline icon set. Match the stroke weight to the interface density — 1.5pt stroke for 20px icons is a good starting point.

3. **Assistant avatar: The AI assistant avatar is a placeholder pattern.** Replace with your brand mark or assistant character. The rounded-square shape (as opposed to user avatars which are circular) is the key design distinction to maintain.

4. **Complex interactions: Components cover visual states only.** Interaction logic — drag-and-drop, auto-suggest, streaming text animation, message threading — requires implementation. The component definitions provide the visual skeleton and state variants; behavior is out of scope.

5. **Dark mode: Token values are defined but component dark mode variants should be tested in context.** The CSS `.dark` class provides the full token inversion, but individual components may need fine-tuning for contrast and legibility in specific layout contexts.

6. **AI-generated system: This design system is AI-generated from brand guidelines.** Color scales, type scale calculations, and component proportions are inferred from the stated brand direction (Apple-inspired clean aesthetic, system blue primary). Refine with real usage data and user testing before production deployment.
