# Number Extractor SaaS

Admin-managed Django SaaS for extracting phone numbers from uploaded PDF, CSV, Excel, and image files.

## Product Model

- You manage everything from Django admin at `/admin/`.
- You create subscription-based user accounts from the backend.
- Users only use the product workspace at `/app/`.
- Users can log in, upload files, process extractions, and download Excel results.
- Admins can manage users, plans, uploads, results, and activity logs from the backend.

## Stack

- Django + Django REST Framework
- JWT authentication with SimpleJWT
- Django admin for account and subscription management
- SQLite for local development
- PostgreSQL-ready via `DATABASE_URL`
- WhiteNoise for static files
- `pandas`, `pdfplumber`, `pytesseract`, `Pillow`, `openpyxl`

## Main Apps

- `apps.accounts` - custom user model, admin-managed account creation, auth, password reset/change
- `apps.subscriptions` - Free and Pro plans with daily file and number limits
- `apps.uploads` - validated uploads and upload history
- `apps.extraction` - parsing, normalization, dedupe, and Excel export
- `apps.dashboard` - workspace summaries and activity tracking

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

- `/admin/` for backend control
- `/app/` for the user workspace

## Admin Workflow

1. Create the first admin with `python manage.py createsuperuser`.
2. Sign in to `/admin/`.
3. Create user accounts from the Users section.
4. Assign the subscription plan directly in the user form.
5. Give the user their login credentials for `/app/`.

`POST /api/register` is admin-only. Public self-signup is disabled.

Alternative bootstrap command:

```bash
python manage.py bootstrap_admin --email owner@example.com --password 'StrongPassword123!'
```

The Docker entrypoint also runs this command automatically when `ADMIN_EMAIL` and `ADMIN_PASSWORD` are present.

## Workspace/API Flow

- `POST /api/login`
- `POST /api/logout`
- `POST /api/change-password`
- `POST /api/forgot-password`
- `POST /api/reset-password`
- `GET /api/me`
- `POST /api/upload`
- `GET /api/uploads`
- `POST /api/process/<file_id>`
- `GET /api/results`
- `GET /api/download/<result_id>`
- `GET /api/dashboard/me`
- `GET /api/dashboard/activity`
- `GET /api/subscription/me`

Admin-only API endpoints:

- `POST /api/register`
- `GET /api/admin/users`
- `GET /api/admin/stats`
- `GET /api/admin/activity`

## Environment

Copy `.env.example` and update the values you need. Important settings:

- `DJANGO_ENV=production` for production mode
- `DJANGO_SECRET_KEY` with a real secret
- `DJANGO_ALLOWED_HOSTS` with your deployment domain(s)
- `DJANGO_CSRF_TRUSTED_ORIGINS` with your HTTPS origin(s)
- `DATABASE_URL` for PostgreSQL in production
- `SITE_URL` pointing to the deployed base URL
- `UPLOAD_PROCESSING_TIMEOUT_SECONDS` to control when a stuck processing job is marked failed
- `GUNICORN_TIMEOUT` to give longer-running extractions enough time to finish on your hosting plan

Production startup now refuses to use the SQLite fallback. If `DATABASE_URL` is missing or points to SQLite, the app will fail fast instead of booting with ephemeral data.

## Email

For Gmail-based password reset and password-change emails:

```env
SITE_URL=https://your-domain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-google-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
```

Use a Google App Password, not your normal Gmail password.

## Docker

```bash
docker compose up --build
```

The included `docker-compose.yml` runs Django with PostgreSQL by default.

## Render Deployment

This repo includes `render.yaml` for a Docker-based Render deploy.

Recommended flow:

1. Push the repo to GitHub.
2. Create the Render Blueprint from `render.yaml`.
3. When Render prompts for secret values, set:
   `SITE_URL`
   `DJANGO_ALLOWED_HOSTS`
   `DJANGO_CSRF_TRUSTED_ORIGINS`
   `ADMIN_EMAIL`
   `ADMIN_PASSWORD`
4. On first deploy, the container will run migrations and create or update the admin automatically.

Notes:

- The blueprint uses a `starter` web service and a persistent disk mounted at `/app/media` so uploads and generated Excel files survive redeploys.
- If you switch the service to a free plan, Render's filesystem becomes ephemeral and files under `/app/media` will not persist across redeploys or restarts.
- This app should use Render PostgreSQL in production. Do not rely on SQLite for deployed data.
- Keep `ADMIN_PASSWORD` only in Render environment variables. Do not commit it to git, `.env.example`, or `render.yaml`.

## GitHub Readiness

- `Procfile` is configured for Gunicorn.
- `.env.example` is sanitized for sharing.
- A GitHub Actions workflow runs `manage.py check` and `manage.py test`.
