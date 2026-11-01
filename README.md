# Thinbi Instagram AI Sales Agent — V1

Initial deployment scaffold. Never add API keys or access tokens to GitHub.

## Instagram automation safety
- Automated Instagram replies remain OFF by default. Keep `INSTAGRAM_AUTO_DMS_ENABLED=false` until Meta permissions, webhook subscriptions, token scopes, and a test event are verified.
- Comment private replies use the Instagram Messaging API `POST /{ig-user-id}/messages` with `recipient: { comment_id }`. Meta permits one private reply per comment; follow-up messaging requires the person to respond and is subject to the 24-hour messaging window.
- The app enforces one initial comment-triggered DM per Instagram-scoped commenter ID, not one per comment.
- State is written to `DATA_DIR/instagram-agent-state.json`. On Render, set `DATA_DIR` to the mount path of a persistent disk. Without a persistent disk, local file state can be lost on redeploy/restart and cannot guarantee deduplication across deployments.
- A failed/ambiguous private-send attempt is reserved rather than automatically retried, to avoid accidentally sending duplicate private replies. Review the pending-comment status before manually clearing any reservation.
- Meta webhook POST requests are rejected unless `META_APP_SECRET` is configured and the request signature is valid.

## Required Render environment variables
Set secrets in Render, never in source control:
- `META_VERIFY_TOKEN`
- `META_APP_SECRET`
- `META_ACCESS_TOKEN` (Page access token appropriate for the Facebook Login flow)
- `INSTAGRAM_ACCOUNT_ID`
- `META_GRAPH_API_VERSION` (currently configured as `v26.0`)
- `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, and optionally `OLLAMA_MODEL`
- `DATA_DIR` must be the actual persistent-disk mount path.

The agent is concise, straight-talking, listens more than it talks, and focuses on longevity/healthy aging, energy, metabolism, and NAD+. It must not pretend to be the account owner, make medical diagnoses, guarantee results, or invent product facts.
