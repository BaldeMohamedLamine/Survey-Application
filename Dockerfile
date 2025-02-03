# Image de base Python
FROM python:3.12-slim-bookworm

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du projet
COPY . .

# Port d'exposition
EXPOSE 8000

# Définir la commande pour démarrer l'application avec Uvicorn
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8080"]
