# Project setup

This project has two main parts:

- Backend: Django REST API with GIS and ML features
- Frontend: Next.js application

## Requirements

Before you start, make sure you have:

- Python 3.12
- pip or pipenv
- Node.js 20 or 22
- npm
- Docker Desktop (optional but recommended)
- PostgreSQL/PostGIS if you do not want to use Docker

## Environment variables

The app expects a root `.env` file for the backend and Docker setup. Keep it in the project root so the backend and container can read it.

For the frontend, create a `frontend/dryad/.env.local` file with:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

If you run the frontend through Docker, the container passes the API URL through its environment settings, so this file is not usually required in that mode.

## Backend setup

From the project root, go into the backend folder:

```bash
cd backend
```

### Option 1: Local Python environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install the dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you prefer Pipenv, use:

```bash
pip install pipenv
pipenv install
```

Apply the database migrations and start the server:

```bash
pipenv run python manage.py migrate
pipenv run python manage.py runserver 0.0.0.0:8000
```

The backend should be available at:

```text
http://localhost:8000
```

### Option 2: Docker

From the project root:

```bash
docker compose up --build
```

This starts the database, backend, and frontend together.

## Frontend setup

Go to the frontend app directory:

```bash
cd frontend/dryad
```

Install dependencies:

```bash
npm install
```

Then start the app in development mode:

```bash
npm run dev
```

Open the frontend in the browser:

```text
http://localhost:3000
```

For a production build:

```bash
npm run build
npm run start
```

## Running both together

A simple workflow is:

1. Start the backend
2. Start the frontend in a second terminal
3. Open the frontend in the browser

Example commands from the project root:

```bash
cd backend
pipenv run python manage.py runserver 0.0.0.0:8000
```

In another terminal:

```bash
cd frontend/dryad
npm install
npm run dev
```

## Docker quick start

If you want the simplest setup, run:

```bash
cd "C:\Users\User\Documents\GitHub\Dryad\Fullstack Web App"
docker compose up --build
```

Then open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api

## Notes

- The backend uses Django and expects a working database connection.
- If you are running on Windows and GDAL or geospatial dependencies fail, install the OSGeo4W packages and make sure `OSGEO4W_BIN_PATH` in the `.env` file points to the correct installation folder.
- If API requests fail in the frontend, check that `NEXT_PUBLIC_API_URL` points to the backend correctly.
