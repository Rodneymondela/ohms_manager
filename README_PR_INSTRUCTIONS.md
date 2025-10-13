# PR: App Factory, Structure, Performance Hooks, and Tests Scaffold

This package contains ready-to-merge files to modernize the project structure and enable testing.

## Files to add
- `app/__init__.py` — app factory with `/health`, blueprint registration
- `app/config.py` — dev/test/prod configs and engine options
- `app/extensions.py` — db, migrate, login, cache, limiter
- `app/blueprints/core/` — example blueprint with cached `/` and rate-limited `/ping`
- `wsgi.py` — production entry for gunicorn
- `tests/` — pytest fixtures + smoke tests
- `.env.example` — safe defaults
- `.github/workflows/tests.yml` — CI (rename from GITHUB_ACTIONS_TESTS.yml)

## How to use
1. **Create a branch**:
   ```bash
   git checkout -b chore/app-factory-structure-tests
   ```
2. **Copy these files** into your repo (preserving paths).
   - Move `GITHUB_ACTIONS_TESTS.yml` to `.github/workflows/tests.yml`.
3. **Install missing dependencies** (if not already present):
   ```bash
   pip install flask-caching flask-limiter python-dotenv
   ```
4. **Run locally**:
   ```bash
   set FLASK_ENV=development
   flask run
   # or: python run.py (ensure it imports create_app or uses FLASK_APP=app:create_app)
   ```
5. **Run tests**:
   ```bash
   pytest -q --cov=app --cov-report=term-missing --cov-fail-under=70
   ```
6. **Update Procfile/render** to use gunicorn:
   ```
   web: gunicorn wsgi:app
   ```
   Render: set Start Command to `gunicorn wsgi:app`.

## Notes
- If the project already has `create_app()`, merge changes carefully—don’t overwrite.
- Add DB indexes via Alembic as you identify slow queries.
- Raise coverage thresholds as you add tests.
