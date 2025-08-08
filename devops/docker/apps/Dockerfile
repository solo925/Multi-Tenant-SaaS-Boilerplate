FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl netcat && \
    pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create non-root user for security
RUN useradd -ms /bin/bash appuser
USER appuser

COPY . /code/
