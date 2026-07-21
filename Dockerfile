# Dockerfile for Benton Drones Lead Ingest
# Works for local Docker testing and Railway deployment.
#
# Build:  docker build -t benton-drones .
# Run:    docker run -p 8000:8000 -e ADMIN_PASSWORD=secret benton-drones
#
# The app is pure Python stdlib with SQLite (default) or PostgreSQL
# (when DATABASE_URL is set).  The pip dependencies are the optional fpdf2
# (for true PDF export) and psycopg2-binary (for PostgreSQL), listed in
# requirements.txt.

FROM python:3.11-slim

# --- Production-safe defaults -------------------------------------------------
# HOST must be 0.0.0.0 so the server binds to all interfaces inside the
# container.  PORT is left unset here so Railway can inject its own value
# at runtime; for local `docker run` the server defaults to 8000.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0

WORKDIR /app

# Install PostgreSQL client libraries (needed if switching from psycopg2-binary
# to source-built psycopg2; psycopg2-binary bundles its own libpq but this keeps
# the image flexible).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application.
COPY . .

# Create the data directory for SQLite, add a non-root user, and hand
# over ownership so the app can write to /app/data without running as root.
RUN mkdir -p /app/data \
    && useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose the default port (Railway overrides via the PORT env var at runtime).
EXPOSE 8000

CMD ["python", "-m", "lead_ingest.server"]
