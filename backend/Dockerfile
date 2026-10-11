
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY backend/migrations/ ./migrations/
COPY backend/alembic.ini ./alembic.ini
COPY backend/import_scholarships.py ./import_scholarships.py

# Make the normalized data available to the importer
COPY scraper/scholarship_scraper/data/normalized_scholarships.json /app/scraper/scholarship_scraper/data/normalized_scholarships.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
