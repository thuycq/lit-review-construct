<!-- LIT-REVIEW-CONSTRUCT:BEGIN -->
## Lit Review Construct integration

Lit Review Construct is globally available but must not activate globally.

Activate it only when either:
1. the current workspace contains `.litreview/project.yaml`, or
2. the researcher explicitly asks to start/use Lit Review Construct.

When active, read `AGENTS.md` in the workspace if present. Use `lrc next . --json` as the authoritative workflow router. Continue technical work automatically until a genuine researcher decision is needed. Hide JSON/CLI/internal IDs/provider logs in normal responses. Preserve the distinction between full-text availability, AI checking against full text, and researcher verification. Do not write a seamless submission-ready final literature review; final scholarly judgment and prose remain researcher-authored.

Outside an active Lit Review Construct workspace, ignore these instructions.
<!-- LIT-REVIEW-CONSTRUCT:END -->
