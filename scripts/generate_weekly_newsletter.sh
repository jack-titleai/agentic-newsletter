#!/bin/bash
# Weekly Newsletter Generation Script
# This script automates the entire newsletter generation pipeline:
# 1. Syncs email sources from config to database
# 2. Downloads emails from all active sources
# 3. Parses emails to extract articles
# 4. Generates bullet points for articles from the past week
# 5. Creates a newsletter from the generated bullet points

set -e  # Exit immediately if a command exits with a non-zero status

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Timestamp for logging
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Starting weekly newsletter generation process"

# Calculate date range (past 7 days)
END_DATE=$(date +"%Y-%m-%d")
START_DATE=$(date -v-7d +"%Y-%m-%d")  # macOS syntax for 7 days ago

# Step 1: Sync email sources
echo "[$TIMESTAMP] Step 1: Syncing email sources"
python "$SCRIPT_DIR/sync_email_sources.py"

# Step 2: Download emails from sources
echo "[$TIMESTAMP] Step 2: Downloading emails from sources"
python "$SCRIPT_DIR/download_from_sources.py"

# Step 3: Parse emails
echo "[$TIMESTAMP] Step 3: Parsing emails to extract articles"
python "$SCRIPT_DIR/parse_emails.py"

# Step 4: Generate bullet points for the past week
echo "[$TIMESTAMP] Step 4: Generating bullet points (${START_DATE} to ${END_DATE})"
python "$SCRIPT_DIR/generate_bullet_points.py" --start-date "$START_DATE" --end-date "$END_DATE" --include-other-topics

# Step 5: Generate newsletter
echo "[$TIMESTAMP] Step 5: Generating newsletter"
python "$SCRIPT_DIR/generate_newsletter.py"

# Get the most recent newsletter file
NEWSLETTER_DIR="$PROJECT_ROOT/data/newsletters"
LATEST_NEWSLETTER=$(ls -t "$NEWSLETTER_DIR" | head -n1)

echo "[$TIMESTAMP] Newsletter generation complete!"
echo "Latest newsletter: $NEWSLETTER_DIR/$LATEST_NEWSLETTER"
