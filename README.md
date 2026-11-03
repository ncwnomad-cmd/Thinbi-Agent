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


## Local ComfyUI GPU coloring-book workflow

The optional coloring-book routes run only on the Windows machine that hosts this agent. They connect to ComfyUI at 127.0.0.1:8188; the route and URL checks reject non-loopback access. Do not expose the ComfyUI API to the public internet.

- GET /coloring-book/status checks local ComfyUI and GPU status.
- POST /coloring-book/create queues one illustration.
- POST /coloring-book/batch queues up to five sequential illustrations.
- GET /coloring-book/history/:promptId checks a ComfyUI job.
- POST /coloring-book/assemble runs print preparation and PDF assembly.

See docs/local-comfyui-gpu.md for the CUDA 12.6 PyTorch setup and verification script. Local settings may be placed in an untracked .env file: COMFYUI_URL, COLORING_BOOK_ROOT, COLORING_BOOK_PYTHON, and COLORING_BOOK_CHECKPOINT.

The Cozy Christmas KDP interior is 100 pages total: 50 illustrated fronts plus 50 blank backs. The generator resumes from existing numbered illustrations, excludes TEST-named outputs, and the assembler defaults to 50 illustrations. Review the art visually before uploading to KDP.

The Render service remains a Node.js web service. These local ComfyUI routes do not provision a GPU on Render and remain unavailable to remote clients by design.
