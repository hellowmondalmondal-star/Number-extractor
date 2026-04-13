# Number Extractor SaaS

Production-structured Django SaaS for extracting phone numbers from uploaded PDF, CSV, Excel, and image files.

## Stack

- Django + Django REST Framework
- JWT authentication with SimpleJWT
- Gmail SMTP-ready password reset and password change notifications
- SQLite for local development
- PostgreSQL-ready via `DATABASE_URL`
- `pandas`, `pdfplumber`, `pytesseract`, `Pillow`, `openpyxl`

## Apps

- `apps.accounts` - custom user model, roles, JWT auth, bootstrap/admin registration, password reset/change flows
- `apps.subscriptions` - Free and Pro plans with daily file/number limits
- `apps.uploads` - validated file uploads and upload history
- `apps.extraction` - readers, regex extraction, cleaning, dedupe, Excel export
- `apps.dashboard` - activity tracking, admin stats, agent dashboard summaries

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## API Endpoints

- `POST /api/register`
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
- `GET /api/admin/users`
- `GET /api/admin/stats`
- `GET /api/admin/activity`
- `GET /api/subscription/me`

## Bootstrap Flow

1. Call `POST /api/register` once with admin credentials to create the first admin account.
2. Log in with `POST /api/login` to get JWT tokens.
3. Create agent accounts using `POST /api/register` as an authenticated admin.
4. Upload a file, process it, and download the generated Excel result.

## Admin Subscription Management

- Django admin user creation lets you assign a subscription plan immediately.
- Django admin user editing lets you change plan, status, auto-renew, and expiry details from the user form.

## Gmail Password Reset

Set these environment variables to use Gmail for password reset and password-change emails:

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

Use PostgreSQL in Docker by updating `.env` with a Postgres `DATABASE_URL`.
