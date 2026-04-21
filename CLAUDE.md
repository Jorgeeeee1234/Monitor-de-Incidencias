# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the application

Requires Python 3.11+ and Ollama running locally with `qwen2.5:3b` pulled.

The project uses the **conda environment `proyecto_seguridad_env`**. Always activate it before running any command.

```bash
# Install dependencies (inside the conda env)
conda run -n proyecto_seguridad_env pip install -r requirements.txt

# Copy env config (first time only)
cp .env.example .env

# Start the server (must run from repo root — paths are relative)
conda run -n proyecto_seguridad_env python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server **must be started from the repo root** because `RuleEngineService` opens `config/rules.yml` and `IncidentService` writes to `logs/` using relative paths (no `__file__`-based resolution).

Ollama setup (Windows):
```powershell
winget install --id Ollama.Ollama -e
ollama pull qwen2.5:3b
```

## Architecture

The system is a FastAPI **security proxy for LLM conversations**. Every user message is analyzed for threats before and after being forwarded to a local Ollama model.

### Request flow for `POST /api/messages/analyze`

```
HTTP request
  → MessageService.analyze_message()
      → SessionService.get_by_key()          # validate session exists
      → RuleEngineService.detect(input)      # regex scan of user message
      → LLMService.generate_response()       # forward to Ollama
      → RuleEngineService.detect(output)     # regex scan of LLM response
      → IncidentService.create_incident()    # if either scan matched
      → db.commit()                          # single transaction for messages + incident
      → IncidentService.write_incident_log() # append to logs/incidents.jsonl (outside tx)
```

### Detection engine (`app/services/rule_engine_service.py`)

Rules live in `config/rules.yml` with two top-level keys:
- `detectors`: named detector configs (enabled flag, description, which ruleset to use)
- `rules`: named rulesets, each a list of `{name, pattern, category, severity, description}`

The engine has two modes:
- `detect()` — returns on the **first** matching rule (fast, not necessarily highest severity)
- `detect_multimatch()` — evaluates all rules, returns all matches plus `_select_top_match()` (highest `SEVERITY_RANK`)

To add a new detector: add an entry under `detectors:` in `rules.yml` pointing to an existing or new ruleset under `rules:`. No Python changes needed.

### Service instantiation

Services are instantiated per-request inside each controller via `Depends(get_db)`. `RuleEngineService` is constructed fresh each request (re-reads the YAML). There is no dependency injection container.

### Data persistence

- **SQLite** (`incidents.db`): managed by SQLAlchemy ORM. Schema is auto-created on startup via `Base.metadata.create_all()` in `main.py`.
- **JSONL** (`logs/incidents.jsonl`): append-only flat log written *after* the DB commit, so a write failure there does not roll back the incident.

### Frontend

Four HTML pages in `frontend/` are served directly as `FileResponse`. They use vanilla JS with `fetch()` against the REST API — no build step, no bundler. Static assets (CSS, JS files if any) are served from `/static` mapped to the `frontend/` directory.

## Commit style

- Messages in Spanish, using conventional commits format (`feat:`, `fix:`, `refactor:`...).
- Keep the subject line short (under 72 characters).
- Do **not** include `Co-Authored-By` lines or any mention of Claude/Anthropic.

## Key constraints

- **No authentication** on any endpoint — all API routes are open.
- **Confidence is hardcoded** at `0.90` for all regex matches (`_build_match_result`).
- **`detect()` returns first match**, not most severe. Use `detect_multimatch()` when severity ranking matters.
- Adding a rule to `rules.yml` under `AI_CLASSIFIER` ruleset has no effect — that detector is disabled (`enabled: false`).

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health
