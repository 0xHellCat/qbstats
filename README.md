# qBittorrent Stats Collector

Petit script pour récupérer des infos de qBittorrent via l’API WebUI et les sauvegarder chaque jour en JSON.

## Utilisation avec Docker

1. Copier `config.example.json` vers `config.json` et remplir vos infos.
2. Construire l’image :

   ```bash
   docker build -t qbstats .
