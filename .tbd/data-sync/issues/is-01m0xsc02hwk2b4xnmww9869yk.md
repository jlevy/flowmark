---
type: is
id: is-01m0xsc02hwk2b4xnmww9869yk
title: "C1 fix: compute the code-span delimiter from the longest backtick run in the content"
kind: bug
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0xsczjbncpddwkvxsehvmsz
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:21.349Z
updated_at: 2026-08-26T01:02:18.755Z
---
Site: src/flowmark/formats/flowmark_markdown.py:711-715, FlowmarkRenderer.render_code_span.

Current code:

    def render_code_span(self, element: inline.CodeSpan) -> str:
        text = element.children
        if text and (text[0] == "`" or text[-1] == "`"):
            return f"`` {text} ``"
        return f"`{element.children}`"

The widening test only looks at the FIRST and LAST characters, so a backtick anywhere in the middle emits a single-backtick delimiter that the inner backtick then closes early. That is defect C1.

Fix: derive the delimiter from the content, per CommonMark 0.31.2 section 6.1.
1. Find the longest run of consecutive backticks anywhere in the content.
2. Delimiter run length = that longest run + 1 (minimum 1).
3. Pad with one space on each side when the content starts OR ends with a backtick, or is entirely backticks. Do not pad otherwise; padding is what the reader strips back off.
4. Content that is entirely spaces must not be padded (the strip rule is inapplicable), which ties to C2 / fm-bj2c.

Keep the existing narrowing behaviour where it is safe: a wide delimiter around content with no backticks may still emit a single backtick, since the render is identical. That case is already correct today and is regression cover, not a change.

Verify against tests/tryscript/fixtures/content/code-inline.md sections A1-A9 and D6. A1, A2, A6 and A9 pass today and must keep passing; A3, A4, A5, A7, A8 and D6 currently fail.
