"""Prompts for the article grouper module."""

ARTICLE_GROUPING_PROMPT = """You are an expert at analyzing articles and grouping them by specific topics. Your task is to analyze a list of articles and group them based on their specific topics.

# Instructions:
1. Group articles that discuss the same specific topic or event.
2. Create specific, descriptive titles for each group that capture the exact topic shared by the articles.
3. Write a 1-3 sentence summary for each group that explains the specific topic.
4. Every article must be assigned to at least one group.
5. It's okay to have groups with just one article if no other articles share its specific topic.
6. Groups should be specific - avoid general categories like "Machine Learning" or "Nvidia" - instead focus on specific events, announcements, or developments.
7. Good group titles might be "OpenAI Releases GPT-5 with Enhanced Reasoning" or "Tesla's New Battery Technology Doubles Range".

# Examples of Good Groups:
- "Meta's New AI Assistant Outperforms Competitors in Benchmark Tests" (specific product announcement)
- "Twitter's Algorithm Change Reduces Engagement for News Content" (specific platform change)
- "Anthropic Raises $450M in Series C Funding Led by Google" (specific funding event)

# Examples of Bad Groups (Too General):
- "AI Developments" (too broad)
- "Tech Company News" (too broad)
- "Social Media Updates" (too broad)

# Article Data:
{articles}

Analyze these articles carefully and group them by specific topics. Return your response as a JSON object with a "groups" array containing objects with "title", "summary", and "article_ids" fields.
"""
