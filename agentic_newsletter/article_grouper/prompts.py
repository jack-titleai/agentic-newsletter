"""Prompts for the article grouper module."""

ARTICLE_GROUPING_PROMPT = """You are an expert content curator for a newsletter about AI and technology.

Your task is to categorize a list of articles into predefined categories. Each article MUST be assigned to EXACTLY ONE category.

Follow these guidelines for consistent categorization:
1. Assign each article to the MOST APPROPRIATE category from the provided list.
2. Each article must be placed in exactly one category - no duplicates or omissions.
3. The category title in your response must EXACTLY match one of the provided category names - do not combine, modify, or create new category names.
4. Write a detailed summary (3-6 sentences) for each category that explains the common themes and topics of the articles in that category.
5. If a category has no relevant articles, do not include it in your response.
6. If an article doesn't fit well into any specific category, assign it to the most relevant category or to a general "other topics" category if provided.
7. DO NOT create your own category names or combine multiple categories with "and/or" - use ONLY the exact category names as provided.
8. CRITICAL: Ensure that the total number of articles assigned across all categories equals the total number of input articles. Each article ID must appear exactly once in your output.

{valid_ids_note}

The predefined categories are:
{categories}

The input is a list of articles with the following fields:
- id: A unique identifier for the article
- title: The title of the article
- summary: A summary of the article content
- source: The source of the article

Your output should be a JSON object with a "groups" field that contains a list of group objects. Each group object should have:
- title: The EXACT name of one of the predefined categories (copy and paste to ensure exactness)
- summary: A detailed summary (3-6 sentences) of what unifies the articles in this category
- article_ids: A list of article IDs that belong to this category

# Articles:
{articles}

Analyze these articles carefully and categorize each one into exactly one of the predefined categories. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""

ARTICLE_GROUPING_RETRY_PROMPT = """You are an expert content curator for a newsletter about AI and technology.

Your task is to categorize a list of articles into predefined categories. Each article MUST be assigned to EXACTLY ONE category.

Follow these guidelines for consistent categorization:
1. Assign each article to the MOST APPROPRIATE category from the provided list.
2. Each article must be placed in exactly one category - no duplicates or omissions.
3. The category title in your response must EXACTLY match one of the provided category names - do not combine, modify, or create new category names.
4. Write a detailed summary (3-6 sentences) for each category that explains the common themes and topics of the articles in that category.
5. If a category has no relevant articles, do not include it in your response.
6. If an article doesn't fit well into any specific category, assign it to the most relevant category or to a general "other topics" category if provided.
7. DO NOT create your own category names or combine multiple categories with "and/or" - use ONLY the exact category names as provided.
8. CRITICAL: Ensure that the total number of articles assigned across all categories equals the total number of input articles. Each article ID must appear exactly once in your output.

{valid_ids_note}

IMPORTANT CORRECTION NEEDED:
Your previous response had errors that need to be fixed:
{error_feedback}

The ONLY valid article IDs are: [{valid_ids_list}]
Do not include any article IDs that are not in this list.
Each article ID must appear exactly once in your output.

The predefined categories are:
{categories}

The input is a list of articles with the following fields:
- id: A unique identifier for the article
- title: The title of the article
- summary: A summary of the article content
- source: The source of the article

Your output should be a JSON object with a "groups" field that contains a list of group objects. Each group object should have:
- title: The EXACT name of one of the predefined categories (copy and paste to ensure exactness)
- summary: A detailed summary (3-6 sentences) of what unifies the articles in this category
- article_ids: A list of article IDs that belong to this category

# Articles:
{articles}

Analyze these articles carefully and categorize each one into exactly one of the predefined categories. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""
