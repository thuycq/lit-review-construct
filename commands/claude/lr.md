Use Literature Review Construct in the current workspace.

If `.litreview/project.yaml` exists, resume from authoritative local state by running `lrc next . --json` and follow the returned Literature Review Construct skill/action. Do not reconstruct project state from chat history.

If `.litreview/project.yaml` does not exist, start a new Literature Review Construct project only because the researcher explicitly invoked this command. Initialize the workspace, then help the researcher complete Research Intent before discovery.

Researcher-facing mode is the default:
- hide JSON, CLI commands, internal IDs, provider/test logs, and file line numbers;
- continue technical steps automatically until a genuine scholarly decision is required;
- show substantive artifacts rather than technical reports about them;
- keep full-text availability, AI full-text checking, and researcher verification distinct;
- preserve researcher authorship and do not produce a seamless submission-ready final literature review.

End checkpoints with one natural-language Suggested next message.