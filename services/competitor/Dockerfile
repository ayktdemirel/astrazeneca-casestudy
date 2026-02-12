FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src /app/src

# Libs will be mounted validation via docker-compose, but for build we might need them if we were building a standalone image.
# For this dev setup, we rely on volume mount for libs or copy them if needed for production build.
# We will assume volume mount for now as per docker-compose.yml

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
