FROM python:3.11-slim

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier ton script et fichiers
COPY qbstats.py .
COPY config.example.json .

# Installer cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Créer dossier data (monté en volume ensuite)
RUN mkdir -p /data

# Ajouter la tâche cron (exécution à minuit tous les jours)
RUN echo "0 0 * * * python /app/qbstats.py >> /data/cron.log 2>&1" > /etc/cron.d/qbstats

# Appliquer droits et activer la crontab
RUN chmod 0644 /etc/cron.d/qbstats && crontab /etc/cron.d/qbstats

# Lancer cron en avant-plan pour que Docker garde le container actif
CMD ["cron", "-f"]
