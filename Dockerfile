# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG CACHEBUST=1
RUN npm run build

# Stage 2: Python backend + serve built frontend
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-deu && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./static

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
EXPOSE ${PORT}
# Run Alembic migrations, then start the server.
# Seed categories/laws as well so a fresh DB has reference data.
CMD ["sh", "-c", "alembic upgrade head && python -c 'from app.database import seed_categories_and_laws; seed_categories_and_laws()' && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info"]
