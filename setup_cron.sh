#!/bin/bash
# This script helps you set up the cron job for qbstats

# Get the absolute path to the qbstats directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# The cron job entry (runs at 00:00 UTC daily)
CRON_ENTRY="0 0 * * * cd $SCRIPT_DIR && /usr/bin/python3 qbstats.py >> $SCRIPT_DIR/cron.log 2>&1"

echo "Add this line to your crontab:"
echo ""
echo "$CRON_ENTRY"
echo ""
echo "To edit your crontab, run: crontab -e"
echo "Then paste the line above and save."
echo ""
echo "Note: This will run at 00:00 UTC every day and log output to cron.log"
