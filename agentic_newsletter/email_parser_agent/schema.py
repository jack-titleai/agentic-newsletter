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
                    "body": {
                        "type": "string",
                        "description": "The full text content of the article"
                    },
                    "url": {
                        "type": ["string", "null"],
                        "description": "URL associated with the article, if present. Use null if no URL is found in the text."
                    },
                    "tags": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            {
                                "type": "null"
                            }
                        ],
                        "description": "Relevant tags or categories for the article. Use null if no tags can be inferred from the text."
                    },
                    "category": {
                        "type": "string",
                        "description": "The specific category assigned to this article from the predefined list of categories."
                    }
                },
                "required": ["title", "body", "url", "tags", "category"],
                "additionalProperties": False
            }
        }
    },
    "required": ["articles"],
    "additionalProperties": False
}
