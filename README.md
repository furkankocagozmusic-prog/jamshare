# JamShare Online MVP

Stack: Flask + Render + Supabase Postgres + Supabase Storage.

## 1. Supabase
Create a Free project. Current Free quota includes 500 MB database and 1 GB file storage.
Run `schema.sql` in Supabase SQL Editor.
Create a Storage bucket named `audio` and make it Public for this MVP.

Get:
- Project URL
- Service Role key (keep secret)

## 2. GitHub
Upload this folder to a GitHub repository.

## 3. Render
Create Web Service from the repository.
Build: `pip install -r requirements.txt`
Start: `gunicorn app:app`
Plan: Free

Environment variables:
SUPABASE_URL = your project URL
SUPABASE_SERVICE_ROLE_KEY = your service-role key
JAMSHARE_SECRET = a long random secret (Render can generate one)

## 4. Admin
After deployment, register a normal account.
In Supabase Table Editor, change that user's `role` from `user` to `admin`.

IMPORTANT:
Never put SUPABASE_SERVICE_ROLE_KEY into frontend code or GitHub.
