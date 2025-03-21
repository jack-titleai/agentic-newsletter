# Agentic Newsletter

An agentic workflow (using langgraph) that parses email newsletters from Gmail and develops a single "super" newsletter containing summaries of the most prevalent and relevant topics.

## Features

- Download emails from specific Gmail accounts
- Store emails in a SQLite database
- Track email sources and download history
- (Future) Parse and analyze newsletter content
- (Future) Generate summarized "super" newsletter

## Installation
You can use the `setup.sh` script to set up the environment, or you can do it manually:

```bash
# Create a conda environment
conda create -n agentic-newsletter python=3.10
conda activate agentic-newsletter

# Install the package
pip install -e .
```

## Gmail API Setup

To use this package, you need to set up the Gmail API:

1. Create a Google Cloud project:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API for your project

2. Create OAuth credentials:
   - In your project, go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" and select "OAuth client ID"
   - Set the application type to "Desktop app"
   - Name your OAuth client
   - Click "Create"

3. Set up the OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type (unless you have a Google Workspace)
   - Fill in the required information (app name, user support email, developer contact information)
   - Add the necessary scopes (Gmail API with read access)
   - **Important**: Add your email address as a test user in the "Test users" section
   - Save the changes

4. Download the credentials:
   - After creating the OAuth client ID, download the JSON file
   - Save this file as `credentials.json` in the root directory of this project

5. Update the `.env` file:
   - Make sure your `.env` file has the correct path to your credentials file:
   ```
   GMAIL_CREDENTIALS_FILE=credentials.json
   ```

> **Note**: Your app will be in "Testing" mode, which means only test users you've added can authenticate with it. When you first run the app, you'll need to authorize it using one of these test user accounts.

## OpenAI API Setup

To use the email parser agent, you need an OpenAI API key:

1. Create an OpenAI account:
   - Go to [OpenAI's website](https://openai.com/)
   - Sign up for an account if you don't have one

2. Generate an API key:
   - Go to the [API keys page](https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Give your key a name (e.g., "Agentic Newsletter")
   - Copy the API key (note: you won't be able to see it again)

3. Add the API key to your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

> **Note**: The email parser agent uses the GPT-4o model by default, which incurs usage costs. Make sure you have billing set up in your OpenAI account. The module uses OpenAI's structured output feature to ensure consistent and reliable JSON responses.

## Configuration

Create a `.env` file in the root directory with the following variables:

```
GMAIL_CREDENTIALS_FILE=credentials.json
OPENAI_API_KEY=your_openai_api_key_here
```

If you saved your credentials file in a different location or with a different name, update the path accordingly.

## Usage

```python
from agentic_newsletter.email_downloader import EmailDownloader

# Initialize the downloader
downloader = EmailDownloader()

# Add email sources
downloader.add_email_source("newsletter@example.com")

# Download emails
downloader.download_emails()
```

## Email Parser Agent Usage

see examples/parse_newsletter.py, no further instruction is needed other than looking at the code here

## Database Integration

The system now includes database integration for storing parsed articles. Two new tables have been added:

1. `parsed_articles` - Stores articles extracted from emails
2. `parser_logs` - Tracks parsing operations with duration and article count statistics

### Parsing Unparsed Emails

To parse emails that have been downloaded but not yet parsed, use the `parse_emails.py` script:

```bash
# Parse all unparsed emails
python scripts/parse_emails.py

# Parse with verbose logging
python scripts/parse_emails.py -v

# Parse only the first 5 unparsed emails
python scripts/parse_emails.py --limit 5

# Dry run (don't save to database)
python scripts/parse_emails.py --dry-run

```

### Database Migration

If you need to migrate the database schema after updates, use the migration scripts provided:

```bash
# Migrate parser_logs table (removes average and median article counts)
python scripts/migrate_parser_logs.py

# Run with verbose logging
python scripts/migrate_parser_logs.py -v

# Dry run (don't modify the database)
python scripts/migrate_parser_logs.py --dry-run
```
