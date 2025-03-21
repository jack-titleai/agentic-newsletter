"""JSON schema definitions for the email parser agent."""

# Schema for article extraction
ARTICLE_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "description": "List of articles extracted from the newsletter",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title or heading of the article"
                    },
                    "summary": {
                        "type": "string",
                        "description": "A 1-2 sentence summary of what the article is about"
                    },
                    "body": {
                        "type": "string",
                        "description": "The full text content of the article"
                    },
                    "url": {
                        "type": ["string", "null"],
                        "description": "URL associated with the article, if present"
                    },
                    "tags": {
                        "type": "array",
                        "description": "Relevant tags or categories for the article",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["title", "summary", "body"],
                "additionalProperties": False
            }
        }
    },
    "required": ["articles"],
    "additionalProperties": False
}
