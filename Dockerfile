FROM python:3.11-slim

# Créer un dossier pour l’app
WORKDIR /app

# Installer dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY qbstats.py .
COPY config.example.json .

# Point d’entrée
CMD ["python", "qbstats.py"]
