# 1. PYTHON BACKEND
FROM python:3.10-slim AS backend
WORKDIR /app
COPY scraper/requirements.txt .

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc
RUN pip install -r requirements.txt
COPY scraper/src ./src

# Expose API Port
EXPOSE 8000
CMD ["python", "src/api.py"]