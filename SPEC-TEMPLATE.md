# SPEC.md Template
# Copy this to the root of every feature branch and fill it in.
# The spec compliance checker reads this file to verify PR changes.

# [Feature Name]
## Spec for Claude Code
## [Date]

## Reference
- Architecture: Read `ARCHITECTURE.md` in the project root FIRST
- Repo: `stygies-viii/epi`
- CLAUDE.md: https://github.com/stygies-viii/black-factory/blob/main/CLAUDE.md

## Purpose
[One paragraph: what are we building and why]

## DO NOT
- Do NOT create a new project or repo
- Do NOT create new auth flows — use existing `get_current_user` dependency
- Do NOT create a new database — use existing Neon database
- Do NOT touch the pixel code
- Do NOT update Clerk, Stripe, or any auth dependencies
- Do NOT modify `frontend/src/middleware.ts` or `backend/app/security.py`
- Work on a feature branch: `feature/[name]`

---

## What Already Exists (Read These First)
[List existing files/tables/endpoints the agent should read before coding]

---

## Changes

### [Change 1: Description]
[What the user should see + what files to change]

### [Change 2: Description]
[What the user should see + what files to change]

---

## Files to Create
- `backend/app/models/[new_file].py` — [description]
- `backend/app/routers/[new_file].py` — [description]
- `backend/app/services/[new_file].py` — [description]
- `backend/app/schemas/[new_file].py` — [description]
- `frontend/src/app/[new-page]/page.tsx` — [description]

## Files to Modify
- `backend/app/main.py` — register new router (one line)
- `frontend/src/lib/api.ts` — add new API methods
- `frontend/src/app/dashboard/page.tsx` — add new tab or display

## Do NOT Modify
- Any file not listed above
- `frontend/src/middleware.ts`
- `backend/app/security.py`
- `backend/app/config.py` (unless spec explicitly says to)
- Pixel code (`pixel/`)
- Slack bot code (`slack_bot/`)
- Docker configuration
- Deployment scripts
- Any dependency versions (package.json, requirements.txt)

---

## Database Changes
[New tables to create via Alembic migration, or "None — using existing tables"]

## Testing
[How to verify it works before merging]
