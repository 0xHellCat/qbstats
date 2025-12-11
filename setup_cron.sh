#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CRON_TZ="TZ=Europe/Paris"
CRON_JOB="0 0 * * * cd $SCRIPT_DIR && /usr/bin/python3 qbstats.py >> $SCRIPT_DIR/cron.log 2>&1"

echo "Nettoyage des anciennes entrées cron pour qbstats..."
CURRENT_CRON=$(crontab -l 2>/dev/null | grep -v "qbstats.py")

# Ajouter TZ si absent
if echo "$CURRENT_CRON" | grep -q "$CRON_TZ"; then
    echo "✔ TZ déjà présent."
else
    echo "➕ Ajout du timezone Europe/Paris..."
    CURRENT_CRON="$CRON_TZ
$CURRENT_CRON"
fi

# Ajouter la tâche
echo "➕ Ajout de la tâche qbstats à minuit..."
CURRENT_CRON="$CURRENT_CRON
$CRON_JOB"

# Installer le nouveau crontab
echo "$CURRENT_CRON" | crontab -

echo ""
echo "🎉 Cron mis à jour sans doublons !"
