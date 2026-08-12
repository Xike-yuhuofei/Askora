# Askora 学习型消息系统设计推荐方案 (Design Recommendations)

**Document**: Design-Recommendations.md  
**Status**: Proposed  
**Created**: 2026-08-10  
**Supersedes**: Preview-only design questions in learning-message-system.html  

---

## 1. Hover Toolbar Positioning & Obstruction

### Problem
The current implementation positions the hover toolbar at `top: -14px`, which may obscure the first line of content in blocks that are not top-aligned with their content. This violates the "content-first" principle.

### Recommendation
**Primary Decision**: Implement an intelligent `hover-actions` slot that appears **inline** (to the right of the block title or on the trailing edge) or uses a **sticky floating panel** at the block's top-right corner that does not overlap the text content.

**Alternatives Considered**:
1.  **Inline Right-Side Slot**: Place action buttons on the right edge of the block's padding. *Rationale: Avoids vertical obstruction, keeps actions contextual.* *Trade-off: May look odd on narrow blocks.*
2.  **Bottom-Right Toolbar**: Toolbar appears below the block's last line. *Rationale: Non-intrusive.* *Trade-off: Separated from the block's visual anchor point, feels disconnected.*

**Chosen Direction**:
Use an inline, right-edge slot by default for blocks with headers (like `knowledge-block`), and a floating top-right slot for plain prose blocks. The slot will have a higher z-index but will be styled to be translucent and non-intrusive, allowing the text below to remain fully readable.

**Rationale**:
*   **Content Priority**: The user is here to read, not to interact with UI chrome. The toolbar should never cover the text.
*   **Consistency**: A single, predictable slot location reduces cognitive load.
*   **A11y**: The right-edge slot is easily reachable by both mouse and keyboard.

**Constraints**:
*   Must not reduce the block's readable width by more than 40px.
*   Must be usable on keyboard focus (not just mouse hover).

---

## 2. KnowledgeBlock Interaction vs. Dynamic Prompt Generation

### Problem
The "Test Understanding" action in the hover toolbar jumps to a static, pre-written `LearningPromptBlock`. This does not demonstrate the true dynamic capability implied by the Canonical Design.

### Recommendation
**Primary Decision**: The "Test Understanding" action should dynamically generate a `LearningPromptBlock` at runtime, tailored to the specific `KnowledgeBlock`'s content (e.g., using its `title` or `content`).

**Alternatives Considered**:
1.  **Static Jump (Current)**: Jump to a pre-written prompt. *Rationale: Simplest to implement.* *Trade-off: Not a true "dynamic" test; feels scripted.*
2.  **New Prompt Creation**: Insert a new prompt block after the current message. *Rationale: Most dynamic.* *Trade-off: Breaks the flow; user expects to see the test related to what they just read.*

**Chosen Direction**:
Generate the prompt dynamically at runtime. When "Test Understanding" is clicked, a new `prompt-block` is injected into the DOM immediately after the current message's blocks. The prompt's question text will be derived from the knowledge block's title (e.g., `为什么【Working Memory】被定义为认知瓶颈？`).

**Rationale**:
*   **Pedagogical Alignment**: The test should directly probe the user's understanding of the specific concept they just interacted with.
*   **Contextual Continuity**: Placing the test immediately after the current turn maintains the conversational flow.

**Constraints**:
*   The prompt must carry a reference (`block_ref_id`) back to the originating `KnowledgeBlock` for future evidence tracking.
*   The dynamically generated block must use the same visual styling as the static `LearningPromptBlock`.

---

## 3. ContextAnchor Persistence After Ask

### Problem
The current implementation clears the `ContextAnchor` (the `↳ 关于「xxx…」` bar) immediately after the user sends the anchored question. This might make the user lose track of what they asked about.

### Recommendation
**Primary Decision**: Preserve the `ContextAnchor` in the conversation history for the user's question, but allow it to remain visible in the composer only until the answer is generated.

**Alternatives Considered**:
1.  **Immediate Clear (Current)**: Clear on send. *Rationale: Clean slate for next input.* *Trade-off: User loses visual confirmation of context.*
2.  **Permanent Anchor**: Keep the anchor in the composer forever. *Rationale: Persistent context.* *Trade-off: Clutters the UI; user must manually clear.*

**Chosen Direction**:
When the user sends an anchored question, the composer's anchor clears immediately (clean slate), but the **user's message bubble** will visually incorporate the anchor context (e.g., `↳ 关于「工作记忆容量」\n我的追问是什么？`). The anchor is therefore preserved *in the message history*, not in the composer.

**Rationale**:
*   **Clarity**: The conversation history should show the full context of the user's input.
*   **Focus**: The composer should be ready for the next input without visual clutter.

**Constraints**:
*   The user message bubble must support multi-line rendering for the anchor context and the main question.
*   The anchor styling in the user bubble should be distinct from the main text (e.g., smaller, muted color).

---

## 4. EvidenceQuoteBlock Multi-Source Support

### Problem
The current `EvidenceQuoteBlock` only supports a single source (`src_01HX3K9N`). Real-world learning often involves synthesizing multiple sources.

### Recommendation
**Primary Decision**: Extend the `EvidenceQuoteBlock` schema to support an array of `SourceRef` objects (e.g., `sources: [{...}, {...}]`). The UI will display a "来源" count and allow clicking each source individually.

**Alternatives Considered**:
1.  **Single Source Only**: Keep as is. *Rationale: Simpler.* *Trade-off: Does not scale to multi-source synthesis.*
2.  **Stacked Blocks**: Create separate `EvidenceQuoteBlock` for each source. *Rationale: Simple implementation.* *Trade-off: Breaks the semantic grouping of a single synthesized statement.*

**Chosen Direction**:
Support multiple sources within a single block. The quote text is the synthesis, and the multiple source references are listed horizontally below it. Clicking a source opens the `Source Context` modal for that specific source.

**Rationale**:
*   **Semantic Correctness**: A single AI-generated explanation might draw from multiple page ranges or chapters.
*   **Traceability**: Users need to see exactly which parts of the source material informed the answer.

**Constraints**:
*   The maximum number of visible source badges should be 3, with a "+N" badge for overflow.
*   Each source badge must be independently clickable.

---

## 5. Next Learning Action Generation

### Problem
The current "测试一下你的理解" button is hardcoded. The Canonical Design implies this should be a dynamic decision made by the Teaching Strategy or Planner.

### Recommendation
**Primary Decision**: Treat the `NextLearningAction` as a distinct block type (`next-action-block`) with a `type` property (e.g., `test`, `apply`, `review`). The preview will simulate this by allowing the action to be changed based on the feedback type (`partial` vs `correct`).

**Alternatives Considered**:
1.  **Single Fixed Action**: Always "Test Your Understanding". *Rationale: Simple.* *Trade-off: Repetitive; not pedagogically optimal.*
2.  **Multiple Choices**: Show 3-4 action buttons. *Rationale: User choice.* *Trade-off: Violates the Canonical Rule of "one action per stopping point".*

**Chosen Direction**:
Use a single, dynamic action. After `correct` feedback, the action is "测试一下你的理解" (Test). After `partial` feedback, the action changes to "尝试另一种方法" (Retry). After multiple correct answers, it might become "应用一下" (Apply). The action's text and icon change based on the system's decision.

**Rationale**:
*   **Pedagogical Efficacy**: The system should guide the learner to the next most effective step.
*   **Adherence to Spec**: Strictly follows the "one AI-generated Next Learning Action" rule.

**Constraints**:
*   The `NextLearningAction` block must be visually distinct from regular buttons to indicate it is a system recommendation, not a user-initiated action.
*   The logic for choosing the action type must be exposed (e.g., in a developer console or hidden attribute) for design validation purposes.